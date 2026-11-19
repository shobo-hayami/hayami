"""札と条文の控えから、通信なしで開ける早見の画面（1枚のHTML）を作る。AIは使わない。
あわせて【原文】の行の数値が、根拠の条文に本当にあるかを確かめ、無い行を出す。
使い方: python 早見を作る.py
"""
import sys as _s; _s.stdout.reconfigure(encoding="utf-8"); _s.stderr.reconfigure(encoding="utf-8")
import json, re, html, datetime, pathlib, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
CARDS = ROOT / "札"
STORE = ROOT / "条文の控え"
OUT = ROOT / "早見.html"

USES = [
    ("1イ", "(1)イ 劇場・映画館"), ("1ロ", "(1)ロ 公会堂・集会場"),
    ("2イ", "(2)イ キャバレー等"), ("2ロ", "(2)ロ 遊技場・ダンスホール"), ("2ハ", "(2)ハ 性風俗関連店舗"), ("2ニ", "(2)ニ カラオケ・ネットカフェ"),
    ("3イ", "(3)イ 待合・料理店"), ("3ロ", "(3)ロ 飲食店"), ("4", "(4) 物販店・百貨店・展示場"),
    ("5イ", "(5)イ 旅館・ホテル"), ("5ロ", "(5)ロ 寄宿舎・共同住宅"),
    ("6イ1", "(6)イ(1) 特定診療科・病床の病院"), ("6イ2", "(6)イ(2) 特定診療科・4床以上の診療所"), ("6イ3", "(6)イ(3) その他の病院・有床診療所"), ("6イ4", "(6)イ(4) 無床診療所・助産所"),
    ("6ロ1", "(6)ロ(1) 特養・老健・認知症グループホーム・ショートステイ／要介護3以上が主の有料老人ホーム・軽費老人ホーム・宿泊ありの小規模多機能"), ("6ロ2", "(6)ロ(2) 救護施設"), ("6ロ3", "(6)ロ(3) 乳児院"), ("6ロ4", "(6)ロ(4) 障害児入所施設"), ("6ロ5", "(6)ロ(5) 障害者支援施設・短期入所・共同生活援助（避難が困難な人が主）"),
    ("6ハ1", "(6)ハ(1) デイサービス・老人福祉センター／ロ(1)に当たらない有料老人ホーム・軽費老人ホーム・小規模多機能"), ("6ハ2", "(6)ハ(2) 更生施設"), ("6ハ3", "(6)ハ(3) 保育所・認定こども園・児童養護施設・一時預かり"), ("6ハ4", "(6)ハ(4) 児童発達支援・放課後等デイサービス"), ("6ハ5", "(6)ハ(5) 生活介護・就労支援・地域活動支援センター・福祉ホーム・ロ(5)に当たらない短期入所や共同生活援助"),
    ("6ニ", "(6)ニ 幼稚園・特別支援学校"), ("7", "(7) 学校"), ("8", "(8) 図書館・博物館"),
    ("9イ", "(9)イ 蒸気・熱気浴場"), ("9ロ", "(9)ロ その他の公衆浴場"), ("10", "(10) 駅・空港の旅客施設"), ("11", "(11) 神社・寺院・教会"),
    ("12イ", "(12)イ 工場・作業場"), ("12ロ", "(12)ロ 映画・テレビスタジオ"), ("13イ", "(13)イ 車庫・駐車場"), ("13ロ", "(13)ロ 航空機格納庫"),
    ("14", "(14) 倉庫"), ("15", "(15) 事務所など"), ("16イ", "(16)イ 特定用途を含む複合ビル"), ("16ロ", "(16)ロ その他の複合ビル"),
    ("16の2", "(16の2) 地下街"), ("16の3", "(16の3) 準地下街"), ("17", "(17) 重要文化財"), ("18", "(18) アーケード"), ("19", "(19) 山林"), ("20", "(20) 舟車"),
]
EQUIP = ["消火器", "屋内消火栓", "スプリンクラー", "特殊消火", "屋外消火栓", "動力消防ポンプ", "自動火災報知", "ガス漏れ", "漏電", "消防機関へ通報",
         "非常警報", "避難器具", "誘導灯", "消防用水", "排煙", "連結散水", "連結送水管", "非常コンセント", "無線通信補助"]
LAW_LABEL = {"法": "消防法", "令": "消防法施行令", "規": "消防法施行規則"}


