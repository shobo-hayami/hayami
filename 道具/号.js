// 号の名前（「令12条1項4号イ」「令26条1項1号・2号」「令13条1項の表（部分）」「令20条1項1号（令11条1項2号の建物）」）から、
// 条文の原文のその部分だけを切り出す。読めない名前・見つからない号は null（広い範囲を出さない）。早見の画面と試験で同じものを使う
function 号の全角(n){ return String(n).replace(/\d/g, function(c){ return '０１２３４５６７８９'[+c]; }); }
function 号の漢数(n){ var d = '〇一二三四五六七八九'; if(n < 10) return d[n]; var t = Math.floor(n / 10), o = n % 10; return (t > 1 ? d[t] : '') + '十' + (o ? d[o] : ''); }
var 号の表の行 = {
  '十三項ロ': function(左){ return 左.indexOf('（十三）項ロ') >= 0; },
  '指定可燃物': function(左){ return 左.indexOf('指定可燃物') >= 0 || 左.indexOf('危険物政令別表第四') >= 0; },
  '部分': function(左){ return !(左.indexOf('（十三）項ロ') >= 0 || 左.indexOf('指定可燃物') >= 0 || 左.indexOf('危険物政令別表第四') >= 0); }
};
// 参照1つを読む。表 を許すかどうかは 表可 で決める
function 号の参照を読む(s, 表可){
  var m = /^令(\d+)条(?:の(\d+))?第?(\d+)項(.*)$/.exec(s);
  if(!m) return null;
  var r = { 名: s, 条: '令' + m[1] + (m[2] ? '_' + m[2] : ''), 項: +m[3], 号: [], いろは: '', 表: false }, rest = m[4];
  if(rest === '') return r;
  if(rest === 'の表'){ if(!表可) return null; r.表 = true; return r; }
  var g = /^(\d+)号((?:・\d+号)*)([イロハニホヘトチリヌ])?$/.exec(rest);
  if(!g) return null;
  r.号 = [+g[1]].concat(g[2] ? g[2].split('・').filter(Boolean).map(function(x){ return +x.replace('号', ''); }) : []);
  r.いろは = g[3] || '';
  return r;
}
function 号の項を切る(t, p){
  var s = 0, e = t.length;
  if(p > 1){ s = t.indexOf('\n' + 号の全角(p) + '　'); if(s < 0) return null; }
  var e2 = t.indexOf('\n' + 号の全角(p + 1) + '　', s + 1); if(e2 > 0) e = e2;
  return t.slice(s, e).replace(/^\n/, '');
}
function 号の号を切る(seg, g, いろは){
  var a = seg.indexOf('\n　' + 号の漢数(g) + '　');
  if(a < 0) return null;
  var b = seg.indexOf('\n　' + 号の漢数(g + 1) + '　', a + 1);
  var x = seg.slice(a + 1, b > 0 ? b : seg.length);
  if(いろは && x.indexOf('\n　　' + いろは + '　') < 0) return null;
  return x;
}
function 号の表を切る(seg, p, 行の名){
  var 選ぶ = 号の表の行[行の名]; if(!選ぶ) return null;
  var L = seg.split('\n'), i = L.indexOf('　〔表〕');
  if(i < 0 || i + 1 >= L.length) return null;
  var 柱 = L.slice(p === 1 ? 1 : 0, i), 見出し = L[i + 1], 行 = [];
  for(var k = i + 2; k < L.length && L[k].indexOf('　｜') === 0; k++){ if(選ぶ(L[k].slice(2).split(' ｜ ')[0])) 行.push(L[k]); }
  if(!行.length) return null;
  return 柱.concat([見出し], 行).join('\n');
}
function 号の参照を切る(r, 文, 行の名){
  var t = 文[r.条]; if(!t) return null;
  var seg = 号の項を切る(t, r.項); if(seg === null) return null;
  if(r.表) return 号の表を切る(seg, r.項, 行の名);
  if(!r.号.length) return seg;
  var out = [];
  for(var i = 0; i < r.号.length; i++){
    var x = 号の号を切る(seg, r.号[i], i === r.号.length - 1 ? r.いろは : '');
    if(x === null) return null; out.push(x);
  }
  return out.join('\n');
}
function 号の原文(号, 文){
  文 = 文 || (typeof 条文 !== 'undefined' ? 条文 : {});
  var m = /^(.*)（([^（）]*)）$/.exec(号), 主 = m ? m[1] : 号, 添え = m ? m[2] : null;
  var r1 = 号の参照を読む(主, true); if(!r1) return null;
  if(r1.表){ if(!添え) return null; return 号の参照を切る(r1, 文, 添え); }
  var t1 = 号の参照を切る(r1, 文); if(t1 === null) return null;
  if(添え === null) return t1;
  var n = /^(.*)の(?:建物|部分)$/.exec(添え); if(!n) return null;
  var r2 = 号の参照を読む(n[1], false); if(!r2) return null;
  var t2 = 号の参照を切る(r2, 文); if(t2 === null) return null;
  return '〔' + 主 + '〕\n' + t1 + '\n\n〔' + n[1] + '〕\n' + t2;
}
if (typeof module !== "undefined") module.exports = { 号の原文: 号の原文, 号の参照を読む: 号の参照を読む };
