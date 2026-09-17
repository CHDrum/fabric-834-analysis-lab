# Data and Rule Dictionary | 834 Analysis

The authoritative contracts are [parse_834.py](../src/parse_834.py), [rules.json](../config/rules.json), and [Warehouse SQL](../sql/01_enrollment_products.sql). This synthetic 005010X220A1 teaching profile is not a certified X12 or partner implementation-guide validator.

## Source and Identity

The [sample](../data/sample/synthetic_834.edi) is 2,907 unchanged bytes with SHA-256 `17908648f246c1bb69d00cb238f3389aa393d809c1537fda9b070101944910e8`. It contains 13 members, including a deliberately duplicated business identifier, and 26 coverage elections. Fake names and 900-series SSNs are fabricated; no actual member or historical/OE file is included.

| Source Concept | Teaching Mapping | Boundary |
| --- | --- | --- |
| ISA/GS/ST and matching trailers | Interchange, group and transaction control values/counts | Segment/envelope-oriented, not line-oriented; mismatches fail parsing |
| INS member loop | `is_subscriber`, relationship and member ordinal | Subscriber/dependent structure, not 837 HL claim hierarchy |
| REF 0F / REF 17 | `family_id` / `member_id` | Synthetic mapping; approve partner identifiers before real use |
| Illustrative REF ZZ | `employee_id` | Not a universal employee-ID convention |
| DMG | Optional DOB, normalized ISO date | Missing fields remain reviewable; malformed dates require validation |
| SSN presence | `has_ssn` and last four digits in restricted curated products | Full SSN stays out of curated tables; raw source still contains it |
| Repeated HD and DTP | Benefit, plan, level, effective/end dates per election | HLT medical / PDG prescription; repeated coverage retained |

`file_id` is the SHA-256 of original bytes, `attempt_id` is a new UUID for an invocation, and `rule_version` identifies immutable rule content. `member_ordinal` is the position in a source file, not a global identity. Source segment and envelope controls support review back to unchanged input. Identifiers, DOB, elections, and plans would constitute PII and potentially PHI in a real file.

## Data Products

| Product / Grain | Fields and Use |
| --- | --- |
| Members: file + member ordinal | File/attempt, member/family IDs, subscriber flag, relationship, optional DOB/employee ID, SSN presence/last4, three control values, source segment |
| Coverage: file + member ordinal + coverage ordinal | File/attempt, benefit, plan ID, coverage level, effective/end dates, source segment |
| Parser issues: source member/segment/issue | File/attempt, ordinal, issue code and severity; no raw segment echo in failure details |
| Manifest: one attempt | Hash, filename/bytes, parser/rule version, start/finish, status, member/subscriber/dependent/coverage/issue counts and sanitized failure code |
| Lakehouse `stage_*` / Warehouse `stg_*` | String staging; overwritten only by a serialized run; reconciled before publication |
| Lakehouse `parse_audit` and Files attempts | Append/per-attempt parsing and staging evidence; early setup failures can precede these writes |
| Warehouse `audit_run` | Attempt-level parse/publication status and counts; not guaranteed for notebook failures because copying is success-only |
| Warehouse `members`, `coverage`, `exception_result` | Retained file/rule products; same file/rule replay replaces that version, other file/rule versions remain |
| `report_members` | Latest member ordinal, synthetic IDs, role/relationship, exception count and lineage; no DOB/employee ID/SSN data |
| `report_exceptions` | Latest member/rule/benefit/severity plus segment, hash, attempt and rule version |
| `report_health` | Latest successful file, hash, attempt, rule/as-of, counts and publication status |

The three physical report tables feed the explicit Direct Lake model. Only Members.member_ordinal (one) -> Exceptions.member_ordinal (many) is related; Health is disconnected. Ordinal-only model relationships are valid because these tables contain **one latest snapshot**. Retained multi-file tables require file/rule composite keys. [Model reference](../solution/portable/measures.md) lists the exact ten measures and aliases.

## Rule Configuration

Version `SYNTHETIC-2027-v1` evaluates at `2027-01-01`. Age 26, relationship 19, no exemptions, required subscriber SSN/DOB/employee ID, required dependent SSN/DOB, comparable HLT/PDG benefits, and pairs MED-A/RX-A or MED-B/RX-B are illustrative workshop settings, not approved organizational policy. Six versioned reference tables hold settings, required fields, relationships/exemptions, comparable benefits, plans and allowed pairs.

| Finding | Meaning |
| --- | --- |
| DUPLICATE_MEMBER | Repeated business member ID in the same file/rule scope |
| MULTIPLE_SUBSCRIBERS / ORPHAN_DEPENDENT / AMBIGUOUS_SUBSCRIBER | More than one subscriber, none, or ambiguous parent within a family |
| MISSING_SSN / MISSING_DOB / MISSING_EMPLOYEE_ID | Configured required field absent for that member role |
| FUTURE_DOB | DOB later than the configured as-of date |
| OVERAGE_DEPENDENT | Nonexempt configured child relationship with whole-year age at or above 26 |
| MISSING_COVERAGE_EFFECTIVE_DATE / INVALID_COVERAGE_PERIOD | Missing coverage start or end before start |
| DUPLICATE_COVERAGE / AMBIGUOUS_COVERAGE | Duplicate active election or more than one active election per benefit |
| UNKNOWN_PLAN | Active benefit/plan pair absent from allowed plans |
| DEPENDENT_PLAN_DIFFERENCE | One unambiguous child and subscriber active plan per comparable benefit differ; both plans must be known |
| SUBSCRIBER_COVERAGE_MISSING | Dependent has a comparable benefit without subscriber coverage |
| MEDICAL_COVERAGE_MISSING / RX_COVERAGE_MISSING | Only one of the medical/Rx benefits is active |
| MEDICAL_RX_MISMATCH | Unambiguous known medical/Rx plans are not an allowed pair |
| PARSE_* | Sanitized nonfatal parser issue promoted for review |

Active means effective date on/before as-of and no earlier end date. Age uses calendar birthday comparison, not days/365. Findings are review signals, not corrections. Multiple findings can affect one member; unknown or ambiguous plans do not also produce misleading known-plan mismatch comparisons. Repeated same-qualified coverage dates and broader proprietary/date edge cases still need production-profile proof.

## Frozen Adversarial Result

[expected.json](../data/sample/expected.json) and [acceptance SQL](../sql/03_validate.sql) compare exact tuples in both directions:

| Ordinal | Expected Findings |
| --- | --- |
| 1 | DUPLICATE_MEMBER; MULTIPLE_SUBSCRIBERS |
| 2 | AMBIGUOUS_SUBSCRIBER; OVERAGE_DEPENDENT |
| 4 | DEPENDENT_PLAN_DIFFERENCE for HLT and PDG |
| 5 | MISSING_DOB; MISSING_EMPLOYEE_ID; MISSING_SSN |
| 7 | MEDICAL_RX_MISMATCH |
| 8 | DEPENDENT_PLAN_DIFFERENCE for PDG |
| 9 | UNKNOWN_PLAN for HLT |
| 10 | ORPHAN_DEPENDENT |
| 12 | MISSING_SSN |
| 13 | DUPLICATE_MEMBER; MULTIPLE_SUBSCRIBERS |

Total: 13 members = 7 subscribers + 6 dependents; 26 elections; zero parser issues; 16 findings affecting 10 members; zero member reconciliation difference. Clean scale files intentionally have no findings and are unsuitable as a replacement for this functional test. Use the [runbook](../instructor/README.md) for replay, failure recovery, scale limitations and human handoff.