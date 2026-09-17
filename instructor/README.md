# Instructor Runbook | 834 Analysis

This repository is independently usable. All files, identities and findings are fabricated. Learners follow the [seven-module browser guide](../lab-guide/README.md); Python executes in Fabric, not on their machines. Keep the existing secure enterprise transfer and external correction process. Automated corrections and downstream enrollment processing are out of scope.

## Workshop Delivery

Plan for 10-15 beginners working in **your tenant and approved capacity**, preferably in pairs. Stagger Spark starts. Provision and validate your own instructor workspace. Capacity headroom and a timed beginner rehearsal must be checked for each workshop.

| Session | Minutes |
| --- | ---: |
| Orientation, tenant check and finished-product tour | 20 |
| Document lab | 130 |
| Break | 20 |
| 834 modules: 10 / 20 / 30 / 30 / 25 / 10 / 5 | 130 |
| Review, ownership and production gates | 30 |
| Total, excluding optional 30-minute buffer | 330 |

Use ten minutes of orientation for the finished-product tour: two minutes each on document catalog, financial reconciliation, unchanged 834 source/manifest, exception review, and human ownership/production gates. Demonstrate your validated reports. Test author rendering and audience access separately.

Preflight every learner's repository ZIP download, workspace/item authoring, Warehouse SQL access, published Environment use, and eligible individual Power BI author/viewer licenses. Authenticate to GitHub if repository visibility requires it. Fabric capacity is not an individual license; below-F64 viewers have separate requirements. Repository access does not grant tenant access. Never publish member data or use Publish to web.

## Lab Items

No hosted workspace or deployed bindings are distributed. Start with [bindings.example.json](bindings.example.json) and create the following items in an approved workspace. Keep actual IDs and endpoints in an ignored local binding file.

| Item | Display Name |
| --- | --- |
| Lakehouse / Warehouse | EnrollmentLanding / EnrollmentProducts |
| Published Environment | EnrollmentRuntime |
| Notebook / pipeline | LandAndParse834 / EnrollmentIngestion |
| Explicit Direct Lake model / report | EnrollmentAnalytics / Fabric 834 Analysis |

Use the approved Fabric runtime 1.3 with the supplied pinned Environment wheels. Confirm current runtime availability, capacity, and licenses with the platform owner; this lab guarantees no SKU, pool size, region, or concurrency allowance. Read [validation status](../docs/validation-status.md) before a tour. Do not change pool defaults or purchase, resize, pause, resume or delete shared capacity as recovery.

## Optional Instructor Setup

Use Python 3.11, an already authenticated Azure CLI session in the approved tenant, and ODBC Driver 18 for SQL Server. `AzureCliCredential` supplies short-lived tokens. Never put credentials in bindings, Git, logs, screenshots, or notebook outputs. Confirm that your selected interpreter contains the dependencies.

From this repository root in PowerShell:

```powershell
py -3.11 -m venv "$env:TEMP\fabric-834-instructor"
& "$env:TEMP\fabric-834-instructor\Scripts\python.exe" -m pip install -r requirements-dev.txt -r instructor/requirements.txt
& "$env:TEMP\fabric-834-instructor\Scripts\python.exe" -m pytest tests -q -p no:cacheprovider
```

Optional report-browser verification requires `playwright==1.58.0` and its Chromium browser. Install that package in the same instructor environment and run `python -m playwright install chromium` before using the report verifier below.

## Deploy Into a New Workspace

Use one new, approved workspace. Do not run creation steps blindly against an existing environment.

