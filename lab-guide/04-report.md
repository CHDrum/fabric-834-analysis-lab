# 04 - Model and Review

**Duration:** 25 minutes

**Objective:** expose minimal review information and reusable measures without automating decisions.

## Build the Model

1. Open `EnrollmentProducts` and select **New semantic model**. Name it `EnrollmentAnalytics` and save it in your lab workspace. Select only `report_members`, `report_exceptions`, and `report_health`: physical Warehouse tables, not views or the sensitive staging/curated tables.
2. Use **Open data model** and rename table display aliases to `Members`, `Exceptions`, and `Health`, respectively. Keep the physical source bindings in Direct Lake.
3. Create one relationship: `Members.member_ordinal` on the **one** side to `Exceptions.member_ordinal` on the **many** side, single-direction filtering from Members to Exceptions. Leave Health disconnected. Remove extra auto-suggested relationships, especially on file or attempt IDs that are repeated.
4. Add every measure in [the generated reference](../solution/portable/measures.md), using its exact aliases, DAX and formats. Mark identifiers/ordinals as **Don't summarize**. The model contains no DOB, employee ID, full SSN, last-four or SSN-presence fields. Author roles can still access underlying items; table projection does not enforce privacy.

## Create Three Browser Report Pages

5. Select **New report** from web modeling and save it as `Fabric 834 Analysis`. Add standard cards, tables, a bar chart and a slicer as below. Avoid overlapping visuals and label the content as synthetic review findings.

| Page | Fields and visuals | Expected unfiltered sample |
| --- | --- | --- |
| File health | Cards: Member Count, Subscribers, Dependents, Coverage Elections, Parser Issues, Member Reconciliation Difference. Table: Health.file_name, rule_version, as_of_date, publication_status. | 13, 7, 6, 26, 0, 0 |
| Exceptions | Cards: Exception Count, Affected Members, Exception Member Rate. Bar chart: Exceptions.rule_code and Exception Count. Table: member_ordinal, rule_code, benefit, severity. Slicer: rule_code. | 16 findings, 10 members, 76.9% |
| Review | Table: Members.member_ordinal, member_id, family_id, member_role, source_segment, exception_count. Second table: Exceptions.member_ordinal, rule_code, benefit, source_segment, file_id, attempt_id, rule_version. Slicer: Members.member_ordinal. | Selecting ordinal 5 shows three missing-field findings |

6. On Review, select member ordinal 5 and verify MISSING_DOB, MISSING_EMPLOYEE_ID and MISSING_SSN. Select ordinal 4 and verify plan differences for HLT and PDG. These are review findings, not instructions to change coverage.
7. Clear filters and reconcile the cards to the source manifest. Health measures remain file-wide; a rule filter on Exceptions intentionally does not reverse-filter Members. Do not add bidirectional relationships to make unrelated cards appear filtered. Explain each denominator when interpreting a filtered rate.
8. Save and reopen all pages in your own browser. Record rendering and permissions separately from model/SQL validation. Check all three pages, displayed values, member filtering, and reset, then test approved non-owner access separately.

## Analyst Handoff

Use file hash, attempt ID, member ordinal, rule code, rule version and segment lineage to identify a finding. Human review determines validity and coordinates resolution with authorized external parties. Never email raw sample structure as a template for real PII, auto-correct an enrollment record, or feed downstream enrollment from this lab.

## Challenge and Answer

**Question:** Why 16 findings but only 10 affected members?

**Answer:** A member can have several findings, and a plan-difference rule can emit one finding per benefit. Findings and affected members have different grains; neither equals the number of corrections or eligibility decisions.

## Completion and Recovery

- [ ] Exactly three minimized physical model tables and one single-direction relationship.
- [ ] Measures and member-filter behavior match the sample.
- [ ] Report rendering status personally observed and recorded.
- [ ] No public sharing or automatic correction path.

If the editor does not open, inspect pop-up blocking and model-write rights. For blank/stale results after publication, refresh/reframe the model and check Warehouse report_health; do not import a second raw copy. For an access failure, verify workspace, model Build/read rights, underlying-data access and individual licenses with the owner. Never bypass controls by exporting intermediate member tables.

[Previous: Products](03-products.md) | [Guide](README.md) | [Next: Validate and replay](05-validate.md)