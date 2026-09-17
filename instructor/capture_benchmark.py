"""Verify a completed clean synthetic scale run against source bytes and retained products."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from instructor.fabric import FabricClient
from src.parse_834 import file_hash


def capture(client, bindings, job_id, members):
    UUID(job_id)
    for name in ("workspace", "warehouse", "pipeline"):
        UUID(bindings[name])
    if bindings.get("synthetic_only") is not True or members not in (100000, 200000):
        raise ValueError("Only the approved clean synthetic benchmark sizes are supported")
    source = ROOT / "data" / "scale" / f"synthetic_{members}.edi"
    digest = file_hash(source)
    job = client.request("GET", f"/v1/workspaces/{bindings['workspace']}/items/{bindings['pipeline']}/jobs/instances/{job_id}")
    if job["status"] != "Completed":
        raise RuntimeError(f"Pipeline has not completed: {job['status']}")
    start = datetime.fromisoformat(job["startTimeUtc"])
    finish = datetime.fromisoformat(job["endTimeUtc"])
    query_started = perf_counter()
    audit_sets = client.sql(bindings["workspace"], bindings["warehouse"],
        f"SELECT TOP (1) * FROM dbo.audit_run WHERE file_id='{digest}' "
        "AND parse_status='Succeeded' AND publication_status='Succeeded' ORDER BY finished_at DESC;")
    if not audit_sets or len(audit_sets[0]) != 1:
        raise AssertionError("No successful retained audit for the exact source bytes")
    audit = audit_sets[0][0]
    if audit["rule_version"] != "SYNTHETIC-2027-v1" or audit["file_name"] != source.name:
        raise AssertionError("Unexpected benchmark profile or file name")
    expected = {"file_bytes": source.stat().st_size, "member_count": members,
        "subscriber_count": members // 2, "dependent_count": members // 2,
        "coverage_count": members * 2, "issue_count": 0}
    for name, value in expected.items():
        if audit[name] != value:
            raise AssertionError(f"Audit {name}: {audit[name]} != {value}")
    predicate = f"file_id='{digest}' AND rule_version='SYNTHETIC-2027-v1'"
    products = client.sql(bindings["workspace"], bindings["warehouse"],
        f"SELECT COUNT_BIG(*) AS member_count, SUM(CAST(is_subscriber AS BIGINT)) AS subscriber_count "
        f"FROM dbo.members WHERE {predicate}; SELECT COUNT_BIG(*) AS coverage_count FROM dbo.coverage WHERE {predicate}; "
        f"SELECT COUNT_BIG(*) AS exception_count FROM dbo.exception_result WHERE {predicate}; "
        "SELECT * FROM dbo.report_health;")
    if products[0][0] != {"member_count": members, "subscriber_count": members // 2}:
        raise AssertionError("Retained member product counts differ")
    if products[1][0]["coverage_count"] != members * 2 or products[2][0]["exception_count"] != 0:
        raise AssertionError("Retained coverage or finding counts differ")
    return {"status": "passed", "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {"file_name": source.name, "sha256": digest, "bytes": source.stat().st_size, "synthetic_only": True},
        "pipeline_job": job, "pipeline_elapsed_seconds": (finish - start).total_seconds(),
        "audit": audit, "physical_counts": products[:3], "latest_report_health_at_observation": products[3],
        "validation_client_elapsed_seconds": round(perf_counter() - query_started, 3),
        "limitations": ["One clean synthetic file per size, not historical proprietary/OE validation.",
            "No cold/warm control, capacity headroom, peak memory, or production SLA established.",
            "Pipeline duration includes all activities; parse/load/rule activity timings were not separately captured.",
            "Client validation duration includes authentication/network overhead; it is not an isolated query benchmark.",
            "Retained products are file/rule-scoped; report tables contain only the latest successful publication."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bindings", type=Path, default=ROOT / "instructor" / "bindings.local.json")
    parser.add_argument("--job", required=True)
    parser.add_argument("--members", type=int, choices=(100000, 200000), required=True)
    arguments = parser.parse_args()
    result = capture(FabricClient(), json.loads(arguments.bindings.read_text(encoding="utf-8")), arguments.job, arguments.members)
    output = ROOT / "docs" / "evidence" / f"benchmark-{arguments.members}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))