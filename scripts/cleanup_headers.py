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

        # Aggressively remove EVERY occurrence of the header block at the start of the file
        while content.strip().startswith('/*-----------------------'):
            # Find the end of the block
            end_index = content.find('----------------------------*/')
            if end_index == -1:
                break

            # Find the next newline after the end of block
            next_nl = content.find('\n', end_index)
            if next_nl == -1:
                content = "" # File was just a header
                break
            else:
                content = content[next_nl+1:]
                # Trim leading whitespace/newlines to catch the next header if it exists
                content = content.lstrip()

        # Final check if there's any stray Microsoft line (just in case)
        lines = content.split('\n')
        lines = [l for l in lines if "Microsoft Corporation. All rights reserved." not in l]
        content = '\n'.join(lines)

        # Inject the single clean header
        new_content = header_text + content

        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

print("Aggressively purging all old headers and re-injecting clean Omni-IDE headers...")
count = 0
for root, dirs, files in os.walk(target_dir):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith(('.ts', '.js', '.mjs', '.css')):
            if process_file(os.path.join(root, file)):
                count += 1

print(f"Successfully cleaned and re-branded {count} files.")
