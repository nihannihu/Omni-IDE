import sys
import os
import json

print('--- MANIFEST CHECK ---')
with open(r'c:\Users\nihan\Desktop\FINAL-PROJECTS\engine\omni-ide\extensions\omni-client\package.json', 'r') as f:
    pkg = json.load(f)
    print(f'Name: {pkg.get("name")}')
    print(f'Engine VSC: {pkg.get("engines", {}).get("vscode")}')
    print('Manifest validates structurally.')

print('\n--- RUNTIME SMOKE TEST ---')
sys.path.append(r'c:\Users\nihan\Desktop\FINAL-PROJECTS\engine\omni-ide\extensions\omni-client\backend')
try:
    from gateway import get_gateway, model_gateway
    print('Gateway imported successfully.')
    gw = get_gateway()
    print('Gateway initialized:', gw is not None)

    from main import app
    print('Main FastAPI app imported successfully.')
    print('Smoke test PASSED.')
except Exception as e:
    import traceback
    print('SMOKE TEST FAILED:')
    traceback.print_exc()
    sys.exit(1)
