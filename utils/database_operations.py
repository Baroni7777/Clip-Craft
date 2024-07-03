import firebase_admin
from firebase_admin import storage, credentials, firestore
import os
import logging as log
import datetime
from dotenv import load_dotenv

load_dotenv()
cred = credentials.Certificate(
    os.getcwd() + "\\credentials\\service_account_credentials.json"
)
firebase_admin.initialize_app(
    cred, {"storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")}
)

db = firestore.client()

bucket = storage.bucket()


class DatabaseOperations:

    #### BUCKET OPERATIONS ####

    def upload_file_by_path(self, file_path: str, file_name: str):
        try:
            log.info(f"Uploading file: {file_path}")
            blob = bucket.blob(file_name)
            blob.upload_from_filename(file_path)
            log.info(f"File {file_path} uploaded to {file_name}.")
        except Exception as e:
            log.error(f"Failed to upload file {file_path}: {e}")

    def download_file(
        self, key: str, destination_path: str = os.getcwd() + "\\bucket_files"
    ):
        try:
            log.info(f"Downloading file: {key} to {destination_path}")
            blob = bucket.blob(key)
            local_file_path = os.path.join(destination_path, key)
            os.makedirs(destination_path, exist_ok=True)
            blob.download_to_filename(local_file_path)
            log.info(f"File {key} downloaded to {destination_path}.")
        except Exception as e:
            log.error(f"Failed to download file {key}: {e}")

    def get_file_link(self, key: str, expiration: int = 40):
        try:
            log.info(f"Generating signed URL for file: {key}")
            blob = bucket.blob(key)
            url = blob.generate_signed_url(
                expiration=datetime.timedelta(minutes=expiration), method="GET"
            )

            log.info(f"Signed URL for {key}: {url}")
            return url
        except Exception as e:
            log.error(f"Failed to generate signed URL for {key}: {e}")
            return None

    #### NO SQL DB OPERATIONS ####

    def create_document(self, collection_name: str, document_id: str, data: dict):
        collection = db.collection(collection_name).document(document_id)
        collection.set(data)
        log.info("Data added to firestore successfully!")

    def get_document(self, collection_name: str, document_id: str):
        doc_ref = db.collection(collection_name).document(document_id)
        doc = doc_ref.get()
        if doc.exists:
            log.info(f"Document data: {doc.to_dict()}")
            return doc.to_dict()
        else:
            log.info("No such document!")
            return None
