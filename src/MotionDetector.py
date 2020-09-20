import cv2
import time
import datetime
import threading
import numpy as np
import flask

timerSetter = 10
app = flask.Flask(__name__)
video_getter = VideoGetter(0)

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
        if motion_detected_event.is_set():
            # TODO: send notification and start streaming
            cv2.imshow('window', frame2)
        if cv2.waitKey(1) == ord('q'):
            cv2.destroyAllWindows()
            thread_timer.join(1)
            break

        gray1 = gray2

@app.route('/')
def index():
   """Video streaming ."""
   return flask.render_template('index.html')

def gen():
   """Video streaming generator function."""
   while True:
       frame = video_getter.frame
       cv2.imwrite('pic.jpg', frame)
       yield (b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + open('pic.jpg', 'rb').read() + b'\r\n')

@app.route('/video_feed')
def video_feed():
   """Video streaming route. Put this in the src attribute of an img tag."""
   return flask.Response(gen(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    video_getter.start()
    app.run(host='0.0.0.0', debug=True, threaded=True, )
    detect_motion()
