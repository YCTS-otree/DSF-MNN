import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dsf_mnn.benchmark import run

output = Path(sys.argv[1] if len(sys.argv) > 1 else "benchmarks/results-v1.0.0.json")
if output.exists():
    raise SystemExit("Refusing to overwrite an existing benchmark result")
result = run(output_root=sys.argv[2] if len(sys.argv) > 2 else ".cache/benchmarks")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for row in result["results"]:
    print(json.dumps({"size": row["size"], "items_per_second": round(row["indexing_items_per_second"], 1),
                      "strategies": {k: {"recall@5": v["recall_at_5"], "median_ms": round(v["latency_ms_median"], 2)} for k, v in row["strategies"].items()}}, ensure_ascii=False))
print(str(output.resolve()))
