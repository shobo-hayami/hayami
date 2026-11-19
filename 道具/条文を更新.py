"""e-Gov 法令APIから消防法・施行令・施行規則を取り、条ごとの原文と指紋を保存する。
AIは使わない。前回と指紋が違う条を「変わった条」として記録する。
使い方: python 条文を更新.py            （取ってきて比べる）
        python 条文を更新.py --local    （保存済みXMLだけで作り直す・通信なし）
"""
import sys as _s; _s.stdout.reconfigure(encoding="utf-8"); _s.stderr.reconfigure(encoding="utf-8")
import sys, json, hashlib, datetime, urllib.request, pathlib, re
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = ROOT / "条文の控え"
LAWS = {
    "法": ("消防法", "323AC1000000186"),
    "令": ("消防法施行令", "336CO0000000037"),
    "規": ("消防法施行規則", "336M50000008006"),
}


def fetch(law_id, dest):
    url = f"https://laws.e-gov.go.jp/api/1/lawdata/{law_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "law-reader/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if b"<Article" not in data:
        raise RuntimeError(f"{law_id}: 条文が入っていない応答")
    dest.write_bytes(data)


def text_of(el):
    return re.sub(r"\s+", "", "".join(el.itertext()))


def article_text(art):
    lines = []
    cap = art.find("ArticleCaption")
    title = art.find("ArticleTitle")
    head = (text_of(title) if title is not None else "") + (text_of(cap) if cap is not None else "")
    lines.append(head)
    for para in art.findall("Paragraph"):
        num = para.find("ParagraphNum")
        sent = para.find("ParagraphSentence")
        p = (text_of(num) + "　" if num is not None and text_of(num) else "") + (text_of(sent) if sent is not None else "")
        lines.append(p)
        for item in para.findall("Item"):
            walk(item, "Item", 1, lines)
        # 項の中の表（令13条の表・規1の3の表など）
        for tbl in para.iter("TableStruct"):
            lines.append("　〔表〕")
            for row in tbl.iter("TableRow"):
                lines.append("　｜" + " ｜ ".join(text_of(c) for c in row.findall("TableColumn")))
    return "\n".join(lines)


def walk(el, tag, depth, lines):
    t = el.find(tag + "Title")
    s = el.find(tag + "Sentence")
    lines.append("　" * depth + (text_of(t) if t is not None else "") + "　" + (text_of(s) if s is not None else ""))
    nxt = "Subitem1" if tag == "Item" else "Subitem" + str(int(tag[7:]) + 1)
    for child in el.findall(nxt):
        walk(child, nxt, depth + 1, lines)


def parse(xml_path):
    root = ET.parse(xml_path).getroot()
    main = root.find(".//MainProvision")
    out = {}
    for art in main.iter("Article"):
        num = art.get("Num")
        body = article_text(art)
        out[num] = {"text": body, "hash": hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]}
    # 別表（用途区分の別表第一など）
    for i, tbl in enumerate(root.iter("AppdxTable"), 1):
        t = tbl.find("AppdxTableTitle")
        lines = [text_of(t) if t is not None else f"別表{i}"]
        for row in tbl.iter("TableRow"):
            lines.append(" ｜ ".join(text_of(c) for c in row.findall("TableColumn")))
        body = "\n".join(lines)
        out[f"別表{i}"] = {"text": body, "hash": hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]}
    return out


def main():
    local = "--local" in sys.argv
    today = datetime.date.today().isoformat()
    index_path = STORE / "条文.json"
    old = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"articles": {}}
    changes_path = STORE / "変わった条.json"
    changes = json.loads(changes_path.read_text(encoding="utf-8")) if changes_path.exists() else []
    new = {"articles": {}, "laws": {}}
    # 3本とも取れてから入れ替える（途中で止まっても前回の控えは残る）
    src = {}
    for key, (name, law_id) in LAWS.items():
        xml = STORE / f"{law_id}.xml"
        if not local:
            tmp = STORE / f"{law_id}.xml.tmp"
            fetch(law_id, tmp)
            src[key] = tmp
        else:
            src[key] = xml
    parsed = {key: parse(src[key]) for key in LAWS}
    # 取り損ねの見張り: 条の数が前回の9割を切ったら何も書き換えずに止める
    for key in LAWS:
        prev_n = sum(1 for a in old["articles"].values() if a.get("law") == key)
        if prev_n and len(parsed[key]) < prev_n * 0.9:
            raise SystemExit(f"取り損ね: {LAWS[key][0]} の条が {len(parsed[key])}（前回 {prev_n}）。何も書き換えていない")
    if not local:
        for key, (name, law_id) in LAWS.items():
            src[key].replace(STORE / f"{law_id}.xml")
    for key, (name, law_id) in LAWS.items():
        arts = parsed[key]
        new["laws"][key] = {"name": name, "id": law_id, "fetched": today if not local else old.get("laws", {}).get(key, {}).get("fetched", today),
                            "url": f"https://laws.e-gov.go.jp/law/{law_id}"}
        for num, a in arts.items():
            k = f"{key}{num}"
            prev = old["articles"].get(k)
            a["law"] = key
            if prev and prev["hash"] != a["hash"] and "--reset" not in sys.argv:
                changes.append({"条": k, "日": today, "前": prev["text"], "後": a["text"]})
            new["articles"][k] = a
    index_path.write_text(json.dumps(new, ensure_ascii=False, indent=0), encoding="utf-8")
    changes_path.write_text(json.dumps(changes, ensure_ascii=False, indent=1), encoding="utf-8")
    n = {k: sum(1 for a in new["articles"].values() if a["law"] == k) for k in LAWS}
    print(f"条の数 {n} / 変わった条（累計） {len(changes)}")


if __name__ == "__main__":
    main()
