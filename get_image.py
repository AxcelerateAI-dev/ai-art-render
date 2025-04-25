import http.client
import json
import pprint
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

image_id = '7b2ade1b-aee4-4565-b167-a33319d88df4'  # TODO: change this to image ID (the ID you got from previous request)
connection = http.client.HTTPSConnection("cl.imagineapi.dev")
headers = {
    'Authorization': f'Bearer {os.getenv('IMAGINE_DEV')}', 
    'Content-Type': 'application/json'
}

try:
    connection.request("GET", f"/items/images/{image_id}", headers=headers)
    response = connection.getresponse()
    data = json.loads(response.read().decode())
    pprint.pp(data, indent=4)
except Exception as error:
    print(f"Error: {error}")