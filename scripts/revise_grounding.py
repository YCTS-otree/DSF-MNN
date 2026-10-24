"""Create a new memory variant; quarantine unsupported exact atoms with version history."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dsf_mnn import MemoryStore, Node, Scope
from dsf_mnn.formation import Formation
from dsf_mnn.model import MemoryError, digest
from dsf_mnn.remote import RemoteProvider
from dsf_mnn.semantic import CONSOLIDATE

parser = argparse.ArgumentParser()
parser.add_argument("run", type=Path)
args = parser.parse_args()
sys.stdout.reconfigure(encoding="utf-8")
work = args.run.resolve() / "work"
original = json.loads((work / "exported/0a5bd41431f657f8.json").read_text(encoding="utf-8"))
scope = Scope("dsf-whale", "authorized-dsf-owner", original["session_id"], "dsf-recovery")
target = work / "cognitive-v2"
target.mkdir(exist_ok=False)
(target / "semantic").mkdir()
with MemoryStore(work / "cognitive/mnn.sqlite") as before:
    before.backup(target / "mnn.sqlite")
audit = json.loads((work / "cognitive/grounding-audit/exact-atoms.json").read_text(encoding="utf-8"))
previous = json.loads((work / "cognitive/semantic/dreaming.json").read_text(encoding="utf-8"))
with MemoryStore(target / "mnn.sqlite") as store:
    for failure in audit["failures"]:
        node = store.node(scope, failure["id"])
        store.evolve(scope, node["id"], node["version"], {"status": "disputed", "metadata": {**node["metadata"], "grounding_review": "unsupported-exact-atoms-await-evidence"}},
                     node["source_refs"], "deterministic-exact-atom-audit-quarantine")
    notes = [n for n in store.nodes(scope) if n["status"] == "active" and n["metadata"].get("extractor")]
    payload = [{"id": n["id"], "content": n["content"], "type": n["type"], "source_refs": n["source_refs"],
                "carryover_candidate": n["metadata"].get("carryover_candidate")} for n in notes]
    provider = RemoteProvider(ROOT.parent / "DS_Friend", work / "provider")
    result, receipt = provider.json(CONSOLIDATE, {"notes": payload, "current_time": datetime.fromtimestamp(original["events"][-1]["time"] / 1000, timezone.utc).isoformat(),
                                                "quarantined_ids": [f["id"] for f in audit["failures"]]}, max_tokens=6000, label="reconsolidate-grounded")
    valid = {n["id"] for n in notes}
    for key in ("themes", "carryover", "decisions"):
        if not isinstance(result.get(key), list) or any(not x.get("memory_refs") or not set(x["memory_refs"]) <= valid for x in result[key]):
            raise MemoryError("grounded-consolidation-invalid-refs")
    result["self_update"] = None
    with store.transaction():
        for goal in store.nodes(scope):
            if goal["type"] == "Goal" and goal["metadata"].get("origin") == "semantic-dreaming" and goal["status"] == "active":
                store.evolve(scope, goal["id"], goal["version"], {"status": "archived"}, goal["source_refs"], "carryover-reconsolidation-old-projection")
        for item in result["carryover"]:
            refs = list(dict.fromkeys(ref for memory in item["memory_refs"] for ref in store.node(scope, memory)["source_refs"]))
            identifier = "carryover_" + digest(item)[:24]
            existing = next((n for n in store.nodes(scope) if n["id"] == identifier), None)
            if existing:
                store.evolve(scope, identifier, existing["version"], {"status": "active"}, refs, "grounded-carryover-reaffirmed")
            else:
                observed = max(store.event(scope, r)["observed_at"] for r in refs)
                store.add_node(scope, Node(identifier, "Goal", item["description"], refs, observed_at=observed,
                    metadata={"layer": "carryover", "memory_refs": item["memory_refs"], "next_actions": item.get("next_actions", []), "origin": "semantic-dreaming"}))
                Formation(store).index(scope, [store.node(scope, identifier)])
    updated = {**previous, "consolidation": result, "notes": len(notes), "quarantined": audit["failures"],
               "parent_variant": "cognitive", "original_notes_retained": 67, "self_update": "noop"}
    (target / "semantic/dreaming.json").write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
    store.backup(target / "after-grounding.sqlite")
print(json.dumps({"active_notes": len(notes), "quarantined_with_history": len(audit["failures"]), "carryover": len(result["carryover"]), "original_variant_unchanged": True}))