1. Create `EnrollmentLanding` and upload the unchanged sample, parser module, and rules to the three paths in [landing](../lab-guide/01-landing.md). Confirm the raw file is 2,907 bytes; its SHA-256 must match [expected.json](../data/sample/expected.json).
2. Create `EnrollmentRuntime`, select approved Fabric runtime 1.3, upload the two pinned wheels and publish. Wait for successful publication. Do not use notebook `%pip` or shell installation in a pipeline-triggered notebook.
3. Import [LandAndParse834.ipynb](../notebooks/LandAndParse834.ipynb). Attach the **new** EnrollmentLanding as default Lakehouse and the **published new** Environment. Save. The portable notebook deliberately has neither instructor bindings nor saved cell outputs.
4. Run [notebook validation](../lab-guide/02-ingestion.md): exact sample filename, parameters cell, bounded batches, successful manifest, source hash, and 13/7/6/26/0 counts. Files upload does not create Delta tables; the notebook creates `stage_members`, `stage_coverage`, `stage_issues`, `stage_manifest`, and append-only `parse_audit`.
5. Create `EnrollmentProducts`; run [schema/products SQL](../sql/01_enrollment_products.sql), then [reference rule SQL](../sql/02_reference_rules.sql). Follow [products](../lab-guide/03-products.md) to build Parse834 -> Copy_manifest -> Record_attempt -> Copy_members -> Load_coverage -> Load_issues -> Publish_products. Use success-only notebook dependency, Workspace staging, and the exact IfCondition expressions. False branches DELETE their corresponding Warehouse staging rows; they must not retain old issues or coverage.
6. Run the pipeline once, wait for completion, and execute [acceptance SQL](../sql/03_validate.sql). Empty output means the exact 16 tuples, counts, hash, rule version, lineage, and successful audit all match. A total of 16 alone is insufficient.
7. Build the explicit model on the three physical report tables using the [model reference](../solution/portable/measures.md), then the three [report pages](../lab-guide/04-report.md). Test browser rendering, filters, refresh and approved non-owner access separately. Model-query success does not prove those behaviors.

### Rebinding and Definition Packages

[bindings.example.json](bindings.example.json) contains placeholders. Copy it to `instructor/bindings.local.json` and supply the new workspace/Lakehouse/Warehouse/notebook/Environment/model IDs and actual Warehouse host/database. The notebook depends on its new default Lakehouse and Environment; the pipeline depends on its new notebook, Lakehouse and Warehouse; the model depends on Warehouse host/database; the report depends on the new semantic-model ID. Create the model before the final report package, then regenerate with that ID.

```powershell
python instructor/package_solution.py --bindings instructor/bindings.example.json --output solution/portable
```

This example rebuilds placeholders only. For deployment, use `--bindings instructor/bindings.local.json --output solution/deployed`; keep that generated folder private and ignored. Submit each request separately to `POST /v1/workspaces/{workspace}/items`. Updating an existing item uses its `updateDefinition` endpoint and only the `definition` body, not both `creationPayload` and `definition`. `build_notebook.py --workspace ... --lakehouse ... --environment ... --output ...` can generate a bound instructor notebook with nbformat. Do not hand-edit notebook JSON.

An `Accepted` export is an operation receipt, not a definition. Retrieve the canonical `/v1/operations/{operationId}/result` after success. Export/package generation alone does not prove a successful deployment. Keep service responses, job histories, bound notebooks, and report screenshots out of the distributable repository. Inspect all bindings before importing.

Use `python instructor/fabric.py --help` and subcommand help for exact flags. The helper retries GET only; after an ambiguous mutation, inspect jobs/items/operation results before submitting again. Respect 429/Retry-After. Never start a new run merely because a previous request timed out.

## Serialized Runs and Recovery

Use one operator and one active pipeline per workspace. Shared staging and latest-report tables have **no cross-run lease**. The run helper's idle preflight is not an atomic lock. Disable schedules and coordinate people before publication, probes or scale tests.

```powershell
python instructor/run_pipeline.py --bindings instructor/bindings.local.json --source-file synthetic_834.edi --output docs/evidence/submission.json
python instructor/fabric.py api GET /v1/workspaces/WORKSPACE_UUID/items/PIPELINE_UUID/jobs/instances/JOB_UUID --save docs/evidence/run.json
python instructor/verify_solution.py --bindings instructor/bindings.local.json --replay --failure-probe
```

Use the actual accepted job ID for the GET example. The starter submits once, never polls, and accepts only approved synthetic names. Wait for a terminal run status before another run or the verifier. Save evidence locally in the ignored `docs/evidence/` directory; an `Accepted` or `InProgress` JSON is never a success claim.

