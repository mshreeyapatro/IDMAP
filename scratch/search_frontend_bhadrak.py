import os

for root, dirs, files in os.walk('frontend/src'):
    for f in files:
        if f.endswith(('.jsx', '.js', '.css')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
                if 'bhadrak' in text.lower():
                    print(f"Found in {path}")
                    for idx, line in enumerate(text.split('\n')):
                        if 'bhadrak' in line.lower():
                            print(f"  Line {idx+1}: {line.strip()[:100]}")

