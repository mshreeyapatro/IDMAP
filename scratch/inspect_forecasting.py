with open('src/forecasting/predictive_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
funcs = re.findall(r'def ([a-zA-Z0-9_]+)\(', text)
print("Functions in predictive_engine.py:")
for func in funcs:
    print(f"  - {func}")

classes = re.findall(r'class ([a-zA-Z0-9_]+)', text)
print("Classes in predictive_engine.py:", classes)

