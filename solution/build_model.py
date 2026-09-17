"""Bind an explicit Direct Lake model to minimized enrollment reporting tables."""

import argparse
import base64
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


TABLES = {
    "Members": ("report_members", {
        "member_ordinal": "int64", "member_id": "string", "family_id": "string", "member_role": "string",
        "relationship": "string", "exception_count": "int64", "source_segment": "int64",
        "file_id": "string", "attempt_id": "string"}),
    "Exceptions": ("report_exceptions", {
        "member_ordinal": "int64", "rule_code": "string", "benefit": "string", "severity": "string",
        "source_segment": "int64", "file_id": "string", "rule_version": "string", "attempt_id": "string"}),
    "Health": ("report_health", {
        "file_name": "string", "file_id": "string", "attempt_id": "string", "rule_version": "string", "as_of_date": "dateTime",
        "member_count": "int64", "subscriber_count": "int64", "dependent_count": "int64", "coverage_count": "int64",
        "exception_count": "int64", "affected_members": "int64", "parse_issue_count": "int64", "publication_status": "string"}),
}

MEASURES = {
    "Members": [("Member Count", "COUNTROWS('Members')", "#,0"),
        ("Subscribers", "CALCULATE(COUNTROWS('Members'), 'Members'[member_role] = \"Subscriber\")", "#,0"),
        ("Dependents", "CALCULATE(COUNTROWS('Members'), 'Members'[member_role] = \"Dependent\")", "#,0")],
    "Exceptions": [("Exception Count", "COUNTROWS('Exceptions')", "#,0"),
        ("Affected Members", "DISTINCTCOUNT('Exceptions'[member_ordinal])", "#,0"),
        ("Exception Member Rate", "DIVIDE([Affected Members], [Member Count])", "0.0%")],
    "Health": [("Source Members", "SUM('Health'[member_count])", "#,0"),
        ("Coverage Elections", "SUM('Health'[coverage_count])", "#,0"),
        ("Parser Issues", "SUM('Health'[parse_issue_count])", "#,0"),
        ("Member Reconciliation Difference", "[Source Members] - CALCULATE([Member Count], REMOVEFILTERS('Members'))", "#,0")],
}


def build(endpoint, database="EnrollmentProducts"):
    if not endpoint.endswith(".datawarehouse.fabric.microsoft.com") or any(character in endpoint for character in '\";\r\n'):
        raise ValueError("Use the Warehouse SQL endpoint host without credentials")
    tables = []
    for name, (source, fields) in TABLES.items():
        tables.append({"name": name, "lineageTag": str(uuid5(NAMESPACE_URL, f"fabric/enrollment/{name}")),
            "columns": [{"name": field, "sourceColumn": field, "dataType": kind, "summarizeBy": "none",
                "lineageTag": str(uuid5(NAMESPACE_URL, f"fabric/enrollment/{name}/{field}")),
                **({"formatString": "yyyy-MM-dd"} if kind == "dateTime" else {})} for field, kind in fields.items()],
            "partitions": [{"name": name, "mode": "directLake", "source": {
                "type": "entity", "entityName": source, "schemaName": "dbo", "expressionSource": "Warehouse"}}],
            "measures": [{"name": measure, "expression": dax, "formatString": formatting,
                "description": "Synthetic teaching profile. Findings require human review, not automatic corrections."}
                for measure, dax, formatting in MEASURES.get(name, [])]})
    return {"compatibilityLevel": 1604, "model": {"culture": "en-US", "sourceQueryCulture": "en-US",
        "defaultPowerBIDataSourceVersion": "powerBI_V3", "discourageImplicitMeasures": True,
        "expressions": [{"name": "Warehouse", "kind": "m",
            "expression": f'Sql.Database({json.dumps(endpoint)}, {json.dumps(database)}, [CreateNavigationProperties=false])'}],
        "tables": tables, "relationships": [{"name": "Exceptions_Members", "fromTable": "Exceptions", "fromColumn": "member_ordinal",
            "toTable": "Members", "toColumn": "member_ordinal", "fromCardinality": "many", "toCardinality": "one",
            "crossFilteringBehavior": "oneDirection"}]}}


def item_payload(model):
    return {"displayName": "EnrollmentAnalytics", "type": "SemanticModel",
        "description": "Minimized synthetic analyst model. No DOB, employee ID or SSN fragments.",
        "definition": {"format": "TMSL", "parts": [{"path": name, "payloadType": "InlineBase64",
            "payload": base64.b64encode(json.dumps(content).encode()).decode()}
            for name, content in [("model.bim", model), ("definition.pbism", {"version": "4.0", "settings": {"qnaEnabled": False}})]]}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--database", default="EnrollmentProducts")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(item_payload(build(arguments.endpoint, arguments.database)), indent=2), encoding="utf-8")