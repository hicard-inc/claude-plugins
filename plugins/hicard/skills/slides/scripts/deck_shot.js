// スライドを1枚ずつ 16:9 で撮る（登壇者が見る形で確認するため）
// 使い方: node scripts/preview/deck_shot.js <html> <出力ディレクトリ> [--dark] [--only=3,7]
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

(async () => {
  const file = process.argv[2];
  const outDir = process.argv[3];
  if (!file || !outDir) {
    console.error('使い方: node scripts/preview/deck_shot.js <html> <出力ディレクトリ> [--dark] [--only=3,7]');
    process.exit(1);
  }
  const dark = process.argv.includes('--dark');
  const onlyArg = process.argv.find((a) => a.startsWith('--only='));
  const only = onlyArg ? onlyArg.slice(7).split(',').map(Number) : null;

  fs.mkdirSync(outDir, { recursive: true });

  const findChromium = require(require('path').join(__dirname, 'find_chromium.js'));
  const exe = findChromium();
  let browser;
  try {
    browser = await chromium.launch(exe ? { executablePath: exe } : {});
  } catch (e) {
    // 🔴 ここで throw すると Node が生の Playwright スタックを出し、
    //    読む人は案内文ではなくスタックを読んでしまう（2026-09-05 パイロットで実測）。
    //    案内文を出して、その場で終わる。
    console.error(findChromium.hint);
    console.error('（詳細を見たいときは DECK_SHOT_DEBUG=1 を付けて実行）');
    if (process.env.DECK_SHOT_DEBUG) console.error(e);
    process.exit(1);
  }
  // 1440x810 = 16:9。プロジェクタと同じ比率で見る
  const page = await browser.newPage({
    viewport: { width: 1440, height: 810 },
    deviceScaleFactor: 2,
    colorScheme: dark ? 'dark' : 'light',
  });
  await page.goto('file://' + path.resolve(file), { waitUntil: 'load' });
  await page.emulateMedia({ reducedMotion: 'reduce' });

  const n = await page.locator('.slide').count();
  const suffix = dark ? '_dark' : '';

  for (let i = 0; i < n; i++) {
    if (only && !only.includes(i + 1)) continue;
    await page.locator('.slide').nth(i).scrollIntoViewIfNeeded();
    await page.waitForTimeout(120);
    const name = String(i + 1).padStart(2, '0') + suffix + '.png';
    await page.screenshot({ path: path.join(outDir, name) });
  }
  await browser.close();
  console.log(`撮った: ${outDir}（${only ? only.length : n}枚 / ${dark ? 'dark' : 'light'}）`);
})();
