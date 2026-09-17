from solution.build_model import MEASURES, TABLES
from solution.build_report import build, item_payload, pages


def test_report_fields_and_layout_match_model():
    assert [name for name, _, _ in pages()] == ["health", "exceptions", "review"]
    for _, _, visuals in pages():
        assert len({visual["name"] for visual in visuals}) == len(visuals)
        for visual in visuals:
            if visual["visual"]["visualType"] == "card":
                assert visual["visual"]["objects"]["categoryLabels"][0]["properties"]["show"]["expr"]["Literal"]["Value"] == "false"
                assert visual["visual"]["objects"]["labels"][0]["properties"]["fontSize"]["expr"]["Literal"]["Value"] == "32"
            position = visual["position"]
            assert 0 <= position["x"] < position["x"] + position["width"] <= 1280
            assert 0 <= position["y"] < position["y"] + position["height"] <= 720
            for role in visual["visual"].get("query", {}).get("queryState", {}).values():
                for projection in role["projections"]:
                    kind, value = next(iter(projection["field"].items()))
                    source = value["Expression"]["SourceRef"]["Entity"]
                    available = TABLES[source][1] if kind == "Column" else {name for name, _, _ in MEASURES[source]}
                    assert value["Property"] in available


def test_report_binds_only_to_supplied_model():
    model = "00000000-0000-4000-8000-000000000001"
    parts = build(model)
    assert parts["definition.pbir"]["version"] == "4.0"
    assert parts["definition/version.json"]["version"] == "2.0.0"
    assert parts["definition.pbir"]["datasetReference"]["byConnection"]["connectionString"] == f"semanticmodelid={model}"
    themes = parts["definition/report.json"]["themeCollection"]
    assert themes["baseTheme"]["name"] == "CY24SU06"
    assert themes["baseTheme"]["reportVersionAtImport"] == themes["customTheme"]["reportVersionAtImport"] == "5.55"
    assert item_payload(parts)["type"] == "Report"