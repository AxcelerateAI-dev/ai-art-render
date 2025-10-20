import magic
import uuid
import os
import aiohttp
import asyncio
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

import shutil 
from starlette.background import BackgroundTask

from fastapi.responses import FileResponse
from pydub import AudioSegment
from tempfile import TemporaryDirectory


load_dotenv(override=True)
router = APIRouter()

ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
TEMP_IMAGE_DIR = "temp_images"

TEMP_AUDIO_BASE_DIR = "temp_audio_sessions"
ALLOWED_AUDIO_MIME_TYPES = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp3", "audio/aac"] # Add more common audio types as needed


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
    
@router.post("/upload-audio-to-session/", name="Upload Audio to Session")
async def upload_audio_to_session(
    session_id: str = Form(..., description="Unique identifier for the audio session."),
    audio_file: UploadFile = File(..., description="Audio file to upload.")
):
    """
    Uploads a single audio file and associates it with a session ID.
    The file is saved in a session-specific temporary directory.
    This endpoint can be called multiple times for the same session_id.
    """
    session_dir = os.path.join(TEMP_AUDIO_BASE_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    file_content = await audio_file.read()
    mime_type = magic.from_buffer(file_content, mime=True)
    
    if mime_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid audio file type. Allowed types are: {', '.join(ALLOWED_AUDIO_MIME_TYPES)}. Detected: {mime_type}"
        )
    
    original_filename = audio_file.filename
    _, extension = os.path.splitext(original_filename)
    if not extension:
        extension = ".mp3"

    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = os.path.join(session_dir, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        logger.info(f"Audio file '{original_filename}' uploaded to session '{session_id}' at {file_path}")
        return {"message": f"Audio file '{original_filename}' uploaded successfully for session '{session_id}'."}
    except Exception as e:
        logger.error(f"Error saving audio file for session '{session_id}': {e}")
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir)
                logger.info(f"Cleaned up temporary audio session directory due to save error: {session_dir}")
            except Exception as cleanup_e:
                logger.error(f"Error during cleanup after save error for {session_dir}: {cleanup_e}")
        raise HTTPException(status_code=500, detail=f"Error saving audio file: {e}")


@router.post("/merge-audio-by-session/", name="Merge Audio by Session")
async def merge_audio_by_session(
    session_id: str = Form(..., description="Unique identifier for the audio session.")
):
    """
    Finds all audio files for a given session ID, merges them sequentially,
    and returns the merged file. All session files are then removed after the response is sent.
    """
    session_dir = os.path.join(TEMP_AUDIO_BASE_DIR, session_id)
    if not os.path.exists(session_dir) or not os.listdir(session_dir):
        raise HTTPException(status_code=404, detail=f"No audio files found for session ID '{session_id}'.")
    supported_extensions = (".mp3", ".wav", ".ogg", ".aac")
    audio_files_in_dir = [f for f in os.listdir(session_dir) if f.lower().endswith(supported_extensions)]
    if not audio_files_in_dir:
        raise HTTPException(status_code=404, detail=f"No supported audio files found for session ID '{session_id}'.")
    audio_files = sorted([os.path.join(session_dir, f) for f in audio_files_in_dir])

    combined_audio = AudioSegment.empty()
    try:
        for file_path in audio_files:
            try:
                audio = AudioSegment.from_file(file_path)
                combined_audio += audio
            except Exception as e:
                logger.warning(f"Could not load audio file {file_path} for session {session_id}: {e}. Skipping.")
        if combined_audio.duration_seconds == 0:
             raise HTTPException(status_code=400, detail=f"No audio data could be processed for session '{session_id}'.")
        merged_filename_final = f"merged_audio_{session_id}.mp3"
        merged_file_path = os.path.join(session_dir, merged_filename_final) 

        combined_audio.export(merged_file_path, format="mp3")
        logger.info(f"Merged audio for session '{session_id}' created at {merged_file_path}")
        task = BackgroundTask(shutil.rmtree, session_dir)
        return FileResponse(
            merged_file_path,
            media_type="audio/mpeg",
            filename=merged_filename_final,
            background=task
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error merging audio for session '{session_id}': {e}")
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir)
                logger.info(f"Cleaned up temporary audio session directory due to error: {session_dir}")
            except Exception as cleanup_e:
                logger.error(f"Error during cleanup after merge error for {session_dir}: {cleanup_e}")
        raise HTTPException(status_code=500, detail=f"Error merging audio files: {e}")