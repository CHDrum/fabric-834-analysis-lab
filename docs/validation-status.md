# Validation Status | 834 Analysis

This is a portable synthetic lab, not a hosted deployment. Example bindings are placeholders. No private tenant inventory, deployment evidence, run history, benchmark history, or report capture is distributed. Local checks do not prove a cloud deployment or audience access.

## Local Checks

Run `python -m pytest tests -q -p no:cacheprovider` from the repository root. The suite checks the bounded parser, exact findings, immutable rules, raw preservation, notebook structure, pipeline dependencies, model/report definitions, rebinding, and lab guides. The validation workflow repeats the local suite without cloud credentials.

## Your Deployment

| Check | Required Result |
| --- | --- |
| Complete pipeline | Parser and success-only downstream activities succeed in sequence |
| Exact SQL/model contract | 13 members = 7 subscribers + 6 dependents; 26 elections; 16 findings; 10 affected; zero parse issues; all ten measures match |
| Replay | Same-file/rule products remain unchanged |
| Failed publication | Failed manifest rejected; preceding snapshot preserved; staging restored; failed audit retained |
| Malformed fixture | Parse834 fails with ENVELOPE_VALIDATION_FAILED; no downstream publication; published products and raw bytes unchanged |
| Raw upload | Identical replay unchanged; differing bytes refused by helper |
| Rule immutability | Identical same-version replay accepted; changed same-version content refused |
| Browser report | Three pages and twelve cards render; member filter/reset works |
| Audience access | Approved non-owner has intended access only, with eligible license |
| Recovery | Restore the valid 13-member fixture through a complete serialized run and repeat acceptance |

Follow the [runbook](../instructor/README.md). Save actual bindings, exports, screenshots, and run evidence only in ignored local folders. Keep placeholder packages unbound when distributing them.

## Production Gates

No cross-run lease is implemented; serialize runs because staging and latest-report tables are shared. Early setup failures can occur before guarded audit capture. The malformed fixture does not test every failure path. Approve representative partner profiles, historical accuracy, realistic error density, cold/warm timing, memory, concurrency, and capacity in your own environment. Optional 100K/200K clean fixtures are test inputs, not a performance promise.

Assess current dependency advisories, privacy/access/export/retention, individual licenses, support, and a timed beginner rehearsal before use. Preserve approved secure enterprise transfer and human review. No automated correction, downstream enrollment processing, actual member data, or partner/HIPAA certification is included. Delete only an explicitly approved disposable workspace, never shared capacity.