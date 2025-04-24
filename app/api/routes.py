from app.services.send_generation_request import send_request
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, APIRouter

from app.models import PromptRequest, ImageStatus
from app.utils import append_to_json_file
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

router = APIRouter()

API_HOST = "cl.imagineapi.dev"
API_AUTH = f"Bearer {os.getenv('IMAGINE_DEV')}"

@router.post("/generate-image/")
def generate_image(prompt_req: PromptRequest):
    data = {
        "prompt": prompt_req.prompt
    }
    headers = {
        'Authorization': API_AUTH,
        'Content-Type': 'application/json'
    }

    try:
        response = send_request('POST', '/items/images/', data, headers)
        return {
            "message": "Image generation started.",
            "id": response['data']['id'],
            "status": response['data']['status']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-status/{image_id}")
def check_status(image_id: str):
    headers = {
        'Authorization': API_AUTH,
        'Content-Type': 'application/json'
    }

    try:
        response = send_request('GET', f"/items/images/{image_id}", headers=headers)
        status = response['data']['status']
        if status in ['completed', 'failed']:
            append_to_json_file(response['data'])
        return response['data']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))