The verifier requires `synthetic_only: true`, refuses active jobs, checks the 13-member acceptance contract, republishes the same file/rule without duplicate products, and compares snapshots. Its optional failure probe assigns a new synthetic attempt ID with `status='Failed'`; Warehouse publication must reject it and preserve the preceding report snapshot. It restores the original manifest in `finally`, leaves the failed audit entry, and queries all ten model measures. This is a publication-guard test, not an end-to-end parser-failure test.

With optional Playwright installed, run `python instructor/verify_report.py --workspace WORKSPACE_UUID --report REPORT_UUID --output docs/images/report`, substituting your target IDs, for a separate browser check. It verifies all three pages, displayed values, member filtering and reset, and saves synthetic screenshots locally without persisting tokens or browser state. Test approved non-owner access separately. PBIR file format 4.0 and internal report definition version 2.0.0 are distinct fields.

If a probe process is forcibly interrupted, inspect `stg_manifest`; restore it using a fresh serialized run of the unchanged small source. If parsing or staging fails, inspect the notebook job, per-attempt Files manifest, and Lakehouse `parse_audit`. The success-only Copy_manifest dependency prevents publishing a previous successful manifest after a new notebook failure. Imports, missing raw/code/config, initial hashing and other early setup failures can occur before the notebook's audit guard, so **a Warehouse or Lakehouse audit row is not guaranteed for every invocation**. Keep the Fabric job ID as independent evidence; do not claim complete invocation correlation.

For a controlled malformed-file exercise, use [synthetic_malformed_834.edi](../data/sample/synthetic_malformed_834.edi): its GE trailer claims two transactions but contains one. Upload it under its distinct raw filename, then use the pipeline starter with `--source-file synthetic_malformed_834.edi`. Run only in an approved isolated workspace with one operator, and expect the pipeline to fail at Parse834 with `ENVELOPE_VALIDATION_FAILED`; downstream publication must not run. Compare published rows, all ten measures, and the raw input before and after the failure. Never publish partial staging, edit the valid raw sample, or infer that every early-failure path has been tested. Restore `synthetic_834.edi` with a new serialized pipeline run and acceptance afterward. This is a synthetic recovery exercise, not automated correction of enrollment data.

## Optional Scale Checks

| Clean Synthetic File | Members / Subscribers / Dependents | Elections / Findings |
| --- | --- | --- |
| 100K | 100,000 / 50,000 / 50,000 | 200,000 / 0 |
| 200K | 200,000 / 100,000 / 100,000 | 400,000 / 0 |

Generate these optional fixtures with [the synthetic generator](../data/generate_synthetic.py) and run only with the capacity owner's approval. Record source SHA-256/bytes, counts, pipeline duration, cold/warm behavior, peak memory, activity timing, error distributions, and concurrency in your own environment. No runtime, capacity headroom, or production SLA is guaranteed. Retained products are file/rule-scoped; report tables show only the latest successful publication. Always restore `synthetic_834.edi` and verify 13 members/16 findings before the tour.

## Rules, Handoff and Production Gates

Use the [data and rule dictionary](../docs/data-dictionary.md), [EDI-01 through EDI-07 matrix](../docs/requirements-traceability.md), module answers and [exact findings](../data/sample/expected.json). The same rule version with changed content is rejected as `RULE_VERSION_IMMUTABLE`. Publish a newly approved version, keep old references/results and reconcile the difference. Regenerate SQL and upload matching JSON before a new parse; do not silently change age or plan rules in place.

Human review remains the final handoff. Export only an approved minimal exception queue with case reference, source hash, attempt, rule version, member ordinal, rule code and source segment. Use secured enterprise channels; do not email real PII/PHI or include SSN/DOB/employee IDs by default. Synthetic member/family IDs in the model would still be sensitive if replaced by real identifiers. Minimization is not row-level security, export enforcement, HIPAA compliance, retention or authorization.

Name the source/transfer owner, rule approver, analyst, platform operator, support owner and capacity owner. Before real use, approve landing, partner profile/identifier mapping, required fields, temporal rules, historical accuracy, timing/reconciliation, privacy/access/export, audit coverage, retention/legal hold, cadence, concurrency lock, failure/recovery and support. Existing secure transfer stays in place. No automated corrections, downstream enrollment processing or partner-guide certification is included. Cleanup applies only to specifically approved learner workspaces after retention review; preserve shared capacity and other owners' workspaces.