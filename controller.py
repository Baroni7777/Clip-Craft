from fastapi.responses import Response
from fastapi import Request
from starlette.datastructures import UploadFile
import logging as log
import os
import aiofiles
import uuid
from utils.database_operations import DatabaseOperations
from content_creator import start_script_generation

DATABASE_OPERATIONS_SERVICE = DatabaseOperations()
class ApiController:

        async def upload_media(self, request: Request, response: Response):
            try:
                request_formdata = await request.form()
                unique_folder_name = str(uuid.uuid4())
                user_provided_media = False
                number_of_media_files = 0
                file_names = []
                # Convert request_formdata to a dictionary for easier access
                formdata_dict = dict(request_formdata)

                for key, value in formdata_dict.items():
                    if isinstance(value, UploadFile):
                        number_of_media_files += 1
                        file_names.append(value.filename)
                        file: UploadFile = value
                        await self.process_file(file=file, unique_folder_name=unique_folder_name)

                if number_of_media_files > 0:
                    user_provided_media = True
                
                # Extract user video options from the form data
                user_video_options = {
                    "title": formdata_dict.get("title"),
                    "description": formdata_dict.get("description"),
                    "template": formdata_dict.get("template"),
                    "duration": formdata_dict.get("duration"),
                    "orientation": formdata_dict.get("orientation"),
                    "user_has_provided_media": user_provided_media,
                    "user_media_path": unique_folder_name,
                    "uploaded_files_names": file_names
                }
                
                log.info(f"User video options: {user_video_options}")
                start_script_generation(user_video_options)
                
            except Exception as e:
                log.error(f"Error processing request: {e}")
                response.status_code = 500
                return {"status": "error", "message": "Internal server error"}
            
            return {"status": "ok"}
        
        
        
        async def process_file(self, file: UploadFile, unique_folder_name: str):
            log.info(f"Processing file: {file.filename}, size: {file.size}")
            save_directory = ".\\temp\\" + unique_folder_name + "\\media\\"
            os.makedirs(save_directory, exist_ok=True)
            file_path = os.path.join(save_directory, file.filename)
            
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            
            log.info(f"File saved to {file_path}")
            
        def test(self):
            #'DATABASE_OPERATIONS_SERVICE.create_document(collection_name="test", document_id="test", data=test_data)
            document = DATABASE_OPERATIONS_SERVICE.get_document(collection_name="test", document_id="test")
            return {"status": "ok"}

