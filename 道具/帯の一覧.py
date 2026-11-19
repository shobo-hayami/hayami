"""いま赤い帯が出る札（確認した後に根拠の条文が変わった札）と、変わった条を並べる。何も書き換えない。"""
import sys, json, pathlib
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import importlib.util
spec = importlib.util.spec_from_file_location("hayami", pathlib.Path(__file__).resolve().parent / "早見を作る.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
arts = json.loads((h.STORE / "条文.json").read_text(encoding="utf-8"))["articles"]
for p in sorted(h.CARDS.glob("*.md")):
    c = h.parse_card(p)
    k = h.changed_keys(c, arts)
    if k:
        print(c["id"], k)
