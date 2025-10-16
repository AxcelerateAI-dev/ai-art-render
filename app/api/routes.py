import magic
import uuid
import os
from app.services.prompt_generator import generate_prompt_gemini, generate_prompt_openai
from app.services.sending_generation_request import send_generation_request, check_generation_status
from fastapi import HTTPException, APIRouter, Form, UploadFile, File
from app.models import (
    Style,
    GenerateImageResponse,
    ImagineDevResponse,
    Prompt,
)
from loguru import logger
from app.utils import append_to_json_file
from dotenv import load_dotenv

load_dotenv(override=True)
router = APIRouter()

ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
TEMP_IMAGE_DIR = "temp_images"

@router.post("/ask_user/", response_model=Prompt, name="Generate Initial Prompt")
async def generate_initial_prompt(
    place: str = Form(..., description="The imaginary or real place."),
    time: str = Form(..., description="The time, era or both."),
    object: str = Form(..., description="The object, person, or other thing."),
    action: str = Form(..., description="What are they doing?"),
    style: Style = Form(..., description="The style for the image."),
    other: str = Form(..., description="Other objects along with the main object."),
    custom_style: str = Form(None, description="Describe a custom style if 'other' is selected."),
):
    """
    Generates an initial prompt based on user's text choices. No image is used here.
    """
    final_style = style.value
    if style == Style.other and not custom_style:
        raise HTTPException(status_code=400, detail="custom_style is required when style is 'other'")
    elif style == Style.other:
        final_style = custom_style
    try:
        prompt_data = generate_prompt_openai(
            place=place, time=time, object=object,
            action=action, style=final_style, other=other
        )
        logger.info(f"Generated initial prompt: {prompt_data['prompt']}")
        return Prompt(text=prompt_data['prompt'])
    except Exception as e:
        logger.error(f"Error during initial prompt generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-prompt/", response_model=Prompt, name="Update Prompt with Image")
async def update_prompt_with_image(
    previous_prompt: str = Form(..., description="The previously generated prompt from the /ask_user endpoint."),
    ref_img: UploadFile = File(..., description="A reference image to inspire the new prompt.")
):
    """
    Updates a prompt by analyzing a reference image.
    """
    image_bytes = await ref_img.read()
    mime_type = magic.from_buffer(image_bytes, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Please upload a valid image. Detected: {mime_type}")

    try:
        prompt_data = generate_prompt_openai(
            previous_prompt=previous_prompt,
            image_bytes=image_bytes,
            mime_type=mime_type
        )
        logger.info(f"Updated prompt with image inspiration: {prompt_data['prompt']}")
        return Prompt(text=prompt_data['prompt'])
    except Exception as e:
        logger.error(f"Error during prompt update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-image/", response_model=GenerateImageResponse, name="Send Image Generation Request")
async def generate_image(
    prompt: str = Form(..., description="The final prompt for image generation (can be from /ask_user or /update-prompt)."),
):
    """
    Generates an image from a final prompt.
    """
    try:
        response = await send_generation_request(prompt)
        return GenerateImageResponse(
            message="Image generation started.",
            id=response['data']['id'],
            status=response['data']['status']
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Failed to send image generation request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-status/{image_id}", response_model=ImagineDevResponse, name="Check Status and Get Generated Images")
async def check_status(image_id: str):
    """
    Check Status and Get Generated Images.
    """
    try:
        response = await check_generation_status(image_id)
        status = response['data']['status']
        if status in ['completed', 'failed']:
            append_to_json_file(response['data'])
        return ImagineDevResponse(**response['data'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))