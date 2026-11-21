with open('frontend/src/components/ForecastView.jsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(600, 650):
    print(f"{i+1}: {lines[i]}", end="")