def kanji(n):
    digits = "〇一二三四五六七八九"
    if n == 0:
        return "〇"
    if n >= 10000:
        return kanji(n // 10000) + "万" + (kanji(n % 10000) if n % 10000 else "")
    s = ""
    for unit, val in (("千", 1000), ("百", 100), ("十", 10)):
        d = n // val
        n %= val
        if d:
            s += ("" if d == 1 else digits[d]) + unit
    if n:
        s += digits[n]
    return s


def parse_card(path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    meta["根拠"] = [x.strip() for x in meta.get("根拠", "").split(",") if x.strip()]
    meta["早見表"] = {k[3:-1]: v for k, v in meta.items() if k.startswith("早見[") and k.endswith("]")}
    meta["指紋"] = dict(x.strip().split("=") for x in meta.get("指紋", "").split(",") if "=" in x)
    meta["body"] = m.group(2)
    meta["id"] = path.stem
    meta.setdefault("確認日", "2000-01-01")
    return meta


REF = re.compile(r"(令|規|法)?\d+条(の\d+)?(第?\d+項)?(第?\d+号)?(の\d+)?|第?\d+(項|号)(の\d+)?|\d{4}年(\d+月)?")
NUM = re.compile(r"(\d[\d,\.]*)\s*(㎡|人|m|階|倍|個|つ)")


def check_numbers(card, arts):
    bad = []
    allsrc = "".join(arts.get(k, {}).get("text", "") for k in card["根拠"])
    for code, txt in card.get("早見表", {}).items():
        for num, unit in NUM.findall(REF.sub("", txt)):
            if "." not in num and kanji(int(num.replace(",", ""))) not in allsrc:
                bad.append(f"{card['id']}: 早見[{code}]の「{num}{unit}」が根拠の条文に見つからない")
    for line in card["body"].splitlines():
        m = re.search(r"【原文:([^】]+)】", line)
        if not m:
            continue
        src = "".join(arts.get(k.strip(), {}).get("text", "") for k in m.group(1).split(","))
        src += "".join(arts.get(k, {}).get("text", "") for k in card["根拠"])
        stripped = REF.sub("", line)
        for num, unit in NUM.findall(stripped):
            if "." in num:
                continue
            k = kanji(int(num.replace(",", "")))
            if k not in src:
                bad.append(f"{card['id']}: 「{num}{unit}」が条文に見つからない → {line.strip()[:60]}")
    return bad


def changed_keys(card, arts):
    """札に記録した指紋と、いまの条文の指紋が違う条（＝確認した後に変わった条）"""
    return [k for k in card["根拠"] if k in arts and card["指紋"].get(k) != arts[k]["hash"]]


def render_body(body):
    out = []
    in_list = False
    for line in body.splitlines():
        line = line.rstrip()
        if not line:
            continue
        cls = ""
        tag = ""
        m = re.search(r"【原文:([^】]+)】", line)
        if m:
            tag = f'<span class="tag ok" onclick="原文へ(this)">原文 {html.escape(m.group(1))} ›</span>'
            line = line.replace(m.group(0), "")
        m = re.search(r"【二次資料\s*([^】]*)】", line)
        if m:
            cls = "second"
            url = m.group(1).strip()
            tag = f'<span class="tag second">二次資料</span> <a href="{html.escape(url)}">{html.escape(url[:40])}…</a>' if url else '<span class="tag second">二次資料</span>'
            line = line.replace(m.group(0), "")
        if "【計算】" in line:
            tag = '<span class="tag calc">条文の数値から計算</span>'
            line = line.replace("【計算】", "")
        if "【未確認】" in line:
            cls = "unknown"
            tag = '<span class="tag unknown">未確認</span>'
            line = line.replace("【未確認】", "")
        if line.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h4>{html.escape('あわせて知っておくこと（未確認の行には印）' if line[3:].strip() == '確かめていないこと' else line[3:])}</h4>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f'<li class="{cls}">{html.escape(line[2:])} {tag}</li>')
        else:
            out.append(f'<p class="{cls}">{html.escape(line)} {tag}</p>')
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


KNUM = {c: i for i, c in enumerate("〇一二三四五六七八九")}


def kan2int(s):
    n, cur = 0, 0
    for ch in s:
        if ch in KNUM:
            cur = KNUM[ch]
        elif ch == "十":
            n += (cur or 1) * 10
            cur = 0
    return n + cur


def load_tables(arts):
    """判定表を読み、数値の照合・号の抜け・条文の変化を見て、例題の試験を回す"""
    import subprocess
    probs, tables = [], []
    for p in sorted((ROOT / "判定表").glob("*.json")):
        t = json.loads(p.read_text(encoding="utf-8"))
        src = "".join(arts.get(k, {}).get("text", "") for k in t["条"])
        for row in t["行"]:
            for c in row.get("条件", []):
                v = c[2]
                if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 and kanji(int(v)) not in src:
                    probs.append(f"判定表 {t['設備']}: {row['号']} の数値 {v} が条文に見つからない")
        # 号の抜け: 1項の号を数え、表に出てこない号を「未収録」にする
        t["未収録"] = []
        key = t.get("網羅")
        if key and key in arts:
            first = arts[key]["text"].split("\n２　")[0]
            nums = {kan2int(m) for m in re.findall(r"^　([一二三四五六七八九十]+)　", first, re.M)}
            have = {int(m) for row in t["行"] for m in re.findall(r"1項(\d+)号", row["号"])}
            t["未収録"] = sorted(nums - have)
            if t["未収録"]:
                probs.append(f"判定表 {t['設備']}: 表に無い号 {t['未収録']}")
        t["変わった"] = [k for k in t["条"] if k in arts and t.get("指紋", {}).get(k) not in (None, arts[k]["hash"])]
        t["確認日"] = t.get("確認日", "")
        tables.append(t)
    r = subprocess.run(["node", str(ROOT / "道具" / "試験_判定.js")], capture_output=True, encoding="utf-8", errors="replace")
    msg = (r.stdout.strip().splitlines() or ["試験が動かなかった"])[-1]
    if r.returncode != 0:
        probs.append("例題の試験に失敗。判定は画面に入れていない: " + r.stdout.strip().replace("\n", " / ")[:400])
    return tables, probs, r.returncode == 0, msg


def 既存の変わった(arts):
    """既存の建物の印の根拠の条で、確かめたときから条文が変わったもの（変わっていれば画面は印を「見直し中」にする）"""
    p = ROOT / "道具" / "既存の印.json"
    if not p.exists():
        return ["既存の印.json が無い"]
    fp = json.loads(p.read_text(encoding="utf-8")).get("指紋", {})
    return [k for k, h in fp.items() if k not in arts or arts[k]["hash"] != h]


def main():
    today = datetime.date.today()
    data = json.loads((STORE / "条文.json").read_text(encoding="utf-8"))
    arts = data["articles"]
    changes = json.loads((STORE / "変わった条.json").read_text(encoding="utf-8"))
    cards = [parse_card(p) for p in sorted(CARDS.glob("*.md"))]
    problems = []
    for c in cards:
        problems += check_numbers(c, arts)
        for k in c["根拠"]:
            if k not in arts:
                problems.append(f"{c['id']}: 根拠の「{k}」が条文の控えに無い")

    sections = []
    for c in cards:
        moved = changed_keys(c, arts)
        changed = [[x for x in changes if x["条"] == k][-1] for k in moved if any(x["条"] == k for x in changes)]
        old = (today - datetime.date.fromisoformat(c["確認日"])).days > 365
        band = ""
        if moved:
            band += '<div class="band red">条文が変わった・要再確認（' + "、".join(f"{k}" + "".join(f" {x['日']}" for x in changed if x["条"] == k) for k in moved) + "）</div>"
            for x in changed:
                band += f'<details class="diff"><summary>{html.escape(x["条"])} の新旧</summary><div class="cols"><pre>{html.escape(x["前"])}</pre><pre>{html.escape(x["後"])}</pre></div></details>'
        if old:
            band += '<div class="band gray">確認が古い（1年を超えた）</div>'
        src = ""
        for k in c["根拠"]:
            a = arts.get(k)
            if not a:
                continue
            law = LAW_LABEL.get(k[0], "")
            src += f'<details class="src" data-k="{html.escape(k)}"><summary>原文 {html.escape(law)} {html.escape(k[1:].replace("_", "の"))}</summary><pre>{html.escape(a["text"])}</pre></details>'
        search = " ".join([c.get("題", ""), c.get("呼び名", ""), c.get("設備", ""), c.get("用途", ""), c["body"]])
        sections.append(
            f'<section class="card" id="{html.escape(c["id"])}" data-s="{html.escape(search)}">'
            f'<h3>{html.escape(c.get("題", ""))}</h3>{band}'
            f'<div class="quick">{html.escape(c.get("早見", ""))}</div>'
            f'{render_body(c["body"])}{src}'
            f'<div class="foot">確認日 {html.escape(c["確認日"])}　最終判断は条文の原文と所轄消防署の運用で</div></section>'
        )

    head = "".join(f'<option value="{html.escape(code)}">{html.escape(label)}</option>' for code, label in USES)
    rows = ""
    基準 = {}
    for code, label in USES:
        items = ""
        for e in EQUIP:
            hit = [(c, c.get("早見", "")) for c in cards if c.get("用途") == code and c.get("設備") == e]
            hit += [(c, c["早見表"][code]) for c in cards if c.get("用途") == "全" and c.get("設備") == e and code in c["早見表"]]
            if hit:
                c, txt = hit[0]
                warn = " warn" if changed_keys(c, arts) else ""
                基準.setdefault(code, {})[e] = [txt, c["id"], bool(warn)]
                items += f'<li class="has{warn}"><b>{html.escape(e)}</b> <a href="#{html.escape(c["id"])}" onclick="openCard()">{html.escape(txt)}</a></li>'
            else:
                common = [c for c in cards if c.get("用途") == "全" and c.get("設備") == e]
                if common:
                    基準.setdefault(code, {})[e] = [common[0].get("早見", ""), common[0]["id"], bool(changed_keys(common[0], arts)), True]
                items += f'<li class="none"><b>{html.escape(e)}</b> 用途で決まる線なし（階・規模の共通の線は設備の札で）</li>'
        rows += f'<ul class="use hide" data-use="{html.escape(code)}">{items}</ul>'
    rows = '<h2>設備ごとの条件（早見）</h2>' + rows
    rules = [c for c in cards if c.get("設備") in ("決まり", "用途区分", "特例")]
    rules_html = '<h2>設備以外の決まり（札を開く）</h2><ul class="rules">' + "".join(
        f'<li><a href="#{html.escape(c["id"])}" onclick="openCard()">{html.escape(c.get("題", ""))}</a> — {html.escape(c.get("早見", ""))}</li>' for c in rules) + "</ul>"

    tables, tproblems, test_ok, test_msg = load_tables(arts)
    problems += tproblems
    judge = ""
    公開設定 = {"公開": False}
    _conf = json.loads((ROOT / "設定.json").read_text(encoding="utf-8")) if (ROOT / "設定.json").exists() else {}
    出典 = ("出典: e-Gov法令検索（https://laws.e-gov.go.jp/）の消防法・消防法施行令・消防法施行規則。"
            "条文を取り出し、判定の表とまとめに編集・加工して作成。加工したのは" + _conf.get("作成者", "この画面の作成者（個人）")
            + "で、国・デジタル庁・消防庁が作ったものではない")
    if os.environ.get("早見_公開") == "1":
        conf = json.loads((ROOT / "設定.json").read_text(encoding="utf-8"))
        公開設定 = {"公開": True, "知らせ先": conf.get("知らせ先URL", ""), "日数": int(conf.get("古さの警告の日数", 40))}
    rows = rows + rules_html
    if test_ok:
        rows = rules_html  # 用途別の基準は判定の表の中に重ねて出す
        js = (ROOT / "道具" / "判定.js").read_text(encoding="utf-8") + "\n" + (ROOT / "道具" / "語.js").read_text(encoding="utf-8") + "\n" + (ROOT / "道具" / "号.js").read_text(encoding="utf-8")
        # 練習問題: 試験に通ったときだけ入口を出す（落ちても早見の本体は出す）
        import subprocess
        rp = subprocess.run(["node", str(ROOT / "道具" / "試験_練習.js")], capture_output=True, encoding="utf-8", errors="replace")
        練習あり = rp.returncode == 0
        test_msg += " / " + ((rp.stdout.strip().splitlines() or ["練習問題の試験が動かなかった"])[-1])
        if not 練習あり:
            problems.append("練習問題の試験に失敗。練習問題の入口は出していない: " + rp.stdout.strip().replace("\n", " / ")[:300])
        # 号を開く: 判定表の号の名前を全部切り出して確かめる。落ちたら一覧に出す（早見の本体は作る）
        rg = subprocess.run(["node", str(ROOT / "道具" / "試験_号.js")], capture_output=True, encoding="utf-8", errors="replace")
        test_msg += " / " + ((rg.stdout.strip().splitlines() or ["号を開く試験が動かなかった"])[-1])
        if rg.returncode != 0:
            problems.append("号を開く試験に失敗: " + rg.stdout.strip().replace("\n", " / ")[:300])
        js += "\n" + (ROOT / "道具" / "練習.js").read_text(encoding="utf-8")
        js += "\nvar 練習あり=" + ("true" if 練習あり else "false") + ";\nvar 練習の例題=" + (ROOT / "道具" / "例題.json").read_text(encoding="utf-8").strip() + ";\nvar 練習の境目=" + (ROOT / "道具" / "例題_境目.json").read_text(encoding="utf-8").strip() + ";"
        judge = ("<script>" + js + "\nvar 表たち=" + json.dumps(tables, ensure_ascii=False) + ";\n" + "var 設備の順=" + json.dumps(EQUIP, ensure_ascii=False) + ";\nvar 基準=" + json.dumps(基準, ensure_ascii=False)
                 + ";\nvar 用途の名=" + json.dumps(dict(USES), ensure_ascii=False)
                 + ";\nvar 条文=" + json.dumps({k: arts[k]["text"] for t in tables for k in t.get("条", []) if k in arts}, ensure_ascii=False)
                 + ";\nvar 決まり=" + json.dumps([[c["id"], c.get("題", ""), c.get("早見", "")] for c in rules], ensure_ascii=False)
                 + ";\nvar 公開版=" + json.dumps(公開設定, ensure_ascii=False)
                 + ";\nvar 既存の変わった=" + json.dumps(既存の変わった(arts), ensure_ascii=False)
                 + ";\n" + (ROOT / "道具" / "練習_画面.js").read_text(encoding="utf-8") + "\n" + UI_JS + "</script>")
    fetched = "・".join(f"{v['name']} {v['fetched']}" for v in data["laws"].values())
    if test_ok:
        main, cardcls = '<div id="app"></div>', "app"
    else:
        main = ('<input id="q" type="search" placeholder="探す（例: デイサービス スプリンクラー）" oninput="filter()">'
                '<div class="tbl"><div class="step">建物の用途を選ぶ</div><select id="use" onchange="pick()">'
                '<option value="">建物の用途を選ぶ（別表第一）</option>%HEAD%</select><div id="check"></div>%ROWS%</div>')
        cardcls = ""
    page = TEMPLATE.replace("%MAIN%", main).replace("%CARDCLS%", cardcls).replace("%HEAD%", head).replace("%ROWS%", rows).replace("%CARDS%", "\n".join(sections)) \
        .replace("%BUILT%", today.isoformat()).replace("%FETCHED%", html.escape(fetched)).replace("%N%", str(len(cards))) \
        .replace("%JUDGE%", judge).replace("%SOURCE%", html.escape(出典))
    OUT.write_text(page, encoding="utf-8")
    print(f"札 {len(cards)}枚 / 数値が条文に見つからない行 {len(problems)}件 / 判定表 {len(tables)}個・{test_msg}")
    for p in problems:
        print("  " + p)


TEMPLATE = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>消防用設備の設置基準 早見（条文つき）</title>
<style>
body{font-family:"Hiragino Sans","Yu Gothic","Meiryo",sans-serif;margin:0;padding:12px;color:#222;line-height:1.6;font-size:15px;background:#fafafa}
h1{font-size:18px;margin:4px 0}
.meta{font-size:12px;color:#666}
#q{width:100%;box-sizing:border-box;font-size:16px;padding:10px;border:2px solid #c33;border-radius:8px;margin:8px 0;position:sticky;top:0;z-index:2}
.tbl{border:1px solid #ddd;background:#fff;margin-bottom:12px;padding:8px;border-radius:8px}
#use{width:100%;font-size:16px;padding:8px}
ul.use,ul.rules{padding-left:0;list-style:none;font-size:14px}
ul.use li,ul.rules li{border-bottom:1px solid #eee;padding:6px 2px}
ul.use li.none{color:#999;font-size:12px}
ul.use li.warn{background:#ffd6d6}
h2{font-size:15px;margin:10px 0 4px}
.step{font-size:13px;color:#555;margin-bottom:4px}
.ans{font-size:13px;padding:6px;border-bottom:1px dashed #ddd;cursor:pointer}
.ans .fix{color:#06c;font-size:12px;float:right}
.ans.auto{color:#999;cursor:default}.ans.auto .fix{color:#999}
.q{background:#fff3f3;border:2px solid #c33;border-radius:8px;padding:10px;margin:8px 0}
.qt{font-weight:bold;margin-bottom:8px}
.q input{font-size:20px;width:60%;padding:8px;box-sizing:border-box}
.b{font-size:16px;padding:10px 14px;margin:4px 4px 0 0;border-radius:8px;border:1px solid #999;background:#fff}
.b.go{background:#c33;color:#fff;border-color:#c33}
.b.dk{color:#666}
.b.copy{width:100%;margin-top:8px}
.done{font-weight:bold;color:#265c26;margin:8px 0}
.rr{border-left:6px solid #999;background:#fff;padding:6px 8px;margin:6px 0;border-radius:4px;font-size:13px}
.rr .rh{display:flex;justify-content:space-between;font-size:15px}
.rr.need{border-color:#d22}.rr.need .st{color:#d22;font-weight:bold}
.rr.no{border-color:#2a8}.rr.no .st{color:#2a8}
.rr.wait{border-color:#e90}.rr.wait .st{color:#b60}
.rr.cant{border-color:#888}.rr.cant .st{color:#666}
.rr.yet{border-color:#ccc}.rr.yet .st{color:#999}
#cards.app .card{display:none}#cards.app .card.show{display:block}
.top{display:flex;justify-content:space-between;margin:0;position:sticky;top:0;z-index:3;background:#fafafa;padding:4px 0}
body.deep h1,body.deep .meta{display:none}
.tag.ok{display:inline-block;padding:6px 10px;font-size:13px;margin:2px 0}
.inline{border:2px solid #9bc;border-radius:6px;padding:4px;margin:4px 0;background:#f1f6ff}
.inline pre{max-height:50vh;overflow:auto;font-size:14px}
.sm{font-size:14px;padding:8px 12px;border-radius:8px;border:1px solid #999;background:#fff;margin:6px 0}
.where{font-size:13px;color:#555;background:#fff;border-radius:6px;padding:4px 8px;margin-bottom:6px}
.nb{display:block;width:100%;text-align:left;font-size:17px;padding:14px 12px;margin:8px 0;border-radius:10px;border:2px solid #c33;background:#fff;color:#222}
.nb.lite{border:1px solid #999;font-size:15px;padding:10px 12px}
.nb.use{font-size:15px}
.nb .num{display:block;font-size:12px;color:#c33}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.nb.sq{text-align:center;padding:12px 0;margin:0}
.grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:6px}.nb.sq2{font-size:15px;margin:0;padding:12px 8px}
.sub{margin-top:18px}
.rb{display:block;width:100%;text-align:left;background:#fff;border:1px solid #ddd;border-left:6px solid #999;border-radius:6px;padding:10px;margin:6px 0;font-size:15px}
.rb .st{float:right;font-size:13px}.rb .kj{display:block;font-weight:normal;font-size:13px}
.rb.need{border-left-color:#d22}.rb.need .st{color:#d22;font-weight:bold}
.rb.wait{border-left-color:#e90}.rb.wait .st{color:#b60}
.rb.cant{border-left-color:#888}.rb.cant .st{color:#666}
.rb.no{border-left-color:#2a8}.rb.no .st{color:#2a8}
.red{color:#d22;font-size:12px}
.b.was{border:3px solid #333}
.vb{font-size:13px;padding:4px 8px;margin:2px;border:1px solid #69c;border-radius:12px;background:#fff;color:#036}
.also{font-size:14px;font-weight:bold;color:#a40;background:#fff4e0;padding:4px;margin:4px 0;border-radius:4px}
mark{background:#ffe066}
.vb.unk{border-color:#e90;color:#a40}
#copied textarea{width:100%;box-sizing:border-box;font-size:13px}
details.sum summary{font-size:13px;color:#036;cursor:pointer}
details.no summary{font-size:15px;padding:10px 0;color:#2a8;cursor:pointer}
.sum{font-size:13px;background:#eef6ff;border-radius:6px;padding:4px 8px;margin:4px 0}
.hint{font-size:13px;color:#555;background:#fff;border-radius:6px;padding:4px 6px;margin-bottom:6px}
.err{color:#d22;font-weight:bold;font-size:14px;min-height:0}
.tag.ok{cursor:pointer;text-decoration:underline}
details.src summary{font-size:15px;padding:10px 4px;border:1px solid #9bc;border-radius:6px;margin:6px 0;background:#f1f6ff}
details.src pre{font-size:14px}
#q2{width:100%;box-sizing:border-box;font-size:16px;padding:10px;border:2px solid #c33;border-radius:8px}
.kj{font-size:13px;font-weight:bold;color:#123}.kj.warn{background:#ffd6d6}
.jou{font-size:12px;color:#666}
.tally{display:flex;flex-wrap:wrap;gap:4px;margin:8px 0;position:sticky;top:60px;z-index:1;background:#fafafa;padding:4px 0}
.tl{font-size:13px;padding:6px 8px;border-radius:16px;border:2px solid #999;background:#fff}
.tl.need{border-color:#d22;color:#d22}.tl.no{border-color:#2a8;color:#2a8}.tl.wait{border-color:#e90;color:#b60}.tl.cant{border-color:#888;color:#666}.tl.yet{border-color:#ccc;color:#999}
.tl.on{background:#333;color:#fff;border-color:#333}
.skip{margin-top:8px;background:none;border:none;color:#06c;font-size:13px;text-decoration:underline;padding:4px 0}
.why{margin:4px 0}.cand{background:#eef6ff;padding:4px;margin:4px 0}.note{color:#666;font-size:12px}
table{border-collapse:collapse;font-size:12px;min-width:900px}
th,td{border:1px solid #ddd;padding:6px;vertical-align:top}
thead th{background:#c33;color:#fff;position:sticky;top:0}
tbody th{background:#fff3f3;position:sticky;left:0;min-width:110px;text-align:left}
td.has a{color:#123;text-decoration:none;display:block}
td.warn{background:#ffd6d6}
td.none{color:#bbb;text-align:center}
.card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:10px 12px;margin:10px 0}
.card h3{font-size:16px;margin:0 0 6px}
.card h4{font-size:14px;margin:10px 0 4px;border-left:4px solid #c33;padding-left:6px}
.card ul{padding-left:18px;margin:4px 0}
.quick{background:#f1f6ff;padding:6px 8px;border-radius:6px;font-weight:bold;font-size:14px}
li.second,p.second{background:#fff7c2}
li.unknown,p.unknown{background:#ffe0e0}
.tag{font-size:11px;padding:1px 5px;border-radius:4px;white-space:nowrap}
.tag.ok{background:#e3f4e3;color:#265c26}
.tag.second{background:#f5d000;color:#000}
.tag.unknown{background:#d22;color:#fff}
.tag.calc{background:#dde6f5;color:#234}
.band{padding:6px;border-radius:6px;margin:6px 0;font-weight:bold}
.band.red{background:#d22;color:#fff}
.band.stale{background:#ffe066;color:#222;position:sticky;top:0;z-index:4}
.band.gray{background:#999;color:#fff}
details.src summary,details.diff summary{color:#06c;cursor:pointer;font-size:13px}
pre{white-space:pre-wrap;font-size:12px;background:#f6f6f6;padding:8px;border-radius:6px}
.cols{display:flex;gap:6px}.cols pre{flex:1}
.foot{font-size:11px;color:#666;margin-top:8px;border-top:1px dashed #ccc;padding-top:4px}
.hide{display:none}
@media print{#q{display:none}.card{break-inside:avoid}details{display:block}table{min-width:0;font-size:9px}.tbl{overflow:visible}}
/* 屋外の光の下でも読める濃さ（文字と背景の比4.5以上）・指で押せる大きさ（高さ44px前後）・小さすぎない字 */
.rr.no .st,.rb.no .st,.tl.no,details.no summary{color:#17704a}
.rr.wait .st,.rb.wait .st{color:#8a4a00}
.ans.auto,.ans.auto .fix,.ans.auto b{color:#5f5f5f}
.sm{min-height:44px;font-size:15px}
.vb{min-height:40px;padding:8px 10px;font-size:14px}
details.sum summary,details.no summary{padding:12px 4px;font-size:15px}
.tag.ok{min-height:36px;line-height:24px}
.note,.jou{font-size:14px}.foot{font-size:13px}.ans .fix{font-size:14px}
.tag.unknown{font-size:13px}
.ptbl{border:1px solid #ccc;border-radius:6px;margin:6px 0;background:#fff}
.ptbl .pr{display:flex;justify-content:space-between;gap:8px;padding:7px 8px;border-bottom:1px solid #eee;cursor:pointer;font-size:14px}
.ptbl .pr b{font-weight:normal;color:#444}.ptbl .pr span{font-weight:bold;text-align:right}
.prow{margin:12px 0;padding:6px 0;border-bottom:1px solid #eee}.prow .pn{font-size:15px;margin-bottom:4px}.prow .b{min-height:44px;min-width:110px}
.rr.bad{outline:3px solid #000}.rr details summary{list-style:none;cursor:pointer}
.kz{display:block;font-size:12px;color:#666;font-weight:normal}
</style></head><body>
<h1>消防用設備の設置基準 早見（条文つき）</h1>
<div class="meta">まとめ %N%枚／画面を作った日 %BUILT%／条文を取った日 %FETCHED%<br>%SOURCE%</div>
%MAIN%
<div id="cards" class="%CARDCLS%">%CARDS%</div>
<div class="disc" style="border-top:1px solid #ccc;margin:16px 0 8px;padding-top:8px;font-size:13px;color:#555;line-height:1.6">個人が条文を読みやすく整理したもので、国・消防庁・消防本部が作ったものではない。判定は条文の条件だけで、特例・国の通知・条例・所轄の運用は入っていない。使うときは条文の原文と所轄の消防署で確かめる。この画面で生じた損害に、作った人は責任を負わない。</div>
<script>
function filter(){
  var w=document.getElementById('q').value.trim().split(/\\s+/).filter(Boolean);
  document.querySelector('.tbl').classList.toggle('hide', w.length>0);
  document.querySelectorAll('.card').forEach(function(c){
    var s=c.getAttribute('data-s');
    c.classList.toggle('hide', !w.every(function(x){return s.indexOf(x)>=0;}));
  });
}
function openCard(){document.getElementById('q').value='';filter();}
function pick(){var v=document.getElementById('use').value;
  document.querySelectorAll('ul.use').forEach(function(u){u.classList.toggle('hide',u.getAttribute('data-use')!==v);});
  if(window.判定の開始) 判定の開始(v);}
</script>
%JUDGE%
</body></html>
"""

UI_JS = r"""
var 答 = {};
var 大分類 = [
  ["人が集まる・遊ぶ", ["1イ","1ロ","2イ","2ロ","2ハ","2ニ"]],
  ["飲食・物販", ["3イ","3ロ","4"]],
  ["泊まる・住む", ["5イ","5ロ"]],
  ["病院・診療所", ["6イ1","6イ2","6イ3","6イ4"]],
  ["福祉・保育", null],
  ["学校・文化", ["6ニ","7","8","11","17"]],
  ["工場・倉庫・車庫・事務所", ["12イ","12ロ","13イ","13ロ","14","15"]],
  ["複合ビル・地下街", ["複合","16の2","16の3"]],
  ["その他（浴場・駅・アーケード・山林・舟車）", ["9イ","9ロ","10","18","19","20"]]
];
var 福祉 = [
  ["高齢の人", ["6ロ1","6ハ1"]],
  ["子ども", ["6ロ3","6ロ4","6ハ3","6ハ4"]],
  ["障害のある人", ["6ロ5","6ハ5"]],
  ["救護・更生", ["6ロ2","6ハ2"]]
];
var 色 = {"要る":"need","要らない":"no","まだ決まらない":"wait","判定できない":"cant","見直し中":"cant"};
var 道 = [];   // 通ってきた画面
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
function 見せる値(v){ return v === true ? "はい" : v === false ? "いいえ" : v; }
function 項(code){ var m = /^(\d+(?:の\d)?)/.exec(code); return m[1]; }
function 番号と名(code){ var t = 用途の名[code], i = t.indexOf(' '); return ['<span class="num">'+esc(t.slice(0,i))+'</span>', esc(t.slice(i+1))]; }
function 条を読む(k){ var m = /^([法令規])(\d+)(?:_(\d+))?$/.exec(k); return m ? m[1]+m[2]+'条'+(m[3]?'の'+m[3]:'') : k; }
var 調べた = [];
// ---- 複合ビル: 入っている用途と、その部分の床面積を並べる ----
var 下書き = [];
function 足せる(c){ return c !== '複合' && parseFloat(項(c)) <= 15 && !/の/.test(項(c)); }
function 短い名(code){ var t = 用途の名[code].split(' ').slice(1).join(' '), m = /^[^・／（]+/.exec(t); return m && m[0].length < t.length ? m[0] + 'など' : t; }
function 部分の札(ps){ return ps.map(function(p){ return 用途の名[p.用途].split(' ')[0] + ' ' + 短い名(p.用途) + ' ' + p.延べ + '㎡'; }); }
function 複合を始める(直す){ 下書き = 直す && 答.部分 ? 答.部分.map(function(p){ return Object.assign({}, p); }) : []; 進む({画面:'複合', 用途:null, 部分:null, 設備:null, 足す:false, 直す: !!直す, 練習から:false}); }
function 複合へ戻る(){ var i = -1; 道.forEach(function(x, j){ if(x.画面 === '複合') i = j; }); if(i >= 0) 何段か戻る(道.length - 1 - i); }
function 部分を直す(i){ 進む({画面:'部分の面積', 足す用途: 下書き[i].用途, 何番: i}); }
function 部分を消す(i){ 下書き.splice(i, 1); 描く(); }
function 部分を入れる(){
  var g = 今(), el = document.getElementById('in_part'), v = parseFloat(el.value), er = document.getElementById('err');
  if(el.value === '' || isNaN(v) || v <= 0){ er.textContent = '0より大きい数字を入れて'; el.focus(); return; }
  if(g.何番 !== null && g.何番 !== undefined) 下書き[g.何番].延べ = v;
  else { var same = 下書き.filter(function(p){ return p.用途 === g.足す用途; })[0]; if(same) same.延べ += v; else 下書き.push({用途: g.足す用途, 延べ: v}); }
  複合へ戻る();
}
function 複合の理由(code){ if(code === '16ロ') return '特定用途の部分が無いため'; var p = 下書き.filter(function(x){ return 用途に当たる(特定の用途, x.用途); })[0]; return 短い名(p.用途) + 'があるため'; }
function 複合を決める(){
  var code = 複合の用途(下書き), ps = 下書き.map(function(p){ return Object.assign({}, p); });
  if(今().直す && 答.部分){
    // 用途を直したときは、建物全体の答えを残し、部分ごとの答えだけ消す
    Object.keys(答).forEach(function(k){ if(/^p\d+_/.test(k)) delete 答[k]; });
    Object.keys(自動で入れた).forEach(function(k){ delete 答[k]; }); 自動で入れた = {};
    答.用途 = code; 答.部分 = ps; 自動を入れる();
    進む({画面:'結果', 用途: code, 部分: ps, 直す: false, 足す: false}); return;
  }
  答 = {用途: code, 部分: ps}; 自動で入れた = {};
  進む({画面:'調べ方', 用途: code, 部分: ps, 設備: null, 足す: false, 直す: false});
}
function 始める(e, keep){
  // 答えを空にして（同じ建物の続きなら残して）、最初の質問へ。効く質問が無ければ結果へ
  if(!keep){ 答 = {用途: 今().用途}; if(今().部分) 答.部分 = 今().部分.map(function(p){ return Object.assign({}, p); }); 自動で入れた = {}; 調べた = []; }
  if(e && 調べた.indexOf(e) < 0) 調べた.push(e);
  var q = 次の質問(対象(e), 答);
  if(q) 進む({画面:'問', 問: q.id, 設備: e});
  else if(e) 進む({画面:'設備', 見る: e, 設備: e, 結果から: true});
  else 進む({画面:'結果', 設備: e});
}
var 言い換え = {"保育園": "保育所", "ぼうかかんり": "防火管理", "老人ホーム": "老人ホーム", "グルホ": "グループホーム", "デイ": "デイサービス"};
function 条件の文(c){
  var f = c[0], op = c[1], v = c[2];
  var nm = f.indexOf('max:') === 0 ? f.slice(4).split(',').map(function(x){ return 語の名[x] || x; }).join('・') + 'のどれか' : (語の名[f] || f);
  if(op === '==') return v === true ? nm : v === false ? nm + 'でない' : nm + 'が' + v;
  var u = 語の単位[f] || (f.indexOf('max:') === 0 ? '㎡' : '');
  if(op === '>=倍') return nm + ' ' + v + u + '以上（耐火などは2〜3倍に読み替え）';
  return nm + ' ' + v + u + ({'>=':'以上','>':'超','<':'未満'}[op] || op);
}
function ほか(e, code){
  var t = 表たち.filter(function(x){ return x.設備 === e; })[0];
  var n = t.行.filter(function(r){ return 用途に当たる(r.用途, code) && r.結果 !== '注記'; }).length;
  return n > 1 ? '（ほかに条件' + (n - 1) + 'つ。押すと全部）' : '';
}
function 表から基準(e, code){
  // この用途に当たる号を、判定の表から1行ずつ文にする
  var t = 表たち.filter(function(x){ return x.設備 === e; })[0], out = [];
  t.行.forEach(function(r){
    if(!用途に当たる(r.用途, code) || r.結果 === '注記') return;
    var s = (r.条件 || []).map(条件の文).join('かつ');
    out.push(r.結果 === '判定できない' ? (s ? s + 'なら' : '') + '個別に判断（' + (r.理由 || '') + '）' : (s || '用途だけで') + 'で要る');
  });
  if(out.length) return out.join(' ／ ').replace(/札を開く/g, '「根拠と条文」で確かめる');
  return 'この用途は、この設備の対象に入っていない（' + (t.条 || []).map(条を読む).join('・') + '）';
}
function 番号を押す(k, 字){
  if(k === '16'){ 複合を始める(); return; }
  var hit = Object.keys(用途の名).filter(function(c){ return 項(c) === k && (!字 || c.charAt(1) === 字); });
  if(hit.length === 1) 用途を決める(hit[0]); else 進む({画面:'番号', 番号: k, 字: 字 || null});
}
function 対象(e){ var g = 今(); if(e === undefined) e = g.設備; if(e){ return 表たち.filter(function(t){ return t.設備 === e; }); } return 表たち; }
function 今(){ return 道[道.length-1] || {}; }
var 履歴あり = true;
function 履歴に積む(){ if(!履歴あり) return; try { history.pushState({n: 道.length}, ''); } catch(e) { 履歴あり = false; } }
function 何段か戻る(k){
  if(k <= 0 || 道.length - k < 1) return;
  if(履歴あり){ try { history.go(-k); return; } catch(e) { 履歴あり = false; } }
  道.length = 道.length - k; 描く(); window.scrollTo(0, 今().y || 0);
}
function 進む(g){ if(道.length) 道[道.length-1].y = window.scrollY; var x = Object.assign({}, 今(), g); 道.push(x); 履歴に積む(); 描く(); window.scrollTo(0,0); }
function 戻る(){ if(道.length > 1) 何段か戻る(1); }
var 待ちの確かめ = null;
function 確かめる(文, 進める文, fn){
  // 確かめの窓の代わりに、画面の上に2つのボタンを出す
  待ちの確かめ = fn;
  var box = document.getElementById('ask'); if(!box){ box = document.createElement('div'); box.id = 'ask'; document.getElementById('app').prepend(box); }
  box.innerHTML = '<div class="also">' + esc(文) + '</div><button class="b go" onclick="var f = 待ちの確かめ; 待ちの確かめ = null; f();">' + esc(進める文) + '</button><button class="b" onclick="this.parentElement.remove()">やめる</button>';
  box.scrollIntoView({block: 'center'});
}
function 最初から(はい){ if(/^練/.test(今().画面) || 今().練習から) はい = true; if(!はい && Object.keys(答).length > 1){ 確かめる('入れた答えを全部消して、最初の画面に戻る？', '消して最初に戻る', function(){ 最初から(true); }); return; } 答 = {}; 自動で入れた = {}; 進む({画面:'大', 大:null, 中:null, 用途:null, 部分:null, 足す:false, 直す:false, 設備:null, 調べ方:null, 練習から:false}); }
window.addEventListener('popstate', function(e){ var n = e.state && e.state.n ? e.state.n : 1; if(n < 道.length){ 道.length = n; } 描く(); window.scrollTo(0, 今().y || 0); });
function 要の名前(ns){
  var out = [];
  ns.forEach(function(n){
    var xs = n.indexOf('max:') === 0 ? n.slice(4).split(',') : n === '平屋以外' ? ['地上', '地下'] : [n];
    xs.forEach(function(x){ if(答[x] !== undefined) return; var t = 名前(x, 答); if(out.indexOf(t) < 0) out.push(t); });
  });
  return out.length ? out : ns.map(function(x){ return 名前(x, 答); });
}
var 特殊の語 = /駐車|道路|通信機器|発電機|変圧器|電気設備|ボイラー|火を多く|ヘリポート|自動車の修理|整備/;
function 効く注記(r){ return r.注記.filter(function(y){ return !(答.特殊部分 === false && 特殊の語.test(y.理由 || '')); }); }
function 見出し(r){
  var st = 見た目(r);
  if(st === '要る' && r.内訳 && r.要る.every(function(y){ return y.どこ !== '建物全体'; })) return '要る（一部の用途）';
  if(st === '要る' && r.要る.every(function(y){ return y.範囲 === '階'; })) return '要る（一部の階）';
  if(st === '要らない' && 効く注記(r).length) return '要らない（条件あり）';
  return st;
}
function 読み替え(t){
  // 面積の基準を構造と内装で読み替える行がこの用途にあるとき、その倍率を1行で
  var has = t.行.some(function(r){ return 用途に当たる(r.用途, 答.用途) && (r.条件 || []).some(function(c){ return c[1] === '>=倍'; }); });
  if(!has) return '';
  var f = 倍率(答);
  if(typeof f !== 'number') return '<div class="also">面積の基準は、造りと内装で2〜3倍に読み替える。造りと内装に答えると決まる</div>';
  if(f === 1) return '<div class="also">造りと内装からは読み替えなし（基準の面積のまま判定）</div>';
  return '<div class="also">造り（' + esc(答.構造) + '）と内装により、面積の基準を' + f + '倍に読み替えて判定した（例: 700㎡なら' + (700 * f) + '㎡）</div>';
}
// 既存の建物の印（判定の状態は変えない）。要る・まだ決まらない・判定できないのときだけ文を出す
function 既存のB(r){ return r.既存 && r.既存.印 === 'B' && 見た目(r) === '要る'; }
function 既存の文(r, st){
  var m = r.既存; if(!m || ['要る','まだ決まらない','判定できない'].indexOf(st) < 0) return '';
  if(m.印 === '見直し中') return '<div class="also">前から建っている建物の扱いは、根拠の条文（消防法17条の2の5・令34条など）が変わったので見直し中</div>';
  var 附 = '基準を変えたときの附則で、期限まで前の基準でよいとしている場合がある。附則はこの早見に入っていない。';
  var co2 = r.設備 === '特殊消火' ? '<br>二酸化炭素を部屋全体に放出する不活性ガス消火設備は、一部の基準（規則19条5項19号イ(ハ)・(ホ)、19条の2）に限り、前から建っている建物にも今の基準を当てはめる（令34条2号・規則33条の2）。' : '';
  if(m.印 === 'A') return '<div class="also">' + (m.理由 === '設備' ? 'この設備は、' : 'この用途は特定防火対象物なので、') + '今の基準ができる前から建っている建物にも、今の基準を当てはめる（' + esc(m.根拠) + '）。' + 附 + co2 + '</div>';
  return '<div class="also">ここに出ているのは今の基準での判定。今の基準ができる前（変わる前）から建っている建物で、設備が今の基準に合わないときは、そのときの基準を当てはめる（消防法17条の2の5第1項）。<br>前の基準でも要る場合がある。この早見は前の基準での判定をしていないので、建った時期と当時の基準を確かめる。' + co2
    + '<details class="sum"><summary>今の基準になる場合</summary>・基準が変わっていなければ、今の基準のまま。<br>・前の基準にも合っていなかった設備（17条の2の5第2項1号）。<br>・基準が変わった後に着工した増築・改築の部分の床面積の合計が1,000㎡以上、または基準が変わった時の延べ面積の2分の1以上になる建物（同2号・令34条の2）。<br>・基準が変わった後に、主要構造部である壁の過半を修繕・模様替えした建物（同2号・令34条の3）。<br>・今の基準に合うようになった設備（同3号）。<br>・用途を変えた建物は別の決まり（17条の3）。変えた後の用途が特定防火対象物でなければ、変える前の用途の基準を当てはめる場合がある。<br>・市町村の火災予防条例の基準にも同じ決まりがある。</details></div>';
}
// 境目までの距離（要らないの設備に、要るに変わる線を出す。判定の状態は変えない）
var 切替の文 = {宿泊:'利用者を入居・宿泊させると要る', 介助主:'介助がなければ避難できない人を主として入所させると要る', 火気:'火を使う設備や器具を設けると要る', 平屋以外:'平屋建でなくなると要る', 鉄網:'下地が準不燃材料でない鉄網入りの壁・床・天井があると要る', 契約50超:'契約電流容量が50アンペアを超えると要る', 高さ31超:'高さが31mを超えると要る', 直通1:'避難階か地上へ直通する階段が1つだけの階（壁で区切られた部分を含む）があると要る', 特定_避難階以外:'特定用途の部分が3階以上か地階に入ると要る', 危険物類:'少量危険物か指定可燃物を貯蔵・取り扱うと要る', 下階特定:'下の階に一項〜四項などの部分が入ると要る', ラック10m超:'天井の高さが10mを超えるラック式倉庫だと要る', 舞台_地階無窓4階:'舞台が地階・無窓階・4階以上の階にあると要る', 地下街_六項イロ:'地下街の中に六項イ(1)(2)・ロの部分があると、その部分に要る', 地下街_自火報の部分:'地下街の中に二項ニ・五項イ・六項イ(1)〜(3)・ロなどの部分があると、その部分に要る', 地下街_直通1:'避難階か地上へ直通する階段が1つだけの階（壁で区切られた部分を含む）があると要る', 地下街_特定の部分:'地下街の中に特定用途の部分が入ると要る', 準地下街_直通1:'避難階か地上へ直通する階段が1つだけの階（壁で区切られた部分を含む）があると要る'};
function 数字(v){ return Number(v).toLocaleString('ja-JP'); }
function 値の名(x){
  if(/^max:/.test(x.名)) return x.名.slice(4).split(',').map(function(k){ return (語の名[k] || k).replace(/の床面積$/, ''); }).join('・') + 'のどれかの階の床面積';
  if(x.名 === '延べ' && x.どこ && x.どこ !== '建物全体') return 'この部分の床面積の合計';
  return 語の名[x.名] || x.名;
}
function 境目の文(x, 形){
  var nm = 値の名(x), u = /^max:/.test(x.名) ? '㎡' : 単位(x.名), 階数 = x.名 === '地上' || x.名 === '地下';
  var 線 = 数字(x.線) + (階数 ? '' : u), 今 = 数字(x.今) + (階数 ? '' : u);
  var あと = 数字(u === '㎡' ? Math.ceil(x.あと * 100) / 100 : Math.ceil(x.あと)) + u;
  var 頭 = x.どこ ? '【' + x.どこ + '】' : '', 階 = x.範囲 === '階' ? '、その階に' : '';
  var 号 = x.号 + (x.倍 && x.倍 > 1 && x.種 !== '場合あり' ? 'の' + 数字(x.元) + u + 'を、造りと内装により' + x.倍 + '倍に読み替え' : '');
  if(x.種 === '切替') return 頭 + 切替の文[x.名] + '（' + x.号 + '）';
  if(形 === '短') return 頭 + nm + ' ' + 線 + '以上で要る（あと' + あと + '）';
  if(x.種 === '超') return 頭 + (x.名 === '床_地階無窓' && x.線 === 0 ? '地階か無窓階があると' : nm + 'が' + 線 + 'を超えると') + (x.範囲 === '階' ? 'その階に' : '') + '要る（' + x.号 + '）';
  if(x.すき間) return '【建物全体】' + nm + 'が' + 線 + '以上になると、管轄で確かめる線を超える（今' + 今 + '・あと' + あと + '。' + x.号 + '）。用途ごとの部分ではどれも超えない。建物全体でも判定するかは条文に書いていない';
  if(x.今 === 0) return 頭 + nm + 'が' + 線 + '以上で' + 階 + '要る（今は0' + (階数 ? '' : u) + '。' + 号 + '）';
  if(x.種 === '場合あり') return 頭 + nm + 'が' + 線 + '以上になると、要る場合がある（今' + 今 + '・あと' + あと + '。' + x.号 + '・2項）。六項ロなどは「700㎡の' + x.倍 + '倍」と「1,000㎡＋省令で定める部分の床面積」の小さい方が線になる';
  return 頭 + nm + 'が' + 線 + '以上で' + 階 + '要る（' + (/^max:/.test(x.名) ? '今いちばん広い階は' : '今') + 今 + '・あと' + あと + '。' + 号 + '）';
}
function 境目の箱(r){
  var b = r.境目; if(!b) return '';
  var 見 = []; if(b.主) 見.push(境目の文(b.主)); b.すき間.forEach(function(x){ 見.push(境目の文(x)); }); b.切替.forEach(function(x){ 見.push(境目の文(x)); });
  var 他 = b.ほか.map(function(x){ return 境目の文(x) + (r.設備 === '非常警報' && x.理由 ? '（' + x.理由 + '）' : ''); })
    .concat(b.未.map(function(x){ return x.号 + '：' + x.名.map(function(n){ return 語の名[n] || n; }).join('・') + 'が分からないので、線を出していない'; }));
  return '<div class="also"><b>要るに変わる線</b><br>' + (見.length ? 見.map(esc).join('<br>') : '近い線は無い（下の「ほかの線」に出している）')
    + '<details class="sum"><summary>ほかの線 ' + 他.length + '件</summary>' + 他.map(esc).join('<br>') + (他.length ? '<br>' : '')
    + '線は、ほかの答えを変えずに、その値だけが増えた場合。増築で階数・無窓階・収容人員が一緒に変わるときは、答えを入れ直して判定する。今の基準での線で、市町村の条例・特例・前から建っている建物の扱いは入っていない。</details></div>';
}
function 見た目(r){
  // 根拠の条文が変わり、まだ人が確かめていない設備は、判定を出さずに「見直し中」
  if(r.変わった && r.変わった.length) return '見直し中';
  return r.状態 === '条件次第' ? 'まだ決まらない' : r.状態;
}
function 用途を決める(code){
  if(今().足す){ 進む({画面:'部分の面積', 足す用途: code, 何番: null}); return; }
  if(/^16[イロ]$/.test(code)){ 複合を始める(); return; }
  答 = {用途: code}; 自動で入れた = {}; 進む({画面:'調べ方', 用途: code, 部分: null, 設備: null, 練習から: false});
}
// 答えたものを、質問の順（建物 → 部分ごと）に並べる
function 答えたid(){
  var ids = []; 質問.forEach(function(q){ if(!q.部分だけ && 答[q.id] !== undefined) ids.push(q.id); });
  (答.部分 || []).forEach(function(p, i){ 質問.forEach(function(q){ var k = 'p' + i + '_' + q.id; if(答[k] !== undefined) ids.push(k); }); });
  return ids;
}
function 語(id){ var m = /^p(\d+)_(.+)$/.exec(id); if(m && 答.部分 && 答.部分[+m[1]]) return '〔' + 短い名(答.部分[+m[1]].用途) + '〕' + (語の名[m[2]] || m[2]); return 語の名[id] || id; }
function 単位(id){ return 語の単位[id.replace(/^p\d+_/, '')] || ''; }
function 結果へ(){ var e = 今().設備; if(e) 進む({画面:'設備', 見る: e, 結果から: true}); else 進む({画面:'結果'}); }
function 次へ(){ var q = 次の質問(対象(), 答); if(q) 進む({画面:'問', 問: q.id}); else 結果へ(); }
function 残り(){
  // 残りの質問に全部「わからない」と答えたときの数＝多くてこれだけ
  var c = Object.assign({}, 答), keep = Object.assign({}, 自動で入れた), n = 0, q;
  while((q = 次の質問(対象(), c)) && n < 40){ c[q.id] = 不明; n++; }
  自動で入れた = keep; return n;
}
function 要約(たたむ){
  var a = [];
  答えたid().forEach(function(id){
    var v = 答[id]; if(自動で入れた[id]) return;
    var nm = 語(id), u = 単位(id);
    var t = v === 不明 ? nm + ': わからない' : v === true ? nm + ': はい' : v === false ? nm + ': いいえ' : nm + ' ' + v + u;
    a.push('<button class="vb'+(v === 不明 ? ' unk' : '')+'" onclick="見直す(\''+id+'\')">'+esc(t)+'</button>');
  });
  if(!a.length) return '';
  if(たたむ) return '<details class="sum"><summary>入れた値 '+a.length+'件（押すと開く・直せる）</summary>'+a.join('')+'</details>';
  return '<div class="sum">入れた値（押すと直せる）: '+a.join('')+'</div>';
}
function 号を開く(btn, 号){
  var nx = btn.nextElementSibling;
  if(nx && nx.classList.contains('inline')){ nx.remove(); return; }
  var t = 号の原文(号), d = document.createElement('div'); d.className = 'inline';
  var m = /号([イロハニホヘトチリヌ])/.exec(号);
  var h = esc(t || '原文の切り出しに失敗。下の札の原文を見る');
  if(t && m) h = h.replace(new RegExp('(　　' + m[1] + '　[^\n]*)'), '<mark>$1</mark>');
  d.innerHTML = '<pre>' + h + '</pre>'; btn.after(d);
}
function 原文へ(el){
  var card = el.closest('.card'), t = el.textContent, hit = null;
  card.querySelectorAll('details.src').forEach(function(d){ var k = d.getAttribute('data-k'); if(!hit && (t.indexOf(k) >= 0 || t.indexOf(k.replace('_','の')) >= 0 || t.indexOf(k.replace(/_\d+/,'')) >= 0)) hit = d; });
  hit = hit || card.querySelector('details.src');
  // その行のすぐ下に原文を開く（もう一度押すと閉じる）。画面は動かさない
  var line = el.parentElement, nx = line.nextElementSibling;
  if(nx && nx.classList.contains('inline')){ nx.remove(); return; }
  if(hit){ var d = document.createElement('div'); d.className = 'inline'; d.innerHTML = '<div class="step">'+esc(hit.querySelector('summary').textContent)+'</div>'; d.appendChild(hit.querySelector('pre').cloneNode(true)); line.after(d); }
}
var 不を開く = false;
function 答える(id, v){
  // 1問だけ差し替える。ほかの答えは残し、階数などから自動で入れた答えだけ入れ直す
  Object.keys(自動で入れた).forEach(function(k){ delete 答[k]; }); 自動で入れた = {};
  答[id] = v;
  自動を入れる();
  // 設備の画面から埋めたときは、その設備の画面へ戻る（履歴を1つ戻すので、もう1回戻ると結果の一覧）
  if(今().戻り) 何段か戻る(1); else 次へ();
}
function 数で答える(id){
  var el = document.getElementById('in_'+id), v = parseFloat(el.value), er = document.getElementById('err');
  function だめ(m){ er.textContent = m; el.focus(); }
  if(el.value === '' || isNaN(v)) return だめ('数字を入れて。分からなければ「わからない」を押す');
  if(v < 0) return だめ('0以上の数字を入れて');
  if((id === '地上' || id === '地下') && v !== Math.floor(v)) return だめ('階数は整数で入れて');
  if(id === '地上' && (v < 1 || v > 100)) return だめ('地上の階数は1〜100で入れて（面積を入れていないか確かめて）');
  if(id === '地下' && v > 10) return だめ('地階の階数は0〜10で入れて（面積を入れていないか確かめて）');
  var pm = /^p(\d+)_(床_|延べ_地上)/.exec(id), pp = pm && 答.部分 ? 答.部分[+pm[1]] : null;
  if(pp && v > pp.延べ){ 確かめる('この値（'+v+'㎡）が、この用途の部分の床面積の合計（'+pp.延べ+'㎡）より大きい。打ち間違いでなければ進める', 'このまま進める', function(){ 答える(id, v); }); return; }
  if(id === '延べ' && 答.部分){ var sm = 答.部分.reduce(function(s, p){ return s + p.延べ; }, 0); if(v < sm){ 確かめる('延べ面積（'+v+'㎡）が、用途の部分の合計（'+sm+'㎡）より小さい。打ち間違いでなければ進める', 'このまま進める', function(){ 答える(id, v); }); return; } }
  if(/^床_/.test(id) && typeof 答.延べ === 'number' && v > 答.延べ){ 確かめる('この階の床面積（'+v+'㎡）が延べ面積（'+答.延べ+'㎡）より大きい。打ち間違いでなければ進める', 'このまま進める', function(){ 答える(id, v); }); return; }
  if(/^収容_/.test(id) && typeof 答.収容 === 'number' && v > 答.収容){ 確かめる('この人数（'+v+'人）が建物全体の収容人員（'+答.収容+'人）より多い。打ち間違いでなければ進める', 'このまま進める', function(){ 答える(id, v); }); return; }
  答える(id, v);
}
function 消す_から(id){
  // その質問から後の答えを消す（後の質問は前の答えで変わるため）
  var drop = false;
  質問.forEach(function(q){ if(q.id === id) drop = true; if(drop){ delete 答[q.id]; delete 自動で入れた[q.id]; } });
}
function 自動を入れる(){ 自動で埋める(答); }
function 一覧へ(){ var i = -1; 道.forEach(function(x, j){ if(x.画面 === '結果') i = j; }); if(i >= 0) 何段か戻る(道.length - 1 - i); }
function 見直す(id){ var g = 今(); 進む({画面:'問', 問: id, 戻り: g.画面 === '設備' ? g.見る : null}); }
function ボタン(文, 押す, cls){ return '<button class="nb '+(cls||'')+'" onclick="'+押す+'">'+文+'</button>'; }
function 札を出す(id){
  document.querySelectorAll('#cards .inline').forEach(function(x){ x.remove(); });
  document.querySelectorAll('#cards .card').forEach(function(c){ c.classList.toggle('show', c.id === id); });
}
function 探す(){
  var raw = document.getElementById('q2').value; 今().語 = raw;
  var w = [];
  raw.trim().split(/\s+/).filter(Boolean).forEach(function(x){ x = (言い換え[x] || x).replace(/等/g, ''); x.split(/[のをとや、]/).forEach(function(y){ if(y.length >= 1) w.push(y); }); });
  var h = '', n = 0, 先 = [], 後 = [];
  if(w.length){
    // 用途の名前に当たれば、その用途の「何を調べる？」へ進める
    Object.keys(用途の名).forEach(function(c){ var t = 用途の名[c] + (/共同生活援助/.test(用途の名[c]) ? ' 障害者グループホーム' : ''); if(w.some(function(x){ return t.indexOf(x) >= 0; })){ n++; var nn = 番号と名(c); h += '<button class="rb" onclick="用途を決める(\''+c+'\')"><span class="kj">用途を選ぶ</span><b>'+nn[1]+'</b> <span class="kj">'+nn[0]+'</span></button>'; } });
    document.querySelectorAll('#cards .card').forEach(function(c){ var t = c.getAttribute('data-s').replace(/等/g, ''), tt = c.querySelector('h3').textContent.replace(/等/g, ''); if(w.every(function(x){ return t.indexOf(x) >= 0; })){ n++; var b = '<button class="rb" onclick="進む({画面:\'札\', 札:\''+c.id+'\'})"><b>'+esc(tt)+' ›</b><span class="kj">'+esc(c.querySelector('.quick').textContent)+'</span></button>'; var pos = Math.min.apply(null, w.map(function(x){ var i = tt.indexOf(x); return i < 0 ? 999 : i; })); (pos < 999 ? 先 : 後).push([pos, b]); } });
  }
  先.sort(function(x, y){ return x[0] - y[0]; });
  h += 先.concat(後).map(function(x){ return x[1]; }).join('');
  document.getElementById('hits').innerHTML = w.length ? '<div class="step">当たった '+n+'件</div>' + (n ? h : '<div class="note">当たらない。言葉を短くするか（例: 防火管理）、最初の画面で用途を選ぶ</div>') : '';
}
function 描く(){
  var g = 今(), h = '<div class="top">';
  h += (道.length > 1 ? '<button class="sm" onclick="戻る()">← 戻る</button>' : '<span></span>');
  h += (g.画面 !== '大' ? '<button class="sm" onclick="最初から()">最初から</button>' : '') + '</div>';
  札を出す(null);
  document.body.classList.toggle('deep', 道.length > 1);
  if(g.用途 && g.画面 !== '大' && g.画面 !== '中' && g.画面 !== '番号'){ var nn = 番号と名(g.用途); h += '<div class="where">'+nn[0]+' '+nn[1]+(答.部分 && 答.用途 === g.用途 ? '（' + esc(答.部分.map(function(p){ return 短い名(p.用途); }).join('・')) + '）' : '')+(g.設備 && g.画面 !== '設備を選ぶ' ? ' ／ '+esc(g.設備)+'だけ' : '')+'</div>'; }
  if(g.画面 === '大'){
    if(g.足す) h += '<div class="qt">足す用途は？</div>';
    else h += ボタン('言葉で探す（例: カラオケ・保育園・防火管理者）', "進む({画面:'探す'})", 'lite') + '<div class="qt">建物の用途は？</div>';
    大分類.forEach(function(x, i){ if(g.足す && x[1] && !x[1].some(足せる)) return; h += ボタン(esc(x[0]), "進む({画面:'中', 大:"+i+", 中:null})"); });
    h += '<div class="sub">' + ボタン('項の番号で選ぶ', "進む({画面:'番号', 番号:null})", 'lite') + '</div>';
    if(練習あり && !g.足す) h += '<div class="sub">' + ボタン('練習問題（建物の例で、要る設備を答える）', "進む({画面:'練入口', 用途:null, 部分:null, 設備:null, 見る:null, 練習から:false})", 'lite') + '</div>';
  } else if(g.画面 === '中'){
    var 組 = 大分類[g.大];
    if(組[1] === null && g.中 === null){
      h += '<div class="qt">'+esc(組[0])+'の、どれ？</div>';
      福祉.forEach(function(x, i){ h += ボタン(esc(x[0]), "進む({画面:'中', 中:"+i+"})"); });
    } else {
      var codes = (組[1] || 福祉[g.中][1]).filter(function(c){ return !g.足す || 足せる(c); });
      h += '<div class="qt">'+esc(組[1] ? 組[0] : 福祉[g.中][0])+'の、どれ？</div>';
      if(codes[0] === '6イ1') h += '<div class="hint">特定診療科＝内科・整形外科・リハビリテーション科など（総務省令で定める科）。(1)はその科があり療養病床か一般病床を持つ病院、(2)はその科があり4人以上入院できる診療所、(3)はそれ以外の病院と入院できる診療所（別表第一(6)イ）</div>';
      codes.forEach(function(c){ if(c === '複合'){ h += ボタン('<span class="num">(16)</span>複合ビル（用途が2つ以上）', "複合を始める()", 'use'); return; } var nn = 番号と名(c); h += ボタン(nn[0]+nn[1], "用途を決める('"+c+"')", 'use'); });
    }
  } else if(g.画面 === '番号'){
    var all = Object.keys(用途の名).filter(function(c){ return !g.足す || 足せる(c); });
    if(!g.番号){
      h += '<div class="qt">項の番号は？</div><div class="grid">';
      all.map(項).filter(function(v,i,a){ return a.indexOf(v) === i; }).sort(function(x, y){ return parseFloat(x) - parseFloat(y) || x.length - y.length || (x < y ? -1 : 1); }).forEach(function(k){ h += '<button class="nb sq" onclick="番号を押す(\''+k+'\')">('+esc(k)+')</button>'; });
      h += '</div>';
    } else {
      var hit = all.filter(function(c){ return 項(c) === g.番号; });
      if(hit.length === 1){ 用途を決める(hit[0]); return; }
      if(g.番号 === '6' && !g.字){
        h += '<div class="qt">(6)の、どれ？</div>';
        [['イ','病院・診療所'],['ロ','入所の福祉施設'],['ハ','通所などの福祉施設・保育所'],['ニ','幼稚園・特別支援学校']].forEach(function(x){ h += ボタン('<span class="num">(6)'+x[0]+'</span>'+x[1], "番号を押す('6','"+x[0]+"')"); });
      } else {
        if(g.番号 === '6') hit = hit.filter(function(c){ return c.charAt(1) === g.字; });
        if(hit.length === 1){ 用途を決める(hit[0]); return; }
        h += '<div class="qt">('+esc(g.番号)+(g.番号 === '6' ? g.字 : '')+')の、どれ？</div>';
        hit.forEach(function(c){ var nn = 番号と名(c); h += ボタン(nn[0]+nn[1], "用途を決める('"+c+"')", 'use'); });
      }
    }
  } else if(g.画面 === '複合'){
    var 種 = 下書き.length;
    h += '<div class="qt">このビルに入っている用途と、その床面積は？</div><div class="note">用途ごとに、その用途に使う部分の床面積の合計を入れる（同じ用途は1つにまとまる）</div>';
    下書き.forEach(function(p, i){ h += '<div class="ans"><span onclick="部分を直す('+i+')">'+esc(部分の札([p])[0])+' <span class="fix">直す</span></span> <button class="sm" onclick="部分を消す('+i+')">✕ 消す</button></div>'; });
    if(種 < 6) h += ボタン('用途を足す', "進む({画面:'大', 足す:true, 大:null, 中:null, 番号:null})", 種 ? 'lite' : '');
    else h += '<div class="note">用途は6つまで</div>';
    if(種 >= 2) h += ボタン('これで決める', '複合を決める()', 'go') + '<div class="note">'+esc(用途の名[複合の用途(下書き)])+' になる（'+esc(複合の理由(複合の用途(下書き)))+'）</div>';
    else if(種 === 1) h += '<div class="note">用途が2つ以上で決められる。用途が1つだけなら、最初の画面でその用途を選ぶ</div>';
    h += '<div class="also">令8条の区画（開口部の無い耐火構造の床・壁）で分かれている部分は、別々の建物として調べる。<br>主な用途に従う部分・共用部分・住宅の部分の割り振りは国の通知にあり、この画面では判定しない。<br>分け方が分からなければ管轄の消防署で確かめる。</div>';
  } else if(g.画面 === '部分の面積'){
    var 前2 = g.何番 !== null && g.何番 !== undefined ? 下書き[g.何番].延べ : '';
    h += '<div class="q"><div class="qt">'+esc(短い名(g.足す用途))+'の部分の床面積の合計は何㎡？</div><div class="hint">この用途に使う部分を全部の階で足した面積</div><div id="err" class="err"></div>'
      + '<input id="in_part" type="number" inputmode="decimal" min="0" value="'+前2+'" onkeydown="if(event.key===\'Enter\')部分を入れる()"><button class="b go" onclick="部分を入れる()">決める</button></div>';
  } else if(g.画面 === '探す'){
    h += '<div class="qt">言葉で探す</div><input id="q2" type="search" placeholder="例: デイサービス スプリンクラー" oninput="探す()"><div id="hits"></div>';
  } else if(g.画面 === '調べ方'){
    if(g.部分) h += '<div class="also">'+esc(用途の名[g.用途])+' と判定（'+esc(g.用途 === '16ロ' ? '特定用途の部分が無いため' : 短い名(g.部分.filter(function(x){ return 用途に当たる(特定の用途, x.用途); })[0].用途) + 'があるため')+'）。用途ごとの部分を1つの建物とみなして判定する（令9条）</div>';
    h += '<div class="qt">何を調べる？</div>';
    h += ボタン('全部の設備を調べる（質問に答える）', "始める(null)");
    h += ボタン('1つの設備だけ調べる', "進む({画面:'設備を選ぶ'})");
    h += ボタン('質問に答えず、基準だけ見る', "進む({画面:'基準'})", 'lite');
  } else if(g.画面 === '設備を選ぶ'){
    h += '<div class="qt">どの設備？</div><div class="grid2">';
    設備の順.forEach(function(e){ h += '<button class="nb sq2" onclick="始める(\''+e+'\','+(g.続き?'true':'false')+')">'+esc(e)+(g.続き && 調べた.indexOf(e) >= 0 ? '<span class="kj">調べた</span>' : '')+'</button>'; });
    h += '</div>';
  } else if(g.画面 === '問'){
    var q = 質問を引く(g.問, 答);
    var 前 = 答[q.id];
    if(q.id === '延べ' && 前 === undefined && 答.部分) 前 = 答.部分.reduce(function(s, p){ return s + p.延べ; }, 0);
    var n = Object.keys(答).filter(function(k){ return k !== '用途' && k !== '部分' && !自動で入れた[k]; }).length;
    var 後 = 残り();
    h += 要約() + '<div class="step">答えた '+n+'問 ／ あと多くて '+後+'問（答えで変わる）</div><div class="q"><div class="qt">'+esc(q.文)+'</div>'
      + (q.補足 ? '<div class="hint">'+esc(q.補足)+'</div>' : '')
      + (q.文.indexOf('無窓階') >= 0 ? '<div class="hint">無窓階＝地上の階のうち、避難や消火活動に有効な開口部（窓など）が足りない階（令10条1項5号）</div>' : '')
      + '<div id="err" class="err"></div>';
    if(q.型 === '数'){
      h += '<input id="in_'+q.id+'" type="number" inputmode="decimal" min="0"'+(typeof 前 === 'number' ? ' value="'+前+'"' : '')+' onkeydown="if(event.key===\'Enter\')数で答える(\''+q.id+'\')">'
        + '<button class="b go" onclick="数で答える(\''+q.id+'\')">決める</button>';
    } else if(q.型 === 'はい'){
      h += '<button class="b'+(前===true?' was':'')+'" onclick="答える(\''+q.id+'\',true)">はい</button><button class="b'+(前===false?' was':'')+'" onclick="答える(\''+q.id+'\',false)">いいえ</button>';
    } else {
      q.選択.forEach(function(s){ h += '<button class="b'+(前===s?' was':'')+'" onclick="答える(\''+q.id+'\',\''+s+'\')">'+esc(s)+'</button>'; });
    }
    h += '<button class="b dk'+(前===不明?' was':'')+'" onclick="答える(\''+q.id+'\',不明)">わからない</button></div>';
    h += '<button class="sm" onclick="結果へ()">ここまでで結果を見る</button>';
  } else if(g.画面 === '結果'){
    var res = 全部を判定(対象(), 答), 要 = [], 確 = [], 不 = [];
    var 条 = [];
    res.forEach(function(r){ var st = 見た目(r); (st === '要る' ? 要 : st === '要らない' ? (効く注記(r).length ? 条 : 不) : 確).push(r); });
    var 名札 = function(r){ var st = 見た目(r), lab = 見出し(r);
      return '<button class="rb '+色[st]+'" onclick="進む({画面:\'設備\', 見る:\''+r.設備+'\', 結果から: true})"><b>'+esc(r.設備)+'</b>'+(r.変わった.length ? ' <span class="red">条文が変わった</span>' : '')+(既存のB(r) ? '<span class="kz">既存の建物は前の基準の場合あり</span>' : '')+'<span class="st">'+lab+' ›</span></button>'; };
    if(答.部分) h += '<div class="also">複合ビルは、用途ごとの部分を1つの建物とみなして判定する（令9条）。令9条のかっこ書きの号だけ、建物全体で判定している</div><div class="sum">入っている用途（押すと直せる）: <button class="vb" onclick="複合を始める(true)">'+esc(部分の札(答.部分).join('・'))+'</button></div>'
      + (答.用途 === '16イ' && 答.地下 >= 1 ? '<div class="note">地下街と一体を成すと消防長・消防署長が指定した地階は、一部の規定で地下街の部分とみなす（令9条の2）</div>' : '');
    h += 要約(true) + '<div class="qt">要る設備 '+要.length+'件</div>' + (要.some(既存のB) ? '<div class="note">「前の基準の場合あり」と付いた設備は、今の基準ができる前（変わる前）から建っている建物では、そのときの基準を当てはめる場合がある。押すと出る。</div>' : '') + (要.length ? 要.map(名札).join('') : '<div class="note">なし</div>');
    if(確.length) h += '<div class="qt">自分で確かめるもの '+確.length+'件</div>' + 確.map(名札).join('');
    if(条.length) h += '<div class="qt">条件しだいで要る '+条.length+'件</div><div class="note">質問で聞いていない条件（危険物の量など）があれば要る。押すと条件が出る</div>' + 条.map(名札).join('');
    var 近 = 不.filter(function(r){ return r.境目 && r.境目.近い; }); 不 = 不.filter(function(r){ return 近.indexOf(r) < 0; });
    if(近.length) h += '<div class="qt">要らないが、線が近い設備 '+近.length+'件</div>' + 近.map(function(r){ return 名札(r) + '<div class="note">'+esc(境目の文(r.境目.主, '短'))+'</div>'; }).join('');
    if(不.length) h += '<details class="no"'+(不を開く?' open':'')+' ontoggle="不を開く=this.open"><summary>'+(近.length ? 'ほかの要らない ' : '要らない ')+不.length+'件（押すと名前が開く）</summary>'+不.map(名札).join('')+'</details>';
    h += '<div class="sub">' + ボタン('答えを見直す', "進む({画面:'見直す'})", 'lite') + ボタン('設備以外の決まり', "進む({画面:'決まり'})", 'lite') + ボタン('結果を写す（コピー）', '写す()', 'lite') + '</div>';
    if(公開版.公開 && 公開版.知らせ先) h += '<a class="nb lite" href="'+esc(公開版.知らせ先)+'" target="_blank" rel="noopener">誤りを知らせる（名前・連絡先・建物の名前や住所は書かない。個別の相談には答えない）</a>';
    h += '<div class="foot">これは条文の案内で、個別の建物の判断ではない。市町村の火災予防条例・消防長等の特例・施行前の改正は入っていない。前から建っている建物の扱いは印と注意書きだけで、前の基準での判定は入っていない。最終の判断は管轄の消防署へ。<br>' + esc(document.querySelector('.meta').textContent) + '</div>';
  } else if(g.画面 === '見直す'){
    h += '<div class="qt">答えを見直す</div><div class="note">押した質問だけ答え直す。ほかの答えは残る</div>';
    if(答.部分) h += '<div class="ans" onclick="複合を始める(true)">入っている用途と床面積 <b>'+esc(部分の札(答.部分).join('・'))+'</b> <span class="fix">直す</span></div>';
    答えたid().forEach(function(id){
      var x = 質問を引く(id, 答);
      if(自動で入れた[id]){ h += '<div class="ans auto">'+esc(x.文)+' <b>'+esc(見せる値(答[id]))+'</b> <span class="fix">'+(答.部分 ? '自動' : '階数から自動')+'</span></div>'; return; }
      h += '<div class="ans" onclick="見直す(\''+id+'\')">'+esc(x.文)+' <b>'+esc(見せる値(答[id]))+'</b> <span class="fix">直す</span></div>';
    });
  } else if(g.画面 === '決まり'){
    h += '<div class="qt">設備以外の決まり</div>';
    var 並び = 決まり.slice().sort(function(x, y){ var a = /介護施設/.test(x[1]) && !/^6[ロハ]/.test(g.用途 || ''), b = /介護施設/.test(y[1]) && !/^6[ロハ]/.test(g.用途 || ''); return a - b; });
    並び.forEach(function(x){ h += '<button class="rb" onclick="進む({画面:\'札\', 札:\''+x[0]+'\'})"><b>'+esc(x[1])+'</b><span class="kj">'+esc(x[2])+'</span></button>'; });
  } else if(g.画面 === '基準'){
    h += '<div class="qt">この用途の基準（19設備）</div>';
    if(/^16[イロ]$/.test(g.用途)) h += '<div class="note">ここに出るのは建物全体で判定する号だけ。ほかは用途ごとの部分で判定する（令9条）</div>';
    設備の順.forEach(function(e){ var kj = (基準[g.用途] || {})[e]; h += '<button class="rb" onclick="進む({画面:\'札\', 札:\''+(kj ? kj[1] : 表たち.filter(function(x){ return x.設備 === e; })[0].札)+'\', 見る:\''+e+'\', 結果から: false})"><b>'+esc(e)+'</b><span class="kj">'+(kj && !kj[3] ? esc(kj[0]) + ほか(e, g.用途) : esc(表から基準(e, g.用途)))+'</span><span class="st">›</span></button>'; });
    h += ボタン('この用途で質問に答える', "始める(null)");
  } else if(g.画面 === '設備'){
    var e = g.見る, t = 表たち.filter(function(x){ return x.設備 === e; })[0], kj = (基準[g.用途] || {})[e];
    var 結果つき = !!g.結果から;
    h += '<div class="qt">'+esc(e)+'</div>';
    if(結果つき) h += 要約(true);
    if(結果つき){
      var r = 全部を判定([t], 答)[0], st = 見た目(r), why = '';
      if(st === '要る') why = r.要る.map(function(y){ return (y.どこ ? '【'+esc(y.どこ)+'】' : '')+esc(y.号)+(y.理由?'（'+esc(y.理由)+'）':'')+(y.範囲==='階'?'（その階に設置）':y.範囲==='舞台部'?'（舞台部に設置）':y.範囲==='その部分'?'（その部分に設置）':'')+(y.線&&y.線.length?'<br>'+esc(y.線.join('・')):''); }).join('<br>');
      if(st === 'まだ決まらない'){
        var ws = [], ids = [];
        r.待ち.forEach(function(w){
          w.説明.forEach(function(v){ if(ws.indexOf(v) < 0) ws.push(v); });
          w.要.forEach(function(n){ (n.indexOf('max:') === 0 ? n.slice(4).split(',') : n === '平屋以外' ? ['地上','地下'] : [n]).forEach(function(x){ var v = 答[x]; if((v === undefined || v === 不明) && ids.indexOf(x) < 0 && 名前(x, 答) !== x) ids.push(x); }); });
        });
        why = 'これが分かれば決まる（押すと答えられる）:' + ids.map(function(x){ return '<button class="nb lite" onclick="見直す(\''+x+'\')">'+esc(名前(x, 答))+(答[x] === 不明 ? '<span class="kj">「わからない」と答えた</span>' : '')+'</button>'; }).join('') + (ws.length ? '<div class="note">'+esc(ws.join(' ／ '))+'</div>' : '');
      }
      if(st === '判定できない') why = r.できない.map(function(y){ return (y.どこ ? '【'+esc(y.どこ)+'】' : '')+esc(y.号)+'：'+esc(y.理由); }).join('<br>');
      if(r.内訳){
        var 無 = r.内訳.filter(function(x){ return x.状態 === '要らない'; }).map(function(x){ return x.どこ; });
        why += '<div class="note">建物全体で判定する号（令9条のかっこ書き）と、用途ごとの部分の判定を合わせた結果'+(無.length ? '。当たらなかったところ: '+esc(無.join('・')) : '')+'</div>';
      }
      if(st === '要らない') why = (r.内訳 ? '建物全体でも、用途ごとの部分（' + esc(答.部分.map(function(p){ return 短い名(p.用途); }).join('・')) + '）でも、設置が要る条件のどれにも当たらない' : 'この用途と入れた値では、設置が要る条件のどれにも当たらない') + 境目の箱(r);
      if(st === '見直し中') why = '根拠の条文（' + esc(r.変わった.map(条を読む).join('・')) + '）が改正などで変わった。人が新しい条文を確かめ終わるまで、この設備の判定は出さない。下の「根拠と条文を見る」で新しい条文は読める';
      h += '<div class="rr '+色[st]+'"><div class="rh"><span class="st">'+st+'</span></div>'
        + (r.変わった.length ? '<div class="band red">条文が変わった・要再確認（'+esc(r.変わった.join('・'))+'）</div>' : '')
        + '<div class="why">'+why+'</div>'
        + (st === '要る' && r.候補.length ? '<div class="cand">付けなくてよくなる場合: '+r.候補.map(esc).join(' ／ ')+'</div>' : '')
        + 既存の文(r, st)
        + (function(){ var ns = 効く注記(r); if(!ns.length) return ''; var tx = ns.map(function(y){ return esc(y.理由); }).join(' ／ ');
            return st === '要る' ? '<details class="sum"><summary>ほかに確かめること '+ns.length+'件</summary>'+tx+'</details>' : '<div class="also">こうなら要る・あわせて確かめること: '+tx+'</div>'; })() + '</div>';
    }
    h += '<div class="kj'+(kj && kj[2] ? ' warn' : '')+'">基準: '+(kj && !kj[3] ? esc(kj[0]) : esc(表から基準(e, g.用途)))+'</div>';
    if(結果つき) h += 読み替え(t);
    h += '<div class="jou">根拠 '+esc((t.条 || []).map(条を読む).join('・'))+'</div>';
    h += ボタン('根拠と条文を見る', "進む({画面:'札', 札:'"+(kj ? kj[1] : t.札)+"'})");
    if(結果つき && !g.設備 && 道.some(function(x){ return x.画面 === '結果'; })) h += ボタン('結果の一覧へ戻る', '一覧へ()', 'lite');
    if(結果つき && g.設備 && 調べた.length > 1) h += '<div class="sum">この建物で調べた設備: ' + 調べた.map(function(x){ var rr = 全部を判定(表たち.filter(function(t2){ return t2.設備 === x; }), 答)[0]; return '<button class="vb" onclick="進む({画面:\'設備\', 見る:\''+x+'\', 設備:\''+x+'\', 結果から: true})">'+esc(x)+' '+esc(見出し(rr))+'</button>'; }).join('') + '</div>';
    if(結果つき && g.設備) h += ボタン('同じ建物で別の設備を調べる', "進む({画面:'設備を選ぶ', 続き: true})", 'lite') + ボタン('結果を写す（コピー）', '写す()', 'lite') + ボタン('答えを見直す', "進む({画面:'見直す'})", 'lite');
  } else if(g.画面 === '札'){
    札を出す(g.札);
    var te = g.見る && 表たち.filter(function(x){ return x.設備 === g.見る; })[0];
    if(te && g.用途){
      var 当 = {}; if(g.結果から){ 全部を判定([te], 答)[0].要る.forEach(function(y){ 当[y.号] = true; }); }
      var rows = te.行.filter(function(r){ return 用途に当たる(r.用途, g.用途) && r.結果 !== '注記'; });
      h += '<div class="qt">'+esc(用途の名[g.用途].split(' ').slice(1).join(' '))+'に当たる号（押すと原文）</div>';
      if(!rows.length) h += '<div class="note">この用途に当たる号はない。下のまとめの「必要になる条件」は、ほかの用途の分</div>';
      rows.forEach(function(r){ var s2 = (r.条件 || []).map(条件の文).join('かつ');
        h += '<button class="rb'+(当[r.号] ? ' need' : '')+'" onclick="号を開く(this, \''+esc(r.号)+'\')"><b>'+esc(r.号)+(当[r.号] ? '（この建物で当たった）' : '')+' ›</b><span class="kj">'+esc(s2 ? s2 + (r.結果 === '判定できない' ? 'なら個別に判断' : 'で要る') : (r.理由 || ''))+'</span></button>'; });
      h += '<div class="step">下はこの設備の札（まとめ）</div>';
    }
  }
  if(/^練/.test(g.画面)) h += 練習の画面(g);
  if(g.練習から && g.画面 === '設備') h = h.replace('<div class="top">', '<div class="also">練習問題の建物を開いている ' + ボタン('練習問題に戻る', '練習に戻る()', 'lite') + '</div><div class="top">');
  document.getElementById('app').innerHTML = h;
  var s2 = document.getElementById('q2'); if(s2){ if(g.語){ s2.value = g.語; 探す(); } else s2.focus(); }
}
function 写す(){
  var g = 今();
  var lines = ['消防用設備のチェック（' + new Date().toLocaleDateString('ja-JP') + '）', '用途: ' + 用途の名[g.用途] + (g.設備 ? '（調べた設備: ' + 調べた.join('・') + '）' : '')];
  if(答.部分) lines.push('入っている用途: ' + 部分の札(答.部分).join('・'));
  答えたid().forEach(function(id){ if(!自動で入れた[id]) lines.push(質問を引く(id, 答).文 + ' ' + 見せる値(答[id])); });
  var 既存あり = false;
  var 順 = {"要る":0,"まだ決まらない":1,"判定できない":1,"見直し中":1,"要らない":2};
  var 写す表 = g.設備 && 調べた.length ? 表たち.filter(function(t){ return 調べた.indexOf(t.設備) >= 0; }) : 対象();
  全部を判定(写す表, 答).sort(function(x, y){ return 順[見た目(x)] - 順[見た目(y)]; }).forEach(function(r){
    lines.push('■' + r.設備 + ': ' + 見出し(r) + (r.要る.length ? '（' + r.要る.map(function(x){ return (x.どこ ? x.どこ + ' ' : '') + x.号; }).join('・') + '）' : '') + (見た目(r) === '要らない' && 効く注記(r).length ? ' ※' + 効く注記(r).map(function(y){ return y.理由; }).join('／') : '') + (既存のB(r) ? ' ※既存の建物は従前の基準の場合あり（法17条の2の5）' : '') + (見た目(r) === '要らない' && r.境目 && r.境目.近い ? ' ※' + 境目の文(r.境目.主) : ''));
    if(既存のB(r)) 既存あり = true;
  });
  if(既存あり) lines.push('判定は今の基準。従前の基準での判定はしていない。');
  lines.push('最終判断は条文の原文と所轄の運用。' + document.querySelector('.meta').textContent);
  var t = lines.join('\n');
  function 見せる(msg){
    var box = document.getElementById('copied'); if(!box){ box = document.createElement('div'); box.id = 'copied'; document.getElementById('app').appendChild(box); }
    box.innerHTML = '<div class="also">' + esc(msg) + '</div><textarea readonly rows="8">' + esc(t) + '</textarea>';
    box.scrollIntoView({block: 'start', behavior: 'smooth'});
  }
  function 古い方法(){
    var ta = document.createElement('textarea'); ta.value = t; document.body.appendChild(ta); ta.select();
    var ok = false; try { ok = document.execCommand('copy'); } catch(e) { ok = false; }
    document.body.removeChild(ta);
    見せる(ok ? 'コピーした。下が写した文' : 'コピーできなかった。下の文を長押しして選んで写す');
  }
  見せる('写した文（コピーできたかは、すぐ上に出る）');
  if(navigator.clipboard && window.isSecureContext){ navigator.clipboard.writeText(t).then(function(){ 見せる('コピーした。下が写した文'); }, 古い方法); }
  else 古い方法();
}
function 古さを見る(){
  if(!公開版.公開 || !window.fetch) return;
  fetch('確かめた日.txt', {cache: 'no-store'}).then(function(r){ return r.ok ? r.text() : ''; }).then(function(t){
    var m = /(\d{4})-(\d{2})-(\d{2})/.exec(t || ''); if(!m) return;
    var days = Math.floor((Date.now() - new Date(+m[1], +m[2] - 1, +m[3]).getTime()) / 86400000);
    if(days > 公開版.日数){ var b = document.createElement('div'); b.className = 'band stale'; b.textContent = '条文を最後に確かめた日（' + m[0] + '）から' + days + '日たっている。改正が入っていないか、e-Gov の原文で確かめて'; document.body.insertBefore(b, document.body.firstChild); }
  }).catch(function(){});
}
古さを見る();
道 = [{画面: '大'}]; try { history.replaceState({n: 1}, ''); } catch(e) { 履歴あり = false; } 描く();
"""

if __name__ == "__main__":
    main()
