"""Build a portable PBIR report for minimized synthetic enrollment review."""

import argparse
import base64
import json
from pathlib import Path
from uuid import UUID


SCHEMA_ROOT = "https://developer.microsoft.com/json-schemas/fabric/item/report"


def expression(value):
    literal = "true" if value is True else "false" if value is False else str(value) if isinstance(value, (int, float)) else "'" + value.replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": literal}}}


def projection(table, name, measure=False):
    return {"field": {"Measure" if measure else "Column": {
        "Expression": {"SourceRef": {"Entity": table}}, "Property": name}},
        "queryRef": f"{table}.{name}", "nativeQueryRef": name}


def visual(name, kind, title, position, roles):
    left, top, width, height = position
    return {"$schema": f"{SCHEMA_ROOT}/definition/visualContainer/2.0.0/schema.json", "name": name,
        "position": {"x": left, "y": top, "width": width, "height": height, "z": top * 10 + left, "tabOrder": top * 10 + left},
        "visual": {"visualType": kind, "query": {"queryState": {
            role: {"projections": values} for role, values in roles.items()}},
            "visualContainerObjects": {"title": [{"properties": {"show": expression(True), "text": expression(title), "fontSize": expression(12)}}],
                "background": [{"properties": {"color": {"solid": {"color": expression("#FFFFFF")}}, "transparency": expression(0)}}]},
            "drillFilterOtherVisuals": True}}


def heading(title, subtitle):
    content = visual("heading", "textbox", title, (24, 12, 1232, 74), {})
    content["visual"].pop("query")
    content["visual"]["visualContainerObjects"]["title"][0]["properties"]["show"] = expression(False)
    content["visual"]["objects"] = {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": title, "textStyle": {"fontSize": "22pt", "fontWeight": "bold", "color": "#005B85"}}]},
        {"textRuns": [{"value": subtitle, "textStyle": {"fontSize": "10pt", "color": "#455560"}}]}]}}]}
    return content


def table(name, title, position, fields):
    return visual(name, "tableEx", title, position, {"Values": [projection(*entry) for entry in fields]})


def cards(measures):
    result = []
    for ordinal, (source, measure, label) in enumerate(measures):
        content = visual(f"metric{ordinal}", "card", label, (24 + ordinal * 310, 90, 296, 110),
                         {"Values": [projection(source, measure, True)]})
        content["visual"]["objects"] = {
            "categoryLabels": [{"properties": {"show": expression(False)}}],
            "labels": [{"properties": {"fontSize": expression(32), "labelDisplayUnits": expression(1)}}]}
        result.append(content)
    return result


def pages():
    return [
        ("health", "01 File and Load Health", [
            heading("Enrollment File Health", "SYNTHETIC 834  |  Latest successful publication  |  Member counts include subscribers and dependents"),
            *cards([("Members", "Member Count", "Members"), ("Members", "Subscribers", "Subscribers"),
                    ("Members", "Dependents", "Dependents"), ("Health", "Coverage Elections", "Coverage elections")]),
            table("loadHealth", "Publication and count reconciliation", (24, 218, 1232, 200),
                [("Health", name) for name in ("file_name", "rule_version", "as_of_date", "publication_status")]
                + [("Health", "Parser Issues", True), ("Health", "Member Reconciliation Difference", True)]),
            table("lineage", "File hash and processing attempt", (24, 438, 1232, 258),
                [("Health", name) for name in ("file_id", "attempt_id", "member_count", "coverage_count", "exception_count", "affected_members")])]),
        ("exceptions", "02 Exception Summary", [
            heading("Enrollment Exceptions", "ILLUSTRATIVE RULES  |  One member can have several findings  |  A finding is not an eligibility determination"),
            *cards([("Exceptions", "Exception Count", "Findings"), ("Exceptions", "Affected Members", "Affected members"),
                    ("Exceptions", "Exception Member Rate", "Affected-member rate"), ("Health", "Parser Issues", "Parser issues")]),
            visual("ruleCounts", "barChart", "Findings by rule", (24, 218, 754, 478),
                {"Category": [projection("Exceptions", "rule_code")], "Y": [projection("Exceptions", "Exception Count", True)]}),
            table("roleCounts", "Member population by role", (802, 218, 454, 220),
                [("Members", "member_role"), ("Members", "Member Count", True)]),
            table("benefitCounts", "Findings by benefit; blank means member-level", (802, 458, 454, 238),
                [("Exceptions", "benefit"), ("Exceptions", "Exception Count", True)])]),
        ("review", "03 Analyst Detail and Traceability", [
            heading("Analyst Review", "SYNTHETIC IDs  |  Human review and external coordination  |  No automated corrections or downstream enrollment changes"),
            *cards([("Members", "Member Count", "Members in context"), ("Exceptions", "Affected Members", "Affected members"),
                    ("Exceptions", "Exception Count", "Findings"), ("Health", "Member Reconciliation Difference", "Member count difference")]),
            table("memberReview", "Member and family context", (24, 218, 1232, 206),
                [("Members", name) for name in ("member_ordinal", "member_id", "family_id", "member_role", "exception_count", "source_segment")]),
            table("findingReview", "Trace each finding to a file, rule version and source segment", (24, 442, 1232, 254),
                [("Exceptions", name) for name in ("member_ordinal", "rule_code", "benefit", "severity", "source_segment", "rule_version", "file_id", "attempt_id")])]),
    ]


