import httpx
import os
from loguru import logger

API_HOST = "cl.imagineapi.dev"
API_AUTH = f"Bearer {os.getenv('IMAGINE_DEV_API_KEY')}"
BASE_URL = f"https://{API_HOST}"

# async def send_generation_request(prompt: str) -> dict:
#     """
#     Sends a request to the Imagine API to generate an image using only a text prompt.
#     """
#     headers = {'Authorization': API_AUTH, 'Content-Type': 'application/json'}
#     url = f"{BASE_URL}/items/images/"
#     json_data = {'prompt': prompt}

#     async with httpx.AsyncClient() as client:
#         try:
#             logger.info("Sending generation request with prompt only.")
#             response = await client.post(url, headers=headers, json=json_data, timeout=5)
#             if not response.raise_for_status:
#                 return response.json()
#             if response.raise_for_status:
#                 for i in range(1,3):
#                     print(f"{i} time retry")
#                     response = await client.post(url, headers=headers, json=json_data)
#                     if response.raise_for_status():
#                         print(f"Sucess at {i}")
#                         break

#         except httpx.HTTPStatusError as e:
#             logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
#             raise
#         except Exception as e:
#             logger.error(f"An error occurred while sending generation request: {e}")
#             raise

async def send_generation_request(prompt: str) -> dict:
    """
    Sends a request to the Imagine API to generate an image using only a text prompt.
    """
    headers = {
        'Authorization': API_AUTH,
        'Content-Type': 'application/json'
    }
    url = f"{BASE_URL}/items/images/"
    json_data = {'prompt': prompt}

    async with httpx.AsyncClient() as client:
        for attempt in range(3): 
            try:
                logger.info(f"Attempt {attempt + 1}: Sending generation request.")
                response = await client.post(url, headers=headers, json=json_data)
                response.raise_for_status()
                logger.success("Image generation request successful.")
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error ({e.response.status_code}): {e.response.text}")
                if attempt == 2:
                    raise  

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt == 2:
                    raise

async def check_generation_status(image_id: str) -> dict:
    """
    Checks the status of an image generation job using httpx.
    """
    headers = {'Authorization': API_AUTH}
    url = f"{BASE_URL}/items/images/{image_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during status check: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"An error occurred during status check: {e}")
            raise