import cv2
import time
import datetime
import threading
import numpy as np

timerSetter = 10

class VideoGetter:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.get, args=()).start()
        return self

    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def stop(self):
        self.stopped = true

def timer(motion_detected_event):
    global timerSetter
    while True:
        motion_detected_event.wait()
        # print (datetime.datetime.now().time(), "started new timer, thread Id", threading.get_ident())
        while timerSetter < 10:
            time.sleep(1)
            timerSetter += 1

        motion_detected_event.clear()

def detect_motion():
    global timerSetter
    video_getter = VideoGetter(0).start()
    frame1 = video_getter.frame
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    motion_detected_event = threading.Event()
    thread_timer = threading.Thread(name='timer', target=timer, args=(motion_detected_event,))
    thread_timer.start()
    while True:
        if not motion_detected_event.is_set():
            time.sleep(1)
        frame2 = video_getter.frame
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        deltaframe = cv2.absdiff(gray1, gray2)
        threshold = cv2.threshold(deltaframe, 100, 255, cv2.THRESH_BINARY)[1]
        if np.any(threshold == 255):
            motion_detected_event.set()
            timerSetter = 0
        # if motion_detected_event.is_set():
        #     # TODO: send notification and start streaming
        #     cv2.imshow('window', frame2)
        # if cv2.waitKey(1) == ord('q'):
        #     cv2.destroyAllWindows()
        #     thread_timer.join(1)
        #     break

        gray1 = gray2

if __name__ == '__main__':
    detect_motion()
