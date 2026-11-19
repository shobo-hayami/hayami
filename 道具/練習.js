// 練習問題: 例題（条文から手で出した答えつき）を問題にする。判定の作り（判定.js）と名前の表（語.js）を使い、どちらも変えない。
// 画面（早見.html に埋め込み）と試験（node 試験_練習.js）の両方で同じものを使う。外へは何も送らず、何も残さない。

var 練習の段の順 = ["基本", "点検", "複合", "決める", "線"];
var 練習の段 = {
  基本: { 名: "基本", 級: "初級", 中身: "用途が1つの建物。面積・階数・収容人員の線" },
  点検: { 名: "階段・階・人数", 級: "中級", 中身: "階段が1つの建物、地下街、11階以上、少量危険物、避難器具の人数" },
  複合: { 名: "複合ビル", 級: "上級", 中身: "用途が2つ以上の建物。用途ごとの部分で判定する号と、建物全体で判定する号" },
  決める: { 名: "細かい決まり", 級: "上級", 中身: "手術室などの区画、舞台部、ラック式倉庫、準地下街、指定可燃物の倍数、無窓階の人数、地下街の中の部分" },
  線: { 名: "線を答える", 級: "上級", 中身: "その値だけが増えるとき、いくつ以上で要るに変わるかを数字で答える" }
};

// 例題の名前の頭で段を決める（手で印を付けない）。どれにも当たらなければ null（試験で失敗にする）
function 練習の段を決める(e) {
  if (e.答え && e.答え.部分) return "複合";
  if (/^点検: /.test(e.名前)) return "点検";
  if (/^決める: /.test(e.名前)) return "決める";
  if (/^(複合|境目): /.test(e.名前)) return null;
  return /^[^:：]+$/.test(e.名前) ? "基本" : null;
}
function 練習に不明あり(e) { return Object.keys(e.答え).some(function (k) { return e.答え[k] === 不明; }); }

// 例題を入れる: 早見で答えるときと同じ順（建物の質問 → 部分ごとの質問）に、例題の値を入れる。
// 階数などから自動で入る値は入れない（表にも出さない）。自動で入った値と例題の値が違えば「食い違い」に残す
function 例題を入れる(e) {
  var a = { 用途: e.答え.用途 }, 手 = [], 食い違い = [];
  if (e.答え.部分) a.部分 = e.答え.部分.map(function (p) { return { 用途: p.用途, 延べ: p.延べ }; });
  自動で入れた = {};
  var ids = [];
  質問.forEach(function (q) { if (!q.部分だけ) ids.push({ id: q.id, q: q }); });
  (a.部分 || []).forEach(function (p, i) { 質問.forEach(function (q) { if (部分の問.indexOf(q.id) >= 0) ids.push({ id: "p" + i + "_" + q.id, q: q, i: i }); }); });
  ids.forEach(function (x) {
    自動で埋める(a);
    if (!(x.id in e.答え)) return;
    var 相手 = x.i === undefined ? a : 部分の答(a, x.i);
    if (x.q.出す && !x.q.出す(相手)) return; // この建物では聞かない質問
    if (a[x.id] === undefined) { a[x.id] = e.答え[x.id]; 手.push(x.id); }
    else if (a[x.id] !== e.答え[x.id]) 食い違い.push(x.id);
  });
  自動で埋める(a);
  return { a: a, 手: 手, 食い違い: 食い違い, 自動: Object.assign({}, 自動で入れた) };
}

function 練習の数(v) { return Number(v).toLocaleString("ja-JP"); }
function 練習の部分名(a, i) {
  var c = a.部分[i].用途, t = (typeof 用途の名 !== "undefined" && 用途の名[c]) ? 用途の名[c].split(" ").slice(1).join(" ") : c;
  var m = /^[^・／（]+/.exec(t); return m && m[0].length < t.length ? m[0] + "など" : t;
}
// 建物の表の1行: 名前と値の文
function 練習の行(id, v, a) {
  var m = /^p(\d+)_(.+)$/.exec(id), base = m ? m[2] : id;
  var 名 = (m ? "〔" + 練習の部分名(a, +m[1]) + "〕" : "") + (語の名[base] || base);
  var 値;
  if (v === true) 値 = "はい"; else if (v === false) 値 = "いいえ";
  else if (base === "構造") 値 = { 耐火: "耐火建築物", 準耐火: "準耐火建築物", その他: "その他（耐火建築物でも準耐火建築物でもない）" }[v] || v;
  else if (typeof v === "number") 値 = 練習の数(v) + (語の単位[base] || "");
  else 値 = String(v);
  return { id: id, 名: 名, 値: 値, 名あり: !!語の名[base], 単位あり: typeof v !== "number" || !!語の単位[base] };
}
function 練習の表(e) {
  var r = 例題を入れる(e);
  return r.手.map(function (id) { return 練習の行(id, r.a[id], r.a); });
}

// 問題を作る。見直し中の設備は出さない。線の問題は、線ちょうどで「要る」・1つ手前で「要らない」になるものだけ
function 練習の問題を作る(例題, 境目, 表たち) {
  var 変わった = {}; 表たち.forEach(function (t) { if (t.変わった && t.変わった.length) 変わった[t.設備] = true; });
  var out = {}; 練習の段の順.forEach(function (k) { out[k] = []; });
  例題.forEach(function (e, n) {
    var 段 = 練習の段を決める(e); if (!段 || 練習に不明あり(e)) return;
    var 行 = Object.keys(e.期待).filter(function (k) { return (e.期待[k] === "要る" || e.期待[k] === "要らない") && !変わった[k]; }).map(function (k) { return { 設備: k, 期待: e.期待[k] }; });
    if (!行.length) return;
    out[段].push({ 段: 段, 番号: out[段].length + 1, 例: e, 行: 行, 元: n });
  });
  境目.forEach(function (e, n) {
    if (!e.期待 || !e.期待.主 || 練習に不明あり(e) || 変わった[e.設備]) return;
    var m = 練習の線(e, 表たち); if (!m) return;
    out.線.push({ 段: "線", 番号: out.線.length + 1, 例: e, 設備: e.設備, 線: m, 元: n });
  });
  return out;
}
function 練習の判定(e, 設備, 表たち) {
  var r = 例題を入れる(e); return 全部を判定(表たち.filter(function (t) { return t.設備 === 設備; }), r.a)[0];
}
function 練習の線(e, 表たち) {
  var r = 練習の判定(e, e.設備, 表たち), m = r.境目 && r.境目.主;
  if (!m || m.種 !== "数" || /^max:/.test(m.名) || (m.どこ && m.どこ !== "建物全体")) return null;
  function 状態(v) { var e2 = JSON.parse(JSON.stringify(e)); e2.答え[m.名] = v; return 練習の判定(e2, e.設備, 表たち).状態; }
  if (状態(m.線) !== "要る" || 状態(m.線 - 1) !== "要らない") return null;
  return m;
}

if (typeof module !== "undefined") module.exports = { 練習の問題を作る: 練習の問題を作る, 例題を入れる: 例題を入れる, 練習の表: 練習の表 };
