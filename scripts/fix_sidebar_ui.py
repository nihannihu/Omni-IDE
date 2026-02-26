import os

target_dir = r"c:\Users\nihan\Desktop\FINAL-PROJECTS\engine\omni-ide\extensions\omni-client\backend\static"

def fix_html_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Standardize to LF for easier parsing
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Remove the /* --- */ header block at the start
        if content.strip().startswith('/*-----------------------'):
            print(f"Removing header from {filepath}")
            # Find the end of the block
            end_index = content.find('----------------------------*/')
            if end_index != -1:
                # Find the next newline after the end of block
                next_nl = content.find('\n', end_index)
                if next_nl == -1:
                    content = ""
                else:
                    content = content[next_nl+1:]

                # Trim leading whitespace/newlines
                content = content.lstrip()

                with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(content)
                return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

print("Purging illegal headers from HTML files in static directory...")
count = 0
for root, dirs, files in os.walk(target_dir):
    for file in files:
        if file.endswith('.html'):
            if fix_html_file(os.path.join(root, file)):
                count += 1

print(f"Successfully cleaned {count} HTML files.")
