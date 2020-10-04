from azure.storage.blob import BlobServiceClient
import cv2
import multiprocessing
import queue
import os
from cryptography.fernet import Fernet
from concurrent.futures import ThreadPoolExecutor
import threading

class ImageUploader:
    def __init__(self, image_stream: multiprocessing.Queue):
        connection_string = open('../secrets/BlobStorageConnectionString.txt', 'r').read()
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = 'pi-surveillance'
        try:
            self.blob_container_client = blob_service_client.create_container(name=container_name)
        except Exception as e:
            self.blob_container_client = blob_service_client.get_container_client(container=container_name)

        self.image_stream = image_stream
        self.process = multiprocessing.Process(target=self.upload, args=())

    def start(self):
        self.process.start()

    def upload(self):
        if not os.path.exists('../secrets/key.key'):
            print ('Generating private key')
            key = Fernet.generate_key()
            file = open('../secrets/key.key', 'wb')
            file.write(key)
            file.close()

        with open('../secrets/key.key', 'rb') as f:
            self.fernet = Fernet(f.read())

        print ('started video uploader')
        with ThreadPoolExecutor(max_workers=5) as executor:
            while True:
                image_q = queue.Queue(10)
                while not image_q.full():
                    image_q.put(self.image_stream.get())

                executor.submit(self.worker, image_q)

    def worker(self, q):
        if q is None or q.empty():
            print ('Empty q detected. Returning early.')
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
