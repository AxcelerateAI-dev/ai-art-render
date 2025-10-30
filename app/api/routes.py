import json
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

# --- Constants ---
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
ALLOWED_AUDIO_MIME_TYPES = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/mp3", "audio/x-wav", "audio/aac"]
TEMP_AUDIO_BASE_DIR = "temp_audio_sessions"

# --- Routes ---
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
    if style == Style.OTHER and not custom_style:
        raise HTTPException(status_code=400, detail="custom_style is required when style is 'other'")
    elif style == Style.OTHER:
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

@router.post("/ask_user_with_img/", response_model=Prompt, name="Generate Prompt with Image")
async def generate_prompt_with_image(
    place: str = Form(..., description="The imaginary or real place."),
    time: str = Form(..., description="The time, era or both."),
    object: str = Form(..., description="The object, person, or other thing."),
    action: str = Form(..., description="What are they doing?"),
    style: Style = Form(..., description="The style for the image."),
    other: str = Form(..., description="Other objects along with the main object."),
    custom_style: str = Form(None, description="Describe a custom style if 'other' is selected."),
    ref_img: UploadFile = File(..., description="A reference image to inspire the new prompt.")
):
    """
    Generates a prompt by analyzing a reference image.
    """
    image_bytes = await ref_img.read()
    mime_type = magic.from_buffer(image_bytes, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Please upload a valid image. Detected: {mime_type}")

    final_style = style.value
    if style == Style.OTHER and not custom_style:
        raise HTTPException(status_code=400, detail="custom_style is required when style is 'other'")
    elif style == Style.OTHER:
        final_style = custom_style

    try:
        prompt_data = generate_prompt_openai(
            place=place, time=time, object=object,
            action=action, style=final_style, other=other,
            image_bytes=image_bytes,
            mime_type=mime_type
        )
        logger.info(f"Generated prompt with image inspiration: {prompt_data['prompt']}")
        return Prompt(text=prompt_data['prompt'])
    except Exception as e:
        logger.error(f"Error during prompt generation with image: {e}")
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

async def download_audio_from_url(url: str) -> bytes:
    """Asynchronously downloads audio content from a URL."""
    try:
        url = f"https:{url}".strip()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                logger.info(f"Successfully downloaded audio from {url}")
                return content
    except aiohttp.ClientError as e:
        logger.error(f"Network or client error during download of {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Network or client error while downloading from URL.")

def save_audio_to_session(session_id: str, file_content: bytes, original_filename: str, source_url: str = None):
    """Saves audio content to a session directory after validation, prevents duplicate uploads."""
    session_dir = os.path.join(TEMP_AUDIO_BASE_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Path for metadata tracking (URLs already used)
    metadata_file = os.path.join(session_dir, "metadata.json")

    # Load existing metadata (if any)
    metadata = {"urls": []}
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
        except Exception:
            logger.warning(f"Could not read metadata.json for session {session_id}, resetting it.")
            metadata = {"urls": []}

    # If a URL is provided, check for duplicates
    if source_url and source_url in metadata["urls"]:
        raise HTTPException(
            status_code=400,
            detail=f"The provided URL has already been added for this session."
        )

    # Validate MIME type
    mime_type = magic.from_buffer(file_content, mime=True)
    if mime_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio file type. Allowed types are: {', '.join(ALLOWED_AUDIO_MIME_TYPES)}. Detected: {mime_type}"
        )

    # Save audio file
    _, extension = os.path.splitext(original_filename)
    if not extension:
        extension = ".mp3"

    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = os.path.join(session_dir, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        logger.info(f"Audio file '{original_filename}' saved for session '{session_id}' at {file_path}")

        # Record the URL in metadata (if applicable)
        if source_url:
            metadata["urls"].append(source_url)
            with open(metadata_file, "w") as f:
                json.dump(metadata, f)
    except Exception as e:
        logger.error(f"Error saving audio file for session '{session_id}': {e}")
        raise HTTPException(status_code=500, detail="Error saving audio file.")

@router.post("/upload-audio-file-to-session/", name="Upload Audio File to Session")
async def upload_audio_file_to_session(
    session_id: str = Form(..., description="Unique identifier for the audio session."),
    audio_file: UploadFile = File(..., description="Audio file to upload."),
):
    """
    Uploads a single audio file from your computer and associates it with a session ID.
    """
    file_content = await audio_file.read()
    save_audio_to_session(session_id, file_content, audio_file.filename)
    return {"message": f"Audio file '{audio_file.filename}' uploaded successfully for session '{session_id}'."}

@router.post("/add-audio-url-to-session/", name="Add Audio URL to Session")
async def add_audio_url_to_session(
    session_id: str = Form(..., description="Unique identifier for the audio session."),
    audio_url: str = Form(..., description="URL of an audio file to download and add."),
):
    """
    Downloads a single audio file from a URL and associates it with a session ID.
    Prevents adding the same URL twice in the same session.
    """
    file_content = await download_audio_from_url(audio_url)
    original_filename = os.path.basename(audio_url.split('?')[0]) or "audio.mp3"
    save_audio_to_session(session_id, file_content, original_filename, source_url=audio_url)
    return {"message": f"Audio from URL added successfully for session '{session_id}'."}

@router.post("/merge-audio-by-session/", name="Merge Audio by Session")
async def merge_audio_by_session(
    session_id: str = Form(..., description="Unique identifier for the audio session.")
):
    """
    Finds all audio files for a given session ID, merges them sequentially,
    and returns the merged file. All session files are removed after the response is sent.
    """
    session_dir = os.path.join(TEMP_AUDIO_BASE_DIR, session_id)
    if not os.path.exists(session_dir) or not os.listdir(session_dir):
        raise HTTPException(status_code=404, detail=f"No audio files found for session ID '{session_id}'.")

    supported_extensions = tuple(f".{ext.split('/')[-1].lower()}" for ext in ALLOWED_AUDIO_MIME_TYPES if '/' in ext)
    audio_files_in_dir = [f for f in os.listdir(session_dir) if f.lower().endswith(supported_extensions)]
    
    if not audio_files_in_dir:
        raise HTTPException(status_code=404, detail=f"No supported audio files found for session ID '{session_id}'.")

    audio_files = sorted([os.path.join(session_dir, f) for f in audio_files_in_dir], key=os.path.getctime)

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
        
        task = BackgroundTask(shutil.rmtree, session_dir)
        return FileResponse(merged_file_path, media_type="audio/mpeg", filename=merged_filename_final, background=task)
    except Exception as e:
        logger.error(f"Error merging audio for session '{session_id}': {e}")
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        raise HTTPException(status_code=500, detail=f"Error merging audio files: {e}")

