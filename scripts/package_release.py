"""Create an immutable research source distribution and verify it standalone."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4
import zipfile
from zoneinfo import ZoneInfo

from record_experiment import ROOT, source_files

sys.path.insert(0, str(ROOT / "src"))
from dsf_mnn import __version__

sys.stdout.reconfigure(encoding="utf-8")
release_root = (ROOT / "Release").resolve()
target = (release_root / ("v" + __version__)).resolve()
target.relative_to(release_root)
if target.exists():
    raise SystemExit("Refusing to overwrite a released version")
run_dir = ROOT / "experiments" / ("release-" + datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:10])
staging = (run_dir / "work").resolve()
staging.relative_to((ROOT / "experiments").resolve())
staging.mkdir(parents=True)
archive = staging / f"DSF-MNN-v{__version__}-research-source.zip"
hashes = {}
files = source_files() + sorted((ROOT / "benchmarks").glob("*.json")) + [ROOT / "experiments/README.md"]
with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as package:
    for source in files:
        relative = source.relative_to(ROOT).as_posix()
        data = source.read_bytes()
        hashes[relative] = hashlib.sha256(data).hexdigest()
        package.writestr(relative, data)
with zipfile.ZipFile(archive) as package:
    if package.testzip() is not None:
        raise SystemExit("Distribution zip integrity failed")
    extracted = staging / "standalone-check"
    extracted.mkdir()
    for info in package.infolist():
        (extracted / info.filename).resolve().relative_to(extracted.resolve())
    package.extractall(extracted)
environment = {**os.environ, "PYTHONPATH": str(extracted / "src"), "PYTHONIOENCODING": "utf-8"}
db = extracted / "data/smoke.sqlite"
commands = []
def execute(arguments, input_bytes=None):
    command = [sys.executable, "-m", "dsf_mnn", "--db", str(db), *arguments]
    result = subprocess.run(command, cwd=extracted, env=environment, input=input_bytes, capture_output=True)
    commands.append({"arguments": arguments, "exit_code": result.returncode, "stdout": result.stdout.decode("utf-8"), "stderr": result.stderr.decode("utf-8")})
    if result.returncode:
        raise SystemExit("Standalone distribution validation failed; artifacts retained in staging")
    return json.loads(result.stdout)
execute(["status"])
execute(["ingest"], (extracted / "configs/synthetic.events.json").read_bytes())
search = execute(["search", "微信幂等"])
if not search["hits"] or "demo-1" not in search["hits"][0]["node"]["source_refs"]:
    raise SystemExit("Standalone evidence recall failed")
execute(["backup", str(extracted / "data/verified.sqlite")])
manifest = {"schema": "dsf-mnn-release-validation/1", "version": __version__, "kind": "offline-research-source", "created_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "source_files": hashes,
            "validation": {"passed": True, "commands": commands},
            "limits": ["Neural embedding unverified", "Production DSH not enabled", "Research experiments retained separately"]}
# Raw standalone test files remain in the experiment work directory.
(staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
artifacts = {p.relative_to(run_dir).as_posix(): {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in staging.rglob("*") if p.is_file()}
(run_dir / "artifacts.json").write_text(json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")
release_root.mkdir(exist_ok=True)
target.mkdir()  # exclusive reservation; never overwrite an earlier release
shutil.copy2(archive, target / archive.name)
shutil.copy2(staging / "manifest.json", target / "manifest.json")
print(json.dumps({"release": str(target), "sha256": manifest["archive_sha256"], "standalone_validation": True}, ensure_ascii=False))
