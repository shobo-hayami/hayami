"""札を読み直して確かめた後に動かす。札の確認日を今日にし、根拠の条のいまの指紋を札に書く。
赤い帯はこれで消える。使い方: python 確認済みにする.py 札の名前（拡張子なし。複数可。all で全部）"""
import sys, json, re, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
arts = json.loads((ROOT / "条文の控え" / "条文.json").read_text(encoding="utf-8"))["articles"]
today = datetime.date.today().isoformat()
sys.stdout.reconfigure(encoding="utf-8")
names = sys.argv[1:]
if names and names[0] == "判定表":
    # 判定表（設備ごとのJSON）の確認日と指紋を書く。名前を続けて書けばその表だけ
    for p in sorted((ROOT / "判定表").glob("*.json")):
        if len(names) > 1 and p.stem not in names[1:]:
            continue
        t = json.loads(p.read_text(encoding="utf-8"))
        t["確認日"] = today
        t["指紋"] = {k: arts[k]["hash"] for k in t["条"] if k in arts}
        p.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"判定表 {p.stem}: 確認日 {today} / 指紋 {len(t['指紋'])}条")
    sys.exit(0)
paths = sorted((ROOT / "札").glob("*.md")) if names == ["all"] else [ROOT / "札" / f"{n}.md" for n in names]
for p in paths:
    raw = p.read_text(encoding="utf-8")
    head, body = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S).groups()
    meta = [l for l in head.splitlines() if not l.startswith(("確認日:", "指紋:"))]
    keys = [x.strip() for l in meta if l.startswith("根拠:") for x in l[3:].split(",") if x.strip()]
    fp = ", ".join(f"{k}={arts[k]['hash']}" for k in keys if k in arts)
    meta += [f"確認日: {today}", f"指紋: {fp}"]
    p.write_text("---\n" + "\n".join(meta) + "\n---\n" + body, encoding="utf-8")
    print(f"{p.stem}: 確認日 {today} / 指紋 {len(fp.split(','))}条")
