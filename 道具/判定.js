// 判定の表を引いて、設備ごとに 要る／要らない／条件次第／判定できない を出す。AIは使わない。
// 画面（早見.html に埋め込み）と試験（node 試験_判定.js）の両方で同じものを使う。

var 質問 = [
  { id: "宿泊", 文: "利用者を入居・宿泊させる？", 型: "はい", 出す: function (a) { return /^6[ハ]/.test(a.用途); } },
  { id: "介助主", 文: "介助がなければ避難できない人を主として入所させる？", 型: "はい", 出す: function (a) { return /^6ロ[245]$/.test(a.用途); } },
  { id: "火気", 文: "火を使う設備や器具がある？（防火上有効な措置をしたものは除く）", 型: "はい", 出す: function (a) { return /^3/.test(a.用途); } },
  { id: "延べ", 文: "延べ面積は何㎡？", 型: "数" },
  { id: "地上", 文: "地上の階数は？（地階を除く）", 型: "数" },
  { id: "地下", 文: "地階の階数は？（無ければ0）", 型: "数" },
  { id: "床_地階無窓", 文: "地階か無窓階のうち、一番広い階の床面積は何㎡？（どちらも無ければ0）", 型: "数" },
  { id: "床_3階", 文: "3階の床面積は何㎡？", 型: "数", 自動: function (a) { return a.地上 !== undefined && a.地上 !== null && a.地上 < 3 ? 0 : undefined; } },
  { id: "床_4以上", 文: "4階〜10階のうち、一番広い階の床面積は何㎡？（4階以上が無ければ0）", 型: "数", 自動: function (a) { return a.地上 !== undefined && a.地上 !== null && a.地上 < 4 ? 0 : undefined; } },
  { id: "構造", 文: "建物の造りは？", 型: "選ぶ", 選択: ["耐火", "準耐火", "その他"] },
  { id: "内装", 文: "壁と天井の内装は難燃材料（またはそれ以上）？", 型: "はい" },
  { id: "収容", 文: "建物全体の収容人員は何人？", 型: "数" },
  { id: "収容_地階無窓", 文: "地階と無窓階の収容人員は合わせて何人？", 型: "数", 自動: function (a) { return a.床_地階無窓 === 0 ? 0 : undefined; } },
  { id: "収容_階最大", 文: "2階以上の階か地階のうち、収容人員が一番多い階は何人？（避難階と11階以上は除く）", 型: "数", 自動: function (a) { return a.地上 === 1 && a.地下 === 0 ? 0 : undefined; } },
  { id: "直通1", 文: "避難階以外の階から、避難階か地上へ直通する階段が1つしかない？", 型: "はい", 自動: function (a) { return a.地上 === 1 && a.地下 === 0 ? false : undefined; } },
  // 第2段（残り11設備）で足した質問
  { id: "床_1と2階", 文: "1階と2階の床面積の合計は何㎡？（平屋なら1階だけ）", 型: "数", 自動: function (a) { return (a.地上 === 1 || a.地上 === 2) && a.地下 === 0 && typeof a.延べ === "number" ? a.延べ : undefined; } },
  { id: "床_地階合計", 文: "地階の床面積の合計は何㎡？", 型: "数", 自動: function (a) { return a.地下 === 0 ? 0 : undefined; } },
  { id: "延べ_地上", 文: "地階を除いた延べ面積は何㎡？", 型: "数", 自動: function (a) { return a.地下 === 0 && typeof a.延べ === "number" ? a.延べ : undefined; } },
  { id: "敷地", 文: "敷地の面積は何㎡？", 型: "数" },
  { id: "高さ31超", 文: "建物の高さは31mを超える？", 型: "はい" },
  { id: "鉄網", 文: "壁・床・天井に、下地（間柱・根太・野縁など）が準不燃材料でない鉄網入り（ラスモルタルなど）のものがある？", 型: "はい" },
  { id: "契約50超", 文: "電気の契約電流容量（契約が複数なら一番大きいもの）は50アンペアを超える？", 型: "はい" },
  { id: "特殊部分", 文: "次のどれかの部分がある？ 駐車場・自動車の修理や整備の場所・発電機や変圧器の部屋・ボイラー室など火を多く使う部屋・通信機器室・屋上のヘリポート・車が通る道路の部分", 型: "はい" }
];

var 不明 = "わからない";
var 自動で入れた = {}; // 階数などから機械が入れた答え（画面で「自動」と出す）

function 用途に当たる(tokens, code) {
  for (var i = 0; i < tokens.length; i++) {
    var t = tokens[i];
    if (t === "*") return true;
    if (t.slice(-1) === "*") {
      var p = t.slice(0, -1);
      if (code.indexOf(p) === 0) {
        var nx = code.charAt(p.length);
        if (!/^[0-9]+$/.test(p) || (!/[0-9]/.test(nx) && nx !== "の")) return true;
      }
    } else if (t === code) return true;
  }
  return false;
}

function 値(a, name) {
  // 答えと、答えから出せる値
  if (name.indexOf("max:") === 0) {
    var xs = name.slice(4).split(","), m = -1;
    for (var i = 0; i < xs.length; i++) {
      var v = 値(a, xs[i]);
      if (v === undefined || v === null || v === 不明) return v === 不明 ? 不明 : undefined;
      if (v > m) m = v;
    }
    return m;
  }
  if (name === "平屋以外") {
    if (a.地上 === undefined || a.地上 === 不明) return a.地上;
    if (a.地上 >= 2) return true;
    if (a.地下 === undefined || a.地下 === 不明) return a.地下;
    return a.地下 >= 1 ? 不明 : false; // 地上1階・地階ありは平屋かどうか条文だけでは決めない
  }
  return a[name];
}

