import time
from subprocess import Popen, PIPE
import io
import cv2
import base64 
import numpy as np
from PIL import Image
import json
from typing import Any, Tuple
from .preprocessing import Preprocessing

class Environment:
  def __init__(self, gameWidth, gameHeight, visualize: bool = False, downsampleFactor = 4, frameStack = 4):
    self.gameTime: int = -1
    self.frameStack = frameStack
    self.downsampleFactor = downsampleFactor
    self.nextGame: bool = False
    self.gameReady: bool = False
    self.visualize: bool = visualize
    self.lastIterationTime: int = 0
    self.actions = ['w', 'a', 'd', 'w|a', 'w|d', 'w|a|shift', 'w|d|shift', 'w|shift', 'd|shift', 'a|shift']
    self.buttonsPressed = {
      "w": False,
      "a": False,
      "d": False,
      "shift": False
    }
    self.gameWidth = gameWidth
    self.gameHeight = gameHeight

  def open(self):
    self.process = Popen("node ../frame-grabber-and-input/dist/main.js width={} height={}".format(self.gameWidth, self.gameHeight), stdin=PIPE, stdout=PIPE)
    self.gameReady = True
  
  def __prepareGameWindow(self):
    while True:
      frameGrabberInfo: bytes = self.process.stdout.readline().strip()
      if (frameGrabberInfo != b'' and frameGrabberInfo.decode() == 'FRAMEGRABBER:READY'):
        self.process.stdin.write(("p").encode())
        break
      time.sleep(1)
  
  def __processInputString(self, inputString: str, separator: str = "|") -> str:
    outputStringKeys = []
    buttonsList = inputString.split(separator)
    for key in self.buttonsPressed:
      if (key in buttonsList):
        if (self.buttonsPressed[key] == False):
          outputStringKeys.append(key)
          self.buttonsPressed[key] = True
      elif (self.buttonsPressed[key] == True):
          outputStringKeys.append(key)
          self.buttonsPressed[key] = False
    return separator.join(outputStringKeys)


  def reset(self):
    assert self.gameReady, "Environment must be open before step call"
    self.process.stdin.write(("NEXTGAME\n").encode())
    self.process.stdin.flush()
    self.gameTime = -1
    self.__prepareGameWindow()
    self.nextGame = False
    _, gameInfo = self.step('')
    self.nextGame = False
    self.__frames = np.empty([int(self.gameHeight / self.downsampleFactor), int(self.gameWidth / self.downsampleFactor), self.frameStack])
    self.__frames[:,:] = np.array(gameInfo['image'])
    return self.__frames

  def step(self, inputString: str) -> Tuple[bool, Any]:
    assert self.gameReady, "Environment must be open before step call"
    assert not self.nextGame, "Cannot perform a step in game that is done, use reset() to prepare next game"

    frameStackArray = np.empty([int(self.gameHeight / self.downsampleFactor), int(self.gameWidth / self.downsampleFactor), self.frameStack])
    stepGameInfo = None
    for i in range(0, self.frameStack):
      iterationStart: float = time.time()
      # Pass input to frame grabber
      self.process.stdin.write((self.__processInputString(inputString) + "\n").encode())
      inputString = ""
      self.process.stdin.flush()
      # Get output from process
      frameGrabberInfo: bytes = self.process.stdout.readline().strip()
      # Process data passed by frame grabber
      if (frameGrabberInfo != b''):
        dataToBePassedToAI: str = frameGrabberInfo.decode()
        # Covert data to json
        gameInfoJson = json.loads(dataToBePassedToAI)
        # Update game time if it changed
        if (self.gameTime != gameInfoJson['time']):
          self.gameTime = gameInfoJson['time']
        if (gameInfoJson['world'] != '1-1' or gameInfoJson['lives'] != 3):
          self.nextGame = True
        # Process game image
        gameImage: bytes = base64.b64decode((gameInfoJson['image']))
        processedImage = cv2.cvtColor(np.array(Image.open(io.BytesIO(gameImage))), cv2.COLOR_BGR2RGB)
        gameInfoJson['image'] = Preprocessing.downsample(Preprocessing.toGrayscale(processedImage), self.downsampleFactor)
        # Display current game state
        if (self.visualize == True):
          cv2.imshow('Game preview', processedImage)
          cv2.waitKey(1)
        frameStackArray[:,:,i] = gameInfoJson['image']
        stepGameInfo = gameInfoJson
      
      iterationEnd: float = time.time()
      self.lastIterationTime = (iterationEnd * 1000) - (iterationStart * 1000)
      # print(self.lastIterationTime)
    stepGameInfo['image'] = frameStackArray
    return (self.nextGame, stepGameInfo)

  def close(self):
    self.process.kill()