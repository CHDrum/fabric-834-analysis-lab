def test_pipeline_libraries_come_from_published_environment():
    notebook = build("workspace", "lakehouse", "environment")
    assert notebook.metadata["dependencies"]["environment"] == {
        "environmentId": "environment", "workspaceId": "workspace"}
    assert all("%pip" not in cell.source for cell in notebook.cells)
    assert 'version("pyx12") == "4.0.0"' in notebook.cells[2].source

import base64
import json

from solution.build_notebook import EXECUTION, build, item_payload


def test_notebook_is_portable_and_uses_bounded_adapter():
    notebook = build()
    assert "dependencies" not in notebook.metadata
    assert len(notebook.cells) == 5
    assert notebook.cells[3].metadata["tags"] == ["parameters"]
    assert all(not cell.get("outputs") for cell in notebook.cells)
    compile(EXECUTION, "notebook", "exec")
    assert "for batch in parser.batches()" in EXECUTION
    assert ".collect(" not in EXECUTION and "toPandas(" not in EXECUTION
    bound = build("workspace", "lakehouse")
    assert bound.metadata.dependencies.lakehouse.default_lakehouse == "lakehouse"
    payload = item_payload(bound)
    decoded = json.loads(base64.b64decode(payload["definition"]["parts"][0]["payload"]))
    assert decoded["metadata"]["dependencies"]["lakehouse"]["default_lakehouse_workspace_id"] == "workspace"