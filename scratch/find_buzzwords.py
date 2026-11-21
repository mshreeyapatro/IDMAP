import re

with open('docs/IDMAP (1).md', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

meta_patterns = [
    r'knowledge[- ]transfer',
    r'the source',
    r'supplied',
    r'documented',
    r'cutting[- ]edge',
    r'revolution',
    r'game[- ]changer',
    r'seamlessly',
    r'harnessing',
    r'testament',
    r'delve',
    r'beacon',
    r'pinnacle',
    r'synergy',
    r'vital cog',
    r'unprecedented',
    r'fosters',
    r'boasts',
    r'plethora',
    r'myriad'
]

print("=== DETECTED META-PHRASES AND BUZZWORDS ===")
for idx, line in enumerate(lines):
    for pat in meta_patterns:
        m = re.search(pat, line, re.IGNORECASE)
        if m:
            print(f"Line {idx+1}: [{m.group(0)}] -> {line.strip()[:110]}")

