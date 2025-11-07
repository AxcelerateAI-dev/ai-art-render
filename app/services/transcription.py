import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from loguru import logger

load_dotenv(override=True)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def transcribe_audio(file_path: str) -> str:
    """
    Transcribes an audio file using OpenAI's Whisper model asynchronously.
    
    Args:
        file_path: The local path to the audio file.
        
    Returns:
        The transcribed text as a string, or an error message if transcription fails.
    """
    if not os.path.exists(file_path):
        logger.error(f"Transcription failed: File not found at {file_path}")
        return "Error: Audio file not found for transcription."

    try:
        with open(file_path, "rb") as audio_file:
            logger.info(f"Starting transcription for {file_path}...")
            
            # The new openai SDK versions handle file objects correctly
            transcription_response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            
            # For response_format="text", the result is a plain string
            transcription_text = transcription_response
            logger.success(f"Transcription successful for {file_path}")
            return transcription_text
    except Exception as e:
        logger.error(f"An error occurred during transcription: {e}")
        return f"Error during transcription: {e}"