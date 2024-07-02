from pydantic import BaseModel

class EditScriptRequestBody(BaseModel):
    scenes: list
    signed_url: str