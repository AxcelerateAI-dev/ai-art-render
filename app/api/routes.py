from app.services.sending_generation_request import send_request
from app.services.prompt_generator import generate_prompt_gemini, generate_prompt_openai
import os
from fastapi import HTTPException, APIRouter, Request, Form

from app.models import (
    PromptRequest, ImageStatus, GenerateImageResponse,
    ImagineDevResponse, Places, UserChoices, Prompt
)
from app.utils import append_to_json_file, store_get_prompt
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

router = APIRouter()

@router.post("/ask_user/", response_model=Prompt, name="Generate Prompt")
def generate_promt(
    request: Request,
    place:str= Form(..., description="The imaginary or real place."),
    time:str= Form(..., description="The time, era or both."),
    object:str= Form(..., description="The object, person, or other thing"),
    other:str= Form(..., description="The other object along with the main object"),
    ):
    """
    Generate Prompt based on user choices
    """
    try:
        prompt = generate_prompt_openai(
            place=place,
            time=time,
            object=object,
            other=other
        )
        return Prompt(
            text=prompt['prompt']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

API_HOST = "cl.imagineapi.dev"
API_AUTH = f"Bearer {os.getenv('IMAGINE_DEV_API_KEY')}"
@router.post("/generate-image/", response_model=GenerateImageResponse, name="Send Image Generation Request")
def generate_image(
    prompt:str = Form(..., description="Prompt to midjourney for image generation")
    ):
    """
    Send Image Generation Request
    """
    data = {
        "prompt": prompt
    }
    headers = {
        'Authorization': API_AUTH,
        'Content-Type': 'application/json'
    }
    try:
        response = send_request('POST', '/items/images/', data, headers)
        return GenerateImageResponse(
            message="Image generation started.",
            id=response['data']['id'],
            status=response['data']['status']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-status/{image_id}", response_model=ImagineDevResponse, name="Check Status and Get Generated Images")
def check_status(image_id:str):
    """
    Check Status and Get Generated Images
    """
    headers = {
        'Authorization': API_AUTH,
        'Content-Type': 'application/json'
    }
    try:
        response = send_request('GET', f"/items/images/{image_id}", headers=headers)
        status = response['data']['status']
        if status in ['completed', 'failed']:
            append_to_json_file(response['data'])
        return ImagineDevResponse(**response['data'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))