import logging as log;
from fastapi import FastAPI, Request;
from fastapi.middleware.cors import CORSMiddleware;
from fastapi.responses import Response;
from controller import ApiController;
from dotenv import load_dotenv
import os
from models.edit_script_request_body import EditScriptRequestBody

app = FastAPI();
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=(os.getenv("ALLOWED_ORIGINS")),
    allow_methods=(os.getenv("ALLOWED_METHODS")),
    allow_headers=(os.getenv("ALLOWED_HEADERS")),
    allow_credentials=True,
)
API_CONTROLLER = ApiController();
log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S %z')

supported_file_formats = []

@app.get("/health-check", status_code=200, 
         summary="Health check endpoint to verify the service is up and running")
def health_check():
    return {"status": "ok"}

@app.post("/v1/upload-media", status_code=200, 
         summary="Upload media for use in the AI generated video")
async def upload_media(request: Request, response: Response):
    return await API_CONTROLLER.upload_media(request=request, response=response);

@app.post("/v1/edit-script", status_code=200, 
         summary="Edit the script for the AI generated video")
def edit_script(response: Response, body: EditScriptRequestBody):
    return API_CONTROLLER.edit_script(response=response, scenes=body.scenes);
   
   
@app.post("/test", status_code=200, 
         summary="Test Endpoint")
def test(request: Request, response: Response):
    return API_CONTROLLER.test();