def build(semantic_model):
    UUID(semantic_model)
    definitions = pages()
    parts = {
        "definition.pbir": {"$schema": f"{SCHEMA_ROOT}/definitionProperties/2.0.0/schema.json", "version": "4.0",
            "datasetReference": {"byConnection": {"connectionString": f"semanticmodelid={semantic_model}"}}},
        "definition/version.json": {"$schema": f"{SCHEMA_ROOT}/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"},
        "definition/report.json": {"$schema": f"{SCHEMA_ROOT}/definition/report/2.0.0/schema.json",
            "themeCollection": {"baseTheme": {"name": "CY24SU06", "type": "SharedResources", "reportVersionAtImport": "5.55"},
                "customTheme": {"name": "FabricWorkshop", "type": "RegisteredResources", "reportVersionAtImport": "5.55"}},
            "resourcePackages": [{"name": "SharedResources", "type": "SharedResources", "items": [
                {"name": "CY24SU06", "path": "BaseThemes/CY24SU06.json", "type": "BaseTheme"}]},
                {"name": "RegisteredResources", "type": "RegisteredResources", "items": [
                {"name": "FabricWorkshop", "path": "FabricWorkshop.json", "type": "CustomTheme"}]}],
            "settings": {"useEnhancedTooltips": True, "defaultFilterActionIsDataFilter": True}},
        "StaticResources/RegisteredResources/FabricWorkshop.json": {"name": "FabricWorkshop",
            "dataColors": ["#007CB2", "#00877D", "#F0B323", "#D8493C", "#718642", "#785E9D"],
            "background": "#FFFFFF", "foreground": "#203B47", "tableAccent": "#007CB2"},
        "definition/pages/pages.json": {"$schema": f"{SCHEMA_ROOT}/definition/pagesMetadata/1.0.0/schema.json",
            "pageOrder": [name for name, _, _ in definitions], "activePageName": definitions[0][0]},
    }
    for name, label, visuals in definitions:
        parts[f"definition/pages/{name}/page.json"] = {"$schema": f"{SCHEMA_ROOT}/definition/page/2.0.0/schema.json",
            "name": name, "displayName": label, "displayOption": "FitToPage", "height": 720, "width": 1280}
        for content in visuals:
            parts[f"definition/pages/{name}/visuals/{content['name']}/visual.json"] = content
    return parts


def item_payload(parts):
    return {"displayName": "Fabric 834 Analysis", "type": "Report",
        "description": "Synthetic file health, exception summary and minimized human-review traceability.",
        "definition": {"format": "PBIR", "parts": [{"path": path, "payloadType": "InlineBase64",
            "payload": base64.b64encode(json.dumps(content).encode()).decode()} for path, content in parts.items()]}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(item_payload(build(arguments.model)), indent=2), encoding="utf-8")