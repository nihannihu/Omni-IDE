import os

target_dir = r"c:\Users\nihan\Desktop\FINAL-PROJECTS\engine\omni-ide"
exclude_dirs = {'.git', 'node_modules', '.build', 'out', 'out-build', 'out-vscode-min'}

header_lines = [
    '/*---------------------------------------------------------------------------------------------',
    ' *  Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). All rights reserved.',
    ' *  Licensed under the MIT License. See License.txt in the project root for license information.',
    ' *--------------------------------------------------------------------------------------------*/',
    ''
]
header_text = "\n".join(header_lines)

# One-liner version for HTML
html_header = f"<!-- Copyright (c) 2026 Mohammed Nihan (Nihan Nihu). Licensed under MIT. -->\n"

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Standardize to LF
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # 1. Remove ANY JS-style header block at the start
        while content.strip().startswith('/*-----------------------'):
            end_index = content.find('----------------------------*/')
            if end_index == -1: break
            next_nl = content.find('\n', end_index)
            if next_nl == -1:
                content = ""
                break
            else:
                content = content[next_nl+1:]
                content = content.lstrip()

        # 2. Remove ANY HTML-style header block at the start
        while content.strip().startswith('<!--'):
            end_index = content.find('-->')
            if end_index == -1: break
            next_nl = content.find('\n', end_index)
            if next_nl == -1:
                content = ""
                break
            else:
                content = content[next_nl+1:]
                content = content.lstrip()

        # 3. Inject correct header
        if filepath.endswith('.html'):
            new_content = html_header + content
        else:
            new_content = header_text + content

        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

print("Global header restoration (fixing illegal HTML comments)...")
count = 0
for root, dirs, files in os.walk(target_dir):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith(('.ts', '.js', '.mjs', '.css', '.html')):
            if process_file(os.path.join(root, file)):
                count += 1

print(f"Successfully processed {count} files.")
