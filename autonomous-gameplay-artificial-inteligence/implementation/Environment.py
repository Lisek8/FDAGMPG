import time
from subprocess import Popen, PIPE
import io
import cv2
import base64 
import numpy as np
from PIL import Image
import json
from typing import Any, Tuple

class Environment:
  def __init__(self, visualize: bool = False):
    self.gameTime = -1
    self.lastTimeSwap = 0
    self.nextGame = False
    self.gameReady = False
    self.visualize = visualize
    self.lastIterationTime = 0

  def open(self):
    self.process = Popen("node ../frame-grabber-and-input/dist/main.js", stdin=PIPE, stdout=PIPE)
    self.__prepareGameWindow()
  
  def __prepareGameWindow(self):
    while True:
      frameGrabberInfo = self.process.stdout.readline().strip()
      if (frameGrabberInfo != b'' and frameGrabberInfo.decode() == 'FRAMEGRABBER:READY'):
        self.process.stdin.write(("p|").encode())
        self.gameReady = True
        break
      time.sleep(1)

  def reset(self):
    assert self.gameReady, "Environment must be open before step call"
    self.process.stdin.write(("NEXTGAME\n").encode())
    self.process.stdin.flush()
    self.nextGame = False
    self.gameTime = -1
    self.lastTimeSwap = 0
    self.__prepareGameWindow()

  def step(self, inputString: str) -> Tuple[bool, Any]:
    assert self.gameReady, "Environment must be open before step call"
    assert self.nextGame, "Cannot perform a step in game that is done, use reset() to prepare next game"

    gameInfoJson = ""
    iterationStart = time.time()
    # Pass input to frame grabber
    self.process.stdin.write((inputString + "\n").encode())
    self.process.stdin.flush()
    # Get output from process
    frameGrabberInfo = self.process.stdout.readline().strip()
    # Process data passed by frame grabber
    if (frameGrabberInfo != b''):
      dataToBePassedToAI = frameGrabberInfo.decode()
      # Covert data to json
      gameInfoJson = json.loads(dataToBePassedToAI)
      # Update game time if it changed
      if (self.gameTime != gameInfoJson['time']):
        self.lastTimeSwap = time.perf_counter()
        self.gameTime = gameInfoJson['time']
      else:
        # If gameTime was uninitialized, initialize it
        if (self.gameTime == -1):
          self.lastTimeSwap = time.perf_counter()
        # In case when game time didn't change for half a second, end the game
        elif ((time.perf_counter() - self.lastTimeSwap) > 0.5):
          self.nextGame = True
      # Process game image
      gameImage = base64.b64decode((gameInfoJson['image']))
      processedImage = cv2.cvtColor(np.array(Image.open(io.BytesIO(gameImage))), cv2.COLOR_BGR2RGB)
      gameInfoJson['image'] = processedImage
      # Display current game state
      if (self.visualize == True):
        cv2.imshow('Game preview', processedImage)
        cv2.waitKey(1)
    
    iterationEnd = time.time()
    self.lastIterationTime = (iterationEnd * 1000) - (iterationStart * 1000)
    return (self.nextGame, gameInfoJson)

  def close(self):
    self.process.kill()