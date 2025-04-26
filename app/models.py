from pydantic import BaseModel
from enum import Enum

#######################################
#           Request Models
#######################################
class PromptRequest(BaseModel): # unused
    prompt: str

class ImageStatus(BaseModel): # unused
    id: str

class Places(Enum): # unused
    beach:str="beach"
    home:str="home"
    park:str="park"
    market:str="market"
    playground:str="playground"
    school:str="school"
    hospital:str="hospital"
    other:str="other"

class UserChoices(BaseModel): # unused
    time:str="morning"
    object:str="white girl"
    other:str="coconut trees"

#######################################
#           Response Models
#######################################

class GenerateImageResponse(BaseModel):
    message:str = "Image generation started."
    id:str
    status:str

class ImagineDevResponse(BaseModel):
    error:str|None
    id:str
    status:str
    progress:str|int|None
    prompt:str
    ref:str|None
    url:str|None
    user_created:str
    date_created:str
    upscaled_urls:list[str]|None
    model_type:str
    integration_id:str|None

class Prompt(BaseModel):
    text: str