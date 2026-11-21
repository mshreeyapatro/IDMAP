with open('src/forecasting/predictive_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches_sst = re.findall(r'.{0,50}28\.5.{0,50}', text)
print("=== 28.5 in predictive_engine.py ===")
for m in matches_sst:
    print(" ", m.strip())

matches_shear = re.findall(r'.{0,50}10\.0.{0,50}', text)
print("\n=== 10.0 / wind shear in predictive_engine.py ===")
for m in matches_shear[:5]:
    print(" ", m.strip())

matches_lat = re.findall(r'.{0,50}19\.8.{0,50}', text)
print("\n=== 19.8 in predictive_engine.py ===")
for m in matches_lat:
    print(" ", m.strip())

