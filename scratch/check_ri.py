with open('src/forecasting/predictive_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
pattern = r'def compute_rapid_intensification_index\(.*?\n(?=(?:def |\Z))'
m = re.search(pattern, text, re.DOTALL)
if m:
    print(m.group(0)[:2000])

