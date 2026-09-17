import io
from importlib.metadata import version
from importlib.resources import files

import pytest
from pyx12.x12file import X12Reader


def tiny_834(element="*", terminator="~"):
    header = [
        "ISA", "00", " " * 10, "00", " " * 10, "ZZ",
        "SYNTHSENDER".ljust(15), "ZZ", "SYNTHRECEIVER".ljust(15),
        "260916", "1200", "^", "00501", "000000001", "0", "T", ":",
    ]
    transaction = [
        "ST*834*0001*005010X220A1",
        "BGN*00*SYNTHETIC-ONLY*20260916*1200",
        "N1*P5*SYNTHETIC EMPLOYER*FI*900000001",
        "N1*IN*SYNTHETIC HEALTH PLAN*FI*900000002",
        "INS*Y*18*030*XN*A***FT",
        "REF*0F*F0001",
        "REF*17*S0001",
        "REF*ZZ*EMP0001",
        "NM1*IL*1*SYNTHETIC*SUBSCRIBER****34*900000001",
        "DMG*D8*19800101*U",
        "HD*030**HLT*MED-A*EMP",
        "DTP*348*D8*20270101",
        "INS*N*19*030*XN*A",
        "REF*0F*F0001",
        "REF*17*D0001",
        "NM1*IL*1*SYNTHETIC*DEPENDENT****34*900000002",
        "DMG*D8*20100101*U",
        "HD*030**HLT*MED-A*CHD",
        "DTP*348*D8*20270101",
    ]
    transaction.append(f"SE*{len(transaction) + 1}*0001")
    segments = [element.join(header)]
    segments.extend(
        segment.replace("*", element)
        for segment in [
            "GS*BE*SYNTHSENDER*SYNTHRECEIVER*20260916*1200*1*X*005010X220A1",
            *transaction, "GE*1*1", "IEA*1*000000001",
        ]
    )
    return terminator.join(segments) + terminator


def test_pinned_distribution_contains_834_map():
    assert version("pyx12") == "4.0.0"
    assert files("pyx12").joinpath("map", "834.5010.X220.A1.xml").is_file()


@pytest.mark.parametrize("element,terminator", [("*", "~"), ("|", "!")])
def test_reader_handles_member_loops_without_newlines(element, terminator):
    source = tiny_834(element, terminator)
    assert "\n" not in source
    assert len(source.split(terminator)[0]) == 105
    members = []
    identifiers = []
    errors = []
    with X12Reader(io.StringIO(source)) as reader:
        for segment in reader:
            if segment.get_seg_id() == "INS":
                members.append((segment.get_value("INS01"), segment.get_value("INS02")))
            if segment.get_seg_id() == "REF" and segment.get_value("REF01") == "17":
                identifiers.append(segment.get_value("REF02"))
            errors.extend(reader.pop_errors())
    assert members == [("Y", "18"), ("N", "19")]
    assert identifiers == ["S0001", "D0001"]
    assert errors == []


def test_streaming_adapter_preserves_lineage_and_bounded_batches(tmp_path):
    from data.generate_synthetic import generate
    from src.parse_834 import EnrollmentParser, file_hash

    path = tmp_path / "source.edi"
    generate(path, members=13)
    before = file_hash(path)
    parser = EnrollmentParser(path, batch_size=3, attempt_id="test-attempt")
    batches = list(parser.batches())
    assert max(len(batch["members"]) for batch in batches) <= 3
    members = [member for batch in batches for member in batch["members"]]
    coverage = [election for batch in batches for election in batch["coverage"]]
    assert len(members) == 13
    assert len(coverage) == 26
    assert members[0]["member_id"] == "S0001"
    assert members[1]["family_id"] == members[0]["family_id"] == "F0001"
    assert members[1]["dob"] == "2001-01-01"
    assert members[4]["has_ssn"] == 0 and members[4]["dob"] == ""
    assert coverage[0]["effective_date"] == "2027-01-01"
    assert {election["benefit"] for election in coverage} == {"HLT", "PDG"}
    assert parser.manifest["status"] == "Succeeded"
    assert parser.manifest["subscriber_count"] == 7
    assert parser.manifest["dependent_count"] == 6
    assert file_hash(path) == before


@pytest.mark.parametrize("mutation", [
    lambda text: text.rsplit("IEA", 1)[0],
    lambda text: text.replace("GE*1*1", "GE*2*1"),
    lambda text: text.replace("005010X220A1", "005010X222A1"),
    lambda text: text.replace("REF*17*S0001~", ""),
])
def test_invalid_envelopes_or_profile_never_succeed(tmp_path, mutation):
    from src.parse_834 import EnrollmentParser, ParseFailure

    path = tmp_path / "bad.edi"
    path.write_text(mutation(tiny_834()), encoding="ascii")
    parser = EnrollmentParser(path, batch_size=1)
    with pytest.raises(ParseFailure):
        list(parser.batches())
    assert parser.manifest["status"] == "Failed"


def test_alternate_delimiters_and_multiple_interchanges(tmp_path):
    from src.parse_834 import EnrollmentParser

    path = tmp_path / "two.edi"
    second = tiny_834("|", "!").replace("000000001", "000000002")
    path.write_text(tiny_834("|", "!") + second, encoding="ascii")
    parser = EnrollmentParser(path)
    batches = list(parser.batches())
    assert sum(len(batch["members"]) for batch in batches) == 4
    assert parser.manifest["status"] == "Succeeded"


def test_published_malformed_fixture_fails_without_mutating_source():
    from pathlib import Path
    from src.parse_834 import EnrollmentParser, ParseFailure, file_hash

    path = Path(__file__).resolve().parents[1] / "data" / "sample" / "synthetic_malformed_834.edi"
    original_hash = file_hash(path)
    parser = EnrollmentParser(path, batch_size=1)
    with pytest.raises(ParseFailure):
        list(parser.batches())
    assert parser.manifest["status"] == "Failed"
    assert parser.manifest["failure_code"]
    assert file_hash(path) == original_hash