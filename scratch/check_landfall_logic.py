with open('src/forecasting/predictive_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# find landfall calculation
match = re.search(r'def calculate_dynamic_landfall_eta_and_target\(.*?\n(?:    .*\n)+', text)
if match:
    print("=== LANDFALL CALCULATION FUNCTION ===")
    print(match.group(0)[:1500])

match2 = re.search(r'def generate_48h_short_range_forecast\(.*?\n(?:    .*\n)+', text)
if match2:
    print("\n=== SHORT RANGE FORECAST FUNCTION ===")
    print(match2.group(0)[:1500])

match3 = re.search(r'def advect_eye_position\(.*?\n(?:    .*\n)+', text)
if match3:
    print("\n=== ADVECT EYE POSITION FUNCTION ===")
    print(match3.group(0)[:1500])

