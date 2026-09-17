"""Bind an enrollment notebook and sequential Lakehouse-to-Warehouse copies."""

import base64
import json


def service(kind, workspace, item, endpoint=None):
    properties = {"workspaceId": workspace, "artifactId": item}
    if kind == "Lakehouse":
        properties["rootFolder"] = "Tables"
    else:
        properties["endpoint"] = endpoint
    return {"name": kind, "properties": {"type": kind, "typeProperties": properties, "annotations": []}}


def build(workspace, lakehouse, warehouse, endpoint, notebook, skip_notebook=False):
    activities = []
    if not skip_notebook:
        activities.append({"name": "Parse834", "type": "TridentNotebook", "dependsOn": [],
            "policy": {"timeout": "0.02:00:00", "retry": 0, "secureInput": True, "secureOutput": True},
            "typeProperties": {"workspaceId": workspace, "notebookId": notebook,
                "parameters": {"source_file": {"type": "string", "value": {"type": "Expression", "value": "@pipeline().parameters.source_file"}},
                               "batch_size": {"type": "int", "value": 10000}}}})
    for table in ("manifest", "members", "coverage", "issues"):
        dependencies = [{"activity": activities[-1]["name"], "dependencyConditions": ["Succeeded"]}] if activities else []
        if table == "members" and not skip_notebook:
            dependencies.append({"activity": "Parse834", "dependencyConditions": ["Succeeded"]})
        copy = {"name": f"Copy_{table}", "type": "Copy", "dependsOn": dependencies,
            "policy": {"timeout": "0.01:00:00", "retry": 1, "retryIntervalInSeconds": 30, "secureInput": True, "secureOutput": True},
            "typeProperties": {
                "source": {"type": "LakehouseTableSource", "datasetSettings": {"type": "LakehouseTable", "annotations": [], "schema": [],
                    "linkedService": service("Lakehouse", workspace, lakehouse), "typeProperties": {"table": f"stage_{table}"}}},
                "sink": {"type": "DataWarehouseSink", "allowCopyCommand": True, "copyCommandSettings": {},
                    "preCopyScript": f"DELETE FROM dbo.stg_{table};", "datasetSettings": {"type": "DataWarehouseTable", "schema": [], "annotations": [],
                        "linkedService": service("DataWarehouse", workspace, warehouse, endpoint), "typeProperties": {"schema": "dbo", "table": f"stg_{table}"}}},
                "enableStaging": True, "translator": {"type": "TabularTranslator", "typeConversion": True,
                    "typeConversionSettings": {"allowDataTruncation": False, "treatBooleanAsNumber": False}}}}
        if table in ("coverage", "issues"):
            copy["dependsOn"] = []
            count_column = "coverage_count" if table == "coverage" else "issue_count"
            activities.append({"name": f"Load_{table}", "type": "IfCondition", "dependsOn": dependencies,
                "typeProperties": {"expression": {"type": "Expression",
                    "value": f"@greater(int(activity('Record_attempt').output.resultSets[0].rows[0].{count_column}), 0)"},
                    "ifTrueActivities": [copy], "ifFalseActivities": [script(f"Clear_{table}", None,
                        f"DELETE FROM dbo.stg_{table};", workspace, warehouse, endpoint)]}})
        else:
            activities.append(copy)
        if table == "manifest":
            activity = script("Record_attempt", "Copy_manifest",
                "EXEC dbo.record_enrollment_attempt; SELECT coverage_count, issue_count FROM dbo.stg_manifest;", workspace, warehouse, endpoint)
            activity["typeProperties"]["scripts"][0]["type"] = "Query"
            activities.append(activity)
    activities.append(script("Publish_products", "Load_issues", "EXEC dbo.publish_enrollment_products;", workspace, warehouse, endpoint))
    return {"properties": {"activities": activities, "parameters": {"source_file": {"type": "string", "defaultValue": "synthetic_834.edi"}}}}


def script(name, predecessor, text, workspace, warehouse, endpoint):
    return {"name": name, "type": "Script", "dependsOn": [{"activity": predecessor, "dependencyConditions": ["Succeeded"]}] if predecessor else [],
        "linkedService": service("DataWarehouse", workspace, warehouse, endpoint),
        "typeProperties": {"scripts": [{"type": "NonQuery", "text": text}], "scriptBlockExecutionTimeout": "00:30:00"}}


def item_payload(content):
    return {"displayName": "EnrollmentIngestion", "type": "DataPipeline", "description": "Synthetic 834 parse, audit, Warehouse load and atomic publication.",
            "definition": {"parts": [{"path": "pipeline-content.json", "payloadType": "InlineBase64",
                "payload": base64.b64encode(json.dumps(content).encode()).decode()}]}}