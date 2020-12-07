import puppeteer, { Browser, ElementHandle, Page } from 'puppeteer';
import { Action } from './action';
import { GameState } from './gameState';

const gameUrl = 'https://supermariobros.io/full-screen-mario/mario.html';
const initialGamePages = 10;

async function openBrowserAndCreatePages() {
  const browser = await puppeteer.launch({ headless: false, args: ['--mute-audio'] });
  const gamePages: Page[] = [];
  for (let i = 0; i < initialGamePages; i++) {
    // gamePages.push(await createPageAndPrepareGame(browser));
    createPageAndPrepareGame(browser, gamePages);
  }
}

async function createPageAndPrepareGame(browser: Browser, gamePages: Page[]) {
  const page: Page = await browser.newPage();
  await page.goto(gameUrl);
  const gameCanvas: ElementHandle<Element> | null = await page.$('body > canvas');
  if (gameCanvas != null) {
    await gameCanvas.click();
    await page.keyboard.press('p');
  }
  gamePages.push(page);
}

async function getGameInfo(page: Page): Promise<GameState> {
  const gameCanvas: ElementHandle<Element> | null = await page.$('body > canvas');
  const gameState: GameState = {
    score: parseInt((await page.$eval('#data_display > td:nth-child(1)', element => element.innerHTML)).split('<br>')[1]),
    coins: parseInt((await page.$eval('#data_display > td:nth-child(2)', element => element.innerHTML)).split('<br>')[1]),
    world: (await page.$eval('#data_display > td:nth-child(3)', element => element.innerHTML)).split('<br>')[1],
    time: parseInt((await page.$eval('#data_display > td:nth-child(4)', element => element.innerHTML)).split('<br>')[1]),
    lives: parseInt((await page.$eval('#data_display > td:nth-child(5)', element => element.innerHTML)).split('<br>')[1]),
    image: gameCanvas != null ? await gameCanvas.screenshot({ path: 'example.png' }) : undefined
  }
  return gameState;
}

async function gameControlIteration(page: Page) {
  const actionsToPerform: Action[] = getActions();
  await performActions(actionsToPerform);
  const gameState: GameState = await getGameInfo(page);
  sendGameState(gameState);
}

function sendGameState(gameState: GameState) {
  // Not implemented
}

function getActions(): Action[] {
  // Not implemented
  return [];
}

async function performActions(actions: Action[]) {
  // Not implemented
}

function acknowledgeReadiness(isReady: boolean) {
  // Not implemented
}

(async () => {
  await openBrowserAndCreatePages();
})();