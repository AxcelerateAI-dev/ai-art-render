from openai import OpenAI
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)  # Load your OpenAI API key from .env file

###########################################################
#                  OPENAI PROMPT
###########################################################

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_prompt_openai(place: str, time: datetime, object: str, other: str) -> str:
    """
    Generate prompt using openai: for midjourney to generate images. 
    """
    system_instruction = """
    Write a detailed prompt for MidJourney image generation based on given scenarios.
    Provide detailed prompt only in text format.
    """
    user_prompt = f"""
    - the place is: {place}
    - the time is: {time}
    - object or person is: {object}
    - other things along with the object or person: {other}
    """
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

###########################################################
#                  GEMINI PROMPT
###########################################################
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path='.env')

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

#previous prompt: Write a detailed prompt for MidJourney image generation based on given scenarios. Provide detailed prompt only in text format.

def generate_prompt_gemini(place: str, time: datetime, object: str, action: str, other: str) -> str:
    """
    Generate prompt using openai: for midjourney to generate images. 

    Args:
        place (str): the place
        time (datetime): the time
        object (str): the person or object
        other (str): other things along with main object
    
    Returns:
        prompt (str): the generated prompt for midjourney
    """
    
    model = "gemini-2.0-flash-lite"  # gemini model name
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"""
            - the place is: {place}
            - the time is: {time}
            - object or person is: {object}
            - object or person is performing: {action}
            - other things along with the object or person: {other}
            """)],
        )]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_mime_type="application/json",  # application/json, text/plain
        system_instruction=[
            types.Part.from_text(text="""
            Write a vivid MidJourney prompt based on the scenario, describing setting, mood, colors, textures, perspective, and artistic influences. Express style naturally in words (e.g., watercolor painting, cinematic lighting, cyberpunk aesthetic) without using --style. Use the same aspect ratio (e.g., --ar 16:9) for all prompts to keep image size consistent. Only provide the final prompt in plain text.

        
        ## Response Format
        {{
            "prompt": <prompt text here>
        }}
        """),
        ],
    )
    response = gemini_client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    ).text
    text = json.loads(response)
    return text

if __name__=="__main__":
    ## inputs
    place="beach",
    time="sunset",
    object="white girl",
    action="standing",
    other="coconut trees"

    ## openai prompt
    # prompt = generate_prompt_openai(
    #     place=place,
    #     time=time,
    #     object=object,
    #     other=other
    # )
    # print("OpenAi Prompt\n", prompt, "\n\n")

    ## gemini prompt
    prompt = generate_prompt_gemini(
        place=place,
        time=time,
        object=object,
        action=action,
        other=other
    )

    print("Gemini Prompt\n", prompt['prompt'])
