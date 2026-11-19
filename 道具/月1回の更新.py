"""月1回、決まった時刻に動く。条文を取り直して比べ、早見の画面を作り直し、結果を記録に1行足す。AIは使わない。
条文が前回から変わった月だけ「載せ直しが要る」の印（条文の控え\\載せ直しが要る.txt）を置く。
印があれば、手元で確かめて画面を載せ直し、印を消す。"""
import subprocess, sys, datetime, pathlib, os, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = ROOT / "条文の控え"
LOG = STORE / "更新の記録.txt"
FLAG = STORE / "載せ直しが要る.txt"
CHANGES = STORE / "変わった条.json"


def 変わった数():
    try:
        return len(json.loads(CHANGES.read_text(encoding="utf-8")))
    except Exception:
        return 0


before = 変わった数()
lines = []
ok_all = True
for s in ("条文を更新.py", "早見を作る.py"):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "道具" / s)], capture_output=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ))
    out = " ".join(r.stdout.strip().splitlines()[:2])
    err = " ".join(r.stderr.strip().splitlines()[-2:]) if r.returncode else ""
    ok_all = ok_all and r.returncode == 0
    lines.append(f"{s}: {'OK' if r.returncode == 0 else 'NG'} {out} {err}")
after = 変わった数()
now = datetime.datetime.now()
if after > before:
    new = json.loads(CHANGES.read_text(encoding="utf-8"))[before:]
    keys = sorted({x.get("条", "") for x in new})
    with FLAG.open("a", encoding="utf-8") as f:
        f.write(f"{now:%Y-%m-%d} 変わった条 {len(keys)}件: {'・'.join(keys)}（画面の作り直し: {'OK' if ok_all else 'NG'}）\n")
    lines.append(f"変わった条 {len(keys)}件 → 載せ直しが要る")
else:
    lines.append("変わった条 0件 → 載せ直し不要")
with LOG.open("a", encoding="utf-8") as f:
    f.write(f"{now:%Y-%m-%d %H:%M} " + " / ".join(lines) + "\n")
