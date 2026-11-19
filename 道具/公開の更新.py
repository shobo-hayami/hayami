"""公開版の毎月の更新。無料でページを公開できる場所（GitHub Pages）の定時実行から動かす。自分のPCからも動く。AIは使わない。
流れ: 条文を取る → 比べる → 例題の試験 → 変わった月だけ公開の画面を入れ替える → 確かめた日と記録を残す。
- 今月もう確かめ終えていれば何もしない（月初の4日間、毎日動くため）。
- 条文が取れなかった月: 何も変えずに終わる（翌日にもう一度動く）。確かめた日が進まないので、40日を過ぎると画面に黄色の警告が出る。
- 試験に落ちた月: 公開の画面は前の版のまま。終わりの合図を「失敗」にする（置き場の持ち主にメールが届く）。
- 条文は同じでも、画面の作りや文を直した月は、公開の画面を入れ替える（作った日だけの違いは入れ替えない）。
- 判定に使う条が変わった月: その設備は画面で「見直し中」になる。人が確かめるまで、見直しが要る.txt を残す（定時実行の最後で失敗にして知らせる）。
"""
import sys as _s; _s.stdout.reconfigure(encoding="utf-8"); _s.stderr.reconfigure(encoding="utf-8")
import subprocess, sys, datetime, pathlib, os, json, shutil, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = ROOT / "条文の控え"
PUB = ROOT / "公開"
CHANGES = STORE / "変わった条.json"
REVIEW = ROOT / "見直しが要る.txt"
today = datetime.date.today()
PUB.mkdir(exist_ok=True)


def 記録(msg):
    with (PUB / "更新の記録.txt").open("a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M} {msg}\n")
    print(msg)


def 変わった数():
    try:
        return len(json.loads(CHANGES.read_text(encoding="utf-8")))
    except Exception:
        return 0


done = PUB / "確かめた日.txt"
if done.exists() and done.read_text(encoding="utf-8")[:7] == today.isoformat()[:7] and "--force" not in sys.argv:
    print("今月はもう確かめ終えている。何もしない")
    sys.exit(0)

before = 変わった数()
r = subprocess.run([sys.executable, "-I", str(ROOT / "道具" / "条文を更新.py")], capture_output=True, encoding="utf-8", errors="replace")
if r.returncode != 0:
    記録("条文が取れなかった（何も変えていない・翌日にもう一度）: " + " ".join((r.stderr or r.stdout).strip().splitlines()[-2:]))
    sys.exit(0)
after = 変わった数()
new = json.loads(CHANGES.read_text(encoding="utf-8"))[before:] if after > before else []
keys = sorted({x.get("条", "") for x in new})

env = dict(os.environ, 早見_公開="1")
b = subprocess.run([sys.executable, "-I", str(ROOT / "道具" / "早見を作る.py")], capture_output=True, encoding="utf-8", errors="replace", env=env)
out = b.stdout.strip()
ok = b.returncode == 0 and "違い 0個" in out and "数値が条文に見つからない行 0件" in out
if not ok:
    記録("試験に落ちた（公開の画面は前の版のまま）: " + out.replace("\n", " / ")[:300])
    sys.exit(1)

# 判定に使う条のうち、人がまだ確かめていない変化
tables = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "判定表").glob("*.json"))]
arts = json.loads((STORE / "条文.json").read_text(encoding="utf-8"))["articles"]
見直し = sorted({f"{t['設備']}（{k}）" for t in tables for k in t.get("条", []) if k in arts and t.get("指紋", {}).get(k) not in (None, arts[k]["hash"])})

def 中身(p):
    # 画面を作った日・条文を取った日だけが違う場合は、同じ画面と見なす
    return re.sub(r"(画面を作った日|条文を取った日) [0-9:\- ]+", "", p.read_text(encoding="utf-8")) if p.exists() else None


載せた = False
if keys or 中身(PUB / "index.html") != 中身(ROOT / "早見.html"):
    shutil.copy2(ROOT / "早見.html", PUB / "index.html")
    載せた = True
done.write_text(f"{today.isoformat()} 条文を確かめた（変わった条 {len(keys)}件）\n", encoding="utf-8")
if 見直し:
    REVIEW.write_text("人の確かめが要る設備: " + "・".join(見直し) + "\n", encoding="utf-8")
elif REVIEW.exists():
    REVIEW.unlink()
記録(f"変わった条 {len(keys)}件{('（' + '・'.join(keys) + '）') if keys else ''} / 試験 OK / 載せ直し {'した' if 載せた else 'しない'}"
     + (f" / 見直し中 {len(見直し)}件" if 見直し else ""))

# 自分のPCで動かしたときは、手元の画面を公開用でない形に戻す
if os.environ.get("GITHUB_ACTIONS") != "true":
    subprocess.run([sys.executable, "-I", str(ROOT / "道具" / "早見を作る.py")], capture_output=True)
