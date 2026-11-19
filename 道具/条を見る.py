"""条文の控えから指定した条を書き出す。例: python 条を見る.py 令12 規13 > 出力先"""
import sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
d = json.loads((ROOT / "条文の控え" / "条文.json").read_text(encoding="utf-8"))
out = open(sys.argv[1], "w", encoding="utf-8")
for k in sys.argv[2:]:
    a = d["articles"].get(k)
    out.write(f"=== {k} ===\n{a['text'] if a else '（無い）'}\n\n")
keys = list(d["articles"].keys())
out.write("令の条: " + " ".join(x for x in keys if x.startswith("令")) + "\n")
