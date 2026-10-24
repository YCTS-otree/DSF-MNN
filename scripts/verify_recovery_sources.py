"""Verify declared original archives and frozen research artifacts, without changing them."""
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

from freeze_baseline import ROOT, verify, git

sys.path.insert(0, str(ROOT.parent / "DS_Friend"))
from scripts import dsf

parser = argparse.ArgumentParser()
parser.add_argument("run", type=Path)
args = parser.parse_args()
run = args.run.resolve()
p0 = json.loads((run / "p0.json").read_text(encoding="utf-8"))
checked = []
for item in p0["archives"]:
    source = ROOT.parent / "DS_Friend/Archive" / item["name"]
    dsf.inspect(source)  # trusted allowlist + per-member checksums; credentials excluded
    checked.append({"archive": item["name"], "unchanged": dsf.digest(source) == item["sha256"], "bytes": source.stat().st_size})
copy = run / "work/source.DSF"
selected = next(a for a in p0["archives"] if a["name"] == p0["selected"])
report = {"original_backups": checked, "isolated_source_copy_unchanged": dsf.digest(copy) == selected["sha256"],
          "research_baseline": verify(ROOT / "baselines/research-29d7de6"),
          "tag_commit": git("rev-list", "-n", "1", "research-baseline-29d7de6").strip()}
report["success"] = all(c["unchanged"] for c in checked) and report["isolated_source_copy_unchanged"] and report["research_baseline"]["verified"] and report["tag_commit"] == p0.get("baseline_commit", "29d7de6b3fcb2e909ea8f49436640de77db09f6d")
target = run / ("integrity-" + uuid4().hex[:12] + ".json")
with target.open("x", encoding="utf-8") as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
print(json.dumps({"report": str(target), **report}))
raise SystemExit(0 if report["success"] else 1)
