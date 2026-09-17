# 00 - Start and Scope

**Duration:** 10 minutes

**Objective:** establish the right environment and preserve the human decision point.

## Steps

1. Sign in to [Fabric](https://app.fabric.microsoft.com/) with your organizational work account. Confirm the tenant in the account menu. Use a learner workspace in your organization's approved capacity, not the instructor's separate testing tenant.
2. Create or open the assigned isolated workspace `Fabric-834-<your-pair-name>`. Confirm permission to create Lakehouse, Environment, Notebook, Data pipeline, Warehouse and semantic-model items. Contributor is an appropriate authoring role for this isolated synthetic lab; workspace creation/capacity assignment can require separate rights.
3. Ask the facilitator to confirm Fabric tenant enablement, approved capacity, Spark availability, custom-library publishing, web modeling, and individual Power BI licenses. Capacity alone does not provide author licenses or unrestricted viewing below F64. Do not purchase capacity or alter shared tenant settings to unblock the workshop.
4. Sign in to this private GitHub repository, use **Code > Download ZIP**, and extract it. Confirm you have the notebook, wheels, source parser, rule configuration, SQL and synthetic sample. No local Python, Git, CLI or Desktop installation is required.
5. Review the [learning requirements](../docs/requirements-traceability.md). Compare the bounded synthetic parsing and review pattern with the additional gates required for real inputs.
6. Nominate one operator per pair. Keep scheduling disabled and do not overlap notebook/pipeline runs. Stop your interactive Spark session before starting the pipeline later, to avoid an unnecessary extra session.

## Business Boundary

This illustrative scenario makes enrollment analysis repeatable as file sizes and seasonal volumes change. Existing secure enterprise transfer and analyst ownership of external resolution remain. Approved historical and representative partner files are future validation inputs, not files supplied in this lab.

The source can contain identifiers, demographics, relationships, dates, benefit elections and plans: PII and potential PHI. Only the fabricated teaching file is permitted. Findings support **human review**; automated correction and downstream enrollment processing are excluded.

## Completion Checklist

- [ ] Correct tenant, isolated workspace, approved capacity and individual licenses.
- [ ] Private repository access works without anonymous links or shared credentials.
- [ ] One operator, no schedules, synthetic data only.
- [ ] You can distinguish a parser/rule demonstration from a certified production enrollment solution.

## Challenge and Answer

**Question:** Does this lab require a new secure file-transfer system?

**Answer:** No. It begins with a synthetic file at a controlled analytical landing boundary. A production handoff from the existing secure transfer needs approval and implementation; the lab does not replace it.

## Recovery

If an item type or runtime is unavailable, resolve that prerequisite with the facilitator. Do not use a production workspace, another person's login, or an unapproved tenant. Do not substitute a real file for missing sample data.

[Guide](README.md) | [Next: Land and configure](01-landing.md)