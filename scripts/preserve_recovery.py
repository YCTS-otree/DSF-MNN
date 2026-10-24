"""Freeze the isolated study, declared runtime dependencies and CPU assets; no secrets."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import platform
import sqlite3
import sys
from uuid import uuid4

from freeze_baseline import ROOT, archive_files, json_write, node_files, python_files, safe_file, sha
from record_experiment import write_source_snapshot

parser = argparse.ArgumentParser()
parser.add_argument("run", type=Path)
args = parser.parse_args()
run = args.run.resolve()
run.relative_to(ROOT / "experiments")
if not run.name.startswith("private-recovery-"):
    raise SystemExit("Private study directory required")
target = run / ("preservation-" + uuid4().hex[:12]); target.mkdir()
source_digest = write_source_snapshot(target)
files, python_packages, plugins = python_files(("tokenizers", "jinja2"))
node_entries, node_packages = node_files(ROOT.parent / "DS_Friend/.runtime/node_modules", (
    "cordis", "dsh-session", "dsh-session-projection", "dsh-agent", "dsh-llm", "dsh-system-prompt", "dsh-tools",
    "dsh-token-meter", "dsh-session-persistence-jsonl", "dsh-agent-loop", "dsh-compaction", "dsh-llm-deepseek"))
files.update(node_entries)
environment = archive_files(target / "environment-windows.zip", files)
json_write(target / "environment-files.json", environment)
json_write(target / "environment-lock.json", {"python": sys.version, "platform": platform.platform(),
    "python_packages": python_packages, "node_packages": node_packages, "pytest_plugins": plugins,
    "network_credentials": "excluded; remote requests require trusted DSF loader at deployment",
    "tokenizer_assets": "private work/tokenizer and original vendor download; no custom downloaded Python executed"})
databases = []
for file in (run / "work").rglob("*"):
    if file.is_file() and file.suffix in {".sqlite", ".sqlite3", ".db"}:
        safe_file(file, run)
        destination = target / "consistent-databases" / file.relative_to(run)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(file.resolve().as_uri() + "?mode=ro", uri=True) as source:
            with sqlite3.connect(destination) as output:
                source.backup(output)
                integrity = output.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    raise SystemExit("Study database integrity failed; failed freeze retained")
        databases.append({"source": file.relative_to(run).as_posix(), "consistent_copy": destination.relative_to(target).as_posix(),
                          "sha256": sha(destination), "integrity": integrity})
json_write(target / "consistent-databases.json", databases)
files = {}
for file in (run / "work").rglob("*"):
    if file.is_file():
        safe_file(file, run)
        # Retain forensic WAL/SHM remnants too; consistent images above use backup API.
        files[file.relative_to(run).as_posix()] = (file, run)
for file in run.glob("*.json"):
    files[file.name] = (file, run)
study = archive_files(target / "private-study.zip", files)
json_write(target / "study-files.json", study)
manifest = {"schema": "dsf-mnn-recovery-preservation/1", "created_at": datetime.now().astimezone().isoformat(),
    "private": True, "source_tree_sha256": source_digest, "study_files": len(study), "environment_files": len(environment),
    "original_study_bytes": sum(row["bytes"] for row in study), "consistent_databases": len(databases),
    "historical_source_limit": "Initial extraction has three SHA-verified critical source files; early native attempts lack full contemporaneous source snapshots. Latest native attempt has explicit source capture.",
    "files": {file.name: {"bytes": file.stat().st_size, "sha256": sha(file)} for file in target.iterdir() if file.is_file()}}
json_write(target / "manifest.json", manifest)
print(json.dumps({"directory": str(target), "study_files": len(study), "environment_files": len(environment),
                  "study_bytes": manifest["original_study_bytes"], "source_tree_sha256": source_digest}))
