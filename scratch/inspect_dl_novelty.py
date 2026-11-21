with open('src/cv_models/backbone.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("=== TCIR BACKBONE (src/cv_models/backbone.py) ===")
print(text[:1200])

with open('src/layer2/anomaly_autoencoder/train_autoencoder.py', 'r', encoding='utf-8') as f:
    text_ae = f.read()

print("\n=== AUTOENCODER (src/layer2/anomaly_autoencoder/train_autoencoder.py) ===")
print(text_ae[:1200])

