const fs = require('fs');
const md = require('markdown-it')({ html: true, linkify: true });
const src = fs.readFileSync(process.argv[2], 'utf8');
const lines = src.split('\n');
let bad = 0;
lines.forEach((line, i) => {
  if (!line.includes('**')) return;
  const html = md.render(line);
  // 描画後に ** が生き残っていたら、その行は太字化に失敗している
  if (html.includes('**')) {
    bad++;
    console.log(`L${i + 1}: ${line.trim().slice(0, 110)}`);
  }
});
console.log(`--- 太字化に失敗している行: ${bad} ---`);
