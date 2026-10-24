"""Source-backed paired evaluation; always creates a new directory, no LLM judge."""
import argparse
from datetime import datetime
import hashlib
import json
import sqlite3
from pathlib import Path
import sys
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dsf_mnn import MemoryStore, Scope
from dsf_mnn.evidence_recall import EvidenceRecall
from dsf_mnn.model import canonical
from dsf_mnn.recall import Recall, RecallBudget
from dsf_mnn.token_budget import CpuTokenCounter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    work = args.run.resolve() / "work"
    target = work / ("comparison-" + uuid4().hex[:12]); target.mkdir()
    gold_file = work / "quality-gold-v2.json"
    gold = json.loads(gold_file.read_text(encoding="utf-8"))
    source = json.loads((work / "exported/0a5bd41431f657f8.json").read_text(encoding="utf-8"))
    scope = Scope("dsf-whale", "authorized-dsf-owner", source["session_id"], "dsf-recovery")
    counter = CpuTokenCounter(work / "tokenizer")
    report = {"schema": "dsf-mnn-paired-quality/1", "created_at": datetime.now().astimezone().isoformat(),
              "gold_sha256": hashlib.sha256(gold_file.read_bytes()).hexdigest(), "gold_cases": len(gold),
              "judging": "exact-source-ref coverage, no LLM judge; retrieval != answer correctness", "variants": {}}
    # The core ranking files are identical to the frozen source; record this check.
    frozen = work / "baseline-v1-source/src/dsf_mnn"
    report["ranking_matches_frozen_source"] = {name: (ROOT / "src/dsf_mnn" / name).read_bytes() == (frozen / name).read_bytes()
                                                for name in ("recall.py", "embedding.py", "store.py")}
    for label, source_db in (("v1", work / "baseline-v1-v2/baseline.sqlite"), ("cognitive", work / "cognitive-v2/after-grounding.sqlite")):
        with sqlite3.connect(source_db.resolve().as_uri() + "?mode=ro", uri=True) as original:
            with sqlite3.connect(target / (label + ".sqlite")) as copy:
                original.backup(copy)
        with MemoryStore(target / (label + ".sqlite")) as store:
            nodes = store.nodes(scope)
            active = [n for n in nodes if n["status"] == "active"]
            results = {"status_before_queries": store.status(scope), "active_nodes": len(active), "strategies": {}}
            results["long_term_source_coverage"] = [g["id"] for g in gold if any(g["source_ref"] in n["source_refs"] for n in active if n["metadata"].get("layer") == "long_term")]
            results["all_active_source_coverage"] = [g["id"] for g in gold if any(g["source_ref"] in n["source_refs"] for n in active)]
            for strategy in ("hybrid", "bfs", "ppr"):
                cases = []
                for g in gold:
                    found = Recall(store).search(scope, g["question"], strategy=strategy, k=5,
                        at="2026-10-24T04:14:29.528000+00:00", budget=RecallBudget(deadline_ms=10000, max_operations=100000000))
                    rank = next((i for i, h in enumerate(found["hits"], 1) if g["source_ref"] in h["node"]["source_refs"]), None)
                    cases.append({"gold_id": g["id"], "correct_source_rank": rank, "latency_ms": found["latency_ms"],
                                  "truncated": found["truncated"], "hits": [{"id": h["node"]["id"], "source_refs": h["node"]["source_refs"], "path": h["path"]} for h in found["hits"]]})
                results["strategies"][strategy] = {"recall_at_5": sum(c["correct_source_rank"] is not None for c in cases) / len(cases),
                    "mrr_at_5": sum(1 / c["correct_source_rank"] if c["correct_source_rank"] else 0 for c in cases) / len(cases), "cases": cases}
            cases = []
            for g in gold:
                started = time.perf_counter()
                context = (EvidenceRecall(store).context(scope, g["question"], byte_budget=4096) if label == "cognitive" else
                           Recall(store).context(scope, g["question"], byte_budget=4096))
                cases.append({"gold_id": g["id"], "source_ref_retained": g["source_ref"] in context["text"],
                              "latency_ms": (time.perf_counter() - started) * 1000,
                              "tokens": counter.count_text(context["text"]), "bytes": context["bytes"], "context": context["text"]})
            results["bounded_context"] = {"bytes_budget": 4096, "source_coverage": sum(c["source_ref_retained"] for c in cases) / len(cases), "cases": cases}
            results["quote_validation"] = {"checked": 0, "mismatches": 0}
            for n in nodes:
                for q in n["metadata"].get("evidence_quotes", []):
                    event = store.event(scope, "dsh-event:" + str(q["seq"]))
                    results["quote_validation"]["checked"] += 1
                    results["quote_validation"]["mismatches"] += q["quote"] not in event["content"]
            report["variants"][label] = results
    receipts = []
    for file in (work / "provider").glob("*.json"):
        data = json.loads(file.read_text(encoding="utf-8"))
        receipts.append({"file": file.name, "success": data.get("success"), "model": data.get("response", {}).get("model"),
                         "usage": data.get("response", {}).get("usage"), "elapsed_seconds": data.get("elapsed_seconds")})
    report["semantic_provider_receipts"] = receipts
    report["semantic_provider_totals"] = {field: sum((r["usage"] or {}).get(field, 0) for r in receipts)
                                            for field in ("prompt_tokens", "completion_tokens", "total_tokens")}
    native = []
    for directory in sorted(work.glob("native-*")):
        data = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        native.append({"directory": directory.name, "success": data["success"], "provider_input": data.get("provider_verified_input_tokens"),
                       "failure": data.get("failure"), "continuation": data.get("continuation")})
    report["native_attempts"] = native
    report["native_provider_totals_all_attempts"] = {"input_tokens_including_cache": 0, "output_tokens": 0, "requests": 0}
    for directory in sorted(work.glob("native-*")):
        probe_file = directory / "provider-budget-probe.json"
        if probe_file.exists():
            probe = json.loads(probe_file.read_text(encoding="utf-8"))
            usage = probe.get("usage")
            if usage:
                totals = report["native_provider_totals_all_attempts"]
                totals["requests"] += 1
                totals["output_tokens"] += usage.get("outputTokens", 0)
                totals["input_tokens_including_cache"] += usage["totalTokens"] - usage.get("outputTokens", 0)
        data = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        for usage in data.get("continuation", {}).get("usage", []):
            if usage:
                totals = report["native_provider_totals_all_attempts"]
                totals["requests"] += 1
                totals["output_tokens"] += usage.get("outputTokens", 0)
                totals["input_tokens_including_cache"] += usage["totalTokens"] - usage.get("outputTokens", 0)
    diagnostic = json.loads((work / "baseline-v1-v2/checkpoint-diagnostic-unbounded.json").read_text(encoding="utf-8"))
    # Count exactly the saved diagnostic payload; it was never accepted for recovery.
    report["v1_diagnostic_payload_tokens"] = counter.count_text("\n".join(b["text"] for b in diagnostic["summary"] if b["type"] == "text"))
    report["v1_diagnostic_tokens_basis"] = "saved SummaryResult.summary text only, without native framing/tools/system/tail"
    plan = json.loads((work / "context-plan-v6.json").read_text(encoding="utf-8"))
    report["acr"] = {"carryover": len(plan["checkpoint"]["current_goals"]), "exact_fragments": len(plan["checkpoint"]["keep_exact"]),
                     "local_tokens": plan["budget"]["local_tokens"], "context_tokens": plan["budget"]["context_tokens"],
                     "pending_requests": len(plan["checkpoint"]["pending_source_requests"])}
    (target / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"directory": str(target), "core_matches_frozen": report["ranking_matches_frozen_source"],
        "variants": {k: {"active": v["active_nodes"], "long_term_sources": len(v["long_term_source_coverage"]),
            "rankings": {s: {m: r[m] for m in ("recall_at_5", "mrr_at_5")} for s, r in v["strategies"].items()},
            "bounded_source_coverage": v["bounded_context"]["source_coverage"], "quote_validation": v["quote_validation"]} for k, v in report["variants"].items()},
        "provider_totals": report["semantic_provider_totals"], "acr": report["acr"], "diagnostic_tokens": report["v1_diagnostic_payload_tokens"]}))


if __name__ == "__main__":
    main()
