with open('frontend/src/components/ForecastView.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_range(start, end):
    for i in range(start-1, min(end, len(lines))):
        print(f"{i+1}: {lines[i]}", end="")

print("=== ForecastView.jsx Lines 650-680 ===")
print_range(650, 680)

print("\n=== ForecastView.jsx Lines 815-835 ===")
print_range(815, 835)

print("\n=== ForecastView.jsx Lines 1615-1635 ===")
print_range(1615, 1635)

