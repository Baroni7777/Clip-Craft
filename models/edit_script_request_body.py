from pydantic import BaseModel

class EditScriptRequestBody(BaseModel):
    scenes: list