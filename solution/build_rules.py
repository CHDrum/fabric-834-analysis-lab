"""Generate versioned Warehouse reference rows from the synthetic rule contract."""

import argparse
import json
from datetime import date
from pathlib import Path


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def build(rules):
    if rules.get("synthetic_only") is not True or not rules["rule_version"].startswith("SYNTHETIC-"):
        raise ValueError("This workshop requires an explicit synthetic rule version")
    date.fromisoformat(rules["as_of_date"])
    if not 0 < rules["child_age_limit"] < 100:
        raise ValueError("Invalid illustrative age limit")
    for fields in (rules["required_subscriber_fields"], rules["required_dependent_fields"]):
        if not set(fields) <= {"ssn", "dob", "employee_id"} or len(fields) != len(set(fields)):
            raise ValueError("Unknown or duplicated required field")
    version = rules["rule_version"]
    rows = {
        "ref_settings": [(version, rules["as_of_date"], rules["child_age_limit"], rules["medical_benefit"], rules["rx_benefit"])],
        "ref_fields": [(version, role, field) for role, fields in [(1, rules["required_subscriber_fields"]), (0, rules["required_dependent_fields"])] for field in fields],
        "ref_relationships": [(version, relation, int(relation in rules["exempt_relationships"])) for relation in sorted(set(rules["child_relationships"]) | set(rules["exempt_relationships"]))],
        "ref_benefits": [(version, benefit) for benefit in rules["comparable_benefits"]],
        "ref_plans": [(version, plan["benefit"], plan["plan_id"]) for plan in rules["plans"]],
        "ref_pairs": [(version, medical, rx) for medical, rx in rules["allowed_medical_rx_pairs"]],
    }
    fields = {
        "ref_settings": "rule_version, as_of_date, child_age_limit, medical_benefit, rx_benefit",
        "ref_fields": "rule_version, is_subscriber, field_name",
        "ref_relationships": "rule_version, relationship, is_exempt",
        "ref_benefits": "rule_version, benefit",
        "ref_plans": "rule_version, benefit, plan_id",
        "ref_pairs": "rule_version, medical_plan, rx_plan",
    }
    statements = [f"IF EXISTS (SELECT 1 FROM dbo.ref_settings WHERE rule_version = {literal(version)})", "BEGIN"]
    for table, values in rows.items():
        actual = f"SELECT {fields[table]} FROM dbo.{table} WHERE rule_version = {literal(version)}"
        mismatch = f"(SELECT COUNT_BIG(*) FROM dbo.{table} WHERE rule_version = {literal(version)}) <> {len(values)}"
        if values:
            supplied = ",\n".join("(" + ", ".join(literal(value) for value in row) + ")" for row in values)
            expected = f"SELECT * FROM (VALUES {supplied}) AS expected ({fields[table]})"
            mismatch += f" OR EXISTS ({actual} EXCEPT {expected}) OR EXISTS ({expected} EXCEPT {actual})"
        statements.append(f"IF {mismatch}\nTHROW 52101, 'RULE_VERSION_IMMUTABLE: use a new version for changed rules.', 1;")
    statements.extend(["END", "ELSE", "BEGIN", "BEGIN TRY", "BEGIN TRANSACTION;"])
    for table, values in rows.items():
        if values:
            statements.append(f"INSERT INTO dbo.{table} VALUES\n" + ",\n".join("(" + ", ".join(literal(value) for value in row) + ")" for row in values) + ";")
    return "\n".join(statements + ["COMMIT TRANSACTION;", "END TRY", "BEGIN CATCH",
        "IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;", "THROW;", "END CATCH", "END;", ""])


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=root / "config/rules.json")
    parser.add_argument("--output", type=Path, default=root / "sql/02_reference_rules.sql")
    arguments = parser.parse_args()
    arguments.output.write_text(build(json.loads(arguments.config.read_text(encoding="utf-8"))), encoding="utf-8")
    print(f"Generated versioned rules: {arguments.output}")