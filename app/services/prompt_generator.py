import os
import json
import base64
from google import genai
from openai import OpenAI
from dotenv import load_dotenv
from google.genai import types

load_dotenv(override=True)
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_INSTRUCTION_CREATE = """
You are a creative assistant for AI art generation. Your task is to write a single, vivid MidJourney prompt based on a user's scenario.

Instructions:
1.  Synthesize all user inputs (place, time, object, action, style, other elements) into a coherent and descriptive paragraph.
2.  Express the artistic style naturally within the description (e.g., "in the style of a baroque painting," "cinematic, dramatic lighting," "a vibrant pop-art aesthetic"). Do not use command-line flags like `--style`.
3.  Always append the aspect ratio `--ar 16:9` at the very end of the prompt.
4.  Your entire output must be a single JSON object in the format: {"prompt": "<your generated prompt text here>"}. Do not include any other text or explanations.
"""

SYSTEM_INSTRUCTION_REF_IMAGE = """
You are a creative assistant for AI art generation. Your task is to write a single, vivid MidJourney prompt based on a user's scenario.
Instructions:
1.  Analyze the provided Reference image for its artistic style, color palette, lighting, composition, and mood.
2.  Synthesize all user inputs (place, time, object, action, style, other elements) into a coherent and descriptive paragraph.
3.  Express the artistic style naturally within the description (e.g., "in the style of a baroque painting," "cinematic, dramatic lighting," "a vibrant pop-art aesthetic"). Do not use command-line flags like `--style`.
4.  Always append the aspect ratio `--ar 16:9` at the very end of the prompt.
5.  Your entire output must be a single JSON object in the format: {"prompt": "<your generated prompt text here>"}. Do not include any other text or explanations
"""

SYSTEM_INSTRUCTION_UPDATE = """
You are a creative assistant for AI art generation. Your task is to update a given MidJourney prompt based on the style and content of a reference image.

Instructions:
1.  Analyze the provided image for its artistic style, color palette, lighting, composition, and mood.
2.  Read the `previous_prompt` to understand the user's original core idea.
3.  Rewrite and enhance the `previous_prompt`, integrating the visual characteristics of the image. The new prompt should retain the subject of the original prompt but be heavily inspired by the visual style of the image.
4.  Always append the aspect ratio `--ar 16:9` at the very end of the new prompt.
5.  Your entire output must be a single JSON object in the format: {"prompt": "<your new, updated prompt text here>"}. Do not include any other text or explanations.
"""

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_prompt_openai(
    place: str = None,
    time: str = None,
    object: str = None,
    action: str = None,
    style: str = None,
    other: str = None,
    previous_prompt: str = None,
    image_bytes: bytes | None = None,
    mime_type: str | None = None
) -> dict:
    """
    Generates or updates a prompt using the OpenAI API.

    - If text preferences (place, time, etc.) are provided, it creates a new prompt using a text model.
    - If a previous_prompt and an image are provided, it updates the prompt using a vision model.
    """
    if (previous_prompt and image_bytes):
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION_UPDATE},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Here is the previous prompt to update:\n\n{previous_prompt}"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                    }
                ]
            }
        ]
        
        model = "gpt-4.1-nano-2025-04-14"
    elif image_bytes and (not previous_prompt):
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION_REF_IMAGE},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"""
                        - place: {place}
                        - time: {time}
                        - object or person: {object}
                        - action: {action}
                        - artistic style: {style}
                        - other elements: {other}
                    """},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                    }
                ]
            }
        ]
        
        model = "gpt-4.1-nano-2025-04-14"

    else:
        user_prompt_text = f"""
            - place: {place}
            - time: {time}
            - object or person: {object}
            - action: {action}
            - artistic style: {style}
            - other elements: {other}
        """
        
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION_CREATE},
            {"role": "user", "content": user_prompt_text}
        ]
        
        model = "gpt-4.1-nano-2025-04-14"

    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    
    except Exception as e:
        print(f"An error occurred with the OpenAI API: {e}")
        raise


def generate_prompt_gemini(
    place: str = None,
    time: str = None,
    object: str = None,
    action: str = None,
    style: str = None,
    other: str = None,
    previous_prompt: str = None,
    image_bytes: bytes | None = None,
    mime_type: str | None = None
) -> dict:
    """
    Generates or updates a prompt using Gemini.
    - If place, time, etc., are provided, it creates a new prompt.
    - If previous_prompt and an image are provided, it updates the prompt.
    """
    model_name = "gemini-2.5-flash-lite"
    parts = []
    
    if previous_prompt and image_bytes:
        system_instruction = SYSTEM_INSTRUCTION_UPDATE
        text_content = f"Here is the previous prompt to update:\n\n{previous_prompt}"
        parts.append(types.Part.from_text(text=text_content))
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        parts.append(image_part)
    else:
        system_instruction = SYSTEM_INSTRUCTION_CREATE
        text_prompt = f"""
            - place: {place}
            - time: {time}
            - object or person: {object}
            - action: {action}
            - artistic style: {style}
            - other elements: {other}
        """
        parts.append(types.Part.from_text(text=text_prompt))

    contents = [types.Content(role="user", parts=parts)]
    
    generate_content_config = types.GenerateContentConfig(
        temperature=1.0, top_p=0.95, top_k=40, max_output_tokens=8192,
        system_instruction=[
            types.Part.from_text(text=system_instruction)],
        response_mime_type="application/json",
    )

    response = gemini_client.models.generate_content(
        model=model_name,
        contents=contents,
        config=generate_content_config,
    ).text

    return json.loads(response)