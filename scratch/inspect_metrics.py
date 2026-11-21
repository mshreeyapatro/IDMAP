import json
import os

print("=== RISK MODEL METRICS ===")
if os.path.exists('reports/risk_model_metrics.json'):
    with open('reports/risk_model_metrics.json') as f:
        print(f.read())

print("\n=== TCIR ENSEMBLE RESULTS ===")
if os.path.exists('reports/tcir_ensemble_results.json'):
    with open('reports/tcir_ensemble_results.json') as f:
        print(f.read())

print("\n=== RETRAINING REPORT ===")
if os.path.exists('reports/retraining/latest_retraining_report.json'):
    with open('reports/retraining/latest_retraining_report.json') as f:
        print(f.read())

