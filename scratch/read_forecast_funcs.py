with open('src/forecasting/predictive_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

def print_func(name):
    pattern = rf'def {name}\(.*?\n(?=(?:def |\Z))'
    m = re.search(pattern, text, re.DOTALL)
    if m:
        print(f"=== {name} ===")
        print(m.group(0))

print_func('advect_eye_position')
print_func('calculate_dynamic_landfall_eta_and_target')

