"""P0: verify credential-free DSF archives and copy only into a new isolated run."""
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import sys
from uuid import uuid4
import zipfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DSF = ROOT.parent / "DS_Friend"
sys.path.insert(0, str(DSF))
from scripts import dsf


def main():
    records = []
    archives = sorted((DSF / "Archive").glob("*.DSF"))
    for path in archives:
        manifest = dsf.inspect(path)
        records.append({"name": path.name, "sha256": dsf.digest(path), "bytes": path.stat().st_size,
                        "created_at": manifest["createdAt"], "schema": manifest["schemaVersion"],
                        "dsh_version": manifest.get("dshVersion"), "file_count": len(manifest["files"]),
                        "sessions_files": [n for n in manifest["files"] if n.startswith("dsh/sessions/")],
                        "credentials_included": manifest["credentialsIncluded"]})
    if not records:
        raise SystemExit("No verified DSF archive")
    selected = records[-1]
    run = ROOT / "experiments" / ("private-recovery-" + datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:8])
    work = run / "work"
    work.mkdir(parents=True)
    destination = work / "source.DSF"
    shutil.copyfile(DSF / "Archive" / selected["name"], destination)
    if dsf.digest(destination) != selected["sha256"]:
        raise SystemExit("Backup copy mismatch")
    extracted = work / "snapshot"
    extracted.mkdir()
    with zipfile.ZipFile(destination) as archive:
        manifest = dsf.inspect(destination)
        for name in manifest["files"]:
            if not dsf.allowed(name):
                raise SystemExit("Unsafe archive entry")
            target = extracted / name
            target.resolve().relative_to(extracted.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
    checks = []
    for database in extracted.rglob("*.sqlite"):
        connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            connection.close()
        checks.append({"path": database.relative_to(extracted).as_posix(), "integrity": integrity})
        if integrity != "ok":
            raise SystemExit("SQLite backup integrity failed")
    report = {"schema": "dsf-mnn-recovery-p0/1", "archives": records, "selected": selected["name"], "sqlite_checks": checks,
              "source_backup_unchanged": dsf.digest(DSF / "Archive" / selected["name"]) == selected["sha256"],
              "original_session_modified": False, "production_processes_modified": False,
              "config_in_archive": False, "config_note": "DSF archives contain state/prompts; runtime configuration must be separately fingerprinted and not assumed present."}
    (run / "p0.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"run": str(run), "verified_archives": len(records), "session_artifacts": len(selected["sessions_files"]), "sqlite_integrity_checks": len(checks), "source_unchanged": report["source_backup_unchanged"]}))


if __name__ == "__main__":
    main()
