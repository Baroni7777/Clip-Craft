from fastapi.responses import Response
from fastapi import Request
from starlette.datastructures import UploadFile
import logging as log
import os
import aiofiles
import uuid
from utils.database_operations import DatabaseOperations
from content_creator import ContentCreator
DATABASE_OPERATIONS_SERVICE = DatabaseOperations()

class ApiController:

        async def upload_media(self, request: Request, response: Response):
            try:
                request_formdata = await request.form()
                unique_folder_name = str(uuid.uuid4())
                user_provided_media = False
                number_of_media_files = 0
                file_names = []
                
                formdata_dict = {}
                media_files = []

                for key, value in request_formdata.multi_items():
                    if key == "media":
                        media_files.append(value)
                    else:
                        formdata_dict[key] = value

                # Add media files to the dictionary
                formdata_dict["media"] = media_files
                
                for key, value in formdata_dict.items():
                    if key == "media":
                        for media in value:
                              if isinstance(media, UploadFile):
                                file: UploadFile = media
                                if self.is_valid_file(file):
                                    number_of_media_files += 1
                                    file_names.append(file.filename)
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
                    "uploaded_files_names": file_names,
                    "use_stock_media": self.string_to_bool(formdata_dict.get("use_stock_media")),
                }
                
                log.info(f"User video options: {user_video_options}")
                content_creator = ContentCreator(user_video_options=user_video_options, DATABASE_OPERATIONS_SERVICE=DATABASE_OPERATIONS_SERVICE)
                response = content_creator.start_script_generation()
                
            except Exception as e:
                log.error(f"Error processing request: {e}")
                response.status_code = 500
                return {"status": "error", "message": "Internal server error"}
            
            return {"scenes": response["scenes"],"signed_url": response["signed_url"]}
            
        
        def is_valid_file(self, file: UploadFile):
            if file.size > 0:
                return True
            return False

        async def process_file(self, file: UploadFile, unique_folder_name: str):
            log.info(f"Processing file: {file.filename}, size: {file.size}")
            save_directory = ".\\temp\\" + unique_folder_name + "\\media\\"
            os.makedirs(save_directory, exist_ok=True)
            file_path = os.path.join(save_directory, file.filename)
            
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            
            log.info(f"File saved to {file_path}")
            
        
        def string_to_bool(self, string: str):
            try:
                if string.lower() == "true":
                    return True
                return False
            except Exception as e:
                log.error(f"Error converting string to bool: {e}")
                return False
        
        
        def edit_script(self, response: Response, scenes: any):
            log.info(scenes)
            return {"status": "ok"}

