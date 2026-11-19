"""例題_第2段.json の例題を 例題.json に足す（同じ名前は足さない）。"""
import json, pathlib, sys
sys.stdout.reconfigure(encoding="utf-8")
D = pathlib.Path(__file__).resolve().parent
base = json.loads((D / "例題.json").read_text(encoding="utf-8"))
add = json.loads((D / sys.argv[1]).read_text(encoding="utf-8"))
names = {e["名前"] for e in base}
n = 0
for e in add:
    if e["名前"] not in names:
        base.append(e)
        n += 1
(D / "例題.json").write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"足した例題 {n}件 / 合計 {len(base)}件")
