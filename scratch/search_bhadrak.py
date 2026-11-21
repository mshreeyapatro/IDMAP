import sys
sys.path.insert(0, '.')
import os
import re

print("Searching for Bhadrak in src and backend...")
for root, dirs, files in os.walk('.'):
    if any(p in root for p in ['.git', 'node_modules', '.venv']):
        continue
    for f in files:
        if f.endswith(('.py', '.jsx', '.json')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
            for idx, line in enumerate(lines):
                if 'bhadrak' in line.lower() and any(k in line.lower() for k in ['landfall', 'target', 'predicted', 'forecast']):
                    print(f"{path}:{idx+1} -> {line.strip()[:100]}")

