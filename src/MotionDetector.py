import cv2
import time
import datetime
from multiprocessing import Process, Event, Value
import numpy as np

def Timer(timerSetter, motionDetectedEvent):
    while True:
        motionDetectedEvent.wait()
        # print (datetime.datetime.now().time(), "started new timer")
        while timerSetter.value < 10:
            time.sleep(1)
            timerSetter.value += 1
        motionDetectedEvent.clear()

def DetectMotion(cap):
    cap.read()
    cap.read()
    ret1,frame1= cap.read()
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    timerSetter = Value('i', 10)
    motionDetectedEvent = Event()
    timerProcess = Process(name='timer', target=Timer, args=(timerSetter,motionDetectedEvent,))
    timerProcess.start()
    while True:
        if timerSetter.value >= 10:
            cv2.destroyAllWindows()
            time.sleep(1)
        ret2,frame2=cap.read()
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        deltaframe = cv2.absdiff(gray1, gray2)
        threshold = cv2.threshold(deltaframe, 100, 255, cv2.THRESH_BINARY)[1]
        if np.any(threshold == 255):
            motionDetectedEvent.set()
            timerSetter.value = 0
        if motionDetectedEvent.is_set():
            # TODO: send notification and start streaming
        #     cv2.imshow('window', frame2)
        #     cv2.waitKey(20)

        gray1 = gray2

if __name__ == '__main__':
    cap = cv2.VideoCapture(0)
    DetectMotion(cap)
