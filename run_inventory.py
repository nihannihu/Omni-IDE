import os
import json

target_dir = r"c:\Users\nihan\Desktop\FINAL-PROJECTS\engine\omni-ide\extensions\omni-client"
inventory = []
for root, dirs, files in os.walk(target_dir):
    if "node_modules" in root or "__pycache__" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith(('.py', '.js', '.json', '.ts', '.md', '.txt')):
            path = os.path.join(root, f)
            size = os.path.getsize(path)
            inventory.append({"file": os.path.relpath(path, target_dir), "size": size})

with open("inventory.json", "w") as f:
    json.dump(inventory, f, indent=2)
print(f"Inventory saved. Found {len(inventory)} relevant files.")