import logging as log
import firebase_admin
from firebase_admin import credentials, firestore
import os

cred = credentials.Certificate(os.getcwd() + "\\credentials\\service_account_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client();

class DatabaseOperations:
    
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