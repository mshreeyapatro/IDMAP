import sys
sys.path.insert(0, '.')
from src.forecasting import predictive_engine

f15 = predictive_engine.generate_15day_extended_forecast()
print("=== 15-DAY EXTENDED FORECAST ===")
for k, v in f15.items():
    if not isinstance(v, list):
        print(f"{k}: {v}")
    else:
        print(f"{k}: list with {len(v)} items")

