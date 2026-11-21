with open('src/layer2/anomaly_autoencoder/train_autoencoder.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
classes = re.findall(r'class [a-zA-Z0-9_]+\(.*?\):', text)
print("Classes in train_autoencoder.py:", classes)
idx = text.find('class ')
if idx != -1:
    print(text[idx:idx+1500])

