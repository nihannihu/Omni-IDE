import os

target_dir = r"c:\Users\nihan\Desktop\FINAL-PROJECTS\engine\omni-ide\extensions\omni-client\backend\static"

def purge_header(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Standardize to LF
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Aggressively remove EVERY occurrence of the header block at the start of the file
        original_len = len(content)
        while content.strip().startswith('/*-----------------------'):
            # Find the end of the block
            end_index = content.find('----------------------------*/')
            if end_index == -1:
                break

            # Find the next newline after the end of block
            next_nl = content.find('\n', end_index)
            if next_nl == -1:
                content = ""
                break
            else:
                content = content[next_nl+1:]
                content = content.lstrip()

        if len(content) != original_len:
            print(f"Purged header from {filepath}")
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

print(f"Purging all injected headers from {target_dir}...")
count = 0
for root, dirs, files in os.walk(target_dir):
    for file in files:
        if purge_header(os.path.join(root, file)):
            count += 1

print(f"Successfully cleaned {count} files in omni-client static assets.")
