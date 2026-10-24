"""One-time preservation of pre-recorder synthetic artifacts. Never rewrites a run."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / "experiments/retained-initial"
target.mkdir(parents=True, exist_ok=False)
records = []
for name in ("baseline-v1.0.0.json", "results-v1.0.0.json"):
    original = ROOT / "benchmarks" / name
    shutil.copy2(original, target / name)
for pattern in ("benchmarks/*/*.sqlite", "pytest-*/*.sqlite", "pytest-*/**/*.sqlite", "adapter-*/*.sqlite"):
    for original in (ROOT / ".cache").glob(pattern):
        relative = original.relative_to(ROOT / ".cache")
        destination = target / "artifacts" / relative
        if destination.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, destination)
        records.append({"original": ".cache/" + relative.as_posix(), "retained": destination.relative_to(target).as_posix(),
                        "bytes": original.stat().st_size, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
provenance = {"schema": "dsf-mnn-retrospective-record/1", "artifacts": records,
              "source_snapshot_at_original_run": None,
              "full_original_console_logs": None,
              "notes": ["Original early run source trees were not captured before execution; do not claim exact historical source provenance.",
                        "Baseline used time.monotonic for retrieval timing; Windows resolution produced zero-valued short-query timings. Index throughput used perf_counter.",
                        "Optimized code skips redundant FTS deletes on insert/rebuild and uses perf_counter for query timing. Rankings unchanged.",
                        "Prior pytest runs: default Windows temporary-directory permission failure; missing .cache parent; SQL edge placeholder failure (6 passed); Windows backup handle failure (26 passed); then 34 passed, 38 passed and Node 5 passed. Full logs were not preserved at that time.",
                        "Retained databases are synthetic-only, including failed/corrupt test artifacts. They are research artifacts, not production backups."]}
(target / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"retained_files": len(records), "bytes": sum(r["bytes"] for r in records)}, ensure_ascii=False))
