import time
from subprocess import Popen, PIPE
import io
import cv2
import base64 
import numpy as np
from PIL import Image
import json

process = Popen("node ../frame-grabber-and-input/dist/main.js", stdin=PIPE, stdout=PIPE)

gameTime = -1
lastTimeSwap = 0
nextGame = False

def waitForNewGameToBePrepared():
    global gameTime, lastTimeSwap
    while True:
        frameGrabberInfo = process.stdout.readline().strip()
        if (frameGrabberInfo != b'' and frameGrabberInfo.decode() == 'FRAMEGRABBER:READY'):
            process.stdin.write(("p").encode())
            break
        time.sleep(1)
    gameTime = -1
    lastTimeSwap = 0


waitForNewGameToBePrepared()
while True:
    iterationStart = time.time()
    if (nextGame == True):
        process.stdin.write(("NEXTGAME\n").encode())
        process.stdin.flush()
        nextGame = False
        gameTime = -1
        lastTimeSwap = 0
        waitForNewGameToBePrepared()
        continue

    # Pass real input here
    process.stdin.write(("d\n").encode())
    process.stdin.flush()
    frameGrabberInfo = process.stdout.readline().strip()
    if (frameGrabberInfo != b''):
        dataToBePassedToAI = frameGrabberInfo.decode()
        gameInfoJson = json.loads(dataToBePassedToAI)
        if (gameTime != gameInfoJson['time']):
            lastTimeSwap = time.perf_counter()
            gameTime = gameInfoJson['time']
        else:
            if (gameTime == -1):
                lastTimeSwap = time.perf_counter()
            elif ((time.perf_counter() - lastTimeSwap) > 0.5):
                nextGame = True
        gameImage = base64.b64decode((gameInfoJson['image']))
        processedImage = cv2.cvtColor(np.array(Image.open(io.BytesIO(gameImage))), cv2.COLOR_BGR2RGB)
        cv2.imshow('Game preview', processedImage)
        cv2.waitKey(1)
            
    iterationEnd = time.time()
    print((iterationEnd * 1000) - (iterationStart * 1000))