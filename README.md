# Framework dedicated to autonomous gameplay in Mario-like platforming games

## Dependecies
- [Python](https://www.python.org/) 3.8.6
- [Node.js](https://nodejs.org/en/) 12.18.1

## Frame grabber and input
Program allowing to extract game image and gameplay status from [Mario game](https://supermariobros.io/)

### Dependencies
- [Puppeteer](https://pptr.dev/) 5.5.0
- [console-read-write](https://www.npmjs.com/package/console-read-write) 0.1.1

### Installation
1. Navigate to **frame-grabber-and-input** folder
2. Execute `npm install` in command line to install dependencies

### Compilation
1. Execute `npm run compile`

## Autonomous gameplay artificial inteligence

### Dependencies
- [tensorflow](https://www.tensorflow.org/) 2.4.0
- [Keras](https://keras.io/) 2.4.3

### Execution
1. Ensure you have compiled a framer-grabber-and-input part of project
2. Navigate to **autonomous-gameplay-artificial-inteligence** folder
3. Execute `python ai.py` in command line

