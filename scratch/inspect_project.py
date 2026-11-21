import os
import re

print("=== BACKEND ENDPOINTS ===")
with open('backend/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

endpoints = re.findall(r'@app\.(get|post|put|delete)\(["\']([^"\']+)["\']', text)
print(f"Total endpoints: {len(endpoints)}")
for method, path in endpoints:
    print(f"  {method.upper():6} {path}")

print("\n=== FRONTEND VIEWS ===")
with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    f_text = f.read()

views = re.findall(r'id:\s*["\']([^"\']+)["\'],\s*label:\s*["\']([^"\']+)["\']', f_text)
if not views:
    # try other pattern
    views = re.findall(r'["\']([a-zA-Z0-9_-]+)["\']:\s*<[A-Z]', f_text)
print("Views in App.jsx:", views)

print("\n=== TESTS ===")
test_files = os.listdir('tests')
for tf in test_files:
    if tf.endswith('.py'):
        with open(os.path.join('tests', tf), 'r', encoding='utf-8') as f:
            t_text = f.read()
        tests = re.findall(r'def (test_[a-zA-Z0-9_]+)', t_text)
        print(f"{tf} ({len(tests)} tests):")
        for t in tests:
            print(f"  - {t}")

