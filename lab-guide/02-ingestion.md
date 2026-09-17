# 02 - Parse and Reconcile the File

**Duration:** 30 minutes

**Objective:** run the supplied bounded parser in Fabric and inspect source-to-staging evidence.

## Steps

1. In your workspace use **Import > Notebook > From this computer** (or the Notebook import option under **New item**) and select [LandAndParse834.ipynb](../notebooks/LandAndParse834.ipynb). Name the imported item `LandAndParse834`.
2. Open it. In the Lakehouse pane choose **Add lakehouse > Existing lakehouse**, select `EnrollmentLanding`, and make it the **default**. The local notebook intentionally contains no instructor workspace bindings.
3. In the notebook's Environment selector choose the successfully published `EnrollmentRuntime`, then save. If an older session is active, stop it so the next session uses the published environment.
4. Inspect the parameter cell. Leave `source_file = "synthetic_834.edi"` and `batch_size = 5000` for the interactive run. The parameter cell is tagged in the provided notebook; preserve that designation so the pipeline can override values.
5. Select **Run all** once. Allow the Spark session to start. Watch for the pinned-package assertions to pass before parsing. Do not launch a second copy while the first runs.
6. Inspect the manifest printed by the final cell. Expect the following; timestamps and `attempt_id` are unique to your run:

| Field | Expected |
| --- | --- |
| file_name / file_bytes | synthetic_834.edi / 2907 |
| file_id | 17908648f246c1bb69d00cb238f3389aa393d809c1537fda9b070101944910e8 |
| status | Succeeded |
| member_count / subscriber_count / dependent_count | 13 / 7 / 6 |
| coverage_count / issue_count | 26 / 0 |
| rule_version | SYNTHETIC-2027-v1 |

7. Refresh Lakehouse **Tables**. Confirm `stage_members`, `stage_coverage`, `stage_issues`, `stage_manifest`, and `parse_audit`. Preview members and coverage; the issues table is intentionally empty. The parser writes Arrow Parquet per attempt, then Delta Tables, rather than accumulating the entire member file in Python memory.
8. In **Files/834-demo/attempts**, find your attempt ID and its `manifest.json`. The file identity is content-derived; the attempt ID identifies this execution. `parse_audit` appends attempts while the stage tables represent only the latest run.
9. Save the notebook and **Stop session** before building the pipeline. Leave the notebook item, default Lakehouse, Environment and parameter cell intact.

## What the Parser Does

The pyx12 adapter handles the supported X12 envelope/member loops and repeated coverage, checks controls/counts, limits batch and per-member growth, sanitizes failures, and records member ordinal plus source-segment lineage. It is not a certified HIPAA or partner implementation-guide validator. Missing business values can become review findings; a fatal structural failure stops publication.

Full SSNs are not retained in curated member output. DOB, employee ID, presence flags and SSN last-four still exist in restricted intermediate products, so excluding them later from the model is not sufficient access control by itself.

## Completion Checklist

- [ ] Package assertions and full notebook execution succeeded.
- [ ] Manifest hash, bytes and all counts match the table above.
- [ ] Four staging tables and append-only parse_audit are visible.
- [ ] Interactive Spark session stopped before pipeline execution.

## Challenge and Answer

**Question:** Why are member ID and member ordinal both needed?

**Answer:** A received member ID may be duplicated or absent. The ordinal identifies the specific occurrence within a file, enabling exact findings and source lineage without pretending the business identifier is unique.

## Recovery

For `ModuleNotFoundError` or version assertions, attach the published Environment and start a new session. For a missing default mount or file, verify the default Lakehouse and the three folders. Do not run failed or stale staging through a Warehouse copy manually. Failures inside the guarded processing block write sanitized attempt evidence; early imports/configuration/setup failures are not guaranteed that manifest or a Warehouse audit row. Use notebook monitoring and `Files/834-demo/runtime-check.json` for those failures.

[Previous: Landing](01-landing.md) | [Guide](README.md) | [Next: Orchestrate products](03-products.md)