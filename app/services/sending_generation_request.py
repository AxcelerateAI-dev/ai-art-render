import httpx
import os
from loguru import logger

API_HOST = "cl.imagineapi.dev"
API_AUTH = f"Bearer {os.getenv('IMAGINE_DEV_API_KEY')}"
BASE_URL = f"https://{API_HOST}"

async def send_generation_request(prompt: str) -> dict:
    """
    Sends a request to the Imagine API to generate an image using only a text prompt.
    """
    headers = {'Authorization': API_AUTH, 'Content-Type': 'application/json'}
    url = f"{BASE_URL}/items/images/"
    json_data = {'prompt': prompt}

    async with httpx.AsyncClient() as client:
        try:
            logger.info("Sending generation request with prompt only.")
            response = await client.post(url, headers=headers, json=json_data, timeout=45.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"An error occurred while sending generation request: {e}")
            raise

async def check_generation_status(image_id: str) -> dict:
    """
    Checks the status of an image generation job using httpx.
    """
    headers = {'Authorization': API_AUTH}
    url = f"{BASE_URL}/items/images/{image_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during status check: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"An error occurred during status check: {e}")
            raise