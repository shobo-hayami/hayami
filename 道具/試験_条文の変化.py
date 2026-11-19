"""改正を見つける仕組みの試験。令21の前回の指紋をわざと変え、その条を根拠にした札だけに赤い帯が出るかを見る。
終わったら控えを元に戻し、画面を作り直す。通信なし。"""
import json, shutil, subprocess, sys, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = ROOT / "条文の控え"
BK = pathlib.Path.home() / ".claude" / "backup" / "消防法の根拠集_試験"
BK.mkdir(parents=True, exist_ok=True)
for f in ("条文.json", "変わった条.json"):
    shutil.copy2(STORE / f, BK / f)
try:
    d = json.loads((STORE / "条文.json").read_text(encoding="utf-8"))
    before = d["articles"]["令21"]["text"]
    after = before.replace("三百平方メートル", "四百平方メートル", 1)
    d["articles"]["令21"] = {"text": after, "hash": "0000000000000000", "law": "令"}
    (STORE / "条文.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    ch = json.loads((STORE / "変わった条.json").read_text(encoding="utf-8"))
    ch.append({"条": "令21", "日": "試験", "前": before, "後": after})
    (STORE / "変わった条.json").write_text(json.dumps(ch, ensure_ascii=False), encoding="utf-8")
    subprocess.run([sys.executable, "-I", str(ROOT / "道具" / "早見を作る.py")], capture_output=True)
    page = (ROOT / "早見.html").read_text(encoding="utf-8")
    hit = re.findall(r'<section class="card" id="([^"]+)"[^>]*><h3>[^<]*</h3><div class="band red">', page)
    print("赤い帯が出た札:", hit)
    print("判定表で変わったと出た設備:", re.findall(r'"設備": "([^"]+)"(?:(?!"設備").)*?"変わった": \["令21"', page))
finally:
    for f in ("条文.json", "変わった条.json"):
        shutil.copy2(BK / f, STORE / f)
    subprocess.run([sys.executable, "-I", str(ROOT / "道具" / "早見を作る.py")], capture_output=True)
    page = (ROOT / "早見.html").read_text(encoding="utf-8")
    print("元に戻した後の赤い帯:", len(re.findall(r"<section[^>]*><h3>[^<]*</h3><div class=\"band red\">", page)),
          "/ 判定表で変わった設備:", len(re.findall(r'"変わった": \["', page)))
