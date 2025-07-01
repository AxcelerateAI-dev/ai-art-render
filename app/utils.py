import os, json
import logging
from dotenv import load_dotenv
load_dotenv(override=True)

def append_to_json_file(data:dict, filename="responses.json")->None:
    """
    Store the generated images response to Json file.
    """
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        else:
            existing_data = []
        ids = [item['id'] for item in existing_data]
        if data['id'] not in ids:
            existing_data.append(data)
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4)
        logging.info(f"✅ Response saved to {filename}")
    except Exception as e:
        logging.error(f"❌ Failed to save response: {e}")
        raise