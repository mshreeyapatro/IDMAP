# IDMAP: Intelligent Disaster Mapping & Advisory Platform

> **Multimodal Generative AI & Spatial RAG Pipeline for Odisha Cyclone Intelligence**

IDMAP (Intelligent Disaster Mapping & Advisory Platform) is an end-to-end disaster intelligence system that combines satellite imagery Computer Vision (CV), unsupervised anomaly detection, XGBoost risk modeling, spatial Graph Neural Network (GNN) district topology, semantic RAG vector retrieval, and LLM explanation generation.

---

## 🚀 Key Technical Highlights

- **Multimodal Feature Fusion**: Pretrained TCIR Convolutional Neural Network (ResNet backbone) extracts 128-dimensional embedding vectors from INSAT-3D satellite imagery crops, fused with IMD best-track meteorological data and Census 2011 socio-economic exposure indicators.
- **Unsupervised Anomaly Detection**: Convolutional Autoencoder measures cross-sectional image reconstruction error ($\text{MSE}$) to flag non-standard cyclone formation patterns.
- **XGBoost Risk Classifier & SHAP Explainability**: Predicts ground-truth cyclone risk profiles ($R^2 = 0.9885$) and computes exact SHAP (SHapley Additive exPlanations) feature attributions to explain model predictions.
- **Spatial GNN District Graph & Evacuation Engine**: Models Odisha's 30 districts as an adjacency graph with node features (coastal distance, Census 2011 population) to calculate shelter capacities, NDRF team allocations, and evacuation targets.
- **Evidence-Grounded RAG Advisory**: Semantic retrieval over official IMD cyclone guidelines and historical disaster reports (Chroma/FAISS vector store) combined with LLM prompt engineering to deliver zero-hallucination, evidence-backed emergency advisories.

---

## 🏗️ System Architecture

```
                                  ┌───────────────────────────────┐
                                  │   INSAT-3D Satellite Crops    │
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │  TCIR CNN Feature Extractor   │
                                  │    (128-dim Embedding Vector) │
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼
                     ┌────────────────────────────┴────────────────────────────┐
                     │                                                         │
                     ▼                                                         ▼
       ┌───────────────────────────┐                             ┌───────────────────────────┐
       │ Convolutional Autoencoder │                             │    XGBoost Risk Model     │
       │ (Anomaly Error Flagging)  │                             │    + SHAP Attribution     │
       └─────────────┬─────────────┘                             └─────────────┬─────────────┘
                     │                                                         │
                     └────────────────────────────┬────────────────────────────┘
                                                  │
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │   Structured Fusion Context   │
                                  │   + GNN District Graph Risk   │
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │   RAG Semantic Vector Search  │
                                  │  (Chroma Store / Vector KB)   │
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │  LLM Fused Advisory Generator │
                                  │ (Grounded Explanation Report) │
                                  └───────────────────────────────┘
```

---

## 🛠️ Project Structure

```
IDMAP/
├── backend/
│   └── main.py                     # FastAPI server exposing ML & RAG endpoints
├── frontend/
│   ├── src/
│   │   ├── api.js                  # Frontend API client
│   │   ├── App.jsx                 # React Dashboard shell & tab navigation
│   │   └── components/             # Overview, AI Advisory, SHAP, What-If, Resource Plan, Graph views
├── src/
│   ├── cv_models/
│   │   ├── backbone.py             # ResNet feature extractor backbone
│   │   └── pretrain_tcir_backbone.py # TCIR pretraining script
│   ├── layer2/
│   │   ├── anomaly_autoencoder/   # Reconstruction error anomaly detector
│   │   ├── feature_fusion/        # Master dataset builder
│   │   └── risk_xgboost/          # XGBoost risk model & SHAP explainability engine
│   ├── agent/
│   │   ├── tools.py                # Agent tools & fact retrieval registry
│   │   ├── whatif_engine.py       # Dynamic scenario simulation engine
│   │   └── resource_planner.py    # Evacuation & shelter allocation planner
│   ├── data_prep/                  # District graph builder & Census metadata extractor
│   └── rag/
│       ├── vector_store.py        # Vector database ingestion & semantic search
│       ├── fusion_context.py      # Multimodal context fusion builder
│       └── prompts.py             # Grounded prompt engineering templates
├── data/                           # Processed datasets, district graph CSVs, vector database
└── reports/                        # Model checkpoints, evaluation curves, SHAP outputs
```

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status` | Returns implementation status of roadmap phases |
| `GET` | `/api/events` | List all cyclone events with matched metadata |
| `GET` | `/api/events/{base_id}` | Detailed event summary & image URLs |
| `POST` | `/api/predict` | Predict cyclone intensity and anomaly error |
| `GET` | `/api/explain/{base_id}` | Compute SHAP feature attributions for risk rating |
| `POST` | `/api/whatif` | Simulate scenario adjustments ($\Delta \text{ wind}$, coastal distance) |
| `GET` | `/api/resources` | District evacuation targets & shelter capacity |
| `POST` | `/api/retrieve` | Semantic vector search over cyclone knowledge base |
| `POST` | `/api/advisory` | Generate evidence-grounded AI advisory report |
| `GET` | `/api/district-graph` | Fetch 30-district adjacency graph topology |

---

## ⚡ Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and `npm`

### 2. Install Dependencies
```bash
# Install Python ML & RAG dependencies
pip install -r requirements.txt

# Install Frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Run Development Servers
```bash
# Terminal 1: Start FastAPI Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start React Dashboard
cd frontend
npm run dev
```

Open `http://localhost:5173` in your browser to interact with the dashboard!

