"""Generate the importable Fabric notebook with nbformat; no saved cell output."""

import argparse
import base64
import json
from pathlib import Path

import nbformat


EXECUTION = '''import json
import sys
import tempfile
from pathlib import Path
import pyarrow as arrow
import pyarrow.parquet as parquet
from pyspark.sql.types import StringType, StructField, StructType

root = Path("/lakehouse/default/Files/834-demo")
sys.path.insert(0, str(root / "code"))
from parse_834 import EnrollmentParser, MEMBER_COLUMNS, COVERAGE_COLUMNS, ISSUE_COLUMNS, MANIFEST_COLUMNS

if Path(source_file).name != source_file or not source_file.endswith(".edi"):
    raise ValueError("source_file must name one .edi file in the approved raw folder")
rules = json.loads((root / "config" / "rules.json").read_text(encoding="utf-8"))
if not rules.get("synthetic_only"):
    raise ValueError("This workshop notebook accepts synthetic data only")
parser = EnrollmentParser(root / "raw" / source_file, rules["rule_version"], batch_size=int(batch_size))
columns = {"members": MEMBER_COLUMNS, "coverage": COVERAGE_COLUMNS, "issues": ISSUE_COLUMNS}
attempt_id = parser.manifest["attempt_id"]
attempt_root = root / "attempts" / attempt_id
attempt_root.mkdir(parents=True, exist_ok=False)
lakehouse = notebookutils.lakehouse.get()
lakehouse_path = f"abfss://{lakehouse.workspaceId}@onelake.dfs.fabric.microsoft.com/{lakehouse.id}"
staging_path = f"{lakehouse_path}/Files/834-demo/attempts/{attempt_id}"
writers = {}

def string_rows(rows, fields):
    return [{field: "" if row.get(field) is None else str(row.get(field, "")) for field in fields} for row in rows]

def delta_rows(table, rows, fields, mode="overwrite"):
    schema = StructType([StructField(field, StringType(), True) for field in fields])
    frame = spark.createDataFrame(string_rows(rows, fields), schema=schema)
    frame.write.format("delta").mode(mode).option("overwriteSchema", "true").saveAsTable(table)

try:
    with tempfile.TemporaryDirectory() as scratch:
        for name, fields in columns.items():
            writers[name] = parquet.ParquetWriter(str(Path(scratch) / f"{name}.parquet"),
                arrow.schema([(field, arrow.string()) for field in fields]), compression="snappy")
        try:
            for batch in parser.batches():
                for name, fields in columns.items():
                    if batch[name]:
                        writers[name].write_table(arrow.Table.from_pylist(string_rows(batch[name], fields),
                            schema=arrow.schema([(field, arrow.string()) for field in fields])))
        finally:
            for writer in writers.values():
                writer.close()
        for name in columns:
            notebookutils.fs.cp(f"file:{Path(scratch) / f'{name}.parquet'}", f"{staging_path}/{name}.parquet")
            frame = spark.read.parquet(f"{staging_path}/{name}.parquet")
            frame.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"stage_{name}")
        actual_members = spark.table("stage_members").count()
        actual_coverage = spark.table("stage_coverage").count()
        actual_issues = spark.table("stage_issues").count()
        if (actual_members != parser.manifest["member_count"] or actual_coverage != parser.manifest["coverage_count"]
            or actual_issues != parser.manifest["issue_count"]):
            raise ValueError("Delta row counts do not reconcile with parser manifest")
    delta_rows("stage_manifest", [parser.manifest], MANIFEST_COLUMNS)
    delta_rows("parse_audit", [parser.manifest], MANIFEST_COLUMNS, "append")
    (attempt_root / "manifest.json").write_text(json.dumps(parser.manifest, indent=2), encoding="utf-8")
    print(json.dumps(parser.manifest, indent=2))
except Exception:
    parser.manifest.update(status="Failed", failure_code=parser.manifest["failure_code"] or "STAGING_WRITE_FAILED")
    (attempt_root / "manifest.json").write_text(json.dumps(parser.manifest, indent=2), encoding="utf-8")
    delta_rows("stage_manifest", [parser.manifest], MANIFEST_COLUMNS)
    delta_rows("parse_audit", [parser.manifest], MANIFEST_COLUMNS, "append")
    raise
'''


def build(workspace=None, lakehouse=None, environment=None):
    notebook = nbformat.v4.new_notebook()
    notebook.metadata.update({"kernelspec": {"display_name": "Synapse PySpark", "language": "python", "name": "synapse_pyspark"},
                              "language_info": {"name": "python"}})
    if workspace and lakehouse:
        notebook.metadata["dependencies"] = {"lakehouse": {
            "default_lakehouse": lakehouse, "default_lakehouse_name": "EnrollmentLanding",
            "default_lakehouse_workspace_id": workspace, "known_lakehouses": [{"id": lakehouse}]}}
    if environment:
        if not workspace:
            raise ValueError("An environment binding requires its workspace")
        notebook.metadata.setdefault("dependencies", {})["environment"] = {
            "environmentId": environment, "workspaceId": workspace}
    notebook.cells = [
        nbformat.v4.new_markdown_cell("# 834 standardization\n\nSynthetic 005010X220A1 teaching profile. Attach EnrollmentLanding as the default lakehouse and the published EnrollmentRuntime environment with the supplied pinned wheels. Upload raw, code and config artifacts first. Do not use real member records. This is not a certified X12 implementation-guide validator."),
        nbformat.v4.new_code_cell('import json, sys\nfrom pathlib import Path\ncheckpoint_root = Path("/lakehouse/default/Files/834-demo")\ncheckpoint_root.mkdir(parents=True, exist_ok=True)\n(checkpoint_root / "runtime-check.json").write_text(json.dumps({"python": sys.version, "raw_exists": (checkpoint_root / "raw").exists(), "code_exists": (checkpoint_root / "code").exists()}), encoding="utf-8")'),
        nbformat.v4.new_code_cell('from importlib.metadata import version\nassert version("pyx12") == "4.0.0", "Attach the published EnrollmentRuntime environment"\nassert version("defusedxml") == "0.7.1", "Attach the published EnrollmentRuntime environment"'),
        nbformat.v4.new_code_cell('source_file = "synthetic_834.edi"\nbatch_size = 5000', metadata={"tags": ["parameters"]}),
        nbformat.v4.new_code_cell(EXECUTION),
    ]
    nbformat.validate(notebook)
    return notebook


def item_payload(notebook):
    return {"displayName": "LandAndParse834", "type": "Notebook",
            "description": "Bounded synthetic 834 parser, audit and Delta staging.",
            "definition": {"format": "ipynb", "parts": [{"path": "notebook-content.ipynb", "payloadType": "InlineBase64",
                "payload": base64.b64encode(nbformat.writes(notebook).encode()).decode()}]}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace")
    parser.add_argument("--lakehouse")
    parser.add_argument("--environment")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "notebooks" / "LandAndParse834.ipynb")
    arguments = parser.parse_args()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(build(arguments.workspace, arguments.lakehouse, arguments.environment), arguments.output)
    print(f"Validated notebook: {arguments.output}")