"""Run the frozen v1.0.0 library on a shared evidence snapshot; no DSH write calls."""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("--source", required=True, type=Path)
parser.add_argument("--records", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--session-id", required=True)
args = parser.parse_args()
sys.stdout.reconfigure(encoding="utf-8")
source = args.source.resolve()
sys.path.insert(0, str(source / "src"))
import dsf_mnn
if dsf_mnn.__version__ != "1.0.0" or not Path(dsf_mnn.__file__).resolve().is_relative_to(source):
    raise SystemExit("Frozen v1.0.0 import not established")
from dsf_mnn import MemoryStore, Scope, Event
from dsf_mnn.compaction import CognitiveCompaction
from dsf_mnn.embedding import HashEmbedding
from dsf_mnn.formation import Formation
from dsf_mnn.lifecycle import Dreaming
from dsf_mnn.association import SpontaneousAssociation
from dsf_mnn.recall import Recall

args.output.mkdir(parents=True, exist_ok=False)
records = json.loads(args.records.read_text(encoding="utf-8"))
scope = Scope("dsf-whale", "authorized-dsf-owner", args.session_id, "dsf-recovery")
events = [Event(r["id"], r["seq"], r["text"], r["observed_at"], r["source_kind"], f"dsh://{args.session_id}/event/{r['seq']}", metadata=r["metadata"]) for r in records]
started = time.perf_counter()
report = {"schema": "dsf-mnn-v1-real-history-replay/1", "version": dsf_mnn.__version__, "source_revision": "29d7de6b3fcb2e909ea8f49436640de77db09f6d",
          "record_sha256": hashlib.sha256(args.records.read_bytes()).hexdigest(), "events": len(events), "original_dsh_writes": 0,
          "configuration": {"embedding": "lexical-hash-baseline/1/256", "checkpoint_default_bytes": 32768, "diagnostic_checkpoint_bytes": 16 * 1024 * 1024}}
def save(name, data):
    (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
with MemoryStore(args.output / "baseline.sqlite") as store:
    formed = Formation(store).ingest(scope, events)
    report["formation"] = {"episode_count": len(formed["episode_ids"]), "through": formed["through"]}
    store.backup(args.output / "before-dreaming.sqlite")
    at = (datetime.fromisoformat(events[-1].to_dict()["observed_at"]) + timedelta(days=1)).isoformat()
    try:
        dreaming = Dreaming(store).tick(scope, at=at, idle=True)
        save("dreaming-default-api.json", dreaming)
        report["dreaming_default_api"] = {"state": dreaming["state"], "consolidated": len(dreaming["consolidated"]), "carryover_refs": len(dreaming["carryover_refs"]), "self_reflection": dreaming["self_reflection"]}
    except Exception as error:
        report["dreaming_default_api"] = {"error_type": type(error).__name__, "error": str(error)[:120]}
    engine = CognitiveCompaction(store)
    for label, budget in (("default", 32768), ("diagnostic-unbounded", 16 * 1024 * 1024)):
        try:
            checkpoint = engine.prepare(scope, events, checkpoint_bytes=budget)
            save("checkpoint-" + label + ".json", checkpoint)
            report["checkpoint_" + label] = {"state": checkpoint["state"], "bytes": checkpoint["checkpoint_bytes"], "accepted_for_recovery": label == "default"}
        except Exception as error:
            failure = {"error_type": type(error).__name__, "error": str(error)[:120], "accepted_for_recovery": False}
            save("checkpoint-" + label + "-failure.json", failure)
            report["checkpoint_" + label] = failure
    report["memory_status"] = store.status(scope)
with MemoryStore(args.output / "before-dreaming.sqlite") as original:
    original.backup(args.output / "cli-mode.sqlite")
with MemoryStore(args.output / "cli-mode.sqlite") as cli:
    try:
        result = Dreaming(cli, association=SpontaneousAssociation(cli, Recall(cli))).tick(scope, at=at, idle=True)
        save("dreaming-cli-mode.json", result)
        report["dreaming_cli_mode"] = {"state": result["state"], "consolidated": len(result["consolidated"])}
    except Exception as error:
        failure = {"error_type": type(error).__name__, "error": str(error)[:120]}
        save("dreaming-cli-mode-failure.json", failure)
        report["dreaming_cli_mode"] = failure
report["elapsed_seconds"] = time.perf_counter() - started
report["dsh_recovery"] = "not-attempted-unless-a-budget-valid-context-plan-exists"
save("baseline.json", report)
print(json.dumps({"events": report["events"], "formation": report["formation"], "dreaming": report.get("dreaming_default_api"), "cli_dreaming": report.get("dreaming_cli_mode"), "checkpoint": report.get("checkpoint_default"), "diagnostic_checkpoint": report.get("checkpoint_diagnostic-unbounded"), "elapsed_seconds": report["elapsed_seconds"]}))
