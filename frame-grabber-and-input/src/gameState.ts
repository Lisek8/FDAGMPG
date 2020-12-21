export interface GameState {
  score: number;
  coins: number;
  world: string;
  time: number;
  lives: number;
  image: string;
  errors?: {
    control: false;
    gameState: false;
    pageCreation: false;
  }
}