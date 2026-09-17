import json

import pytest

from solution.build_model import build, item_payload


def test_only_minimized_physical_tables_are_published():
    model = build("synthetic.datawarehouse.fabric.microsoft.com")
    assert {table["partitions"][0]["source"]["entityName"] for table in model["model"]["tables"]} == {
        "report_members", "report_exceptions", "report_health"}
    for table in model["model"]["tables"]:
        assert table["partitions"][0]["mode"] == "directLake"
        assert not {"dob", "employee_id", "ssn", "ssn_last4", "has_ssn"} & {column["name"] for column in table["columns"]}
    assert model["model"]["relationships"][0]["crossFilteringBehavior"] == "oneDirection"
    assert len(item_payload(model)["definition"]["parts"]) == 2


def test_model_rebinds_without_instructor_ids():
    model = build("other.datawarehouse.fabric.microsoft.com", "OtherWarehouse")
    assert "OtherWarehouse" in json.dumps(model)
    assert "1db886a3" not in json.dumps(model)
    with pytest.raises(ValueError):
        build("localhost;password=not-allowed")