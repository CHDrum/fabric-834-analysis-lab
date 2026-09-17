# 03 - Orchestrate Versioned Review Products

**Duration:** 30 minutes

**Objective:** reproduce the verified conditional-copy pipeline and publish explainable Warehouse findings.

## Prepare the Warehouse

1. Create a **Warehouse** named `EnrollmentProducts`, separate from the Lakehouse SQL analytics endpoint. In its SQL editor run all of [01_enrollment_products.sql](../sql/01_enrollment_products.sql), then all of [02_reference_rules.sql](../sql/02_reference_rules.sql). Keep `GO` separators on their own lines.
2. Confirm four `stg_...` tables, six `ref_...` tables, `audit_run`, member/coverage/exception products, and three physical `report_...` tables. The rules must match the uploaded configuration and retain the same immutable version.

## Create the Pipeline

3. Create a **Data pipeline** named `EnrollmentIngestion`. Select blank canvas, open **Parameters**, and add String parameter `source_file` with default `synthetic_834.edi`.
4. Add a **Notebook** activity named `Parse834`, selecting your `LandAndParse834` notebook. Add base parameters `source_file` (String) using dynamic expression `@pipeline().parameters.source_file` and `batch_size` (Int) with value `10000`. Set notebook retry to zero. Confirm it uses the notebook's published Environment and default Lakehouse.
5. Add **Copy data** named `Copy_manifest`. Connect only `Parse834` **Succeeded** to it. Source: your `EnrollmentLanding`, **Tables**, `stage_manifest`. Destination: your `EnrollmentProducts`, existing `dbo.stg_manifest`, Insert. Set destination advanced **Pre-copy script** to `DELETE FROM dbo.stg_manifest;`. Import schemas and map columns by matching names. Under Settings enable **staging > Workspace**. Keep truncation/skip-incompatible-row options off.
6. Add a **Script** named `Record_attempt`, connected from `Copy_manifest` Succeeded. Select the Warehouse connection, choose script type **Query**, and enter exactly:

```sql
EXEC dbo.record_enrollment_attempt;
SELECT coverage_count, issue_count FROM dbo.stg_manifest;
```

The Query type and final SELECT are required because the following conditions read its result set.

7. Add `Copy_members` after `Record_attempt` Succeeded. Use the same Copy settings as manifest, but source `stage_members`, destination `dbo.stg_members`, and pre-copy `DELETE FROM dbo.stg_members;`. Refresh mappings for this table. Its execution follows notebook success through the chain; an additional explicit Parse834 Succeeded dependency is also used by the reference builder.
8. Add an **If Condition** named `Load_coverage` after `Copy_members` Succeeded. In its Activities expression enter:

```text
@greater(int(activity('Record_attempt').output.resultSets[0].rows[0].coverage_count), 0)
```

Use the pencil icon to edit the **True** branch: add `Copy_coverage`, source `stage_coverage`, destination `dbo.stg_coverage`, pre-copy `DELETE FROM dbo.stg_coverage;`, matching columns and Workspace staging. In the **False** branch add a Warehouse **Script**, NonQuery, named `Clear_coverage`, containing `DELETE FROM dbo.stg_coverage;`.

9. Return to the outer pipeline canvas. Add **If Condition** `Load_issues` after `Load_coverage` Succeeded. Its expression is:

```text
@greater(int(activity('Record_attempt').output.resultSets[0].rows[0].issue_count), 0)
```

True branch: `Copy_issues` from `stage_issues` to `dbo.stg_issues`, pre-copy `DELETE FROM dbo.stg_issues;`, matching columns and Workspace staging. False branch: NonQuery Script `Clear_issues` with `DELETE FROM dbo.stg_issues;`. This sample executes the False branch; an empty Delta table need not have a file for Copy to read.

10. On the outer canvas add Script `Publish_products` after `Load_issues` Succeeded. Choose the Warehouse, **NonQuery**, and enter `EXEC dbo.publish_enrollment_products;`. Do not create a Completed or failure path that publishes stale data.
11. Save, validate, confirm no other run is active, and **Run** once with the default source filename. Use Output/Monitoring to observe the notebook, copy, condition and publication stages. The first run can include Spark startup; do not mistake a small-file duration for parser throughput.

## Expected Sequence

`Parse834 -> Copy_manifest -> Record_attempt -> Copy_members -> Load_coverage -> Load_issues -> Publish_products`

All outer dependencies are Succeeded. Copy activities can retry the same load with pre-copy clearing; the full workflow is still **single-operator and serialized**, not protected by a distributed lock.

## Verify Publication

12. Run these Warehouse queries:

```sql
SELECT * FROM dbo.report_health;
SELECT member_ordinal, rule_code, benefit FROM dbo.report_exceptions
ORDER BY member_ordinal, rule_code, benefit;
SELECT * FROM dbo.audit_run ORDER BY started_at DESC;
```

Expect 13 members, 7 subscribers, 6 dependents, 26 coverage elections, 0 parser issues, 16 findings, 10 affected members and publication Succeeded. The current report tables are the latest snapshot; the member/coverage/exception products retain file+rule identity and the audit tracks attempts.

## Challenge and Answer

**Question:** Why clear an empty optional destination rather than simply skip it?

**Answer:** Skipping without clearing leaves earlier rows in shared staging. Copying an empty Delta table can fail because no data file exists. The False branch must delete prior staging rows before publication.

## Completion and Recovery

- [ ] Manifest only follows notebook success; Script result set drives both conditions.
- [ ] True and False branches configured for both optional tables.
- [ ] Latest report health and findings match the reference counts.
- [ ] No schedule or overlapping interactive notebook/pipeline run.

If the expression cannot find `resultSets`, check `Record_attempt` is Query and contains the SELECT with unchanged activity and column names. If a zero-row copy fails, correct the If branch instead of injecting dummy records. For `RULE_VERSION_IMMUTABLE`, restore the approved configuration or use a separately approved new version and regenerated reference SQL; do not silently edit existing reference rows. For failed parsing, inspect notebook/attempt evidence and rerun the entire pipeline only after resolving the input/setup problem.

[Previous: Parsing](02-ingestion.md) | [Guide](README.md) | [Next: Model and review](04-report.md)