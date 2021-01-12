import puppeteer, { Browser, Page } from 'puppeteer';
import { GameState } from './gameState';
import readline from 'readline';
import * as path from 'path';

const inputStream = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});
// const gameUrl = 'https://supermariobros.io/full-screen-mario/mario.html';
const gameUrl = `file:${path.join(__dirname, '../supermariobros.io/mario.html')}`;
const initialGamePages = 10;
const keysPressed: any = {
  w: false,
  a: false,
  s: false,
  d: false,
  shift: false
};
const errors: any = {
  control: false,
  pageCreation: false,
  gameState: false
};
const gamePages: Page[] = [];
let browser: Browser;
let currentPage: Page;
let prevGameState: GameState = {
  score: 0,
  coins: 0,
  world: '1-1',
  time: 400,
  lives: 3,
  image: ''
}

async function openBrowserAndCreatePages() {
  browser = await puppeteer.launch({ headless: true, args: [gameUrl, '--mute-audio'], defaultViewport: { width: 600, height: 600 } });
  gamePages.push((await browser.pages())[0]);
  currentPage = gamePages[0];
  await currentPage.waitForSelector('body > canvas');
  await prepareGameWindow(currentPage);
  for (let i = 0; i < initialGamePages; i++) {
    await createPageAndPrepareGame(browser, false);
  }
  await currentPage.bringToFront();
}

async function prepareGameWindow(page: Page) {
  const gameCanvas = await page.$('body > canvas');
    if (gameCanvas != null) {
      await gameCanvas.click();
      await page.keyboard.press('p');
    }
}

async function createPageAndPrepareGame(browser: Browser, focusOnCurrentPage: boolean) {
  try {
    const page: Page = await browser.newPage();
    await page.goto(gameUrl);
    await prepareGameWindow(page);
    gamePages.push(page);
    if (focusOnCurrentPage === true) {
      await currentPage.bringToFront();
    }
  } catch (error) {
    errors.pageCreation = true;
  }
}

async function getGameInfo(page: Page): Promise<GameState> {
  let gameState = prevGameState;
  try {
    gameState = await page.evaluate(() => {
      const gameBodyElement: HTMLElement | null = document.querySelector('body');
      const worldInfoTableChildren: HTMLCollection = gameBodyElement!.children[1].children;
      const canvas: HTMLCanvasElement = gameBodyElement!.children[0] as HTMLCanvasElement;
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
  } catch (error) {
    errors.gameState = true;
  }
  return gameState;
}

async function gameControlIteration(inputLine: string) {
  await performGameControl(inputLine);
  if (inputLine === 'NEXTGAME') {
    console.log('FRAMEGRABBER:READY');
    return;
  }
  let gameState = await getGameInfo(currentPage);
  if (errors.gameState === false) {
    prevGameState = gameState;
  }
  gameState!.errors = errors;
  console.log(JSON.stringify(gameState));
  errors.control = false;
  errors.gameState = false;
  errors.pageCreation = false;
}

async function switchToNextGame() {
  if (currentPage != null) {
    await currentPage.close();
  }
  gamePages.shift();
  currentPage = gamePages[0];
  await createPageAndPrepareGame(browser, true);
}

async function performGameControl(inputLine: string) {
  if (inputLine === 'NEXTGAME') {
    await switchToNextGame();
  } else {
    const keys: Array<string> = inputLine.split('|');
    await keys.forEach(async key => {
      try {
        if (key === 'p' || key === 'ctrl') {
          await currentPage.keyboard.press(key);
          return;
        }
        if (keysPressed[key]) {
          await currentPage.keyboard.up(key);
        } else {
          await currentPage.keyboard.down(key);
        }
        keysPressed[key] = !keysPressed[key];
      } catch (error) {
        errors.control = true;
      }
    });
  }
}

async function runFrameGrabber() {
  await openBrowserAndCreatePages();
  console.log('FRAMEGRABBER:READY');
  for await (const line of inputStream) {
    await gameControlIteration(line);
  }
}

runFrameGrabber();