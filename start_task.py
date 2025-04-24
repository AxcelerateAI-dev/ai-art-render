import requests
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)
url = "https://cl.imagineapi.dev/items/images/"
payload = {
    "prompt": """
A tall Maltese man in his 20s, wearing a casual hat and a sporty soccer jersey, standing confidently.
Beside him, a young woman in her 20s with long, flowing red hair, wearing a vibrant floral dress, smiling gently.
Bright daylight, natural setting, full-body view, cinematic style, ultra-realistic --chaos 40 --stylize 1000 --ar 16:9
"""
}
headers = {
    'Authorization': f'Bearer {os.getenv('IMAGINE_DEV')}',
    'Content-Type': 'application/json'
}
 
response = requests.request("POST", url, headers=headers, json=payload)
 
print(response.text)