from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str

class ImageStatus(BaseModel):
    id: str