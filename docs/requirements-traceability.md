# Requirements Traceability | 834 Analysis

This original synthetic workshop demonstrates bounded X12 834 parsing, versioned rules, and human review. `EDI-*` IDs identify learning requirements. **Built** means synthetic implementation; **Gate/context** means described but not connected or certified. No organization's files, operating history, staffing, or deployment inventory is included.

| ID | Learning Requirement and Coverage | Learner Module | Artifact | Acceptance |
| --- | --- | --- | --- | --- |
| EDI-01 | Make enrollment analysis repeatable while preserving secure enterprise transfer and human review. Gate/context plus bounded synthetic pattern. | [Start](../lab-guide/00-start.md) | [Runbook](../instructor/README.md) | Illustrative review workflow and proposed approved landing; no transfer integration claim. |
| EDI-02 | Preserve source bytes, parse identifiers/demographics/relationships/dates/elections/plans, reconcile members and failures. Built synthetic profile. | [Parse](../lab-guide/02-ingestion.md) | [Parser](../src/parse_834.py) and [dictionary](data-dictionary.md) | Exact hash/bytes, 13 = 7 + 6, 26 elections, ordinal/control/segment lineage; [malformed-fixture recovery procedure](../instructor/README.md#serialized-runs-and-recovery); parser/landing nodes. |
| EDI-03 | Overage dependents, subscriber/dependent plan differences, missing SSN/DOB/employee ID, medical/Rx mismatch, duplicates and configurable rules. Built illustrative rules. | [Products](../lab-guide/03-products.md) | [Rules](../config/rules.json) and [SQL](../sql/01_enrollment_products.sql) | [Exact contract](../data/sample/expected.json): 16 tuples, 10 affected; immutable rule content; rules node. |
| EDI-04 | Reduce manual preparation while retaining analyst review and coordination of external resolution; exclude corrections/downstream enrollment. Built review products, no automation of decisions. | [Report](../lab-guide/04-report.md) | [Model reference](../solution/portable/measures.md) | Three minimized physical report tables, ten DAX measures; check health/exceptions/review pages, cards, and filter/reset after deployment. Test non-owner access separately; human-review node. |
| EDI-05 | Exercise optional 100K/200K synthetic scale with timing and reconciliation. Generator supplied; production performance and accuracy are gates. | [Validate](../lab-guide/05-validate.md) | [Synthetic generator](../data/generate_synthetic.py) | Expect 100K/200K members and 200K/400K elections with zero findings for clean fixtures. Measure in your own environment; no SLA or headroom promise. |
| EDI-06 | PII/potential PHI, approved landing, privacy, audit, access/export and retention. Built minimized synthetic model/lineage; production controls are gates. | [Landing](../lab-guide/01-landing.md) | [Runbook](../instructor/README.md) | Raw/curated/report boundaries, no full SSN curated and no DOB/SSN/employee ID in model. Early-failure audit and non-owner control gaps are explicit; governance/details panels. |
| EDI-07 | Cadence, ownership/support, concurrency/recovery, capacity and production acceptance. Built serialized pattern/replay guard; production coordination is a gate. | [Wrap-up](../lab-guide/06-wrap-up.md) | [Verifier](../instructor/verify_solution.py) and [runbook](../instructor/README.md) | Validate exact SQL/model results, replay, failure preservation, and valid-source recovery; one-operator restriction, no cross-run lease; operational handoff and production gates. |

## Required Gates Before Real Inputs

| Gate | Evidence Still Required |
| --- | --- |
| Source profile and historical accuracy | Approved partner mapping and required-field/temporal policies; reconciled historical fixtures and representative seasonal inputs |
| Timing and capacity | Representative errors/coverage density, cold/warm and concurrent runs, activity timings, peak memory, recovery load and capacity-owner headroom approval |
| Privacy/access/export/retention | Approved landing and secure transfer contract; tested non-owner roles, report/SQL/OneLake permissions, minimal export, retention/legal hold and disposal |
| Audit and support | Complete invocation correlation including early failures, approved sanitized logs, alerting, owners and support escalation |
| Concurrency and recovery | Real cross-run coordination or isolated attempt staging; restart/rollback/replay tests under failure and contention |
| Human review | Approved case-routing/export process and external resolution ownership; no automated correction or downstream enrollment processing |

The repositories use no historical files, actual member data, real transfer connection, or certified partner parser. Keep the existing enterprise transfer and approval process in place.