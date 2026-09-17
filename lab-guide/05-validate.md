# 05 - Validate Exact Findings and Replay

**Duration:** 10 minutes

**Objective:** prove the expected source, finding set and replay behavior, not just a successful activity status.

## Steps

1. Run all of [03_validate.sql](../sql/03_validate.sql) in `EnrollmentProducts`. **Zero failure rows is success.** The script targets the 13-member adversarial sample and its exact hash; it is not the scale-file acceptance script.
2. Compare [expected.json](../data/sample/expected.json) and the table below. The expected set includes benefit qualifiers; checking only a rule count is insufficient.

| Member ordinal | Findings | Benefit where applicable |
| --- | --- | --- |
| 1 | DUPLICATE_MEMBER; MULTIPLE_SUBSCRIBERS | |
| 2 | AMBIGUOUS_SUBSCRIBER; OVERAGE_DEPENDENT | |
| 4 | DEPENDENT_PLAN_DIFFERENCE twice | HLT; PDG |
| 5 | MISSING_DOB; MISSING_EMPLOYEE_ID; MISSING_SSN | |
| 7 | MEDICAL_RX_MISMATCH | |
| 8 | DEPENDENT_PLAN_DIFFERENCE | PDG |
| 9 | UNKNOWN_PLAN | HLT |
| 10 | ORPHAN_DEPENDENT | |
| 12 | MISSING_SSN | |
| 13 | DUPLICATE_MEMBER; MULTIPLE_SUBSCRIBERS | |

3. Confirm no pipeline/notebook is active. Execute `EXEC dbo.publish_enrollment_products;` again against the unchanged successful staging, then run the same validation SQL. It must not append duplicate file+rule products. This tests publication replay, not a new parsing attempt.
4. Inspect `dbo.audit_run` and the current `dbo.report_health`. A later complete pipeline replay creates a new attempt ID while preserving source hash/rule identity and exact product results. Do not start that extra Spark run inside the timebox unless the facilitator directs it.
5. Verify the report/model's unfiltered 13/7/6/26/16/10 counts and zero reconciliation difference. A failed report render is a separate failure from the SQL checks, not something a passing pipeline overrides.

## Rules Are Configurable, Not Arbitrary

The teaching age is 26 on 2027-01-01, relationship 19, with no exemptions. Subscribers require SSN/DOB/employee ID; dependents require SSN/DOB. Real rules require approved owners, policy, historical accuracy and version promotion. Never edit an existing rule version in place. The rule generator and SQL guard reject incompatible definitions under the same version.

## Challenge and Answer

**Question:** Does a clean 100,000- or 200,000-member result prove the rules work on proprietary files?

**Answer:** No. A clean scale fixture tests one synthetic shape and execution volume, with a deliberately low exception workload. Historical accuracy, partner profiles, realistic error distributions, privacy, concurrency and capacity headroom are separate gates. Restore the adversarial file after scale testing before applying this module's acceptance script.

## Completion and Recovery

- [ ] Exact finding set, counts, hash and lineage validated with no failure rows.
- [ ] Same successful staging replay does not multiply products.
- [ ] SQL/model/report/access evidence kept distinct.

If the source hash differs, restore the original sample without editing it. If the latest report is a scale file, rerun the full pipeline with `synthetic_834.edi` after confirming it is idle, then rerun this check. For a rule-version mismatch, restore the approved configuration/reference pair rather than altering expected results. A failed parse must not trigger manual publication of old staging.

[Previous: Reporting](04-report.md) | [Guide](README.md) | [Next: Wrap up](06-wrap-up.md)