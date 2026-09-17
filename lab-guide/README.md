# Fabric 834 Enrollment Lab Guide

Work in order in your your tenant. The provided notebook runs Python in Fabric; learners need no local development tools. Do not upload actual enrollment files.

| Module | Minutes | Outcome |
| --- | ---: | --- |
| [00 - Start and scope](00-start.md) | 10 | Correct tenant, workspace, privacy and human-review boundary |
| [01 - Land and configure](01-landing.md) | 20 | Synthetic inputs and published pinned Environment |
| [02 - Parse and reconcile](02-ingestion.md) | 30 | Imported notebook, manifest and Delta staging |
| [03 - Orchestrate products](03-products.md) | 30 | Conditional copy pipeline and versioned Warehouse rules |
| [04 - Model and review](04-report.md) | 25 | Minimized semantic model and three report pages |
| [05 - Validate and replay](05-validate.md) | 10 | Exact findings and stable same-file/rule replay |
| [06 - Wrap up](06-wrap-up.md) | 5 | Accountable handoff and production discovery |
| **Total** | **130** | |

Environment publication and Spark startup can vary. The facilitator should preflight tenant settings, available runtime, custom-library publication, capacity, licenses, repository access and a complete pipeline run before the workshop. If setup exceeds the module timebox, use an instructor-prepared pair workspace in **your tenant**, with its actual permissions and bindings verified. Do not treat the instructor's test-tenant workspace as a learner guest environment.

Pairing and staggered starts are recommended for 10-15 learners. This is an operating precaution, not proof of capacity headroom.

[Repository home](../README.md) | [Begin Module 00](00-start.md)