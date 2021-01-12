from collections import deque
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
  def __init__(self, visualize: bool = False, frameStack = 4):
    self.gameTime: int = -1
    self.frameStack = frameStack
    self.nextGame: bool = False
    self.gameReady: bool = False
    self.visualize: bool = visualize
    self.lastIterationTime: int = 0
    self.actions = ['w', 'a', 'd']

  def open(self):
    self.process = Popen("node ../frame-grabber-and-input/dist/main.js", stdin=PIPE, stdout=PIPE)
    self.gameReady = True
  
  def __prepareGameWindow(self):
    while True:
      frameGrabberInfo: bytes = self.process.stdout.readline().strip()
      if (frameGrabberInfo != b'' and frameGrabberInfo.decode() == 'FRAMEGRABBER:READY'):
        self.process.stdin.write(("p").encode())
        break
      time.sleep(1)

  def reset(self):
    assert self.gameReady, "Environment must be open before step call"
    self.process.stdin.write(("NEXTGAME\n").encode())
    self.process.stdin.flush()
    self.nextGame = False
    self.gameTime = -1
    self.__prepareGameWindow()
    _, gameInfo = self.step('')
    self.__frames = np.empty([300, 300, self.frameStack])
    self.__frames[:,:] = np.array(gameInfo['image'])
    return self.__frames

  def step(self, inputString: str) -> Tuple[bool, Any]:
    assert self.gameReady, "Environment must be open before step call"
    assert not self.nextGame, "Cannot perform a step in game that is done, use reset() to prepare next game"

    frameStackArray = np.empty([300, 300, self.frameStack])
    stepGameInfo = None
    for i in range(0, self.frameStack):
      iterationStart: float = time.time()
      # Pass input to frame grabber
      self.process.stdin.write((inputString + "\n").encode())
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
        gameInfoJson['image'] = Preprocessing.downsample(Preprocessing.toGrayscale(processedImage))
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