import http.client
import json
import pprint
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)

image_id = '5a6d32c1-bdf7-4929-a82e-c1f88aad2a96'  
 
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