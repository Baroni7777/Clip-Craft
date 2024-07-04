from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import os
import logging as log
from dotenv import load_dotenv
from controller import ApiController
from models.edit_script_request_body import EditScriptRequestBody
from fastapi.middleware.gzip import GZipMiddleware

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=(os.getenv("ALLOWED_ORIGINS")),
    allow_methods=(os.getenv("ALLOWED_METHODS")),
    allow_headers=(os.getenv("ALLOWED_HEADERS")),
    allow_credentials=True,
)
API_CONTROLLER = ApiController()
log.basicConfig(
    level=log.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %z",
)

supported_file_formats = []


@app.get(
    "/health-check",
    status_code=200,
    summary="Health check endpoint to verify the service is up and running",
)
def health_check():
    return {"status": "ok"}


@app.post(
    "/v1/generate-video",
    status_code=200,
    summary="Generate scenes for the AI generated video",
)
async def generate_video(request: Request, response: Response):
    return await API_CONTROLLER.generate_video(request=request, response=response)


@app.post(
    "/v1/edit-video",
    status_code=200,
    summary="Edit the scenes for the AI generated video",
)
def edit_video(response: Response, body: EditScriptRequestBody):
    return API_CONTROLLER.edit_video(
        response=response, scenes=body.scenes, final_video_url=body.signed_url
    )
