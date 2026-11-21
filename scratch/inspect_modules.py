import os

print("=== CV MODELS ===")
for root, dirs, files in os.walk('src/cv_models'):
    for f in files:
        if f.endswith('.py'):
            print(os.path.join(root, f))

print("\n=== LAYER 2 ===")
for root, dirs, files in os.walk('src/layer2'):
    for f in files:
        if f.endswith('.py'):
            print(os.path.join(root, f))

print("\n=== RAG / KNOWLEDGE ===")
for root, dirs, files in os.walk('src/rag'):
    for f in files:
        if f.endswith('.py'):
            print(os.path.join(root, f))

print("\n=== RETRAINING ===")
for root, dirs, files in os.walk('src/retraining'):
    for f in files:
        if f.endswith('.py'):
            print(os.path.join(root, f))

print("\n=== DB ===")
for root, dirs, files in os.walk('src/db'):
    for f in files:
        if f.endswith('.py'):
            print(os.path.join(root, f))

