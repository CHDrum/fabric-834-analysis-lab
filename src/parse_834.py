"""Bounded streaming adapter for the documented synthetic 834 teaching profile."""

import hashlib
import uuid
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from pyx12.x12file import X12Reader


MEMBER_COLUMNS = ("file_id", "attempt_id", "member_ordinal", "member_id", "family_id", "is_subscriber",
                  "relationship", "dob", "has_ssn", "ssn_last4", "employee_id", "interchange_control",
                  "group_control", "transaction_control", "source_segment")
COVERAGE_COLUMNS = ("file_id", "attempt_id", "member_ordinal", "coverage_ordinal", "benefit", "plan_id",
                    "coverage_level", "effective_date", "end_date", "source_segment")
ISSUE_COLUMNS = ("file_id", "attempt_id", "member_ordinal", "source_segment", "issue_code", "severity")
MANIFEST_COLUMNS = ("file_id", "attempt_id", "file_name", "file_bytes", "parser_version", "rule_version",
                    "started_at", "finished_at", "status", "member_count", "subscriber_count",
                    "dependent_count", "coverage_count", "issue_count", "failure_code")


class ParseFailure(ValueError):
    pass


def file_hash(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class EnrollmentParser:
    def __init__(self, source, rule_version="SYNTHETIC-2027-v1", batch_size=5000, attempt_id=None):
        self.source = Path(source)
        if not 1 <= batch_size <= 10000:
            raise ValueError("batch_size must be between 1 and 10000 members")
        if version("pyx12") != "4.0.0":
            raise ValueError("This workshop is tested with pyx12==4.0.0")
        self.batch_size = batch_size
        self.manifest = dict(zip(MANIFEST_COLUMNS, [""] * len(MANIFEST_COLUMNS), strict=True))
        self.manifest.update({"file_id": file_hash(self.source), "attempt_id": attempt_id or str(uuid.uuid4()),
                              "file_name": self.source.name, "file_bytes": self.source.stat().st_size,
                              "parser_version": version("pyx12"), "rule_version": rule_version,
                              "started_at": utc_now(), "status": "Running", "member_count": 0,
                              "subscriber_count": 0, "dependent_count": 0, "coverage_count": 0, "issue_count": 0})
        self.used = False

    def batches(self):
        if self.used:
            raise RuntimeError("Create a new parser instance for each attempt")
        self.used = True
        batch = {"members": [], "coverage": [], "issues": []}
        current = None
        current_coverage = []
        controls = {"interchange_control": "", "group_control": "", "transaction_control": ""}
        segment_number = 0
        envelope_open = False
        transaction_open = False
        closed_interchanges = 0
        member_segment_count = 0

        def issue(code):
            batch["issues"].append({"file_id": self.manifest["file_id"], "attempt_id": self.manifest["attempt_id"],
                                    "member_ordinal": current["member_ordinal"] if current else 0,
                                    "source_segment": segment_number, "issue_code": code, "severity": "Review"})
            self.manifest["issue_count"] += 1

        def parse_date(value, code):
            if not value:
                return ""
            try:
                return datetime.strptime(value, "%Y%m%d").date().isoformat()
            except ValueError:
                issue(code)
                return ""

        def finish_member():
            nonlocal current, current_coverage
            if current is not None:
                if not current["member_id"] or not current["family_id"]:
                    raise ParseFailure("MISSING_PROFILE_LINKAGE")
                batch["members"].append(current)
                batch["coverage"].extend(current_coverage)
                self.manifest["member_count"] += 1
                role = "subscriber_count" if current["is_subscriber"] else "dependent_count"
                self.manifest[role] += 1
                self.manifest["coverage_count"] += len(current_coverage)
                current, current_coverage = None, []

        try:
            with self.source.open("r", encoding="ascii", newline="") as source, X12Reader(source) as reader:
                for segment in reader:
                    segment_number += 1
                    tag = segment.get_seg_id()
                    if reader.pop_errors():
                        raise ParseFailure("ENVELOPE_VALIDATION_FAILED")
                    if tag == "ISA":
                        if envelope_open:
                            raise ParseFailure("NESTED_INTERCHANGE")
                        envelope_open = True
                        controls["interchange_control"] = segment.get_value("ISA13")
                    elif tag == "GS":
                        if segment.get_value("GS08") != "005010X220A1":
                            raise ParseFailure("UNSUPPORTED_IMPLEMENTATION_VERSION")
                        controls["group_control"] = segment.get_value("GS06")
                    elif tag == "ST":
                        if transaction_open or segment.get_value("ST01") != "834":
                            raise ParseFailure("UNSUPPORTED_OR_NESTED_TRANSACTION")
                        if segment.get_value("ST03") != "005010X220A1":
                            raise ParseFailure("UNSUPPORTED_IMPLEMENTATION_VERSION")
                        transaction_open = True
                        controls["transaction_control"] = segment.get_value("ST02")
                    elif tag == "INS":
                        if not transaction_open:
                            raise ParseFailure("MEMBER_OUTSIDE_TRANSACTION")
                        finish_member()
                        if len(batch["members"]) >= self.batch_size:
                            yield batch
                            batch = {"members": [], "coverage": [], "issues": []}
                        indicator = segment.get_value("INS01")
                        if indicator not in ("Y", "N"):
                            raise ParseFailure("INVALID_SUBSCRIBER_INDICATOR")
                        current = {column: "" for column in MEMBER_COLUMNS}
                        current.update({"file_id": self.manifest["file_id"], "attempt_id": self.manifest["attempt_id"],
                                        "member_ordinal": self.manifest["member_count"] + 1, "is_subscriber": int(indicator == "Y"),
                                        "relationship": segment.get_value("INS02"), "has_ssn": 0,
                                        "source_segment": segment_number, **controls})
                        member_segment_count = 0
                    elif tag == "SE":
                        finish_member()
                        if not transaction_open:
                            raise ParseFailure("UNEXPECTED_TRANSACTION_TRAILER")
                        transaction_open = False
                    elif tag == "IEA":
                        if transaction_open or not envelope_open:
                            raise ParseFailure("UNEXPECTED_INTERCHANGE_TRAILER")
                        envelope_open = False
                        closed_interchanges += 1
                    elif current is not None:
                        member_segment_count += 1
                        if member_segment_count > 2000:
                            raise ParseFailure("MEMBER_SEGMENT_LIMIT")
                        if tag == "REF" and not current_coverage:
                            qualifier, value = segment.get_value("REF01"), segment.get_value("REF02")
                            field = {"0F": "family_id", "17": "member_id", "ZZ": "employee_id"}.get(qualifier)
                            if field:
                                if current[field]:
                                    raise ParseFailure("REPEATED_PROFILE_IDENTIFIER")
                                current[field] = value
                        elif tag == "NM1" and segment.get_value("NM101") == "IL":
                            ssn = segment.get_value("NM109") if segment.get_value("NM108") == "34" else ""
                            valid = len(ssn) == 9 and ssn.isdigit()
                            current["has_ssn"] = int(valid)
                            current["ssn_last4"] = ssn[-4:] if valid else ""
                            if ssn and not valid:
                                issue("INVALID_SSN_FORMAT")
                        elif tag == "DMG":
                            if segment.get_value("DMG01") != "D8":
                                issue("UNSUPPORTED_DOB_FORMAT")
                            else:
                                current["dob"] = parse_date(segment.get_value("DMG02"), "INVALID_DOB")
                        elif tag == "HD":
                            if len(current_coverage) >= 256:
                                raise ParseFailure("MEMBER_COVERAGE_LIMIT")
                            coverage = {column: "" for column in COVERAGE_COLUMNS}
                            coverage.update({"file_id": self.manifest["file_id"], "attempt_id": self.manifest["attempt_id"],
                                             "member_ordinal": current["member_ordinal"], "coverage_ordinal": len(current_coverage) + 1,
                                             "benefit": segment.get_value("HD03"), "plan_id": segment.get_value("HD04"),
                                             "coverage_level": segment.get_value("HD05"), "source_segment": segment_number})
                            current_coverage.append(coverage)
                        elif tag == "DTP" and current_coverage:
                            qualifier = segment.get_value("DTP01")
                            field = {"348": "effective_date", "349": "end_date"}.get(qualifier)
                            if field:
                                if segment.get_value("DTP02") != "D8":
                                    issue("UNSUPPORTED_COVERAGE_DATE_FORMAT")
                                else:
                                    current_coverage[-1][field] = parse_date(segment.get_value("DTP03"), "INVALID_COVERAGE_DATE")
                if reader.pop_errors():
                    raise ParseFailure("ENVELOPE_VALIDATION_FAILED")
            if envelope_open or transaction_open or not closed_interchanges or current is not None:
                raise ParseFailure("TRUNCATED_ENVELOPE")
            if not self.manifest["member_count"]:
                raise ParseFailure("NO_MEMBERS")
            if file_hash(self.source) != self.manifest["file_id"]:
                raise ParseFailure("SOURCE_CHANGED_DURING_PARSE")
            self.manifest.update({"status": "Succeeded", "finished_at": utc_now()})
            if any(batch.values()):
                yield batch
        except Exception as error:
            code = str(error) if isinstance(error, ParseFailure) else "PARSER_OR_IO_FAILURE"
            self.manifest.update({"status": "Failed", "failure_code": code, "finished_at": utc_now()})
            raise ParseFailure(code) from error