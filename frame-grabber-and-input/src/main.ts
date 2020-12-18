import puppeteer, { Browser, ElementHandle, Page } from 'puppeteer';
import { Action } from './action';
import { GameState } from './gameState';
import readline from 'readline';

const gameUrl = 'https://supermariobros.io/full-screen-mario/mario.html';
const initialGamePages = 1;
const keysPressed: any = {
  w: false,
  a: false,
  s: false,
  d: false,
  shift: false
};
let currentPage: Page;

async function openBrowserAndCreatePages() {
  const browser = await puppeteer.launch({ headless: false, args: ['--mute-audio'] });
  const gamePages: Page[] = [];
  for (let i = 0; i < initialGamePages; i++) {
    await createPageAndPrepareGame(browser, gamePages);
    currentPage = gamePages[0];
  }
}

async function createPageAndPrepareGame(browser: Browser, gamePages: Page[]) {
  const page: Page = await browser.newPage();
  await page.goto(gameUrl);
  const gameCanvas = await page.$('body > canvas');
  if (gameCanvas != null) {
    await gameCanvas.click();
    await page.keyboard.press('p');
  }
  gamePages.push(page);
}

async function getGameInfo(page: Page): Promise<GameState> {
  const gameState = await page.evaluate(() => {
    const worldInfoTableChildren = document.getElementById('data_display')!.children;
    const canvas: HTMLCanvasElement | null = document.querySelector('canvas');
    const canvasDataUrl: string = canvas!.toDataURL();
    const gameState: GameState = {
      score: parseInt(worldInfoTableChildren![0].innerHTML.split('<br>')[1]),
      coins: parseInt(worldInfoTableChildren![1].innerHTML.split('<br>')[1]),
      world: worldInfoTableChildren![2].innerHTML.split('<br>')[1],
      time: parseInt(worldInfoTableChildren![3].innerHTML.split('<br>')[1]),
      lives: parseInt(worldInfoTableChildren![4].innerHTML.split('<br>')[1]),
      image: canvasDataUrl.substr(canvasDataUrl.indexOf(',') + 1)
    }
    return gameState;
  });
  gameState.image = Buffer.from(gameState.image as string, 'base64')
  return gameState;
}

async function gameControlIteration(page: Page) {
  const actionsToPerform: Action[] = getActions();
  await performActions(actionsToPerform);
  const gameState: GameState = await getGameInfo(page);
  // sendGameState(gameState);
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

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

(async () => {
  const browser = await puppeteer.launch({ headless: false, args: ['--mute-audio'] });
  const gamePages: Page[] = [];
  await createPageAndPrepareGame(browser, gamePages);
  currentPage = gamePages[0];
  console.log('FRAMEGRABBER:READY');
  for await (const line of rl) {
    const keys: Array<string> = line.split('|');
    keys.forEach(key => {
      if (key === 'p' || key === 'ctrl') {
        currentPage.keyboard.press(key);
        return;
      }
      if (keysPressed[key]) {
        currentPage.keyboard.up(key);
      } else {
        currentPage.keyboard.down(key);
      }
      keysPressed[key] = !keysPressed[key];
    });
    console.log(JSON.stringify(await getGameInfo(currentPage)))
  }
})();