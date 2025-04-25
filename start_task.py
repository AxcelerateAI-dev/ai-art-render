import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)


import http.client
import json
import pprint
 
data = {
    "prompt": "a pretty lady at the beach --ar 9:21 --chaos 40 --stylize 1000"
}

headers = {
    'Authorization': f'Bearer {os.getenv("IMAGINE_DEV")}',  # <<<< TODO: remember to change this
    'Content-Type': 'application/json'
}
 
conn = http.client.HTTPSConnection("cl.imagineapi.dev")
conn.request("POST", "/items/images/", body=json.dumps(data), headers=headers)
 
response = conn.getresponse()
response_data = json.loads(response.read().decode('utf-8'))
 
pprint.pp(response_data)