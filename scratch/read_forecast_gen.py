with open('src/forecasting/predictive_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('def generate_48h_short_range_forecast')
if idx != -1:
    print(text[idx:idx+2500])

