import json
import os
import sys

# Define the target file
file_path = 'product.json'

# The "Ghosts" we want to bust
ghosts = [
    "ms-vscode.chat",
    "vscode.chat",
    "github.copilot",
    "github.copilot-chat"
]

def clean_json():
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f) # This parses JSON safely

        print("JSON loaded successfully.")

        # 1. Clean builtInExtensions
        if 'builtInExtensions' in data:
            original_count = len(data['builtInExtensions'])
            # Keep only extensions that are NOT in our ghost list
            data['builtInExtensions'] = [
                ext for ext in data['builtInExtensions']
                if ext.get('name') not in ghosts
            ]
            new_count = len(data['builtInExtensions'])
            print(f"Removed {original_count - new_count} Ghost extensions.")

        # 2. Clean extensionAllowedProposedApi
        if 'extensionAllowedProposedApi' in data:
            data['extensionAllowedProposedApi'] = [
                api for api in data['extensionAllowedProposedApi']
                if api not in ghosts
            ]
            print("Cleaned API permissions.")

        # 3. Save the file with PERFECT syntax
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4) # indent=4 makes it readable

        print("Success! The Ghost is gone and JSON is valid.")

    except json.JSONDecodeError as e:
        print(f"Critical Error: Your current product.json is ALREADY broken: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8') # Ensure print supports unicode anyway
    clean_json()
