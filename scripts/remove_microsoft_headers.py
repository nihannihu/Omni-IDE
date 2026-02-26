import os
import re

target_dir = r"c:\Users\nihan\Desktop\FINAL-PROJECTS\engine\omni-ide"
exclude_dirs = {'.git', 'node_modules', '.build', 'out', 'out-build', 'out-vscode-min'}

# Match the standard VS Code copyright block
# Handles both \n and \r\n line endings
block_pattern = re.compile(
    r"/\*---------------------------------------------------------------------------------------------\r?\n"
    r" \*  Copyright \(c\) Microsoft Corporation\. All rights reserved\.\r?\n"
    r" \*  Licensed under the MIT License\. See License\.txt in the project root for license information\.\r?\n"
    r" \*--------------------------------------------------------------------------------------------\*/\r?\n?",
    re.MULTILINE
)

# Match single line comments with Microsoft Copyright
line_pattern = re.compile(r"//\s*Copyright\s*\(c\)\s*Microsoft\s*Corporation.*", re.IGNORECASE)

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove the big block headers
        new_content = block_pattern.sub("", content)

        # Remove single line comments containing Microsoft Copyright
        lines = new_content.splitlines()
        filtered_lines = [line for line in lines if not line_pattern.search(line)]

        final_content = "\n".join(filtered_lines)

        if final_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(final_content)
            return True
    except Exception as e:
        # Silently skip binaries or weird encodings
        pass
    return False

print("Starting removal of Microsoft headings...")
count = 0
for root, dirs, files in os.walk(target_dir):
    # Exclude directories
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith(('.ts', '.js', '.mjs', '.css', '.html')):
            if process_file(os.path.join(root, file)):
                count += 1

print(f"Successfully cleaned {count} files.")
