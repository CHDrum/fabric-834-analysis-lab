# 01 - Land Inputs and Publish the Environment

**Duration:** 20 minutes

**Objective:** preserve the raw sample and make pipeline notebook dependencies repeatable.

## Land Three Artifacts

1. In the workspace choose **New item > Lakehouse**, name it `EnrollmentLanding`, and open **Files**. Create `834-demo` and its `raw`, `code` and `config` subfolders.
2. Upload the exact files below with **Upload files**. If asked to overwrite an existing raw file, cancel and verify the existing artifact. Do not upload the whole repository or the source customer narratives.

| Repository artifact | Lakehouse destination |
| --- | --- |
| [synthetic_834.edi](../data/sample/synthetic_834.edi) | Files/834-demo/raw/synthetic_834.edi |
| [parse_834.py](../src/parse_834.py) | Files/834-demo/code/parse_834.py |
| [rules.json](../config/rules.json) | Files/834-demo/config/rules.json |

3. Confirm the raw sample is 2,907 bytes. Its reference SHA-256 is `17908648f246c1bb69d00cb238f3389aa393d809c1537fda9b070101944910e8`. You will compare the parser manifest to this value later; no local hashing tool is required.

## Publish the Runtime

4. Create an **Environment** named `EnrollmentRuntime`. In its runtime settings select **Fabric runtime 1.3** (Python 3.11). This is the verified teaching runtime. If your tenant does not offer it, ask the facilitator to validate the available runtime first; do not silently assume equivalent behavior.
5. In **Libraries > Custom libraries**, upload both wheels from [resources/wheels](../resources/wheels): `pyx12-4.0.0-py3-none-any.whl` and `defusedxml-0.7.1-py2.py3-none-any.whl`. The folder includes the corresponding third-party license material. Do not upload license text as a package.
6. Save and **Publish** the Environment. Wait for its publish status to succeed. While publication runs, read the rule configuration: version `SYNTHETIC-2027-v1`, as-of `2027-01-01`, illustrative child age 26, relationship 19, no exemptions, and the allowed MED-A/RX-A and MED-B/RX-B pairs.
7. Leave pool sizing at your administrator-approved workshop setting. The instructor reference used a Starter Pool; it does not prove headroom for all participants. Do not copy a larger pool configuration without the capacity owner's approval.

## Completion Checklist

- [ ] Raw, code and config files are in three separate subfolders.
- [ ] Environment publication succeeded with both pinned libraries.
- [ ] Rules are explicitly illustrative, not approved organizational eligibility policy.
- [ ] No notebook `%pip`, shell installation, external storage account or gateway was needed.

## Challenge and Answer

**Question:** Why not add `%pip install pyx12` at the top of the notebook?

**Answer:** Pipeline-triggered Fabric notebooks do not support that installation path. A published Environment carries the pinned dependencies into both interactive and pipeline execution. Attaching an unpublished environment is not equivalent.

## Recovery

If library publication fails, inspect the Environment's publish errors and verify the wheel filenames/runtime. Do not bypass the restriction with shell pip. If permissions prevent publication, the facilitator can publish the approved Environment and grant the required use rights within your tenant. Conditional-create checks in the instructor helper are not WORM storage, portal overwrite protection, or a retention policy.

[Previous: Start](00-start.md) | [Guide](README.md) | [Next: Parse and reconcile](02-ingestion.md)