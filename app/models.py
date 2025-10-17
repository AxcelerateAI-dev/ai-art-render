from pydantic import BaseModel, Field
from enum import Enum

#######################################
#           Request Models
#######################################

class Style(str, Enum):
    PHOTOREALISTIC = "Photorealistic"
    SURREALIST = "Surrealist"
    VINTAGE_COMIC_BOOK = "Vintage Comic Book"
    WATERCOLOUR = "Watercolour"
    IMPRESSIONIST = "Impressionist"
    CLAYMATION = "Claymation"
    CUBISM = "Cubism"
    FUTURISM = "Futurism"
    BAROQUE = "Baroque"
    OTHER = "Other"

#######################################
#           Response Models
#######################################

class GenerateImageResponse(BaseModel):
    message: str = "Image generation started."
    id: str
    status: str

class ImagineDevResponse(BaseModel):
    error: str | None
    id: str
    status: str
    progress: str | int | None
    prompt: str
    ref: str | None
    url: str | None
    user_created: str
    date_created: str
    upscaled_urls: list[str] | None
    model_type: str
    integration_id: str | None

class Prompt(BaseModel):
    text: str
