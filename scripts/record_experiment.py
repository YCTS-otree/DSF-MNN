"""Append-only local experiment recorder. Reads only explicit project source directories."""
import argparse
from datetime import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import time
from uuid import uuid4
import zipfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = ("src", "tests", "adapters", "scripts", "configs", "docs")
SUFFIXES = {".py", ".sql", ".mjs", ".json", ".ps1", ".sh", ".md"}


def source_files():
    files = [ROOT / name for name in ("pyproject.toml", "README.md", "AGENTS.md", "CHANGELOG.md", "THIRD_PARTY_NOTICES.md", ".gitignore", ".gitattributes") if (ROOT / name).is_file()]
    for directory in SOURCE_DIRS:
        files.extend(p for p in (ROOT / directory).rglob("*") if p.is_file() and p.suffix in SUFFIXES and "__pycache__" not in p.parts)
    return sorted(files)


def write_source_snapshot(target):
    hashes = {}
    with zipfile.ZipFile(target / "source.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in source_files():
            name = file.relative_to(ROOT).as_posix()
            data = file.read_bytes()
            hashes[name] = hashlib.sha256(data).hexdigest()
            archive.writestr(name, data)
    (target / "source-files.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    return hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()


def capture(argv, environment, directory):
    started = time.perf_counter()
    result = subprocess.run(argv, cwd=ROOT, env=environment, capture_output=True)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "stdout.log").write_bytes(result.stdout)
    (directory / "stderr.log").write_bytes(result.stderr)
    print(result.stdout.decode("utf-8", errors="replace"), end="")
    if result.stderr:
        print(result.stderr.decode("utf-8", errors="replace"), end="", file=sys.stderr)
    return {"command": argv, "exit_code": result.returncode, "elapsed_seconds": time.perf_counter() - started}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", choices=["test", "benchmark"])
    parser.add_argument("--dsh-node-modules")
    parser.add_argument("--label", default="validation")
    args = parser.parse_args()
    local = datetime.now(ZoneInfo("Asia/Shanghai"))
    run_id = local.strftime("%Y%m%dT%H%M%S%z") + "-" + uuid4().hex[:10]
    run_dir = ROOT / "experiments" / run_id
    run_dir.mkdir(parents=True)
    source_digest = write_source_snapshot(run_dir)
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"}
    environment["MNN_TEST_ARTIFACTS"] = str(run_dir / "work" / "node")
    if args.dsh_node_modules:
        environment["DSH_NODE_MODULES"] = str(Path(args.dsh_node_modules).resolve())
    git_read = ["git", "-c", "safe.directory=" + ROOT.as_posix()]
    revision = subprocess.run([*git_read, "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    status = subprocess.run([*git_read, "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    node = subprocess.run(["node", "--version"], capture_output=True, text=True)
    manifest = {"schema": "dsf-mnn-experiment/1", "id": run_id, "label": args.label, "suite": args.suite,
                "started_at": local.isoformat(), "timezone": "Asia/Shanghai", "source_tree_sha256": source_digest,
                "git_revision": revision.stdout.strip() if revision.returncode == 0 else None,
                "git_dirty": bool(status.stdout.strip()), "python": sys.version, "python_executable": sys.executable,
                "sqlite": sqlite3.sqlite_version, "node": node.stdout.strip(), "platform": platform.platform(),
                "dataset": "synthetic-only", "model": "lexical-hash-baseline/1/256", "network_model_requests": 0,
                "dsh_installed_path": environment.get("DSH_NODE_MODULES"), "steps": []}
    manifest["pytest"] = importlib.metadata.version("pytest")
    if environment.get("DSH_NODE_MODULES"):
        package_dir = Path(environment["DSH_NODE_MODULES"]) / "@deepseek-ai"
        manifest["dsh_packages"] = {}
        for name in ("dsh-compaction-basic", "dsh-compaction", "cordis"):
            manifest["dsh_packages"][name] = {
                "version": json.loads((package_dir / name / "package.json").read_text(encoding="utf-8"))["version"],
                "sha256": hashlib.sha256((package_dir / name / "lib/index.js").read_bytes()).hexdigest(),
            }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        if args.suite == "test":
            work = run_dir / "work"
            # A brand new run directory; pytest is never pointed at an existing result directory.
            manifest["steps"].append(capture([sys.executable, "-m", "pytest", "-q", "--tb=short", "--basetemp", str(work), "--junitxml", str(run_dir / "junit.xml")], environment, run_dir / "python"))
            node_tests = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "tests").glob("*.test.mjs"))]
            manifest["steps"].append(capture(["node", "--test", *node_tests], environment, run_dir / "node"))
        else:
            manifest["steps"].append(capture([sys.executable, "scripts/benchmark.py", str(run_dir / "results.json"), str(run_dir / "work")], environment, run_dir / "benchmark"))
    except Exception as error:
        # Keep a failed orchestration as an experiment too; don't leave a success-shaped record.
        manifest["recorder_failure"] = type(error).__name__
    manifest["finished_at"] = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    manifest["success"] = not manifest.get("recorder_failure") and bool(manifest["steps"]) and all(s["exit_code"] == 0 for s in manifest["steps"])
    # Update only this run's pending manifest; completed run directories are immutable by convention.
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifacts = {p.relative_to(run_dir).as_posix(): {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
                 for p in run_dir.rglob("*") if p.is_file() and p.suffix not in {".key", ".pem"}}
    (run_dir / "artifacts.json").write_text(json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")
    print("EXPERIMENT=" + str(run_dir))
    return 0 if manifest["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
