import os

target_dir = r"c:\Users\nihan\Desktop\FINAL-PROJECTS\engine\omni-ide"
exclude_dirs = {'.git', 'node_modules', '.build', 'out', 'out-build', 'out-vscode-min'}

header = [
    '/*---------------------------------------------------------------------------------------------',
    ' *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.',
    ' *  Licensed under the MIT License. See License.txt in the project root for license information.',
    ' *--------------------------------------------------------------------------------------------*/',
    ''
]
header_text = "\n".join(header)

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Standardize to LF
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Remove any existing copyright header
        if content.startswith('/*-----------------------'):
            end_index = content.find('----------------------------*/')
            if end_index != -1:
                next_nl = content.find('\n', end_index)
                if next_nl != -1:
                    content = content[next_nl+1:]
                    while content.startswith('\n'):
                        content = content[1:]

        new_content = header_text + content

        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        return True
    except Exception as e:
        pass
    return False

print("Purging old headers and injecting LF Omni-IDE headers...")
count = 0
for root, dirs, files in os.walk(target_dir):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith(('.ts', '.js', '.mjs', '.css', '.html')):
            if process_file(os.path.join(root, file)):
                count += 1

print(f"Successfully processed {count} files.")
