with open('frontend/src/components/Overview.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'.{0,50}(?:generated_at|timestamp|updated|sync|refresh).{0,50}', text, re.IGNORECASE)
for m in matches[:15]:
    print(" ", m.strip().replace('\n', ' '))

