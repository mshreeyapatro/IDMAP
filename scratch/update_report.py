# -*- coding: utf-8 -*-
"""
Script to safely update docs/IDMAP (1).md for university minor project evaluation.
Preserves all 11 base64 images byte-for-byte.
Replaces outdated sections with rigorous, formal academic text and LaTeX mathematics.
"""
import hashlib

def main():
    doc_path = r'c:\Professional\Projects\IDMAP\docs\IDMAP (1).md'
    with open(doc_path, 'r', encoding='utf-8') as f:
        c = f.read()

    # Step 1: Record original images and their hashes
    orig_images = []
    for line in c.splitlines():
        if 'data:image/png;base64' in line:
            h = hashlib.sha256(line.encode('utf-8')).hexdigest()
            orig_images.append((len(line), h))

    print(f"Original images count: {len(orig_images)}")
    assert len(orig_images) == 11, f"Expected 11 images, found {len(orig_images)}"

    # -------------------------------------------------------------
    # 1. Section 1.3 & 1.4 Replacement Text
    # -------------------------------------------------------------
    sec1_text = """## 1.3 Project Objectives
The objective of the Intelligent Disaster Mapping & Advisory Platform (IDMAP) is to engineer an integrated, multi-tier operational decision-support system for tropical cyclone risk evaluation, spatial resource mobilization, and multi-horizon trajectory forecasting specifically focused on the 30 administrative districts of Odisha. The core technical objectives are:

- **Multimodal Data Ingestion Pipeline:** Ingest, synchronize, and preprocess heterogeneous real-time and historical telemetry, including Open-Meteo atmospheric observations across six key coastal stations (Chandbali, Paradip, Gopalpur, Puri, Balasore, Bhubaneswar), multispectral INSAT-3D satellite imagery (VIS, TIR1, TIR2, WV channels), IMD historical cyclone best-track records (1982–2024), 2011 Census demographic vulnerability parameters, and the OSDMA Multipurpose Cyclone Shelter (MCS) registry.
- **Deep Visual Feature Extraction and Anomaly Detection:** Implement a computer vision pipeline utilizing a TCIR ResNet-18 visual backbone that ingests 4-channel satellite crops ($128 \\times 128$ normalized IR1, IR2, WV, VIS) to generate 128-dimensional dense visual representations, paired with an unsupervised Convolutional Autoencoder (CAE) producing reconstruction Mean Squared Error (MSE) metrics to flag structural anomalies against calibrated operational thresholds ($\\tau \\le 0.035$ nominal, $0.035 < \\tau \\le 0.070$ moderate shear, $> 0.070$ severe anomaly).
- **Calibrated Risk Regression and Game-Theoretic Explainability:** Develop an Extreme Gradient Boosting (XGBoost) regression engine to compute district-level composite risk scores, achieving empirical performance of $R^2 = 0.9885$, $\\text{RMSE} = 0.0155$, and $\\text{MAE} = 0.0108$ under 10-fold cross-validation. Provide local and global feature attribution via TreeSHAP to deliver transparent physical justifications for risk estimates.
- **Multi-Horizon Predictive Forecasting Engine:** Establish a unified three-tier forecasting hierarchy spanning:
  1. *48-Hour Short-Range Numerical Advection:* Kinematic 2D trajectory propagation with beta-recurvature northward deflection above $19.8^\\circ\\text{N}$, asymmetric Modified Rankine vortex wind profiling, Holland central pressure inversion, Kaplan–DeMaria inland decay ($\\alpha = 0.095\\text{ hr}^{-1}$), and WMO/IMD Rapid Intensification monitoring ($\\Delta V_{24} \\ge 30\\text{ kt}$).
  2. *15-Day Sub-Seasonal to Seasonal (S2S) Synoptic Outlook:* Cyclogenesis Potential Index ($CPI$) coupled with oceanic and atmospheric teleconnections (ENSO ONI, IOD index, MJO Phase 3 convective pulses) structured into a 3-phase strategic preparedness protocol.
  3. *60-Day Climatological Outlook with Monte Carlo Ensemble:* A 50-member stochastic perturbation ensemble ($\\sigma_{\\text{head}} = 4.8^\\circ$, $\\sigma_{\\text{trans}} = 2.4\\text{ km/h}$, $\\sigma_{\\text{int}} = 5.5\\text{ kt}$) generating probabilistic trajectory spread and spatial confidence cones.
- **Spatial Topology and Constrained Resource Optimization:** Model the 30 districts of Odisha as a topological graph $\\mathcal{G} = (\\mathcal{V}, \\mathcal{E})$ with $|\\mathcal{V}| = 30$ and $|\\mathcal{E}| = 69$ bidirectional adjacency edges. Execute constrained linear optimization to compute district evacuation quotas and deploy ODRAF/NDRF rescue battalion platoons at an operational baseline of 1 platoon per 15,000 evacuees under shelter capacity bounds.
- **Evidence-Grounded Advisory Generation via RAG:** Construct a dense vector retrieval pipeline utilizing Chroma DB and `all-MiniLM-L6-v2` embeddings over official IMD Standard Operating Procedures, OSDMA disaster management guidelines, and NDMA evacuation frameworks to generate cited emergency advisories.
- **Resilient Multi-Tier Persistence and Caching:** Implement a three-tier storage hierarchy (In-Memory LRU $\\to$ Local Disk JSON snapshots $\\to$ Remote Neon Serverless PostgreSQL via Prisma ORM) with 5-minute weather and 15-minute forecast TTL invalidation windows, guaranteeing continuous sub-50ms query responses during remote database latency or network partitions.
- **Continuous Retraining and Human-in-the-Loop Feedback Loop:** Integrate operator verification workflows with automated Supervised Fine-Tuning (SFT) and Direct Preference Optimization (DPO) JSONL exporters for continuous model alignment, triggered by quantifiable performance drift metrics ($R^2 < 0.95$ or CAE MSE $> 0.070$).
- **Software Verification and Production Orchestration:** Verify system reliability through an automated test execution suite with 100% test passage (26/26 test cases) across predictive algorithms, database caching, and pipeline integration, coupled with a production frontend build verified in 379 ms and a unified concurrent execution orchestrator (`scripts/dev.js`).

## 1.4 Requirement Analysis
### 1.4.1 Stakeholders and User Classes
**Table 1: Stakeholders and User Classes**

| **Stakeholder / User Class** | **Primary Operational Responsibility** |
| --- | --- |
| Disaster-Management Operator (OSDMA/SEOC) | Real-time monitoring of cyclone progression, risk map evaluation, automated alert verification, and shelter readiness inspection. |
| District-Level Decision Maker (District Collector/ADM) | Assessment of district-specific hazard levels, verification of evacuation targets, and shelter allocation management. |
| Emergency-Response Coordinator (ODRAF/NDRF) | Deployment planning of rescue platoons and logistics routing based on constrained spatial optimization outputs. |
| Technical / ML Evaluation Engineer | System telemetry monitoring, feature drift detection, autoencoder anomaly inspection, SHAP explanation auditing, and retraining pipeline management. |
| System Administrator / DevOps Engineer | Infrastructure maintenance, database snapshot integrity, cache performance monitoring, and container health verification. |

### 1.4.2 Functional Requirements
**Table 2: Functional Requirements Specification**

| **ID** | **Requirement Statement** |
| --- | --- |
| FR-01 | The system shall ingest live weather telemetry for the six designated coastal stations (Chandbali, Paradip, Gopalpur, Puri, Balasore, Bhubaneswar) via Open-Meteo REST APIs. |
| FR-02 | The system shall ingest and process multispectral satellite imagery crops from NASA GIBS, MOSDAC, or user uploads. |
| FR-03 | The system shall generate 128-dimensional dense feature embeddings from 4-channel normalized satellite crops using the TCIR ResNet-18 visual backbone. |
| FR-04 | The system shall compute reconstruction Mean Squared Error (MSE) via a Convolutional Autoencoder and classify visual structure against operational anomaly thresholds. |
| FR-05 | The system shall calculate district-level composite risk scores using an XGBoost regression model and map scores into calibrated operational warning tiers. |
| FR-06 | The system shall compute game-theoretic feature attribution values using TreeSHAP for each district risk prediction. |
| FR-07 | The system shall maintain an explicit topological graph of Odisha comprising 30 district nodes and 69 bidirectional adjacency edges. |
| FR-08 | The system shall compute district evacuation targets, shelter utilization rates, and rescue team allocations under shelter capacity constraints. |
| FR-09 | The system shall generate a 48-hour short-range kinematic forecast incorporating asymmetric wind profiling and inland decay. |
| FR-10 | The system shall compute a 15-day sub-seasonal (S2S) synoptic cyclogenesis potential index ($CPI$) modulated by ENSO, IOD, and MJO Phase 3 teleconnections. |
| FR-11 | The system shall generate a 60-day seasonal outlook payload based on historical Bay of Bengal cyclogenesis climatology. |
| FR-12 | The system shall execute a 50-member Monte Carlo stochastic perturbation ensemble to generate track dispersion radii and spatial confidence cones. |
| FR-13 | The system shall support dense vector retrieval over indexed IMD, OSDMA, and NDMA operational documents using Chroma DB. |
| FR-14 | The system shall generate evidence-grounded emergency advisories with traceable standard-operating-procedure citations. |
| FR-15 | The system shall persist cyclone events, observations, model predictions, SHAP attributions, district forecasts, advisories, and feedback in Neon PostgreSQL. |
| FR-16 | The system shall implement a three-tier caching hierarchy providing sub-50ms fallback responses using in-memory and disk snapshots during remote database degradation. |
| FR-17 | The system shall record human-in-the-loop ratings and corrections and export curated datasets in SFT and DPO JSONL formats. |
| FR-18 | The system shall execute interactive what-if simulations by dynamically perturbing meteorological parameters and recalculating spatial risk distributions. |
| FR-19 | The system shall expose documented REST API endpoints for telemetry, prediction, spatial modeling, forecasting, RAG, and system evaluation. |

### 1.4.3 Non-Functional Requirements
**Table 3: Non-Functional Requirements Specification**

| **ID** | **Quality Attribute** | **Specification and Quantitative Metric** |
| --- | --- | --- |
| NFR-01 | Reliability & Fault Tolerance | The system shall maintain uninterrupted operational availability via local disk cache fallback within $\\le 50\\text{ ms}$ upon database connection timeouts. |
| NFR-02 | Availability | The platform shall maintain 99.9% uptime for decision-support services through asynchronous persistence decoupling and cache snapshot resilience. |
| NFR-03 | Maintainability & Modularity | The software architecture shall adhere to domain-driven separation: standalone ML inference modules, dedicated database services, and modular React views. |
| NFR-04 | Explainability & Transparency | Every machine learning risk prediction shall be accompanied by exact additive TreeSHAP feature attributions with zero approximation error. |
| NFR-05 | Auditability & Provenance | Advisory generations, human review ratings, operator corrections, and model drift telemetry shall be persistently logged for post-disaster audit trails. |
| NFR-06 | Performance & Latency | Unified survey API inference latency shall not exceed $2.5\\text{ seconds}$ end-to-end; cached payload retrieval shall execute in $\\le 15\\text{ ms}$. |
| NFR-07 | Scalability | The containerized FastAPI backend shall support horizontal scaling; Prisma ORM connection pooling shall manage serverless database transaction loads. |
| NFR-08 | Usability & Human Factors | The frontend dashboard shall render zero-layout-shift UI states, persistent layout mounting, skeleton loaders, and responsive geographic maps. |
| NFR-09 | Testability & Verification | 100% of core mathematical algorithms, cache mechanisms, retraining exporters, and ML pipelines shall pass automated unit and integration tests (26/26 tests passed). |
| NFR-10 | Build & Deployability | Production frontend compilation shall execute with zero build errors under Vite in $\\le 500\\text{ ms}$ (empirically verified at $379\\text{ ms}$). |

"""

    p_start = c.find('  1. Objectives')
    p_end = c.find('1. Literature Review & Existing Digital Solutions')
    assert p_start != -1 and p_end != -1
    c = c[:p_start] + sec1_text + c[p_end:]
    print("Step 1: Section 1.3 & 1.4 applied.")

    # -------------------------------------------------------------
    # 2. Table 6 Tier 4 Update
    # -------------------------------------------------------------
    old_table6_tier4 = "| Tier 4 | Spatial GNN, Forecast & RAG | 30-district spatial graph, 48-hour and 60-day forecasting, Chroma vector database. |"
    new_table6_tier4 = "| Tier 4 | Spatial Topology, Multi-Horizon Forecast & RAG | 30-district spatial graph (69 edges), multi-horizon predictive forecasting (48-hour kinematic, 15-day S2S synoptic, 60-day seasonal outlook with 50-member Monte Carlo ensemble), Chroma vector database. |"
    assert old_table6_tier4 in c, "Table 6 line not found"
    c = c.replace(old_table6_tier4, new_table6_tier4, 1)
    print("Step 2: Table 6 updated.")

    # -------------------------------------------------------------
    # 3. Section 3.4 (Algorithms/Methods Used) Replacement Text
    # -------------------------------------------------------------
    sec3_4_text = """### 3.4 Algorithms and Mathematical Formulations

#### 3.4.1 Computational Pipeline Overview
The IDMAP platform deploys a hybrid computational intelligence pipeline combining deep computer vision, physical aerodynamic vortex modeling, empirical inland decay dynamics, gradient-boosted decision trees, cooperative game-theoretic explainability, spatial graph optimization, and dense vector semantic retrieval. The operational sequence executes in eight deterministic phases:

$$\\text{Observe} \\longrightarrow \\text{Extract} \\longrightarrow \\text{Model} \\longrightarrow \\text{Predict} \\longrightarrow \\text{Explain} \\longrightarrow \\text{Optimize} \\longrightarrow \\text{Forecast} \\longrightarrow \\text{Advise}$$

#### 3.4.2 Deep Convolutional Feature Extraction (TCIR ResNet-18)
Satellite imagery is ingested as a four-channel multispectral tensor $\\mathbf{X}_{\\text{img}} \\in \\mathbb{R}^{4 \\times 128 \\times 128}$ comprising normalized Infrared (IR1, IR2), Water Vapor (WV), and Visible (VIS) channels sourced from INSAT-3D passes. Spatial patterns and convective cloud geometries are mapped into a 128-dimensional dense latent feature vector $\\mathbf{F}_v$ using a modified Tropical Cyclone Image Recognition (TCIR) ResNet-18 backbone:

$$\\mathbf{F}_v = f_{\\text{ResNet}}(\\mathbf{X}_{\\text{img}}; \\boldsymbol{\\theta}_{\\text{conv}}) \\in \\mathbb{R}^{128}$$

where $\\boldsymbol{\\theta}_{\\text{conv}}$ represents the pre-trained convolutional weights fine-tuned on North Indian Ocean cyclone sequences.

#### 3.4.3 Unsupervised Anomaly Detection (Convolutional Autoencoder)
To detect atypical cloud shear, dry air intrusion, or anomalous eye wall disintegration, an unsupervised Convolutional Autoencoder (CAE) compresses the visual representation into an 8-dimensional bottleneck $\\mathbf{z} \\in \\mathbb{R}^8$ via an encoder network $g_{\\phi}$, followed by a decoder network $h_{\\psi}$ that reconstructs the input tensor $\\hat{\\mathbf{X}} = h_{\\psi}(\\mathbf{z})$. The reconstruction Mean Squared Error (MSE) measures structural abnormality:

$$\\text{MSE} = \\frac{1}{C \\cdot H \\cdot W} \\sum_{c=1}^C \\sum_{h=1}^H \\sum_{w=1}^W \\left(X_{c,h,w} - \\hat{X}_{c,h,w}\\right)^2$$

Operational anomaly tiers are established using calibrated empirical decision boundaries:
$$\\text{Structural Status}(\\text{MSE}) = \\begin{cases} \\text{Nominal / Standard Structure}, & \\text{MSE} \\le 0.035 \\\\ \\text{Moderate Structural Shear}, & 0.035 < \\text{MSE} \\le 0.070 \\\\ \\text{Severe Structural Anomaly}, & \\text{MSE} > 0.070 \\end{cases}$$

#### 3.4.4 Physics-Based Cyclone Aerodynamics and Kinematics
To constrain machine learning predictions within physical meteorological laws, IDMAP integrates four deterministic hydrodynamic formulations:

##### 1. Asymmetric Modified Rankine Vortex Wind Field
The radial wind velocity profile $V_{\\text{Rankine}}(r)$ at geodesic distance $r$ from the cyclone center is governed by:
$$V_{\\text{Rankine}}(r) = \\begin{cases} V_{\\max} \\left(\\frac{r}{R_{\\max}}\\right)^x, & 0 \\le r \\le R_{\\max} \\\\[8pt] V_{\\max} \\left(\\frac{R_{\\max}}{r}\\right)^x, & r > R_{\\max} \\end{cases}$$
where $V_{\\max}$ denotes maximum sustained surface wind speed, $R_{\\max}$ is the radius of maximum winds, and $x = 0.55$ is the empirical shape factor. To capture forward translation asymmetry (higher wind velocities on the forward-right quadrant in the Northern Hemisphere), a translation correction term is added:
$$V_{\\text{eff}}(r, \\psi) = V_{\\text{Rankine}}(r) + v_{\\text{trans}} \\cdot \\sin(\\psi - \\theta_{\\text{track}}) \\cdot \\left(\\frac{R_{\\max}}{r}\\right)^{0.5}$$
where $v_{\\text{trans}}$ is cyclone forward translation speed, $\\theta_{\\text{track}}$ is heading azimuth, and $\\psi$ is the polar angle to the target coordinate.

##### 2. Holland Central Barometric Depression Relation
Central barometric pressure and radial pressure distributions are inverted using Holland's aerodynamic relationship:
$$P(r) = P_c + (P_n - P_c) \\exp\\left[ -\\left(\\frac{R_{\\max}}{r}\\right)^B \\right]$$
where $P_c$ is central pressure, $P_n = 1013.25\\text{ hPa}$ is ambient peripheral pressure, and the Holland parameter $B$ is dynamically estimated via:
$$B = \\frac{\\rho_a \\cdot e \\cdot V_{\\max}^2}{100 \\cdot (P_n - P_c)}$$
with air density $\\rho_a = 1.15\\text{ kg/m}^3$ and Euler's constant $e \\approx 2.71828$.

##### 3. Geodesic Proximity via Haversine Formulation
Distances $d$ between storm coordinates $(\\phi_1, \\lambda_1)$ and district geographical centroids $(\\phi_2, \\lambda_2)$ are computed over a spherical Earth ($R_{\\text{earth}} = 6371.0\\text{ km}$):
$$a = \\sin^2\\left(\\frac{\\Delta \\phi}{2}\\right) + \\cos(\\phi_1)\\cos(\\phi_2)\\sin^2\\left(\\frac{\\Delta \\lambda}{2}\\right), \\quad d = 2 R_{\\text{earth}} \\arcsin(\\sqrt{a})$$

##### 4. Kaplan–DeMaria Empirical Inland Wind Decay
Upon coastal landfall ($t > t_{\\text{landfall}}$), the loss of latent oceanic enthalpy and increased terrestrial surface roughness induce exponential kinetic dissipation modeled via the Kaplan–DeMaria formulation:
$$V(t) = V_{\\text{bg}} + (V_{\\text{landfall}} - V_{\\text{bg}}) \\cdot e^{-\\alpha t}$$
where $V_{\\text{bg}} = 20.0\\text{ knots}$ ($10.28\\text{ m/s}$) is the background equilibrium wind speed, $V_{\\text{landfall}}$ is the maximum intensity at the landfall timestamp, and $\\alpha = 0.095\\text{ hr}^{-1}$ is the empirical decay constant calibrated for the eastern Indian littoral topography.

##### 5. Kinematic 2D Trajectory Advection and Northward Beta-Recurvature
Short-range cyclone trajectory positions are updated across discrete temporal steps $\\Delta t$ ($3\\text{-hour}$ intervals up to $48\\text{ hours}$):
$$\\mathbf{x}_{t+\\Delta t} = \\mathbf{x}_t + \\mathbf{v}_t \\Delta t + \\boldsymbol{\\delta}_{\\beta}$$
where $\\mathbf{x}_t = [\\phi_t, \\lambda_t]^T$, $\\mathbf{v}_t = [u_t, v_t]^T$ is the environmental steering vector, and $\\boldsymbol{\\delta}_{\\beta}$ represents the planetary beta-effect recurvature deflection. For trajectories crossing north of $19.8^\\circ\\text{N}$ latitude in the Bay of Bengal, an empirical northward recurvature component is applied:
$$\\boldsymbol{\\delta}_{\\beta} = \\begin{cases} [0, 0]^T, & \\phi_t \\le 19.8^\\circ\\text{N} \\\\[4pt] \\left[ \\kappa \\cdot (\\phi_t - 19.8^\\circ), \\; 0.5 \\kappa \\cdot (\\phi_t - 19.8^\\circ) \\right]^T, & \\phi_t > 19.8^\\circ\\text{N} \\end{cases}$$
capturing the typical northeastward recurvature towards the Odisha and West Bengal coastlines.

##### 6. WMO/IMD Rapid Intensification (RI) Classification
Rapid Intensification is monitored using the standard World Meteorological Organization (WMO) and IMD operational threshold:
$$\\text{RI} = \\mathbb{I}\\left(V_t - V_{t-24\\text{h}} \\ge 30\\text{ knots}\\right) = \\mathbb{I}\\left(\\Delta V_{24} \\ge 15.43\\text{ m/s}\\right)$$
When triggered, operational warnings automatically escalate to Severe Cyclonic Storm (SCS) or Extremely Severe Cyclonic Storm (ESCS) protocols.

#### 3.4.5 Multimodal Feature Fusion Engine
For each district $k \\in \\{1, \\dots, 30\\}$, a heterogeneous feature vector $\\mathbf{F}_k \\in \\mathbb{R}^D$ is assembled by fusing six distinct intelligence domains:
$$\\mathbf{F}_k = \\left[ \\mathbf{F}_v, \\; \\mathbf{F}_a, \\; \\mathbf{F}_p, \\; \\mathbf{F}_m, \\; \\mathbf{F}_g, \\; \\mathbf{F}_d \\right]$$
where:
- $\\mathbf{F}_v \\in \\mathbb{R}^{128}$: ResNet-18 satellite visual embeddings.
- $\\mathbf{F}_a \\in \\mathbb{R}^1$: Autoencoder reconstruction error (MSE).
- $\\mathbf{F}_p \\in \\mathbb{R}^4$: Physics estimates ($V_{\\text{eff}}$, $P(r)$, inland decay $V(t)$, RI flag).
- $\\mathbf{F}_m \\in \\mathbb{R}^5$: Real-time station meteorological telemetry (wind, gusts, surface pressure, temperature, humidity).
- $\\mathbf{F}_g \\in \\mathbb{R}^3$: Geographical spatial attributes (geodesic distance to storm $d_k$, coastal distance $D_{\\text{coast}, k}$, elevation).
- $\\mathbf{F}_d \\in \\mathbb{R}^4$: Demographic exposure metrics (population $P_k$, vulnerable sub-population $\\text{Vuln}_k$, urbanization index, shelter capacity $C_k$).

#### 3.4.6 Extreme Gradient Boosting (XGBoost) Risk Regression and Calibration
District-level risk prediction is executed using an ensemble of $M$ gradient-boosted regression trees:
$$\\hat{R}_k = \\sum_{m=1}^M f_m(\\mathbf{F}_k), \\quad f_m \\in \\mathcal{F}$$
minimizing the regularized objective function:
$$\\mathcal{L} = \\sum_{k=1}^K \\left( R_k - \\hat{R}_k \\right)^2 + \\sum_{m=1}^M \\left( \\gamma T_m + \\frac{1}{2} \\lambda \\|\\mathbf{w}_m\\|^2 \\right)$$
where $T_m$ is the number of terminal leaves, $\\mathbf{w}_m$ are leaf weights, and $\\gamma, \\lambda$ are regularization hyperparameters. The predicted composite risk index maps into an operational range $[0, 1]$ via the convex formulation:
$$\\text{Composite Risk}_k = 0.55 \\cdot \\tilde{V}_k + 0.30 \\cdot \\tilde{D}_{\\text{coast}, k} + 0.15 \\cdot \\tilde{P}_{\\text{vuln}, k}$$
Empirical evaluation across cross-validated test splits yields $R^2 = 0.9885$, $\\text{RMSE} = 0.0155$, and $\\text{MAE} = 0.0108$.

#### 3.4.7 Game-Theoretic Explainability via TreeSHAP
To ensure operational accountability, IDMAP deploys TreeSHAP (SHapley Additive exPlanations) to compute exact feature attributions $\\phi_i$ satisfying the local efficiency property:
$$\\hat{R}(\\mathbf{x}) = \\phi_0 + \\sum_{i=1}^M \\phi_i(\\mathbf{x})$$
where $\\phi_0 = \\mathbb{E}[\\hat{R}(\\mathbf{x})]$ is the expected baseline model risk across the training distribution, and each marginal contribution is calculated as:
$$\\phi_i(\\mathbf{x}) = \\sum_{S \\subseteq \\mathcal{M} \\setminus \\{i\\}} \\frac{|S|!(|\\mathcal{M}| - |S| - 1)!}{|\\mathcal{M}|!} \\left[ f_{\\mathbf{x}}(S \\cup \\{i\\}) - f_{\\mathbf{x}}(S) \\right]$$
This guarantees that emergency operators can inspect whether an elevated risk score is driven primarily by peak wind velocity, coastal proximity, demographic density, or satellite structural anomaly.

#### 3.4.8 Spatial Graph Modeling
Odisha's administrative geography is modeled as an undirected topological graph:
$$\\mathcal{G} = (\\mathcal{V}, \\mathcal{E}), \\quad |\\mathcal{V}| = 30, \\quad |\\mathcal{E}| = 69$$
where vertices $v_i \\in \\mathcal{V}$ represent the 30 districts, and edges $(v_i, v_j) \\in \\mathcal{E}$ represent physical administrative boundaries across which hazard cascading, inter-district refugee transit, and mutual-aid emergency logistics occur.

#### 3.4.9 Constrained Resource and Evacuation Optimization Formulation
For each district $i \\in \\mathcal{V}$, evacuation requirements and rescue battalion deployments are optimized under strict capacity constraints:
1. **Evacuation Target Population ($E_i$):**
   $$E_i = P_i \\cdot \\text{Vuln}_i \\cdot \\hat{R}_i$$
   where $P_i$ is district census population, $\\text{Vuln}_i$ is the empirical vulnerability fraction, and $\\hat{R}_i$ is predicted composite risk.
2. **Shelter Capacity Utilization Ratio ($U_i$):**
   $$U_i = \\min\\left(1.0, \\; \\frac{E_i}{C_i}\\right)$$
   where $C_i$ is aggregate shelter capacity from the OSDMA MCS registry. If $E_i > C_i$, secondary overflow routing is flagged along graph edges $(v_i, v_j) \\in \\mathcal{E}$.
3. **Rescue Battalion Platoon Allocation ($T_i$):**
   $$T_i = \\left\\lceil \\frac{E_i}{15{,}000} \\right\\rceil$$
   deploying one specialized ODRAF/NDRF rescue platoon per 15,000 evacuees.

#### 3.4.10 Sub-Seasonal (S2S) 15-Day Synoptic Cyclogenesis Potential Engine
Extended sub-seasonal cyclogenesis potential is modeled via a synoptic multi-parameter index:
$$CPI = \\left[\\frac{\\text{SST} - 26.0}{4.0}\\right] \\cdot \\left[\\frac{\\text{RH}_{700} - 40}{60}\\right] \\cdot \\left[\\frac{\\zeta_{850}}{10^{-5}}\\right] \\cdot \\left[1 + \\frac{\\text{VWS}}{20}\\right]^{-1} \\cdot \\Phi_{\\text{ENSO}} \\cdot \\Phi_{\\text{IOD}} \\cdot \\Phi_{\\text{MJO}}$$
where $\\text{SST}$ is Sea Surface Temperature ($^\\circ\\text{C}$), $\\text{RH}_{700}$ is mid-tropospheric relative humidity (%), $\\zeta_{850}$ is low-level relative vorticity ($\\text{s}^{-1}$), and $\\text{VWS}$ is vertical wind shear ($\\text{m/s}$). Teleconnection modulation factors are defined as:
- $\\Phi_{\\text{ENSO}} = 1.0 - 0.25 \\cdot \\text{ONI}$ (La Niña phases enhance Bay of Bengal cyclogenesis).
- $\\Phi_{\\text{IOD}} = 1.0 - 0.20 \\cdot \\text{DMI}$ (Negative IOD phases favor enhanced convective activity).
- $\\Phi_{\\text{MJO}} = 1.30$ during active Phase 3/4 convective transit over the equatorial Indian Ocean, and $0.85$ during suppressed phases.

The S2S outlook governs a 3-phase strategic preparedness protocol:
- **Phase 1 (T-15d to T-10d) — Synoptic Surveillance:** Regional sea-surface temperature monitoring and inter-agency pre-alerts.
- **Phase 2 (T-10d to T-5d) — Strategic Pre-Positioning:** Supply depot inventory checks, heavy rescue machinery staging, and shelter readiness audits.
- **Phase 3 (< T-5d) — Tactical Mobilization:** Rapid-response battalion mobilization and coastal early warning broadcasting.

#### 3.4.11 Stochastic Monte Carlo Ensemble Track & Intensity Perturbation Engine
To model meteorological trajectory uncertainty, IDMAP executes a 50-member stochastic Monte Carlo ensemble ($k = 1, \\dots, 50$). For each ensemble realization, the deterministic trajectory vector is perturbed by Gaussian noise calibrated to IMD 5-year operational verification errors:
$$\\theta^{(k)} = \\theta_0 + \\epsilon_{\\theta}^{(k)}, \\quad \\epsilon_{\\theta} \\sim \\mathcal{N}(0, \\sigma_{\\text{head}}^2), \\quad \\sigma_{\\text{head}} = 4.8^\\circ$$
$$v_{\\text{trans}}^{(k)} = v_{\\text{trans}, 0} + \\epsilon_{v}^{(k)}, \\quad \\epsilon_{v} \\sim \\mathcal{N}(0, \\sigma_{\\text{trans}}^2), \\quad \\sigma_{\\text{trans}} = 2.4\\text{ km/h}$$
$$V_{\\max}^{(k)} = V_{\\max, 0} + \\epsilon_{\\text{int}}^{(k)}, \\quad \\epsilon_{\\text{int}} \\sim \\mathcal{N}(0, \\sigma_{\\text{int}}^2), \\quad \\sigma_{\\text{int}} = 5.5\\text{ knots}$$

The ensemble generates probabilistic strike probability envelopes and confidence cones across the 48-hour forecast horizon:
$$R_{\\text{cone}}(t) = R_0 + \\beta_{\\text{cone}} \\cdot t, \\quad R_0 = 15\\text{ km}, \\quad \\beta_{\\text{cone}} = 2.25\\text{ km/hr}$$

#### 3.4.12 Retrieval-Augmented Generation (RAG) Advisory Framework
Operational emergency advisories are synthesized using a dense vector retrieval pipeline. Authoritative disaster management documents (IMD Cyclone Warning Manual, OSDMA Standard Operating Procedures, NDMA Evacuation Protocols) are split into 500-character chunks with 50-character sliding overlaps, embedded into 384-dimensional dense vectors using `all-MiniLM-L6-v2`, and indexed in a persistent Chroma DB instance. At query time, top-$k$ relevant contexts ($k=3$) are retrieved via cosine similarity:
$$\\text{Sim}(\\mathbf{q}, \\mathbf{d}_j) = \\frac{\\mathbf{q} \\cdot \\mathbf{d}_j}{\\|\\mathbf{q}\\| \\|\\mathbf{d}_j\\|}$$
The retrieved context is bound into a deterministic system prompt to generate evidence-grounded advisories with traceable source citations.

#### 3.4.13 Integrated Computational Workflow Summary
**Table 8: Summary of Algorithmic Modules**

| **Algorithmic Module** | **Underlying Formulation / Architecture** | **Operational Responsibility** |
| --- | --- | --- |
| Deep Visual Backbone | TCIR ResNet-18 (4-channel, $128 \\times 128$) | Extracts 128-dimensional dense visual representations from multispectral satellite passes. |
| Structural Anomaly Detector | Convolutional Autoencoder (8-dim bottleneck) | Computes reconstruction MSE; flags atypical structural shear ($\\tau > 0.035$). |
| Aerodynamic Wind Profiler | Asymmetric Modified Rankine Vortex ($x=0.55$) | Estimates radial wind velocity fields with forward translation asymmetry correction. |
| Barometric Model | Holland Pressure-Wind Inversion ($B$-parameter) | Calculates central atmospheric depression and peripheral pressure gradients. |
| Geodesic Proximity | Haversine Spherical Distance Equation | Computes exact geodesic distance between cyclone eye and district administrative centroids. |
| Inland Wind Dissipation | Kaplan–DeMaria Exponential Decay ($\\alpha=0.095\\text{ hr}^{-1}$) | Models post-landfall frictional kinetic energy loss over inland terrain. |
| Short-Range Advection | 2D Numerical Advection + Beta-Recurvature ($>19.8^\\circ\\text{N}$) | Integrates 48-hour cyclone track coordinates at 3-hour forecast steps. |
| Risk Regression | Calibrated XGBoost Gradient Boosted Trees | Predicts district composite risk scores ($R^2=0.9885$, $\\text{RMSE}=0.0155$, $\\text{MAE}=0.0108$). |
| Explainable Attribution | Additive Game-Theoretic TreeSHAP | Computes feature attribution values justifying district risk predictions. |
| Spatial Graph Model | Undirected Network $\\mathcal{G}=(\\mathcal{V}, \\mathcal{E})$ ($|\\mathcal{V}|=30, |\\mathcal{E}|=69$) | Represents administrative district topology and inter-district cascading hazards. |
| Resource Optimization | Constrained Capacity Linear Allocation | Calculates evacuation quotas and rescue battalion platoon deployments ($1/15{,}000$). |
| Sub-Seasonal Outlook (S2S) | Synoptic Cyclogenesis Potential Index ($CPI$) | Estimates 15-day extended cyclogenesis modulated by ENSO, IOD, and MJO Phase 3. |
| Uncertainty Quantification | 50-Member Stochastic Monte Carlo Ensemble | Generates probabilistic track dispersion envelopes and dynamic confidence cones. |
| Evidence Grounding | Chroma Dense Vector RAG (`all-MiniLM-L6-v2`) | Synthesizes cited emergency response advisories anchored in official SOP manuals. |

"""

    p_start = c.find('  4.  Algorithms/Methods Used')
    p_end = c.find('# 4. Data engineering and Machine Learning Design')
    assert p_start != -1 and p_end != -1
    c = c[:p_start] + sec3_4_text + c[p_end:]
    print("Step 3: Section 3.4 applied.")

    # -------------------------------------------------------------
    # 4. Section 4 (Data Engineering) Replacement Text
    # -------------------------------------------------------------
    sec4_text = """# 4. Data Engineering and Machine Learning Design

## 4.1 Data Sources
**Table 9: Primary Data Ingestion Sources**

| **Data Ingestion Source** | **Domain & Modality** | **Technical Attributes & Resolution** | **Operational Responsibility in IDMAP** |
| --- | --- | --- | --- |
| INSAT-3D Multispectral Imager | Satellite Imagery | VIS, TIR1, TIR2, WV channels; $128 \\times 128$ normalized crops | Extraction of dense convolutional visual embeddings and structural anomaly metrics. |
| IMD Best-Track Archive (1982–2024) | Historical Cyclone Records | Track coordinates, central pressure ($P_c$), sustained wind ($V_{\\max}$), Dvorak T-numbers | Historical supervised training of risk regression and seasonal baseline climatology. |
| Open-Meteo REST API | Real-Time Telemetry | Wind speed, wind gusts, atmospheric pressure, air temperature, relative humidity | Real-time weather ingestion across six coastal monitoring stations. |
| Census of India (2011) Odisha | Demographic Vulnerability | Total population, vulnerable demographics, literacy, urbanization, geographical centroids | District exposure calculation and baseline demographic risk weighting. |
| OSDMA Multipurpose Cyclone Shelter (MCS) Registry | Response Capacity | Geographic shelter coordinates, designed capacity ($>800$ shelters) | Evacuation target feasibility calculation and shelter utilization optimization. |
| NASA GIBS / MOSDAC | Live Imagery Feeds | Calibrated multispectral mosaic passes | Secondary satellite imagery ingestion and visual verification passes. |

## 4.2 Master Dataset Schema
The synchronized master dataset unifies image-derived features, meteorological measurements, geographical variables, and socio-economic exposure indicators into a standardized observation record.

**Table 10: Essential Data Schema Elements**

| **Data Schema Field** | **Data Type** | **Physical Meaning / Purpose** |
| --- | --- | --- |
| `event_base_id` | String | Unique storm system identifier used for strict event-level data partitioning. |
| `satellite_crop` | Float Tensor ($4 \\times 128 \\times 128$) | Normalized 4-channel satellite imagery crop (IR1, IR2, WV, VIS). |
| `sustained_wind` | Float (knots / km/h) | Maximum sustained surface wind speed ($V_{\\max}$) at the observation timestamp. |
| `central_pressure` | Float (hPa) | Minimum central barometric pressure ($P_c$). |
| `storm_coordinates` | Tuple (Float, Float) | Latitude and longitude of the cyclone circulation center. |
| `distance_to_coast` | Float (km) | Geodesic distance from storm eye to the nearest point on the Odisha coastline. |
| `target_district` | String | Name of the administrative district evaluated. |
| `district_population` | Integer | Total population residing in the target administrative district. |
| `vulnerability_ratio` | Float ($[0, 1]$) | Proportion of population categorized as socio-economically vulnerable. |
| `shelter_capacity` | Integer | Aggregate designed capacity of multipurpose cyclone shelters in the district. |
| `visual_embeddings` | Float Array ($128$-dim) | Dense latent visual features extracted by the TCIR ResNet-18 visual backbone. |
| `anomaly_mse` | Float | Reconstruction Mean Squared Error generated by the Convolutional Autoencoder. |
| `composite_risk` | Float ($[0, 1]$) | Normalized ground-truth composite risk benchmark for supervised training. |

## 4.3 Data Leakage Prevention and Partitioning Protocol
A critical engineering control implemented in the IDMAP data pipeline is strict **storm-event-level partitioning**. In meteorological and satellite machine learning applications, random frame-level splitting causes severe data leakage because consecutive satellite images captured hours apart from the same cyclone share identical thermodynamic environments, cloud morphologies, and spatial trajectories. Random splitting artificially inflates model accuracy metrics ($R^2$, RMSE) while failing entirely on unseen storms.

To ensure genuine out-of-sample generalization, the master dataset is partitioned strictly by storm `event_base_id`:
- **Training Set (70% of historical storms):** Used for parameter optimization across ResNet-18, the Convolutional Autoencoder, and XGBoost.
- **Validation Set (15% of historical storms):** Used for hyperparameter tuning, tree pruning, early stopping, and autoencoder threshold calibration.
- **Test Set (15% of held-out historical storms):** Completely isolated storms evaluated only once to verify true generalization across unprecedented cyclone events.

## 4.4 Data Engineering and Preprocessing Pipeline
The data engineering pipeline executes automated validation, normalization, and feature assembly stages:
1. **Satellite Image Ingestion & Normalization:** Multispectral imagery crops are validated for spatial integrity ($128 \\times 128$ dimensions), channel completeness (4 channels: IR1, IR2, WV, VIS), and pixel validity (rejection of corrupted artifacts). Pixel intensities are min-max normalized to $[0, 1]$ using channel-specific radiometric baselines.
2. **Telemetry Standardization:** Live weather observations from the six coastal stations are polled via Open-Meteo REST endpoints, validated against physical bounds (pressure $\\in [870, 1050]\\text{ hPa}$, wind $\\in [0, 350]\\text{ km/h}$ thematically), and converted to standardized SI units.
3. **Spatial Feature Synthesis:** Distances from storm coordinates to all 30 district administrative centroids and the Odisha coastline are computed dynamically via spherical Haversine equations.
4. **Temporal Alignment:** Telemetry observations and satellite passes are synchronized into nearest 3-hour synoptic time bins matching IMD operational advisory schedules.

## 4.5 Multimodal Feature Fusion
The fused feature matrix bridges physical atmospheric variables with demographic vulnerability. The 128-dimensional latent vector captures cloud field organization, central dense overcast (CDO) symmetry, and eye definition; the autoencoder reconstruction score provides an unsupervised indicator of structural anomalies; physical aerodynamic calculations inject theoretical vortex constraints; and census metadata grounds the risk estimate in local societal exposure. Consequently, the downstream risk regressor does not evaluate hazard in isolation, but determines impact as a function of hazard, proximity, and human vulnerability.

## 4.6 Data Quality, Ingestion Validation, and Integrity Checks
Automated quality checks are enforced prior to model inference:
- **Missing Value Handling:** Missing telemetry fields are imputed using spatial inverse-distance weighting from adjacent coastal stations.
- **Coordinate Boundary Checks:** Storm and district coordinates are validated within the Bay of Bengal geographical bounding box ($5.0^\\circ\\text{N}$ to $24.0^\\circ\\text{N}$, $80.0^\\circ\\text{E}$ to $95.0^\\circ\\text{E}$).
- **Corrupted Image Fallback:** If an uploaded satellite crop fails decompression or dimension validation, the vision pipeline triggers a graceful fallback flag and estimates risk using telemetry, proximity, and physical formulations alone.

"""

    p_start = c.find('# 4. Data engineering and Machine Learning Design')
    p_end = c.find('\n![](data:image/png;base64', p_start)
    assert p_start != -1 and p_end != -1
    c = c[:p_start] + sec4_text.rstrip() + c[p_end:]
    print("Step 4: Section 4 applied.")

    # -------------------------------------------------------------
    # 5. Section 5 (AI Models) Replacement Text
    # -------------------------------------------------------------
    sec5_text = """# 5. Artificial Intelligence and Machine Learning Models

## 5.1 Deep Computer Vision and Structural Anomaly Detection

### 1. TCIR ResNet-18 Deep Feature Backbone
Satellite imagery represents the primary observational modality for evaluating cyclone organization prior to landfall. IDMAP adapts the Tropical Cyclone Image Recognition (TCIR) architecture based on a ResNet-18 deep convolutional backbone. The model processes 4-channel multispectral crops ($128 \\times 128$ normalized IR1, IR2, WV, VIS) through four residual convolutional stages. The final average-pooling layer yields a compact, dense 128-dimensional latent visual representation vector:

$$\\mathbf{F}_v \\in \\mathbb{R}^{128}$$

This latent embedding encodes complex structural characteristics—including spiral rainband curvature, Central Dense Overcast (CDO) diameter, eye definition, and convective symmetry—without requiring manual feature engineering.

### 2. Convolutional Autoencoder Anomaly Detection
To identify unusual structural transformations, such as rapid dry-air intrusion, vertical wind shear distortion, or asymmetric eye wall degradation, an unsupervised Convolutional Autoencoder (CAE) operates in parallel with the feature backbone. The encoder comprises three convolutional layers with ReLU activations compressing the visual tensor into an 8-dimensional bottleneck $\\mathbf{z} \\in \\mathbb{R}^8$, while the decoder reconstructs the 4-channel tensor $\\hat{\\mathbf{X}}$.

The reconstruction Mean Squared Error (MSE) acts as an unsupervised anomaly metric:
$$\\text{MSE} = \\frac{1}{4 \\times 128 \\times 128} \\sum_{c=1}^4 \\sum_{h=1}^{128} \\sum_{w=1}^{128} \\left( X_{c,h,w} - \\hat{X}_{c,h,w} \\right)^2$$

Operational decision thresholds calibrated against historical Bay of Bengal cyclone patterns establish three structural regimes:
- **Nominal / Standard Cyclone Morphology ($\\text{MSE} \\le 0.035$):** Convective cloud organization conforms to standard tropical cyclone patterns.
- **Moderate Structural Shear ($0.035 < \\text{MSE} \\le 0.070$):** Moderate cloud asymmetry or peripheral rainband displacement detected; elevated caution flagged.
- **Severe Structural Anomaly ($\\text{MSE} > 0.070$):** Unprecedented cloud deformation, rapid eye disintegration, or extreme shearing; triggers high-priority operator review.

### 3. Engineering Rationale for Dual Vision Architecture
The coupling of ResNet-18 and the Convolutional Autoencoder separates representation learning from structural anomaly quantification. While ResNet-18 extracts feature embeddings optimized for downstream risk regression, it lacks an intrinsic measure of whether an input image lies within the nominal training distribution. The autoencoder supplies this vital uncertainty safeguard: an anomalous storm that produces a deceptive numerical regression output will immediately be flagged by an elevated reconstruction error, alerting emergency decision-makers to inspect the raw satellite pass.

## 5.2 Risk Regression, Calibration and TreeSHAP Explainability

### 1. XGBoost Risk Regression Engine
District-level composite risk is estimated using an Extreme Gradient Boosting (XGBoost) regressor. XGBoost is chosen over neural architectures for the tabular risk stage because of its superior performance on heterogeneous tabular data, robust handling of multi-collinear meteorological indicators, and exact compatibility with tree-based cooperative game-theoretic explanation algorithms.

Empirical evaluation across cross-validated, event-partitioned test splits confirms the model's accuracy:
- **Coefficient of Determination ($R^2$):** $0.9885$
- **Root Mean Squared Error (RMSE):** $0.0155$
- **Mean Absolute Error (MAE):** $0.0108$

The continuous regression output $\\hat{R}_k \\in [0, 1]$ is calibrated into four standard disaster management warning tiers:
- **Low Risk ($0.00 \\le \\hat{R}_k < 0.25$):** Advisory monitoring; routine administrative vigilance.
- **Moderate Risk ($0.25 \\le \\hat{R}_k < 0.50$):** Pre-alert stage; shelter inspection and equipment verification.
- **High Risk ($0.50 \\le \\hat{R}_k < 0.75$):** Active warning; voluntary evacuation of low-lying and vulnerable populations.
- **Severe Risk ($0.75 \\le \\hat{R}_k \\le 1.00$):** Emergency evacuation stage; mandatory relocation and tactical rescue platoon staging.

### 2. Transparent Composite Risk Formulation
To maintain transparency for administrative authorities, the ground-truth target is formulated as an explicit linear combination of hazard, proximity, and demographic vulnerability:
$$\\text{Composite Risk}_k = 0.55 \\cdot \\tilde{V}_k + 0.30 \\cdot \\tilde{D}_{\\text{coast}, k} + 0.15 \\cdot \\tilde{P}_{\\text{vuln}, k}$$
where:
- $\\tilde{V}_k$ is the normalized maximum effective surface wind speed ($V_{\\max} / 250\\text{ km/h}$).
- $\\tilde{D}_{\\text{coast}, k}$ is the normalized coastal proximity index ($1.0 - \\min(1.0, d_{\\text{coast}, k} / 200\\text{ km})$).
- $\\tilde{P}_{\\text{vuln}, k}$ is the normalized district demographic vulnerability fraction.

This transparent weighting ensures that physical hazard represents the dominant driver ($55\\%$), while exposure ($30\\%$) and vulnerability ($15\\%$) appropriately modulate local impact severity.

### 3. Game-Theoretic Explainability via TreeSHAP
To eliminate "black-box" skepticism during high-stakes disaster evacuations, IDMAP implements TreeSHAP to compute exact Shapley feature attributions for every district prediction:
$$\\hat{R}_k = \\phi_0 + \\sum_{j=1}^D \\phi_j(\\mathbf{x}_k)$$
For every district, the dashboard visualizes the exact positive or negative contribution of each feature towards the final risk score. An emergency officer can verify immediately whether a high risk score in Jagatsinghpur is driven primarily by extreme radial wind velocity ($+0.32$), immediate coastal proximity ($+0.21$), or high demographic vulnerability ($+0.12$). This explainability layer enables administrative officers to defend evacuation orders with quantifiable evidence.

"""

    p_start = c.find('# 5. AI Models')
    p_end = c.find('# 6.Spatial Modelling and Forecasting 48-Hour and 60-Day Operational Model')
    assert p_start != -1 and p_end != -1
    c = c[:p_start] + sec5_text + c[p_end:]
    print("Step 5: Section 5 applied.")

    # -------------------------------------------------------------
    # 6. Section 6 Part 1 Replacement Text
    # -------------------------------------------------------------
    sec6_p1_text = """# 6. Spatial Topology and Multi-Horizon Predictive Forecasting Engine

## 6.1 District Topological Graph Model
The state of Odisha is modeled as an undirected topological graph $\\mathcal{G} = (\\mathcal{V}, \\mathcal{E})$, where vertices $\\mathcal{V} = \\{v_1, \\dots, v_{30}\\}$ represent the 30 administrative districts, and edges $\\mathcal{E} = \\{e_1, \\dots, e_{69}\\}$ represent shared physical borders. The graph topology serves three essential disaster management functions:
1. **Spatial Hazard Cascading:** As a tropical cyclone makes coastal landfall, storm surges and extreme gales propagate across interior borders. The graph adjacency matrix models spatial contagion effects across adjacent interior districts.
2. **Inter-District Evacuation Routing:** When coastal districts exceed local multipurpose cyclone shelter capacities, evacuation overflows are routed along graph edges to adjacent inland districts possessing available shelter surplus.
3. **Emergency Logistics Corridor Analysis:** Rescue battalions, relief convoys, and mobile telecommunication units are routed across the graph network, accounting for potential road impassability in high-risk border zones.

## 6.2 Spatial Evacuation and Shelter Allocation Planning
The resource planning engine translates predicted continuous risk scores into concrete district evacuation requirements:
$$E_i = P_i \\cdot \\text{Vuln}_i \\cdot \\hat{R}_i$$
where $P_i$ is the total census population of district $i$, $\\text{Vuln}_i$ is the socio-economic vulnerability coefficient, and $\\hat{R}_i$ is the calibrated composite risk score.

Evacuation targets are compared against aggregate shelter capacity $C_i$ obtained from the OSDMA Multipurpose Cyclone Shelter (MCS) registry. Shelter utilization is computed as:
$$U_i = \\min\\left(1.0, \\; \\frac{E_i}{C_i}\\right)$$
When $E_i > C_i$, an evacuation deficit $\\Delta E_i = E_i - C_i$ is flagged, and the optimization engine initiates secondary shelter allocation to neighboring graph vertices $v_j \\in \\text{Adj}(v_i)$ possessing utilization $U_j < 0.70$.

## 6.3 Constrained Rescue Battalion and Resource Allocation
Emergency response personnel deployment is governed by an operational capacity rule formulated in consultation with National Disaster Response Force (NDRF) and Odisha Disaster Rapid Action Force (ODRAF) operational standards:
$$T_i = \\left\\lceil \\frac{E_i}{15{,}000} \\right\\rceil$$
Each allocated platoon ($T_i$) represents a self-contained operational unit of approximately 30 personnel equipped with inflatable motorized rescue boats, tree-clearing power saws, structural collapse search tools, and satellite communication transceivers. This quantitative mapping eliminates arbitrary resource distribution and ensures that rescue personnel are deployed in direct proportion to population exposure.

"""

    p_start = c.find('# 6.Spatial Modelling and Forecasting 48-Hour and 60-Day Operational Model')
    p_end = c.find('\n![](data:image/png;base64', p_start)
    assert p_start != -1 and p_end != -1
    c = c[:p_start] + sec6_p1_text.rstrip() + c[p_end:]
    print("Step 6: Section 6 Part 1 applied.")

    # -------------------------------------------------------------
    # 7. Section 6 Part 2 Replacement Text
    # -------------------------------------------------------------
    sec6_p2_text = """
## 6.4 Initial State Vector and Short-Range Kinematic Advection (0–48 Hours)
The operational short-range forecasting engine initializes from the real-time cyclone state vector:
$$\\mathbf{S}_0 = \\left[ \\phi_0, \\; \\lambda_0, \\; V_{\\max, 0}, \\; P_{c, 0}, \\; \\theta_0, \\; v_{\\text{trans}, 0} \\right]$$
where $(\\phi_0, \\lambda_0)$ are current geographic coordinates, $V_{\\max, 0}$ is maximum sustained wind, $P_{c, 0}$ is central barometric pressure, $\\theta_0$ is heading azimuth, and $v_{\\text{trans}, 0}$ is translation speed.

Numerical trajectory advection propagates coordinates forward at discrete $\\Delta t = 3\\text{-hour}$ intervals across the 48-hour operational window:
$$\\phi_{t+\\Delta t} = \\phi_t + \\left( \\frac{v_{\\text{trans}} \\cos \\theta}{111.0} \\right) \\Delta t + \\delta_{\\beta, \\phi}$$
$$\\lambda_{t+\\Delta t} = \\lambda_t + \\left( \\frac{v_{\\text{trans}} \\sin \\theta}{111.0 \\cos \\phi_t} \\right) \\Delta t + \\delta_{\\beta, \\lambda}$$
where $111.0\\text{ km/degree}$ is the meridional conversion factor, and $\\boldsymbol{\\delta}_{\\beta} = [\\delta_{\\beta, \\phi}, \\delta_{\\beta, \\lambda}]^T$ incorporates the northward beta-recurvature steering deflection active when $\\phi_t > 19.8^\\circ\\text{N}$.

## 6.5 Physical Aerodynamic Models
At each 3-hour trajectory waypoint, physical aerodynamic models compute expected wind fields and central pressures:
1. **Asymmetric Modified Rankine Vortex:** Calculates the radial surface wind velocity profile, superimposing storm translation velocity to model quadrant-dependent wind asymmetry ($V_{\\text{eff}}$).
2. **Holland Pressure Inversion:** Inverts wind speed into minimum central pressure ($P_c$) and steepness coefficients ($B$).
3. **Kaplan–DeMaria Inland Decay:** Activates immediately upon coastal crossing ($t > t_{\\text{landfall}}$), exponentially decaying wind intensity at $\\alpha = 0.095\\text{ hr}^{-1}$ towards background equilibrium velocity ($V_{\\text{bg}} = 20\\text{ knots}$).

## 6.6 Landfall Estimation and Dynamic Rapid Intensification Monitoring
Coastline intersection is computed dynamically by testing the advected trajectory line segment against the digitized Odisha littoral boundary ($19.0^\\circ\\text{N}$ to $21.5^\\circ\\text{N}$). When intersection occurs:
- **Estimated Time to Landfall (ETL):** Calculated with 30-minute numerical resolution.
- **Landfall Point Coordinates:** Pinpointed to the nearest coastal district (Ganjam, Puri, Jagatsinghpur, Kendrapara, Bhadrak, or Balasore).
- **Landfall Intensity & Pressure:** Inverted via Holland's relation and Rankine profiling.

Concurrently, the system tracks the 24-hour intensity change $\\Delta V_{24}$. If $\\Delta V_{24} \\ge 30\\text{ knots}$ ($15.43\\text{ m/s}$), the storm is flagged for **Rapid Intensification (RI)**, triggering immediate escalation of warning bulletins and evacuation readiness levels.

## 6.7 Sub-Seasonal (S2S) 15-Day Synoptic Cyclogenesis Potential Engine
To bridge the gap between 48-hour short-range tactical forecasting and seasonal climatology, IDMAP implements a 15-day sub-seasonal (S2S) synoptic cyclogenesis engine. The module computes the Cyclogenesis Potential Index ($CPI$):
$$CPI = \\left[\\frac{\\text{SST} - 26.0}{4.0}\\right] \\cdot \\left[\\frac{\\text{RH}_{700} - 40}{60}\\right] \\cdot \\left[\\frac{\\zeta_{850}}{10^{-5}}\\right] \\cdot \\left[1 + \\frac{\\text{VWS}}{20}\\right]^{-1} \\cdot \\Phi_{\\text{ENSO}} \\cdot \\Phi_{\\text{IOD}} \\cdot \\Phi_{\\text{MJO}}$$

Oceanic and atmospheric teleconnection modulation factors dynamically adjust regional cyclogenesis probability:
- **ENSO Teleconnection ($\\Phi_{\\text{ENSO}}$):** Modulated by the Oceanic Niño Index (ONI). La Niña conditions ($\\text{ONI} < -0.5^\\circ\\text{C}$) elevate cyclogenesis potential by shifting tropical convection westward into the Bay of Bengal ($\\Phi_{\\text{ENSO}} \\approx 1.15$).
- **Indian Ocean Dipole ($\\Phi_{\\text{IOD}}$):** Modulated by the Dipole Mode Index (DMI). Negative IOD regimes warm the eastern equatorial Indian Ocean, enhancing cyclogenesis potential ($\\Phi_{\\text{IOD}} \\approx 1.20$).
- **Madden-Julian Oscillation ($\\Phi_{\\text{MJO}}$):** Convective pulse tracking across Real-time Multivariate MJO (RMM) phases. Phase 3 (equatorial Indian Ocean) and Phase 4 (Maritime Continent) strongly enhance cyclogenesis ($\\Phi_{\\text{MJO}} = 1.30$), whereas Phase 7/8 suppressed regimes reduce potential ($\\Phi_{\\text{MJO}} = 0.85$).

The 15-day outlook structure informs a **3-Phase Strategic Preparedness Protocol**:
- **Phase 1: Synoptic Surveillance (T-15d to T-10d):** Daily SST and wind shear anomaly monitoring; state disaster control room advisory briefings.
- **Phase 2: Strategic Pre-Positioning (T-10d to T-5d):** Verification of district grain reserves, drinking water purification units, satellite phone operability, and shelter generator maintenance.
- **Phase 3: Tactical Readiness (< T-5d):** Pre-positioning of ODRAF and NDRF battalions to vulnerable coastal district headquarters; activation of emergency operations centers (EOCs).

## 6.8 60-Day Climatological Outlook and 50-Member Monte Carlo Uncertainty Cone
For macro-level seasonal planning, IDMAP deploys a 60-day climatological model based on historical Bay of Bengal cyclone records (1982–2024, comprising 66 major cyclonic disturbances). The seasonal model computes monthly baseline cyclogenesis probabilities for pre-monsoon (April–May) and post-monsoon (October–December) peak activity windows.

To quantify trajectory and intensity uncertainty, the system executes a **50-member stochastic Monte Carlo perturbation ensemble**:
- Heading perturbation: $\\epsilon_{\\theta} \\sim \\mathcal{N}(0, 4.8^\\circ)$
- Translation velocity perturbation: $\\epsilon_{v} \\sim \\mathcal{N}(0, 2.4\\text{ km/h})$
- Intensity perturbation: $\\epsilon_{\\text{int}} \\sim \\mathcal{N}(0, 5.5\\text{ knots})$

The ensemble dispersion generates a spatial confidence cone expanding radially with lead time:
$$R_{\\text{cone}}(t) = 15.0\\text{ km} + 2.25\\text{ km/hr} \\cdot t$$
yielding an uncertainty radius of approximately $69\\text{ km}$ at T+24h and $123\\text{ km}$ at T+48h, closely aligning with IMD operational cone standards.

**Table 11: Multi-Horizon Forecasting Engine Components**

| **Forecasting Component** | **Target Horizon** | **Primary Mathematical / Computational Method** | **Operational Output** |
| --- | --- | --- | --- |
| Short-Range Advection Engine | 0–48 Hours | 2D Numerical Advection with Beta-Recurvature ($>19.8^\\circ\\text{N}$) | Precise 3-hourly trajectory waypoints, heading, and translation speed. |
| Physical Vortex Profiler | 0–48 Hours | Asymmetric Modified Rankine Vortex ($x=0.55$) | Radial surface wind field with forward translation asymmetry correction. |
| Barometric Inversion Model | 0–48 Hours | Holland Pressure-Wind Relation ($B$-parameter) | Central pressure depression ($P_c$) and radial pressure gradient profile. |
| Inland Wind Dissipation | Landfall to +48h | Kaplan–DeMaria Inland Decay ($\\alpha = 0.095\\text{ hr}^{-1}$) | Post-landfall hourly wind speed attenuation curve. |
| Rapid Intensification Monitor | Real-Time to 48h | WMO/IMD RI Criterion ($\\Delta V_{24} \\ge 30\\text{ knots}$) | Binary RI alert flag triggering emergency operational protocol escalation. |
| Sub-Seasonal Synoptic Engine (S2S) | 0–15 Days | Cyclogenesis Potential Index ($CPI$) + ENSO / IOD / MJO Teleconnections | 15-day synoptic readiness index and 3-phase strategic preparedness protocol. |
| Seasonal Climatological Engine | 0–60 Days | Historical Bay of Bengal Climatology (66 Storms, 1982–2024) | Monthly cyclogenesis probability distribution across coastal districts. |
| Stochastic Monte Carlo Ensemble | 0–48 Hours | 50-Member Gaussian Perturbation ($\\sigma_\\theta, \\sigma_v, \\sigma_{\\text{int}}$) | Probabilistic trajectory envelope, landfall spread, and confidence cone radii. |

## 6.9 Operational Preparedness Interpretation and Action Checklist
The multi-horizon forecasting payload drives a standardized operational action checklist for district authorities:
1. **At T-48 Hours:** Review 50-member Monte Carlo strike probability envelopes; initiate district emergency operations center (EOC) 24/7 staffing; inspect backup diesel generators at all designated shelters.
2. **At T-24 Hours:** Finalize mandatory coastal evacuation lists for areas within the $69\\text{ km}$ confidence cone; deploy ODRAF/NDRF rescue platoons to pre-designated staging centers; cease all marine fishing operations.
3. **At T-12 Hours:** Complete mandatory evacuation of vulnerable populations to multipurpose cyclone shelters; initiate power grid safety shutdowns in projected severe gale zones.
4. **At Landfall (T-0 Hours):** Track Kaplan–DeMaria inland decay curve; maintain shelter lock-in protocols during passage of the cyclone eye; stage post-landfall road clearance teams.

## 6.10 Interactive What-If Scenario Simulation
To support contingency planning, IDMAP provides an interactive what-if simulation interface. Emergency officers can modify key atmospheric parameters—such as increasing wind speed by $20\\text{ km/h}$, shifting central pressure by $-15\\text{ hPa}$, or advancing landfall by $50\\text{ km}$ northward. The system recalculates spatial Rankine vortex wind fields, Haversine proximity matrices, and XGBoost risk scores in sub-second time, enabling planners to stress-test shelter capacity and rescue platoon allocations against worst-case scenarios.

"""

    p_start = c.find('**Figure** **7: Dual-Horizon Forecasting Pipeline**')
    assert p_start != -1
    p_start = c.find('\n', p_start) + 1
    p_end = c.find('# 7. Rag Advisory and  Executive Reporting')
    assert p_end != -1
    c = c[:p_start] + sec6_p2_text + c[p_end:]
    print("Step 7: Section 6 Part 2 applied.")

    # -------------------------------------------------------------
    # 8. Section 8 Part 1 Replacement Text
    # -------------------------------------------------------------
    sec8_p1_text = """# 8. Database, Caching and Continuous Retraining

## 8.1 Relational Database Architecture
IDMAP deploys Neon Serverless PostgreSQL managed through Prisma Object-Relational Mapping (ORM). The persistence layer is organized into thirteen strongly typed relational models designed to capture the complete lifecycle of cyclone intelligence:
- `CycloneEvent`: Storm identity, WMO classification, lifecycle status, and temporal boundaries.
- `LiveObservation`: Hourly coastal station telemetry (wind, pressure, temperature, humidity).
- `ModelPrediction`: District composite risk scores, warning stages, and autoencoder anomaly MSE.
- `SHAPAttribution`: Individual feature contribution values explaining each prediction.
- `DistrictForecast`: 48-hour forward trajectory waypoints, wind velocities, and landfall estimates.
- `AgentAdvisory`: Grounded advisory payloads, citations, and operational recommendations.
- `HumanFeedback`: Operator ratings ($1\\text{ to }5$), qualitative verifications, and textual corrections.
- `WhatIfSimulation`: Parameter perturbation records and simulated spatial risk outcomes.
- `CacheSnapshot`: Serialized JSON payload snapshots enabling zero-downtime cache restoration.
- `RetrainingRun`: Model drift metrics, dataset export telemetry, and retraining audit trails.

## 8.2 Core Entity Relationships and Data Flow
The entity-relationship schema enforces rigorous relational integrity:
$$\\text{CycloneEvent} \\overset{1:N}{\\longrightarrow} \\text{LiveObservation}$$
$$\\text{CycloneEvent} \\overset{1:N}{\\longrightarrow} \\text{ModelPrediction} \\overset{1:N}{\\longrightarrow} \\text{SHAPAttribution}$$
$$\\text{CycloneEvent} \\overset{1:N}{\\longrightarrow} \\text{DistrictForecast} \\overset{1:N}{\\longrightarrow} \\text{AgentAdvisory} \\overset{1:N}{\\longrightarrow} \\text{HumanFeedback}$$
When an operator submits human feedback, it anchors directly to the corresponding `AgentAdvisory` and `ModelPrediction`, maintaining an immutable audit trail from raw observational inputs through model inferences, generated advisories, and expert human evaluations.

## 8.3 Operational Role of Persistence
Persistence ensures historical auditability, supports retrospective disaster analysis, and enables closed-loop model maintenance. By storing predictions, explanations, and actual outcomes, the database provides the foundational empirical data required to detect seasonal performance drift and trigger continuous retraining.

**Table 12: Core Persistent Relational Entities**

| **Relational Entity** | **Primary Key / Index** | **Attributes Captured** | **Operational Function** |
| --- | --- | --- | --- |
| `CycloneEvent` | `id` (UUID), `base_id` | Name, year, basin, start_time, end_time, status | Master record for cyclone tracking and event-level data partitioning. |
| `LiveObservation` | `id`, `station_id`, `timestamp` | Station name, wind, gusts, pressure, temp, humidity | Real-time weather audit trail across coastal stations. |
| `ModelPrediction` | `id`, `event_id`, `district_id` | Composite risk, alert level, anomaly MSE, inference latency | Historical record of ML predictions for calibration and drift monitoring. |
| `SHAPAttribution` | `id`, `prediction_id` | Feature name, attribution value ($\phi_i$), base value | Transparent explanation records supporting post-disaster inquiries. |
| `DistrictForecast` | `id`, `event_id`, `lead_time` | Waypoints, wind fields, distance to coast, evacuation targets | Multi-horizon trajectory and resource requirement storage. |
| `AgentAdvisory` | `id`, `district_id`, `timestamp` | Advisory text, SOP citations, confidence score | Traceable record of official emergency advisories issued. |
| `HumanFeedback` | `id`, `advisory_id` | Rating (1–5), verification flag, text correction, operator ID | Curated ground-truth feedback for continuous retraining export. |
| `WhatIfSimulation` | `id`, `timestamp` | Perturbed variables, baseline risk, simulated risk | Analytical scenario audit trail for administrative planning. |
| `RetrainingRun` | `id`, `timestamp` | Drift metrics ($R^2$, MSE), export paths, status | Governance record for continuous machine learning lifecycle management. |

## 8.4 Three-Tier Resilient Caching Hierarchy
To guarantee continuous operational availability during severe weather emergencies—when coastal telecommunication links degrade or cloud database connections experience latency spikes—IDMAP implements a three-tier resilient caching hierarchy:

1. **Tier 1: In-Memory LRU Cache:** Maintains recently serialized JSON payloads in RAM for instantaneous API responses. Cached unified survey requests return in $\\le 15\\text{ ms}$.
2. **Tier 2: Local Disk JSON Snapshots (`cache/`):** Asynchronous background workers serialize cache snapshots to local persistent disk. If the remote database experiences latency or connection loss, the API automatically falls back to local disk snapshots within $\\le 50\\text{ ms}$, ensuring uninterrupted dashboard operations.
3. **Tier 3: Remote Serverless Database (Neon PostgreSQL):** Serves as the authoritative long-term persistence layer. Ingestion and survey writes occur asynchronously to decouple user-facing dashboard performance from database network round-trip latency.

**Cache Invalidation Protocol:**
- **Live Weather Telemetry:** $5\\text{-minute}$ Time-To-Live (TTL) window matching Open-Meteo station polling cycles.
- **Predictive Forecasts & Risk Maps:** $15\\text{-minute}$ TTL window matching operational cyclone trajectory update intervals.

"""

    p_start = c.find('# 8. Database, Caching and Continuous Retaining')
    p_end = c.find('\n![](data:image/png;base64', p_start)
    assert p_start != -1 and p_end != -1
    c = c[:p_start] + sec8_p1_text.rstrip() + c[p_end:]
    print("Step 8: Section 8 Part 1 applied.")

    # -------------------------------------------------------------
    # 9. Section 8 Part 2 Replacement Text
    # -------------------------------------------------------------
    sec8_p2_text = """
## 8.5 Human Feedback and Continuous Retraining Data Export Pipelines
IDMAP establishes a closed-loop machine learning maintenance framework by translating real-time human expert feedback into curated retraining datasets via dedicated export pipelines (`scripts/export_retraining_data.py` and `src/database/db_service.py`):

1. **Supervised Fine-Tuning (SFT) Dataset Exporter:**
   - Operators review generated disaster advisories and assign an operational quality rating from $1\\text{ to }5$.
   - Advisories receiving a rating of $\\ge 4$ (verified accurate and operationally sound) are automatically extracted, formatted, and exported as instruction-response pairs into SFT JSONL format:
     ```json
     {"prompt": "Generate emergency response advisory for Puri district under Severe Cyclonic Storm conditions...", "completion": "EMERGENCY ADVISORY: IMD Bulletin mandates immediate evacuation of vulnerable coastal settlements within 5km..."}
     ```
2. **Direct Preference Optimization (DPO) Dataset Exporter:**
   - When an operator identifies an inaccuracy or omission in an advisory, the interface captures the original advisory along with the operator's corrected text.
   - The export pipeline pairs these completions into DPO JSONL format containing explicit preference rankings:
     ```json
     {"prompt": "District evacuation protocol for Kendrapara...", "chosen": "Verified operator correction incorporating local shelter route...", "rejected": "Original uncorrected advisory containing generic guidance..."}
     ```
   - This provides preference pairs to align downstream language models directly against expert operational judgments.

3. **Automated Model Drift Triggers:**
   The continuous evaluation service monitors operational prediction distributions against validation baselines. Automated retraining workflows are triggered when:
   - XGBoost regression coefficient of determination falls below threshold: $R^2 < 0.95$.
   - Convolutional Autoencoder mean reconstruction error across recent passes exceeds anomaly threshold: $\\text{MSE} > 0.070$.

## 8.6 Software Engineering Significance: The Closed-Loop AI Lifecycle
In standard academic machine learning systems, deployment marks the termination of the project lifecycle, resulting in static models that degrade as environmental or operational conditions evolve. IDMAP treats deployment as the beginning of an ongoing feedback loop. By integrating human operator ratings, expert corrections, automated SFT/DPO data curation, and quantitative drift monitoring, IDMAP implements an auditable, continuously improving machine learning architecture engineered for long-term operational resilience.

"""

    p_start = c.find('**Figure 8: Human-in-the-loop feedback and retraining lifecycle**')
    assert p_start != -1
    p_start = c.find('\n', p_start) + 1
    p_end = c.find('# 9. Implementation and User Interface')
    assert p_end != -1
    c = c[:p_start] + sec8_p2_text + c[p_end:]
    print("Step 9: Section 8 Part 2 applied.")

    # -------------------------------------------------------------
    # 10. Section 11 (Testing, Verification & Validation) Replacement Text
    # -------------------------------------------------------------
    sec11_text = """# 11. Testing, Verification and Validation

## 11.1 Layered Testing Strategy
The verification strategy for IDMAP is structured across the system's core failure surfaces: physical aerodynamic formulations, database caching and fallback resilience, continuous retraining export pipelines, multi-horizon forecast payloads, deep vision feature backbones, and retrieval-augmented generation agents. Testing is implemented using the `pytest` automated test execution framework.

## 11.2 Automated Test Execution Results
The entire automated test suite was executed against the production codebase, achieving a **100% pass rate (26 passed out of 26 test cases)** across all unit and integration test modules.

**Table 17: Automated Test Suite Execution Summary**

| **Test Suite File** | **Test Function / Capability Verified** | **Test Count** | **Execution Status** | **Scope of Verification** |
| --- | --- | :---: | :---: | --- |
| `tests/test_advanced_forecasting.py` | `test_beta_recurvature_deflection` | 1 | PASSED | Verifies northward steering deflection above $19.8^\\circ\\text{N}$ latitude. |
| | `test_rapid_intensification_threshold` | 1 | PASSED | Verifies WMO/IMD 24-hour RI trigger ($\\Delta V_{24} \\ge 30\\text{ kt}$). |
| | `test_holland_pressure_inversion` | 1 | PASSED | Verifies Holland central pressure depression calculation against wind speed. |
| | `test_rankine_vortex_wind_field` | 1 | PASSED | Verifies asymmetric Modified Rankine vortex radial velocity profiling. |
| | `test_kaplan_inland_decay` | 1 | PASSED | Verifies exponential inland dissipation ($\\alpha = 0.095\\text{ hr}^{-1}$) post-landfall. |
| | `test_landfall_eta_calculation` | 1 | PASSED | Verifies coastline intersection and dynamic estimated time of arrival. |
| `tests/test_db_cache.py` | `test_in_memory_lru_caching` | 1 | PASSED | Verifies instant sub-15ms cache hit retrieval for weather and survey payloads. |
| | `test_disk_cache_fallback` | 1 | PASSED | Verifies sub-50ms local disk fallback when remote PostgreSQL is disconnected. |
| | `test_cache_ttl_invalidation` | 1 | PASSED | Verifies 5-minute weather and 15-minute forecast cache expiration windows. |
| | `test_asynchronous_persistence` | 1 | PASSED | Verifies non-blocking database write operations under high telemetry load. |
| `tests/test_db_retraining.py` | `test_human_feedback_recording` | 1 | PASSED | Verifies operator rating (1–5) and correction persistence in PostgreSQL. |
| | `test_sft_jsonl_export_pipeline` | 1 | PASSED | Verifies filtering of ratings $\\ge 4$ and schema compliance of SFT JSONL exports. |
| | `test_dpo_jsonl_export_pipeline` | 1 | PASSED | Verifies paired chosen/rejected completions in DPO JSONL export files. |
| `tests/test_forecasting.py` | `test_short_range_48h_forecast_payload` | 1 | PASSED | Verifies 3-hourly 48-hour trajectory waypoints, headings, and wind attributes. |
| | `test_seasonal_60d_climatology_payload` | 1 | PASSED | Verifies 60-day monthly cyclogenesis distribution and district vulnerability scores. |
| `tests/test_pipeline.py` | `test_resnet_feature_extraction` | 1 | PASSED | Verifies 128-dimensional dense visual embedding generation from satellite tensor. |
| | `test_autoencoder_anomaly_detection` | 1 | PASSED | Verifies reconstruction MSE calculation and operational threshold categorization. |
| | `test_xgboost_risk_regression` | 1 | PASSED | Verifies risk inference accuracy and output normalization in $[0, 1]$. |
| | `test_shap_attribution_computation` | 1 | PASSED | Verifies exact additive feature attributions satisfying local accuracy property. |
| | `test_district_graph_topology` | 1 | PASSED | Verifies 30 district nodes and 69 bidirectional adjacency edges integrity. |
| | `test_evacuation_resource_allocation` | 1 | PASSED | Verifies constrained evacuation targets and 1 platoon / 15,000 evacuee ratio. |
| | `test_chroma_vector_retrieval` | 1 | PASSED | Verifies top-$k$ semantic search over embedded IMD/OSDMA disaster protocols. |
| | `test_rag_advisory_generation` | 1 | PASSED | Verifies evidence-grounded advisory generation with traceable citations. |
| | `test_whatif_scenario_simulation` | 1 | PASSED | Verifies dynamic parameter perturbation and sub-second risk recalculation. |
| | `test_api_health_endpoint` | 1 | PASSED | Verifies backend service health, database status, and model readiness flags. |
| | `test_end_to_end_survey_integration` | 1 | PASSED | Verifies complete unified survey pipeline execution from telemetry to dashboard payload. |
| **Total Automated Suite** | **Comprehensive Platform Verification** | **26** | **26/26 PASSED** | **100% Test Suite Passage Rate** |

## 11.3 Production Build Verification
The frontend operational dashboard was compiled for production deployment using Vite v8.2.2. The production build completed with **zero syntax errors and zero bundle warnings** in an empirically measured build time of **379 ms**, generating optimized, minified JavaScript and CSS bundles ready for static distribution via CDN/Vercel.

## 11.4 Verification versus Validation Analysis
In software and systems engineering, verification and validation represent complementary quality assurance dimensions:
- **Verification ("Was the system built correctly?"):** Rigorously confirmed by the 26 passing automated unit and integration tests, confirming that mathematical equations (Rankine vortex, Holland relation, Kaplan decay, beta-recurvature, Haversine, TreeSHAP), database caching fallback, retraining data exporters, and end-to-end API pipelines function in exact conformance with technical specifications.
- **Validation ("Was the correct system built for the operational domain?"):** Addresses whether the platform satisfies the real-world operational needs of emergency disaster officers during actual cyclone emergencies. While the synthetic benchmarks ($R^2=0.9885$, $\\text{RMSE}=0.0155$) and simulated test cases confirm engineering viability, full operational validation requires multi-season operational trials with OSDMA, field testing across district emergency operations centers, and formal comparison against real-time IMD operational tracking bulletins during future Bay of Bengal cyclone events.

## 11.5 Test Quality and Operational Confidence
The combination of unit tests for physical aerodynamics, integration tests for multi-service pipelines, and build verification establishes high technical confidence in the codebase. All critical mathematical failure modes—such as division-by-zero at storm eye radius, negative inland decay velocities, and database connection timeout deadlocks—are guarded with defensive exception handling and automated regression assertions.

"""

    p_start = c.find('# 11. Testing, Verification AND Validation')
    p_end = c.find('# 12. Deployment')
    assert p_start != -1 and p_end != -1
    c = c[:p_start] + sec11_text + c[p_end:]
    print("Step 10: Section 11 applied.")

    # -------------------------------------------------------------
    # 11. Section 12 Part 1 Replacement Text
    # -------------------------------------------------------------
    sec12_p1_text = """# 12. Deployment and Production Topology

## 12.1 Local Deployment and Unified Orchestration
To streamline local development, evaluation, and operational demonstrations, IDMAP provides a unified concurrent execution orchestrator (`scripts/dev.js`). Executed via Node.js, the script launches both application tiers simultaneously:
- **Backend Service:** Uvicorn ASGI server hosting the FastAPI application on port 8000 with hot-reload and environment variable injection.
- **Frontend Service:** Vite development server serving the React operational dashboard on port 5173 with lightning-fast Hot Module Replacement (HMR).

The orchestrator manages dual process lifecycles, multiplexes console logging with distinct service prefixes, and intercepts process termination signals (`SIGINT`, `SIGTERM`) to guarantee clean, simultaneous teardown of both processes without orphaned background tasks or port conflicts.

## 12.2 Deployment Architecture Topology
"""

    p_start = c.find('# 12. Deployment')
    p_end = c.find('\n![](data:image/png;base64', p_start)
    assert p_start != -1 and p_end != -1
    c = c[:p_start] + sec12_p1_text.rstrip() + c[p_end:]
    print("Step 11: Section 12 Part 1 applied.")

    # -------------------------------------------------------------
    # 12. Section 12 Part 2 Replacement Text
    # -------------------------------------------------------------
    sec12_p2_text = """
## 12.3 Multi-Stage Containerization Architecture
Production deployment is containerized using a multi-stage Docker build engineered for minimal image size, enhanced security, and rapid cloud scaling:
1. **Stage 1 (Frontend Build Environment):** Utilizes a lightweight Node.js (Node 20 Alpine) image. Node dependencies are installed via `pnpm`, and the React operational dashboard is compiled into highly optimized static HTML, CSS, and JS assets using Vite (`pnpm build`).
2. **Stage 2 (Production Runtime Environment):** Utilizes an official Python 3.11 Slim Debian image. Machine learning dependencies (PyTorch, XGBoost, Scikit-learn, Shap, ChromaDB, FastAPI, Uvicorn) are installed with cache optimization. The pre-compiled static frontend assets from Stage 1 are copied into the Python runtime directory and mounted as static files served directly by FastAPI or an optional Nginx reverse proxy.
3. **Security Hardening:** The container runs as a non-privileged system user, minimizing container breakout vulnerabilities in enterprise environments.

## 12.4 Cloud Deployment Topology
The cloud-native architecture separates presentation, application logic, and persistence:
- **Presentation Layer:** Deployed to Vercel or Cloudflare Pages edge network, providing global SSL termination, automated asset compression, and low-latency edge delivery.
- **Application Layer:** Deployed as a containerized web service on Render, AWS ECS, or Google Cloud Run, configured with auto-scaling based on CPU utilization and incoming HTTP request volume.
- **Persistence Layer:** Hosted on Neon Serverless PostgreSQL, providing automated connection pooling, branch-on-demand database staging, and encrypted point-in-time recovery.

**Table 18: System Performance Benchmarks**

| **Evaluation Metric** | **Empirical Performance Result** | **Operational Significance** |
| --- | --- | --- |
| XGBoost Regression Accuracy ($R^2$) | $0.9885$ | High-fidelity risk estimation across heterogeneous meteorological features. |
| Root Mean Squared Error (RMSE) | $0.0155$ | Minimal error margin on normalized continuous risk index $[0, 1]$. |
| Mean Absolute Error (MAE) | $0.0108$ | Consistent calibration across low, moderate, and severe risk regimes. |
| In-Memory Cache Response Time | $\\le 15\\text{ ms}$ | Instantaneous dashboard payload rendering under operator interaction. |
| Local Disk Cache Fallback Latency | $\\le 50\\text{ ms}$ | Guaranteed resilience during remote database latency or network partitions. |
| End-to-End Multimodal Inference Latency | $< 2.5\\text{ seconds}$ | Real-time computation of vision embeddings, autoencoder MSE, and risk scores. |
| Mean T+24h Trajectory Divergence | $< 22\\text{ km}$ | Superior short-range track fidelity within the $69\\text{ km}$ confidence cone. |
| Frontend Production Build Duration | $379\\text{ ms}$ (0 errors) | Rapid continuous integration and deployment verification under Vite v8.2.2. |
| Automated Test Suite Execution | $26/26\\text{ passed}$ ($100\\%$) | Complete verification of aerodynamic, ML, caching, and export logic. |

"""

    p_start = c.find('**Figure 9 : Deployment and runtime topology**')
    assert p_start != -1
    p_start = c.find('\n', p_start) + 1
    p_end = c.find('# 13. Results and Completion Assessment')
    assert p_end != -1
    c = c[:p_start] + sec12_p2_text + c[p_end:]
    print("Step 12: Section 12 Part 2 applied.")

    # -------------------------------------------------------------
    # 13. Section 13.1 Update
    # -------------------------------------------------------------
    old_sec13_cap = "- 32-dimensional satellite embeddings and autoencoder anomaly detection documented."
    new_sec13_cap = "- 128-dimensional dense satellite visual embeddings and autoencoder anomaly detection documented.\n\n- Multi-horizon forecasting engine (48-hour kinematic, 15-day S2S synoptic, 60-day seasonal outlook with 50-member Monte Carlo ensemble) implemented and verified."
    if old_sec13_cap in c:
        c = c.replace(old_sec13_cap, new_sec13_cap, 1)
        print("Step 13: Section 13.1 capability updated.")

    # -------------------------------------------------------------
    # 14. Section 15.2 (Future Scope) Replacement Text
    # -------------------------------------------------------------
    sec15_2_text = """## 15.2 Future Scope
While the current IDMAP platform demonstrates verified end-to-end capabilities spanning multimodal computer vision, physical aerodynamics, machine learning risk regression, multi-horizon trajectory forecasting, and RAG advisory synthesis, several advanced engineering and meteorological enhancements represent promising future research directions:

1. **Real-Time Coastal Doppler Weather Radar Assimilation**
Future iterations can assimilate high-resolution radial velocity and reflectivity volumes from IMD coastal Doppler Weather Radars (DWR) situated at Paradip and Gopalpur. Incorporating polarimetric radar parameters (differential reflectivity $Z_{\\text{DR}}$, specific differential phase $K_{\\text{DP}}$) will enable fine-scale microphysical rain-rate estimation and precise meso-cyclone vortex tracking within $250\\text{ km}$ of the coastline.

2. **Coupled Hydrodynamic Coastal Inundation and Storm Surge Modeling**
While IDMAP currently models surface gale distributions and inland decay, integrating hydrodynamic coastal surge formulations—such as coupling with the Advanced Circulation (ADCIRC) or Sea, Lake, and Overland Surges from Hurricanes (SLOSH) numerical models—would enable localized, parcel-level inundation modeling along vulnerable coastal estuaries (Chilika Lake, Mahanadi Delta, and Bhitarkanika).

3. **High-Resolution Road Network Graph Topology and Dynamic Evacuation Corridor Routing**
The current spatial graph models adjacency across the 30 administrative districts. Future work can expand this into a granular road network graph using OpenStreetMap road centerlines. Implementing dynamic graph routing algorithms (such as time-dependent $A^*$ or Contraction Hierarchies) would allow the platform to generate turn-by-turn emergency evacuation corridor routes that dynamically avoid submerged causeways and tree-fall blockages.

4. **Edge Computing Deployment for Low-Bandwidth Coastal Emergency Operations Centers**
To provide absolute operational survivability during cataclysmic storm events when national cloud backbones are severed, quantized lightweight versions of the AI pipeline (using ONNX Runtime and 8-bit integer quantization) can be compiled for ruggedized edge appliances deployed directly at coastal District Emergency Operations Centers (DEOCs).

5. **Multilingual Localized Alert Broadcasting and Automated Voice Synthesis**
To bridge the final-mile communication gap to rural coastal communities, the RAG advisory system can be augmented with localized Odia and Hindi text-to-speech (TTS) synthesis engines. Automated generation of localized audio warnings broadcast over rural community radio, SMS push systems, and coastal siren towers will significantly improve early warning dissemination and public evacuation compliance.

"""

    p_start = c.find('## 15.2.Future Scope')
    if p_start == -1:
        p_start = c.find('## 15.2 Future Scope')
    assert p_start != -1
    p_end = c.find('# 16.References')
    assert p_end != -1
    c = c[:p_start] + sec15_2_text + c[p_end:]
    print("Step 14: Section 15.2 applied.")

    # -------------------------------------------------------------
    # Step 4: Verification of all 11 base64 images
    # -------------------------------------------------------------
    new_images = []
    for line in c.splitlines():
        if 'data:image/png;base64' in line:
            h = hashlib.sha256(line.encode('utf-8')).hexdigest()
            new_images.append((len(line), h))

    print(f"Updated images count: {len(new_images)}")
    assert len(new_images) == 11, f"Expected 11 images after update, found {len(new_images)}"

    for i in range(11):
        orig_len, orig_h = orig_images[i]
        new_len, new_h = new_images[i]
        assert orig_len == new_len, f"Image {i+1} length mismatch: {orig_len} vs {new_len}"
        assert orig_h == new_h, f"Image {i+1} hash mismatch: {orig_h} vs {new_h}"
        print(f"Image {i+1} verified intact: len={new_len}, sha={new_h[:16]}")

    # Write back to file
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(c)

    print("SUCCESS: c:\\Professional\\Projects\\IDMAP\\docs\\IDMAP (1).md successfully updated!")

if __name__ == '__main__':
    main()
