from azure.storage.blob import BlobServiceClient
import cv2
import multiprocessing
import threading
import queue

class ImageUploader:
    def __init__(self, image_stream: multiprocessing.Queue):
        connection_string = open('../secrets/BlobStorageConnectionString.txt', 'r').read()
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = 'pi-surveillance'
        self.read_lock = threading.Lock()

        try:
            self.blob_container_client = blob_service_client.create_container(name=container_name)
        except Exception as e:
            self.blob_container_client = blob_service_client.get_container_client(container=container_name)

        self.image_stream = image_stream

    def start(self):
        print ('started video uploader')
        for i in range(10):
            t = threading.Thread(target=self.worker, name=i)
            t.start()

    def worker(self):
        print ('Starting thread', threading.current_thread().name)
        q = queue.Queue(10)
        while True:
            video_id = None
            ts = None

            self.read_lock.acquire()
            while not q.full():
                video_id, ts, img = self.image_stream.get()
                q.put(img)
            self.read_lock.release()

            print ('Read images. Thread Id: ', threading.current_thread().name)
            codec = 'MJPG'
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = None

            video_path = ts.isoformat(sep=' ', timespec='milliseconds') + ".avi"
            print (video_path)
            while not q.empty():
                frame = q.get()
                if writer is None:
                    (h, w) = frame.shape[:2]
                    writer = cv2.VideoWriter(video_path, fourcc, 20, (w, h), True)

                writer.write(frame)

            writer.release()
            print ('Uploading video. Thread Id: ', threading.current_thread().name)
            self.upload_to_blob(video_id, video_path)

    def upload_to_blob(self, video_id, video_file):
        video_blob_path = "videos/" + video_id + "/" + video_file
        with open(video_file, "rb") as vfile:
            self.blob_container_client.upload_blob(name=video_blob_path, data=vfile)
