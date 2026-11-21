with open('src/forecasting/predictive_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== LINES 2260-2285 ===")
for i in range(2255, min(2290, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

print("\n=== LINES 2450-2475 ===")
for i in range(2445, min(2475, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")

