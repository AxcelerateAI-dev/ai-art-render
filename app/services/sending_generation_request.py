import os
import httpx
import traceback
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

API_HOST = "cl.imagineapi.dev"
API_KEY = os.getenv("IMAGINE_DEV_API_KEY")

if not API_KEY:
    logger.warning("⚠️ IMAGINE_DEV_API_KEY is not set. API requests will fail!")

API_AUTH = f"Bearer {API_KEY}" if API_KEY else ""
BASE_URL = f"https://{API_HOST}"

logger.add(
    "logs.log",
    level="DEBUG",
    backtrace=True,
    diagnose=True,
    rotation="10 MB",
    retention="10 days",
)


async def send_generation_request(prompt: str) -> dict:
    """
    Sends a request to the Imagine API to generate an image using only a text prompt.
    Includes detailed debugging logs for failed requests.
    """
    headers = {
        "Authorization": API_AUTH,
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/items/images/"
    json_data = {"prompt": prompt}

    logger.debug(f"POST {url} with headers={headers} and json={json_data}")

    async with httpx.AsyncClient() as client:
        for attempt in range(3):
            try:
                logger.info(f"Attempt {attempt + 1}: Sending generation request.")
                response = await client.post(url, headers=headers, json=json_data)
                response.raise_for_status()
                logger.success("✅ Image generation request successful.")
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"❌ HTTP error ({e.response.status_code}): {e.response.text}"
                )
                logger.error(traceback.format_exc())
                if attempt == 2:
                    raise

            except httpx.RequestError as e:
                # Catches network/DNS/timeout issues
                logger.error(f"🌐 RequestError: {type(e).__name__} - {e}")
                logger.error(traceback.format_exc())
                if attempt == 2:
                    raise

            except Exception as e:
                logger.error(f"💥 Unexpected error: {type(e).__name__} - {e}")
                logger.error(traceback.format_exc())
                if attempt == 2:
                    raise


async def check_generation_status(image_id: str) -> dict:
    """
    Checks the status of an image generation job using httpx with detailed debugging logs.
    """
    headers = {"Authorization": API_AUTH}
    url = f"{BASE_URL}/items/images/{image_id}"

    logger.debug(f"GET {url} with headers={headers}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            logger.success(f"✅ Status check successful for image_id={image_id}")
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ HTTP error during status check: {e.response.status_code} - {e.response.text}"
            )
            logger.error(traceback.format_exc())
            raise

        except httpx.RequestError as e:
            logger.error(f"🌐 RequestError during status check: {type(e).__name__} - {e}")
            logger.error(traceback.format_exc())
            raise

        except Exception as e:
            logger.error(f"💥 An error occurred during status check: {type(e).__name__} - {e}")
            logger.error(traceback.format_exc())
            raise

if __name__ == "__main__":
    import asyncio

    async def test():
        prompt = "A futuristic city skyline at sunset, cinematic lighting."
        try:
            gen_resp = await send_generation_request(prompt)
            logger.info(f"Response: {gen_resp}")

            image_id = gen_resp.get("data", {}).get("id") or gen_resp.get("id")
            if image_id:
                status = await check_generation_status(image_id)
                logger.info(f"Status response: {status}")
            else:
                logger.warning("No image_id returned from generation response.")
        except Exception as e:
            logger.error(f"Test failed: {e}")
            logger.error(traceback.format_exc())

    asyncio.run(test())
