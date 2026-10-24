import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dsf_mnn import MemoryStore, Scope
from dsf_mnn.acr import AdaptiveContextReconstruction
from dsf_mnn.token_budget import CpuTokenCounter

parser = argparse.ArgumentParser()
parser.add_argument("run", type=Path)
parser.add_argument("--output", default="context-plan.json")
parser.add_argument("--memory-directory", default="cognitive")
args = parser.parse_args()
work = args.run.resolve() / "work"
data = json.loads((work / "exported/0a5bd41431f657f8.json").read_text(encoding="utf-8"))
records = json.loads((work / "shared-normalized-events-v2.json").read_text(encoding="utf-8"))
memory = (work / args.memory_directory).resolve()
memory.relative_to(work)
dreaming = json.loads((memory / "semantic/dreaming.json").read_text(encoding="utf-8"))
scope = Scope("dsf-whale", "authorized-dsf-owner", data["session_id"], "dsf-recovery")
with MemoryStore(memory / "mnn.sqlite") as store:
    plan = AdaptiveContextReconstruction(CpuTokenCounter(work / "tokenizer")).build(data, records, store, scope, dreaming)
plan["memory_database"] = (memory / "mnn.sqlite").relative_to(work).as_posix()
target = work / args.output
with target.open("x", encoding="utf-8") as output:
    json.dump(plan, output, ensure_ascii=False, indent=2)
print(json.dumps({"plan": str(target), "local_tokens": plan["budget"]["local_tokens"], "carryover": len(plan["checkpoint"]["current_goals"]),
                  "exact_fragments": len(plan["checkpoint"]["keep_exact"]), "retained_tail_events": len(plan["tail_seqs"]), "identity_unchanged": True}))
