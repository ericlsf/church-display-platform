#!/usr/bin/env python3
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
JOBS_FILE = ROOT / "hub" / "config" / "jobs.json"

data = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
jobs = data.get("jobs", data if isinstance(data, list) else [])

groups = defaultdict(list)

for job in jobs:
    if job.get("type") != "deploy_update":
        continue
    payload = job.get("payload", {})
    key = (
        job.get("display_id"),
        payload.get("target"),
        str(payload.get("dry_run", True)).lower(),
    )
    groups[key].append(job)

resolved = 0

for key, matching in groups.items():
    successful = [
        job for job in matching
        if str(job.get("status", "")).lower() == "success"
    ]
    if len(successful) <= 1:
        continue

    successful.sort(key=lambda job: job.get("created_at", ""))
    keep = successful[0]

    for job in successful[1:]:
        job["resolved"] = True
        job["message"] = (
            "Duplicate successful deployment record; "
            f"canonical job is {keep.get('id')}."
        )
        job["updated_at"] = datetime.now().isoformat(timespec="seconds")
        resolved += 1

JOBS_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"Marked {resolved} duplicate deployment record(s) resolved.")
