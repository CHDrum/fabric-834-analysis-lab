import json
from pathlib import Path

from solution.build_pipeline import build
from solution.build_rules import build as build_rules


def test_failure_audit_does_not_publish_partial_members():
    activities = build("workspace", "lakehouse", "warehouse", "endpoint", "notebook")["properties"]["activities"]
    assert activities[1]["dependsOn"] == [{"activity": "Parse834", "dependencyConditions": ["Succeeded"]}]
    members = next(activity for activity in activities if activity["name"] == "Copy_members")
    assert {dependency["activity"] for dependency in members["dependsOn"]} == {"Record_attempt", "Parse834"}
    assert all(dependency["dependencyConditions"] == ["Succeeded"] for dependency in members["dependsOn"])
    assert activities[-1]["dependsOn"][0]["activity"] == "Load_issues"
    for name in ("coverage", "issues"):
        activity = next(item for item in activities if item["name"] == f"Load_{name}")
        assert activity["type"] == "IfCondition"
        assert activity["typeProperties"]["ifTrueActivities"][0]["name"] == f"Copy_{name}"
        empty = activity["typeProperties"]["ifFalseActivities"][0]
        assert empty["dependsOn"] == []
        assert empty["typeProperties"]["scripts"][0]["text"] == f"DELETE FROM dbo.stg_{name};"
    record = next(item for item in activities if item["name"] == "Record_attempt")
    assert record["typeProperties"]["scripts"][0]["type"] == "Query"


def test_reference_rules_derive_from_config():
    rules = json.loads((Path(__file__).resolve().parents[1] / "config/rules.json").read_text(encoding="utf-8"))
    sql = build_rules(rules)
    assert "'2027-01-01', '26', 'HLT', 'PDG'" in sql
    assert sql.count("INSERT INTO") == 6
    assert "DELETE" not in sql