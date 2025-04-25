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


def store_get_prompt(id: str, filename: str, prompt: str = None):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file:
                prompts = json.load(file)
        else:
            prompts = {}

        if prompt is not None:
            # Store the prompt
            prompts[id] = prompt
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(prompts, file, indent=4)
            print(f"✅ Prompt saved to {filename}")
            return True
        else:
            # Retrieve the prompt
            result = prompts.get(id)
            if result:
                print(f"📥 Retrieved prompt for ID '{id}': {result}")
            else:
                print(f"⚠️ No prompt found for ID '{id}'")
            return result
    except Exception as e:
        print("❌ Error in store_or_get_prompt:", e)
        return None

