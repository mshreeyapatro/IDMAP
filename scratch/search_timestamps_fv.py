with open('frontend/src/components/ForecastView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.{0,40}(?:generated_at|last_updated|as of|updated at|live feed|synced).{0,40}', text, re.IGNORECASE)
for m in matches[:15]:
    print(" ", m.strip().replace('\n', ' '))

