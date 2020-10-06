import cv2
import time
import threading
import numpy as np
import multiprocessing
import datetime
from src.UploadToStorageAes import ImageUploader

timerSetter = 10
video_id = None

class VideoGetter:
    def __init__(self, src, motion_detected_event, img_queue):
        self.stream = cv2.VideoCapture(src)
        self.motion_detected_event = motion_detected_event
        self.image_queue = img_queue
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.get, args=()).start()
        return self

    def get(self):
        global video_id
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                if self.motion_detected_event.is_set():
                    self.image_queue.put((video_id, datetime.datetime.utcnow(), self.frame))
                (self.grabbed, self.frame) = self.stream.read()

    def stop(self):
        self.stopped = True

def timer(motion_detected_event):
    global timerSetter, video_id
    while True:
        motion_detected_event.wait()
        video_id = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        print (video_id, 'starting new timer. Thread Id: ', threading.get_ident())
        while timerSetter < 10:
            time.sleep(1)
            timerSetter += 1

        print ('No motion detected for last 10 seconds')
        motion_detected_event.clear()

def upload_images(img_queue: multiprocessing.Queue, motion_detected_event: multiprocessing.Event):
    uploader = ImageUploader(img_queue, motion_detected_event)
    uploader.start()

def detect_motion():
    global timerSetter
    motion_detected_event = multiprocessing.Event()
    img_queue = multiprocessing.Queue()

    video_getter = VideoGetter(0, motion_detected_event, img_queue).start()
    threading.Thread(name='timer', target=timer, args=(motion_detected_event,)).start()
    multiprocessing.Process(name='image_uploader', target=upload_images, args=(img_queue,motion_detected_event,)).start()

    frame1 = video_getter.frame
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)

    while True:
        if not motion_detected_event.is_set():
            time.sleep(1)
        frame2 = video_getter.frame
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        delta_frame = cv2.absdiff(gray1, gray2)
        threshold = cv2.threshold(delta_frame, 50, 255, cv2.THRESH_BINARY)[1]
        if np.any(threshold == 255):
            motion_detected_event.set()
            timerSetter = 0
        # if motion_detected_event.is_set():
        #     # TODO: send notification
        #     cv2.imshow('window', frame2)
        # if cv2.waitKey(1) == ord('q'):
        #     cv2.destroyAllWindows()
        #     thread_timer.join(1)
        #     break

        gray1 = gray2

if __name__ == '__main__':
    detect_motion()
