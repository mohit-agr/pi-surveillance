from azure.storage.blob import BlobServiceClient
import cv2
import multiprocessing
import datetime

class ImageUploader:
    def __init__(self, image_stream):
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
        while True:
            img = self.image_stream.get()
            img_str = cv2.imencode('.jpg', img)[1].tobytes()
            blob_name = datetime.datetime.utcnow().isoformat(sep=' ', timespec='milliseconds') + '.jpg'
            self.blob_container_client.upload_blob(name=blob_name, data=img_str)
