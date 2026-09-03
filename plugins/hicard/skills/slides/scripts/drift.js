// 資料(.md) と ページ(.html) の本文を突き合わせて、片方にしか無い文を出す
const fs = require('fs');
const md = require('markdown-it')();
const { chromium } = require('playwright-core');

const norm = (t) => t
  .replace(/<[^>]+>/g, '')
  .replace(/[\s　]+/g, '')
  .replace(/[。、．，]/g, '')
  .replace(/[「」『』（）()【】\[\]]/g, '')
  .replace(/[ｰ―—──…・:：]/g, '');

const sentences = (text) => text
  .split(/[\n。]/).map((s) => norm(s)).filter((s) => s.length >= 8);

(async () => {
  const mdText = md.render(fs.readFileSync(process.argv[2], 'utf8'));
  const findChromium = require(require('path').join(__dirname, 'find_chromium.js'));
  const exe = findChromium();
  let browser;
  try {
    browser = await chromium.launch(exe ? { executablePath: exe } : {});
  } catch (e) {
    console.error(findChromium.hint);
    throw e;
  }
  const page = await browser.newPage();
  await page.goto('file://' + require('path').resolve(process.argv[3]), { waitUntil: 'load' });
  const htmlText = await page.evaluate(() => document.body.innerText);
  await browser.close();

  const mdAll = norm(mdText);
  const htmlAll = norm(htmlText);

  const onlyHtml = sentences(htmlText).filter((s) => !mdAll.includes(s));
  const onlyMd = sentences(mdText).filter((s) => !htmlAll.includes(s));

  console.log('=== ページにしか無い文 ===');
  onlyHtml.forEach((s) => console.log('  ' + s.slice(0, 70)));
  console.log('=== 資料にしか無い文 ===');
  onlyMd.forEach((s) => console.log('  ' + s.slice(0, 70)));
  console.log(`--- ページのみ ${onlyHtml.length} / 資料のみ ${onlyMd.length} ---`);
})();
