import os
import re

print("=== SEARCHING FOR SYNC / REFRESH IN FRONTEND ===")
for root, dirs, files in os.walk('frontend/src'):
    for f in files:
        if f.endswith(('.jsx', '.js', '.css')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
            for idx, line in enumerate(lines):
                if any(w in line.lower() for w in ['sync', 'refresh', 'last_updated', 'lastupdated', 'poll', 'refreshing']):
                    # print snippet
                    print(f"{os.path.basename(path)}:{idx+1} -> {line.strip()[:100]}")

