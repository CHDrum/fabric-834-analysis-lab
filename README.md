# 834 Enrollment Analysis in Microsoft Fabric

A synthetic workshop for turning enrollment files into bounded parsing, reconciled products, versioned rules, and human review. Keep existing secure enterprise transfer and external correction processes; do not automate enrollment corrections.

**Audience:** Fabric beginners. **Hands-on time:** 130 minutes. **Learner tools:** a browser and the repository ZIP. No local Python, Git, CLI, or Power BI Desktop is required. Python executes in the provided Fabric notebook, not on the learner's machine.

## Start Here

1. Select **Code > Download ZIP** and extract it. Sign in to GitHub first if repository access requires it.
2. Follow the [seven-module lab guide](lab-guide/README.md) in **your tenant and approved capacity**. Provision your own lab workspace; no shared demo access is included.
3. Use the [instructor runbook](instructor/README.md) for deployment preparation and the [validation checklist](docs/validation-status.md) to verify your own environment.

## What You Build

`Preserved synthetic X12 -> EnrollmentLanding -> published EnrollmentRuntime -> LandAndParse834 -> EnrollmentIngestion -> EnrollmentProducts -> EnrollmentAnalytics -> human review`

The parser uses pyx12 4.0.0 with bounded member batches, then Arrow Parquet and Delta staging. The pipeline copies only after notebook success, handles empty coverage/issue tables explicitly, and executes transactional T-SQL publication. Physical reporting tables exclude DOB, employee ID, full SSN and SSN fragments from the semantic model. This is data minimization, not a complete security boundary.

| Verified adversarial fixture | Result |
| --- | ---: |
| Members / subscribers / dependents | 13 / 7 / 6 |
| Coverage elections / parser issues | 26 / 0 |
| Findings / affected members | 16 / 10 |
| Member reconciliation difference | 0 |
| Rule version / as-of date | SYNTHETIC-2027-v1 / 2027-01-01 |

The [exact result contract](data/sample/expected.json) identifies every finding, not just the total. The [synthetic generator](data/generate_synthetic.py) also supports larger clean fixtures for optional capacity testing. Measure runtime, concurrency, and error distributions in your own environment; this repository provides no performance SLA or partner-file certification.

## Deployment Status

This repository is a portable lab, not a hosted service. Supply your own workspace, capacity, identities, and bindings. See [validation status](docs/validation-status.md) for the checks to repeat after deployment.

Validate exact SQL/model results, replay, failed-publication preservation, and all three report pages. Run the malformed-file recovery exercise only in an isolated synthetic workspace. **User access requires appropriate permissions and eligible licenses.** A model query does not prove report rendering or audience access.

## Repository Contents

| Location | Purpose |
| --- | --- |
| [lab-guide](lab-guide/README.md) | Seven browser-first modules, answer keys and recovery |
| [data/sample](data/sample) | Fabricated X12 and exact expected findings |
| [src/parse_834.py](src/parse_834.py) | Bounded pyx12 adapter and lineage contracts |
| [config/rules.json](config/rules.json) | Illustrative, immutable-version business rules |
| [notebooks/LandAndParse834.ipynb](notebooks/LandAndParse834.ipynb) | Importable notebook without saved outputs or instructor bindings |
| [resources/wheels](resources/wheels) | Pinned custom Environment wheels and licenses |
| [sql](sql) | Schema, rules, transactional publication and exact acceptance |
| [solution](solution) | Independent rebindable builders and portable request packages |
| [model reference](solution/portable/measures.md) | Exact aliases, DAX, formats and relationship |
| [instructor runbook](instructor/README.md) | Deployment, rebinding, serialized runs, recovery, scale and handoff |
| [data and rule dictionary](docs/data-dictionary.md) | Source mapping, product grains, rule semantics and exact findings |
| [requirements traceability](docs/requirements-traceability.md) | EDI-01 through EDI-07 and production acceptance gates |
| [tests](tests) | Parser, rule, model, report, helper and artifact checks |

This repository works independently of the [Document Administration lab](https://github.com/CHDrum/fabric-document-administration-lab). Together they fit the 330-minute agenda: orientation 20, document 130, break 20, 834 130, wrap-up 30. Reserve an optional 30-minute buffer. For 10-15 beginners, pair learners and stagger Spark starts.

## Boundaries

Large enrollment files and seasonal volume changes are generic design considerations. No real member data, historical partner files, transfer-system integration, or downstream enrollment processing is included. The synthetic 005010X220A1 profile is not HIPAA or partner implementation-guide certification.

Use one active run per workspace. Shared staging/latest-report tables have no cross-run lease. Early notebook setup failures are not guaranteed a Warehouse audit row. Real use requires approved landing, privacy, access/export tests, audit, retention, reconciliation, historical accuracy, timing, cadence, ownership, support, and capacity assessment. Do not expose tenant data or reports through Publish to web. Do not pause or delete shared capacity as cleanup.

Original workshop content; the [FabricHackathon guide](https://github.com/nairsanjeev/FabricHackathon/tree/master/lab-guide) informed learning sequence only.