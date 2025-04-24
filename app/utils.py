import os, json

def append_to_json_file(data, filename="responses.json"):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file:
                existing_data = json.load(file)
        else:
            existing_data = []

        existing_data.append(data)

        with open(filename, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, indent=4)
        print(f"✅ Response saved to {filename}")
    except Exception as e:
        print("❌ Failed to save response:", e)