export interface GameState {
  score: number;
  coins: number;
  world: string;
  time: number;
  lives: number;
  image?: Buffer;
}