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
  Shift: false
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
};
let gameSize = {
  width: 600, // Minimum require width (>= 600)
  height: 432 // Minimum required height (>= 431)
};

if (process.argv.length < 4) {
  console.error('Invalid number of arguments, please pass width and height of game window as program arguments in format \'width=<number> height=<number>\'');
  process.exit(1);
}

try {
  gameSize = {
    width: parseInt(process.argv[2].split('=')[1]),
    height: parseInt(process.argv[3].split('=')[1])
  };
} catch (error) {
  console.error('Failed to parse command line arguments, please make sure arguments are in format \'width=<number> height=<number>\'');
  process.exit(2);
}

async function openBrowserAndCreatePages() {
  browser = await puppeteer.launch({ headless: true, args: [gameUrl, '--mute-audio'], defaultViewport: gameSize });
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
    console.error('[FRAMEGRABBER]: ' + error);
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
    console.error('[FRAMEGRABBER]: ' + error);
  }
  return gameState;
}

async function gameControlIteration(inputLine: string) {
  await performGameControl(inputLine);
  if (inputLine === 'NEXTGAME') {
    for (const key in keysPressed) {
      keysPressed[key] = false;
    }
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
  } else if (inputLine != '') {
    const keys: Array<string> = inputLine.split('|');
    if (keys.includes('p')) {
      await currentPage.keyboard.press('p');
      return;
    }
    if (keys.includes('ctrl')) {
      await currentPage.keyboard.press('Ctrl');
    }
    for (const key in keysPressed) {
      if (keysPressed[key] === true && keys.includes(key) === false) {
        await currentPage.keyboard.up(key);
        keysPressed[key] = false;
      } else if (keysPressed[key] === false && keys.includes(key) === true) {
        await currentPage.keyboard.down(key);
        keysPressed[key] = true;
      }
    }
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