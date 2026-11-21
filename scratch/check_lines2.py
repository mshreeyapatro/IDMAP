with open('src/forecasting/predictive_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== LINES 2150-2220 ===")
for i in range(2150, min(2220, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

