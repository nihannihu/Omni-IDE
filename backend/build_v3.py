import PyInstaller.__main__
import os
import shutil

print("--- OMNI-IDE BUILD SCRIPT v3 ---")

# Step 1: Clean previous builds
print("🧹 Cleaning previous build directories...")
for folder in ['build', 'dist', 'Professional-Installer-Prep']:
    if os.path.exists(folder):
        shutil.rmtree(folder)

print("❄️  Freezing OmniIDE Core Logic...")

# Step 2: Run PyInstaller
args = [
    'desktop.py',  # Main entry point for the desktop wrapper
    '--name=OmniIDE',
    '--onedir',    # Directory output
    '--noconsole', # Hide console window
    '--contents-directory=internal', # professional feature: hides all DLLs inside an internal folder
    '--add-data=static;static',
    '--add-data=.env.example;.',
    '--clean',
    '--hidden-import=uvicorn',
    '--hidden-import=engineio.async_drivers.threading',
    
    # We must explicitly include smolagents and litellm to ensure tool-calling works
    '--collect-all=smolagents',
    '--collect-all=litellm',
    '--collect-all=huggingface_hub',
    
    # EXCLUDE HEAVY ASSETS & MODELS (Keep .exe ultra-light)
    # The models are now handled safely by Ollama outside the python bundle!
    '--exclude-module=torch',
    '--exclude-module=tensorflow',
    '--exclude-module=transformers',
    '--exclude-module=bitsandbytes',
    '--exclude-module=uvloop',
    '--exclude-module=tkinter',
    '--exclude-module=pygame',
]

if os.path.exists('static/icon.ico'):
    args.append('--icon=static/icon.ico')

PyInstaller.__main__.run(args)

# Step 3: Create Professional Folder Layout
print("\n📦 Arranging Professional Installer Structure...")
prep_dir = 'Professional-Installer-Prep'
os.makedirs(prep_dir, exist_ok=True)

dirs_to_create = [
    os.path.join(prep_dir, 'config'),
    os.path.join(prep_dir, 'docs')
]
for d in dirs_to_create:
    os.makedirs(d, exist_ok=True)

# Move compiled binary folder contents into prep_dir
if os.path.exists('dist/OmniIDE'):
    for item in os.listdir('dist/OmniIDE'):
        shutil.move(os.path.join('dist/OmniIDE', item), os.path.join(prep_dir, item))

# Copy documentation
if os.path.exists('../README.md'):
    shutil.copy('../README.md', os.path.join(prep_dir, 'docs', 'README.md'))
if os.path.exists('../LICENSE.txt'):
    shutil.copy('../LICENSE.txt', os.path.join(prep_dir, 'docs', 'LICENSE.txt'))

# Copy config templates
if os.path.exists('.env.example'):
    shutil.copy('.env.example', os.path.join(prep_dir, 'config', '.env.example'))

# Copy existing Inno Setup script if available
if os.path.exists('OmniIDE-Installer.iss'):
    shutil.copy('OmniIDE-Installer.iss', prep_dir)

print(f"✅ Build Complete! The professional staging environment is ready at: {os.path.abspath(prep_dir)}")
print("   Next step: Compile 'OmniIDE-Installer.iss' with Inno Setup Compiler.")
