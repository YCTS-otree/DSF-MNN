"""Validate the archived baseline using only its unpacked runtime and dependencies."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
import zipfile
from zoneinfo import ZoneInfo

from freeze_baseline import COMMIT, ROOT, json_write, sha, verify


def extract(archive, destination):
    destination.mkdir(parents=True)
    with zipfile.ZipFile(archive) as source:
        for entry in source.infolist():
            (destination / entry.filename).resolve().relative_to(destination.resolve())
        source.extractall(destination)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    baseline = ROOT / "baselines/research-29d7de6"
    checked = verify(baseline)
    run_id = "frozen-reproduction-" + datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:10]
    run = ROOT / "experiments" / run_id
    work = run / "work"
    extract(baseline / "artifacts/source-29d7de6.zip", work / "source")
    extract(baseline / "artifacts/environment-windows.zip", work / "environment")
    source = work / "source"
    python_home = work / "environment/python"
    python = python_home / "python.exe"
    node_bin = work / "environment/node/bin"
    temporary = work / "tmp"
    temporary.mkdir()
    system_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
    environment = {
        "SystemRoot": str(system_root), "WINDIR": str(system_root),
        "COMSPEC": str(system_root / "System32/cmd.exe"),
        "PATH": os.pathsep.join([str(python_home), str(node_bin), str(system_root / "System32")]),
        "PATHEXT": ".COM;.EXE;.BAT;.CMD", "TEMP": str(temporary), "TMP": str(temporary),
        "PYTHONHOME": str(python_home), "PYTHONPATH": str(source / "src"), "PYTHONIOENCODING": "utf-8",
        "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
        "DSH_NODE_MODULES": str(work / "environment/node/node_modules"),
        "MNN_TEST_ARTIFACTS": str(work / "node-tests"),
    }
    result = {"schema": "dsf-mnn-frozen-reproduction/1", "id": run_id, "commit": COMMIT,
              "started_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
              "baseline_manifest_sha256": sha(baseline / "manifest.json"), "baseline_integrity": checked,
              "execution": "Only unpacked frozen Python/Node/dependencies; sanitized environment; no original node_modules or installation used.",
              "configuration": {"python_hash_seed": 0, "pytest_plugin_autoload": True, "user_site_packages": False, "model_requests": 0},
              "steps": [], "historical_results_overwritten": False}
    def execute(label, command):
        completed = subprocess.run([str(arg) for arg in command], cwd=source, env=environment, capture_output=True)
        (run / (label + "-stdout.log")).write_bytes(completed.stdout)
        (run / (label + "-stderr.log")).write_bytes(completed.stderr)
        result["steps"].append({"label": label, "command": [str(arg) for arg in command], "exit_code": completed.returncode})
        print(completed.stdout.decode("utf-8", errors="replace"), end="")
        if completed.stderr:
            print(completed.stderr.decode("utf-8", errors="replace"), end="")
        return completed.returncode
    try:
        execute("environment", [python, "-c", "import sys,sqlite3,importlib.metadata,json; print(json.dumps({'python':sys.version,'prefix':sys.prefix,'sqlite':sqlite3.sqlite_version,'pytest':importlib.metadata.version('pytest')}))"])
        execute("python", [python, "-m", "pytest", "-q", "--tb=short", "--basetemp", work / "python-tests", "--junitxml", run / "junit.xml"])
        execute("node", [node_bin / "node.exe", "--test", "tests/adapter.test.mjs"])
    except Exception as error:
        result["orchestration_failure"] = type(error).__name__
    result["success"] = len(result["steps"]) == 3 and all(s["exit_code"] == 0 for s in result["steps"]) and not result.get("orchestration_failure")
    result["finished_at"] = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    json_write(run / "manifest.json", result)
    files = {}
    for file in sorted(run.rglob("*")):
        if file.is_file():
            files[file.relative_to(run).as_posix()] = {"bytes": file.stat().st_size, "sha256": sha(file)}
    json_write(run / "artifacts.json", files)
    print(json.dumps({"experiment": run_id, "success": result["success"]}, ensure_ascii=False))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
