with open('frontend/src/components/ForecastView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.{0,50}(?:bhadrak|landfall|target).{0,50}', text, re.IGNORECASE)
print(f"Matches in ForecastView.jsx: {len(matches)}")
for m in matches[:10]:
    print(" ", m.strip().replace('\n', ' '))