function 倍率(a) {
  if (a.構造 === undefined || a.構造 === 不明) return a.構造;
  if (a.構造 === "その他") return 1;
  if (a.内装 === undefined || a.内装 === 不明) return a.内装;
  if (a.構造 === "耐火") return a.内装 ? 3 : 2;
  return a.内装 ? 2 : 1; // 準耐火
}

// 条件1つ: true / false / null（まだ） / 不明
function 条件を見る(c, a, row) {
  var name = c[0], op = c[1], v = c[2];
  var x = 値(a, name);
  if (x === undefined || x === null) return { r: null, 要: [name] };
  if (x === 不明) return { r: 不明, 要: [name] };
  if (op === ">=倍") {
    var f = 倍率(a);
    if (f === undefined || f === null) return { r: null, 要: ["構造", "内装"] };
    if (f === 不明) return { r: 不明, 要: ["構造", "内装"] };
    var hi = v * f;
    if (row.特例 && f > 1) {
      var lo = Math.min(hi, 1000);
      if (x >= hi) return { r: true };
      if (x < lo) return { r: false };
      return { r: 不明, 要: [], 説明: "六項ロなどは「1,000㎡＋省令で定める部分の床面積」と比べた小さい方で読む（令11条2項）。その部分の床面積しだい" };
    }
    return { r: x >= hi, 線: hi, 倍: f };
  }
  if (op === ">=") return { r: x >= v };
  if (op === ">") return { r: x > v };
  if (op === "<") return { r: x < v };
  if (op === "==") return { r: x === v };
  return { r: 不明 };
}

function 名前(id) {
  for (var i = 0; i < 質問.length; i++) if (質問[i].id === id) return 質問[i].文;
  return id;
}

function 設備を判定(表, a) {
  var 要る = [], 待ち = [], できない = [], 注記 = [], 候補 = (表.候補 || []).slice();
  表.行.forEach(function (row) {
    if (!用途に当たる(row.用途, a.用途)) return;
    if (row.結果 === "注記") { 注記.push(row); return; }
    if (row.結果 === "判定できない") {
      // 条件つきの「判定できない」は、条件が満たされたときだけ（例: 特殊な部分が「ある」と答えたとき）
      var hit = true, nd = [];
      (row.条件 || []).forEach(function (c) { var r = 条件を見る(c, a, row); if (r.r === false) hit = false; else if (r.r !== true) { if (hit) hit = null; nd = nd.concat(r.要 || []); } });
      if (hit === true) できない.push(row);
      else if (hit === null) 待ち.push({ row: row, 要: nd, 説明: [] });
      return;
    }
    if (/^6イ[12]$|^6ロ/.test(a.用途) && ((表.設備 === "屋内消火栓" && row.号 === "令11条1項2号") || row.倍特例)) row = Object.assign({}, row, { 特例: true });
    var ok = true, need = [], 説明 = [], 線 = [];
    for (var i = 0; i < row.条件.length; i++) {
      var r = 条件を見る(row.条件[i], a, row);
      if (r.r === false) { ok = false; break; }
      if (r.r !== true) { ok = null; need = need.concat(r.要 || []); if (r.説明) 説明.push(r.説明); }
      if (r.線) 線.push("構造と内装により基準を" + r.倍 + "倍に読み替え（" + r.線 + "㎡で判定）");
    }
    if (ok === true) 要る.push(Object.assign({ 線: 線 }, row));
    else if (ok === null) 待ち.push({ row: row, 要: need, 説明: 説明 });
  });
  var 状態;
  if (要る.length) 状態 = "要る";
  else if (待ち.length) 状態 = "条件次第";
  else if (できない.length) 状態 = "判定できない";
  else 状態 = "要らない";
  if (状態 === "要らない" && 表.未収録 && 表.未収録.length) {
    状態 = "判定できない";
    できない.push({ 号: 表.条[0] + "の" + 表.未収録.join("・") + "号", 理由: "判定表にまだ入れていない号がある" });
  }
  要る.forEach(function (r) { if (r.候補) 候補.push(r.候補); });
  return { 設備: 表.設備, 状態: 状態, 要る: 要る, 待ち: 待ち, できない: できない, 注記: 注記, 候補: 候補, 札: 表.札, 変わった: 表.変わった || [] };
}

function 全部を判定(表たち, a) {
  return 表たち.map(function (t) { return 設備を判定(t, a); });
}

// 次に聞く質問: まだ決まっていない設備の判定に効く質問だけ
function 次の質問(表たち, a) {
  if (!a.用途) return null;
  var res = 全部を判定(表たち, a), 効く = {};
  res.forEach(function (r) { if (r.状態 === "条件次第") r.待ち.forEach(function (w) { w.要.forEach(function (n) { 効く[n] = true; }); }); });
  // max: の中身や、平屋以外は元の質問に分ける
  if (効く["平屋以外"]) { 効く.地上 = true; 効く.地下 = true; }
  Object.keys(効く).forEach(function (k) { if (k.indexOf("max:") === 0) k.slice(4).split(",").forEach(function (x) { 効く[x] = true; }); });
  for (var i = 0; i < 質問.length; i++) {
    var q = 質問[i];
    if (a[q.id] !== undefined) continue;
    if (q.出す && !q.出す(a)) continue;
    if (q.自動) { var v = q.自動(a); if (v !== undefined) { a[q.id] = v; 自動で入れた[q.id] = true; return 次の質問(表たち, a); } }
    if (効く[q.id]) return q;
  }
  return null;
}

if (typeof module !== "undefined") module.exports = { 質問: 質問, 全部を判定: 全部を判定, 次の質問: 次の質問, 不明: 不明, 名前: 名前 };
