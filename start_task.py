import requests
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)
url = "https://cl.imagineapi.dev/items/images/"
payload = {
    "prompt": "Cinematic Portrait, GodlyBeautiful french supermodel, dynamic lighting, [light + space of James Turrell + Bauhaus architectural forms], BeautyCore, Sharp Details --ar 21:9 --style raw"
}
headers = {
    'Authorization': f'Bearer {os.getenv('IMAGINE_DEV')}',
    'Content-Type': 'application/json'
}
 
response = requests.request("POST", url, headers=headers, json=payload)
 
print(response.text)