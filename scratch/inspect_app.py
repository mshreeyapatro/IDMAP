with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# look for components imported
imports = [line.strip() for line in text.split('\n') if 'import' in line and 'components' in line]
print("Component imports:")
for imp in imports:
    print(" ", imp)

# look for navigation tabs
print("\nTabs/Nav definitions:")
for idx, line in enumerate(text.split('\n')):
    if 'NAV' in line or 'tabs' in line.lower() or 'activeTab' in line or 'activeView' in line:
        print(f"  Line {idx+1}: {line.strip()[:100]}")

