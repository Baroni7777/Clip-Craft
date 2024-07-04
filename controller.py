from fastapi.responses import Response
from fastapi import Request
from starlette.datastructures import UploadFile
import os
import aiofiles
import uuid
import logging as log
from utils.database_operations import DatabaseOperations
from content_creator import ContentCreator


DATABASE_OPERATIONS_SERVICE = DatabaseOperations()


class ApiController:

    async def generate_video(self, request: Request, response: Response):
        # try:
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

        formdata_dict["media"] = media_files

        for key, value in formdata_dict.items():
            if key == "media":
                for media in value:
                    if isinstance(media, UploadFile):
                        file: UploadFile = media
                        if self.is_valid_file(file):
                            number_of_media_files += 1
                            file_names.append(file.filename)
                            await self.process_file(
                                file=file, unique_folder_name=unique_folder_name
                            )

        if number_of_media_files > 0:
            user_provided_media = True

        user_video_options = {
            "title": formdata_dict.get("title"),
            "description": formdata_dict.get("description"),
            "template": formdata_dict.get("template"),
            "duration": formdata_dict.get("duration"),
            "orientation": formdata_dict.get("orientation"),
            "use_stock_media": self.string_to_bool(
                formdata_dict.get("use_stock_media")
            ),
            "user_has_provided_media": user_provided_media,
            "user_media_path": unique_folder_name,
            "uploaded_files_names": file_names,
        }

        log.info(f"User video options: {user_video_options}")
        content_creator = ContentCreator(
            user_video_options=user_video_options,
            DATABASE_OPERATIONS_SERVICE=DATABASE_OPERATIONS_SERVICE,
        )
        response = content_creator.start_script_generation()

        # except Exception as e:
        #     log.error(f"Error processing request: {e}")
        #     response.status_code = 500
        #     return {"status": "error", "message": "Internal server error"}

        return {"script": response["script"], "signed_url": response["signed_url"]}

    def is_valid_file(self, file: UploadFile):
        if file.size > 0:
            return True
        return False

    async def process_file(self, file: UploadFile, unique_folder_name: str):
        log.info(f"Processing file: {file.filename}, size: {file.size}")
        save_directory = ".\\temp\\" + unique_folder_name + "\\media\\"
        os.makedirs(save_directory, exist_ok=True)
        file_path = os.path.join(save_directory, file.filename)

        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

    def string_to_bool(self, string: str):
        try:
            if string.lower() == "true":
                return True
            return False
        except Exception as e:
            log.error(f"Error converting string to bool: {e}")
            return False

    def edit_video(self, response: Response, scenes: any, final_video_url: str):
        edited_scene_index = 0
        for i in range(len(scenes)):
            if (
                "edited" in scenes[i]
                and self.string_to_bool(scenes[i]["edited"]) == True
            ):
                edited_scene_index = i
                break

        content_creator = ContentCreator(
            DATABASE_OPERATIONS_SERVICE=DATABASE_OPERATIONS_SERVICE
        )
        edited_video_signed_url = content_creator.edit_video(
            scene=scenes[edited_scene_index], final_video_url=final_video_url
        )

        return {"signed_url": edited_video_signed_url}
