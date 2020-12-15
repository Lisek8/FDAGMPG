import time
from subprocess import Popen, PIPE

process = Popen("node ../frame-grabber-and-input/dist/main.js", stdin=PIPE, stdout=PIPE)
 
while True:
    frameGrabberInfo = process.stdout.readline().strip()
    if (frameGrabberInfo != b'' and frameGrabberInfo.decode() == 'FRAMEGRABBER:READY'):
        time.sleep(5)
        break
    time.sleep(1)

process.stdin.write(("p|").encode())
while True:
    iterationStart = time.time()
    process.stdin.write(("d\n").encode())
    process.stdin.flush()
    frameGrabberInfo = process.stdout.readline().strip()
    if (frameGrabberInfo != b''):
        dataToBePassedToAI = frameGrabberInfo.decode()
    iterationEnd = time.time()
    print((iterationEnd * 1000) - (iterationStart * 1000))
    time.sleep(0.25)