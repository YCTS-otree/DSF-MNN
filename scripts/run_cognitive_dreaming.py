"""Run real semantic Dreaming only after the frozen v1 replay has been recorded."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dsf_mnn import MemoryStore, Scope, __version__
from dsf_mnn.model import digest
from dsf_mnn.remote import RemoteProvider
from dsf_mnn.semantic import SemanticDreaming, normalize_export
from dsf_mnn.token_budget import CpuTokenCounter


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--export", default="0a5bd41431f657f8.json")
    parser.add_argument("--variant", default="cognitive")
    args = parser.parse_args()
    run = args.run.resolve()
    run.relative_to(ROOT / "experiments")
    if not run.name.startswith("private-recovery-"):
        raise SystemExit("Private isolated recovery directory required")
    work = run / "work"
    baseline = json.loads((work / "baseline-v1-v2/baseline.json").read_text(encoding="utf-8"))
    records_file = work / "shared-normalized-events-v2.json"
    if hashlib.sha256(records_file.read_bytes()).hexdigest() != baseline["record_sha256"]:
        raise SystemExit("Shared baseline data changed")
    exported = work / "exported" / args.export
    data = json.loads(exported.read_text(encoding="utf-8"))
    if normalize_export(data) != json.loads(records_file.read_text(encoding="utf-8")):
        raise SystemExit("New pipeline must use the same normalized evidence as baseline")
    output = (work / args.variant).resolve()
    output.relative_to(work)
    output.mkdir(exist_ok=True)
    provenance = {"version": __version__, "session_id": data["session_id"], "source_event_digest": digest(data["events"]),
                  "shared_record_sha256": baseline["record_sha256"], "baseline_precedes_llm_history_processing": True,
                  "started_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(), "device": "cpu",
                  "provider": "deepseek-flash", "input_chunk_tokens": 12000, "concurrency": 3,
                  "source_files": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT / "src/dsf_mnn/semantic.py", ROOT / "src/dsf_mnn/remote.py", ROOT / "adapters/dsh/remote-provider.mjs"]}}
    provenance_file = output / "provenance.json"
    if provenance_file.exists():
        old = json.loads(provenance_file.read_text(encoding="utf-8"))
        if {k: v for k, v in old.items() if k != "started_at"} != {k: v for k, v in provenance.items() if k != "started_at"}:
            raise SystemExit("Run provenance changed; choose a new --variant")
    else:
        with provenance_file.open("x", encoding="utf-8") as handle:
            json.dump(provenance, handle, ensure_ascii=False, indent=2)
    scope = Scope("dsf-whale", "authorized-dsf-owner", data["session_id"], "dsf-recovery")
    provider = RemoteProvider(ROOT.parent / "DS_Friend", work / "provider")
    counter = CpuTokenCounter(work / "tokenizer")
    with MemoryStore(output / "mnn.sqlite") as store:
        if not (output / "before-dreaming.sqlite").exists():
            store.backup(output / "before-dreaming.sqlite")
        engine = SemanticDreaming(store, scope, provider, counter, output / "semantic")
        history, records = engine.run(data, progress=lambda value: print(json.dumps(value), flush=True))
        status = store.status(scope)
        target = output / "after-dreaming.sqlite"
        if not target.exists():
            store.backup(target)
        print(json.dumps({"completed": True, "notes": history["notes"], "rejected_notes": history["rejected_notes"], "chunks": history["chunks"],
                          "carryover": len(history["consolidation"]["carryover"]), "edges": status["edges"], "self_update": history["self_update"]}), flush=True)


if __name__ == "__main__":
    main()
