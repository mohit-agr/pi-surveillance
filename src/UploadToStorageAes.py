from azure.storage.blob import BlobServiceClient
import cv2
import multiprocessing
import queue
import os
from cryptography.fernet import Fernet
from concurrent.futures import ThreadPoolExecutor
import threading

class ImageUploader:
    def __init__(self, image_stream: multiprocessing.Queue, motion_detected_event: multiprocessing.Event):
        connection_string = open('../secrets/BlobStorageConnectionString.txt', 'r').read()
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = 'pi-surveillance'
        try:
            self.blob_container_client = blob_service_client.create_container(name=container_name)
        except Exception as e:
            self.blob_container_client = blob_service_client.get_container_client(container=container_name)

        self.image_stream = image_stream
        self.motion_event = motion_detected_event

        if not os.path.exists('../secrets/key.key'):
            print('Generating private key')
            key = Fernet.generate_key()
            file = open('../secrets/key.key', 'wb')
            file.write(key)
            file.close()

        with open('../secrets/key.key', 'rb') as f:
            self.fernet = Fernet(f.read())

    def start(self):
        print ('started video uploader. Process ID:', multiprocessing.current_process().ident)
        with ThreadPoolExecutor(max_workers=5) as executor:
            while True:
                self.motion_event.wait()

                image_q = None
                while self.motion_event.is_set() or not self.image_stream.empty():
                    if image_q is None:
                        image_q = queue.Queue(10)

                    image_q.put(self.image_stream.get(timeout=10))

                    if image_q.full():
                        executor.submit(self.worker, image_q)
                        image_q = None

                if not image_q is None:
                    executor.submit(self.worker, image_q)

    def worker(self, q):
        if q is None or q.empty():
            return

        print ('Starting thread', threading.current_thread().ident)
        codec = 'MJPG'
        fourcc = cv2.VideoWriter_fourcc(*codec)

        video_id = None

        print ('Read images. Thread Id: ', threading.current_thread().ident)
        video_path = None
        writer = None
        while not q.empty():
            video_id, ts, frame = q.get()
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if writer is None:
                video_path = ts.isoformat(sep=' ', timespec='milliseconds') + ".avi"
                print(video_path)
                (h,w) = img.shape
                writer = cv2.VideoWriter(video_path, fourcc, 20, (w,h), False)

            writer.write(img)

        writer.release()
        with open(video_path, "rb") as f:
            data = f.read()

        encrypted_data = self.fernet.encrypt(data)
        print ('Uploading video. Thread Id: ', threading.current_thread().ident)
        self.upload_to_blob(video_id, video_path + ".encrypted", encrypted_data)
        os.remove(video_path)

    def upload_to_blob(self, video_id, video_file, data):
        video_blob_path = "videos/" + video_id + "/" + video_file
        self.blob_container_client.upload_blob(name=video_blob_path, data=data)
