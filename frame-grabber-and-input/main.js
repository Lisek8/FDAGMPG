const puppeteer = require('puppeteer');

async function createPage(browser) {
  // Create page and load game site
  const page = await browser.newPage();
  await page.goto('https://supermariobros.io/full-screen-mario/mario.html');
  return page;
}

async function launchGame(page) {
  // Focus on game
  await page.bringToFront();
  const gameCanvas = await page.$('body > canvas');
  await gameCanvas.click();
  // Example keyboard input
  await page.keyboard.down('d');
  // Example screenshot (doesn't have to be to file)
  await gameCanvas.screenshot({ path: 'example.png' });
}

(async () => {
  const browser = await puppeteer.launch({ headless: false, args: ['--mute-audio'] });
  const page = await createPage(browser);
  const page1 = await createPage(browser);
  await launchGame(page);
  await launchGame(page1);
})();