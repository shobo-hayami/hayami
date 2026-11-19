"""条文の控えから語を含む条を探す。例: python 語を探す.py 出力先 要介護状態区分"""
import sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
d = json.loads((ROOT / "条文の控え" / "条文.json").read_text(encoding="utf-8"))
out = open(sys.argv[1], "w", encoding="utf-8")
word = sys.argv[2]
for k, a in d["articles"].items():
    t = a["text"]
    i = t.find(word)
    while i >= 0:
        out.write(f"{k}: …{t[max(0, i-150):i+250]}…\n\n")
        i = t.find(word, i + 1)
