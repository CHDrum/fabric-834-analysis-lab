import copy
import json
from pathlib import Path

import pytest

from data.generate_synthetic import generate
from src.parse_834 import EnrollmentParser
from tests.rule_oracle import evaluate


ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT / "config" / "rules.json").read_text(encoding="utf-8"))
EXPECTED = [
    (1, "DUPLICATE_MEMBER", ""), (1, "MULTIPLE_SUBSCRIBERS", ""),
    (2, "AMBIGUOUS_SUBSCRIBER", ""), (2, "OVERAGE_DEPENDENT", ""),
    (4, "DEPENDENT_PLAN_DIFFERENCE", "HLT"), (4, "DEPENDENT_PLAN_DIFFERENCE", "PDG"),
    (5, "MISSING_DOB", ""), (5, "MISSING_EMPLOYEE_ID", ""), (5, "MISSING_SSN", ""),
    (7, "MEDICAL_RX_MISMATCH", ""), (8, "DEPENDENT_PLAN_DIFFERENCE", "PDG"),
    (9, "UNKNOWN_PLAN", "HLT"), (10, "ORPHAN_DEPENDENT", ""), (12, "MISSING_SSN", ""),
    (13, "DUPLICATE_MEMBER", ""), (13, "MULTIPLE_SUBSCRIBERS", ""),
]


def parsed(tmp_path, members=2, adversarial=False):
    path = tmp_path / "source.edi"
    generate(path, members, adversarial=adversarial)
    batches = list(EnrollmentParser(path).batches())
    return ([member for batch in batches for member in batch["members"]],
            [election for batch in batches for election in batch["coverage"]])


def test_hand_checked_exception_set(tmp_path):
    members, coverage = parsed(tmp_path, 13, True)
    assert evaluate(members, coverage, RULES) == EXPECTED
    assert len({ordinal for ordinal, _, _ in EXPECTED}) == 10


def test_published_sample_contract():
    import hashlib

    sample = ROOT / "data" / "sample" / "synthetic_834.edi"
    expected = json.loads(sample.with_name("expected.json").read_text(encoding="utf-8"))
    assert expected["sha256"] == hashlib.sha256(sample.read_bytes()).hexdigest()
    assert expected["file_bytes"] == sample.stat().st_size
    parser = EnrollmentParser(sample)
    batches = list(parser.batches())
    members = [member for batch in batches for member in batch["members"]]
    coverage = [election for batch in batches for election in batch["coverage"]]
    assert evaluate(members, coverage, RULES) == [tuple(finding) for finding in expected["findings"]] == EXPECTED
    for field in ("member_count", "subscriber_count", "dependent_count", "coverage_count"):
        assert parser.manifest[field] == expected[field]
    assert parser.manifest["issue_count"] == expected["parse_issue_count"]
    assert expected["exception_count"] == len(EXPECTED)
    assert expected["affected_members"] == len({ordinal for ordinal, _, _ in EXPECTED})
    assert expected["rule_version"] == RULES["rule_version"]
    assert expected["as_of_date"] == RULES["as_of_date"]


def test_rule_sql_checks_existing_version_contents():
    from solution.build_rules import build

    content = build(RULES)
    assert content.count("RULE_VERSION_IMMUTABLE") == 6
    assert content.count(" EXCEPT ") == 12
    assert "ROLLBACK TRANSACTION" in content
    changed = copy.deepcopy(RULES)
    changed["child_age_limit"] = 27
    assert build(changed) != content


@pytest.mark.parametrize("birthday,expected", [("2001-01-01", True), ("2001-01-02", False), ("2000-12-31", True)])
def test_exact_age_boundary(tmp_path, birthday, expected):
    members, coverage = parsed(tmp_path)
    members[1]["dob"] = birthday
    findings = evaluate(members, coverage, RULES)
    assert ((2, "OVERAGE_DEPENDENT", "") in findings) is expected


def test_role_specific_fields_and_exemptions(tmp_path):
    members, coverage = parsed(tmp_path)
    assert evaluate(members, coverage, RULES) == []
    members[1]["dob"] = "1990-01-01"
    rules = copy.deepcopy(RULES)
    rules["exempt_relationships"] = ["19"]
    assert evaluate(members, coverage, rules) == []
    rules["required_dependent_fields"].append("employee_id")
    assert evaluate(members, coverage, rules) == [(2, "MISSING_EMPLOYEE_ID", "")]


def test_coverage_duplicates_unknowns_and_periods(tmp_path):
    members, coverage = parsed(tmp_path)
    coverage.append(copy.deepcopy(coverage[0]))
    assert (1, "DUPLICATE_COVERAGE", "HLT") in evaluate(members, coverage, RULES)
    assert (1, "AMBIGUOUS_COVERAGE", "HLT") in evaluate(members, coverage, RULES)
    coverage.pop()
    coverage[1]["end_date"] = "2026-12-31"
    assert (1, "RX_COVERAGE_MISSING", "") in evaluate(members, coverage, RULES)
    coverage[0]["plan_id"] = "UNMAPPED"
    assert (1, "UNKNOWN_PLAN", "HLT") in evaluate(members, coverage, RULES)