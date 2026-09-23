# IDMAP Cyclone Forecasting Accuracy & Multi-Model Ensemble Architecture
**Project:** Intelligent Disaster Management & Action Platform (IDMAP)  
**Target Domain:** Bay of Bengal Tropical Cyclones & Odisha Coastal Disaster Preparedness  
**Meteorological Standards Alignment:** IMD (RSMC New Delhi), WMO TCP, NOAA NHC, ECMWF

---

## 1. Executive Summary

To achieve **zero-casualty** disaster preparedness in Odisha, cyclone trajectory and intensity forecasting must transition from deterministic single-path approximations to **probabilistic multi-hazard spatial envelopes**. This document defines the mathematical formulation, empirical calibrations, operational integration roadmap, and advanced physics extensions for maximum forecast accuracy in IDMAP.

---

## 2. Mathematical & Algorithmic Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │           MULTIMODAL DATA INGESTION          │
                  │  • NASA GIBS / INSAT-3D Vision Telemetry     │
                  │  • Open-Meteo Coastal AWS & Marine Buoys     │
                  │  • INCOIS Ocean Heat Content (TCHP & SST)    │
                  │  • NWP Pressure Levels (850-200 hPa Winds)   │
                  │  • IMD Doppler Weather Radar (DWR Paradip)   │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │    2D/3D KINEMATIC & STEERING ADVECTION      │
                  │  • Deep-Layer Mass-Weighted Steering Flow    │
                  │  • Beta-Drift & Subtropical Ridge Deflection │
                  │  • Dynamic Trajectory-Coastline Intersection │
                  │  • IMD Uncertainty Cone: R_cone(h) = 3.0*h^1.02│
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │  50-MEMBER MONTE CARLO PROBABILISTIC ENSEMBLE│
                  │  • Heading Perturbations (σ = 4.8°)          │
                  │  • Translation Speed Perturbations (σ = 2.4) │
                  │  • Core Intensity Perturbations (σ = 5.5 kt) │
                  └──────────────────────┬───────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
┌──────────────────────────────────────┐   ┌──────────────────────────────────────┐
│     RADIAL & ASYMMETRIC VORTEX       │   │       DYNAMIC HAZARD COUPLING        │
│  • Modified Rankine Radial Profile   │   │  • Jelesnianski Coastal Surge        │
│  • Double-Rankine Eyewall (ERC)      │   │  • NOAA R-Index 24h Rainfall         │
│  • Translation Vector Addition       │   │  • NOAA SHIPS / INCOIS RI Index      │
│  • Kaplan-DeMaria Overland Decay     │   │  • PWP 1D Ocean Cold Wake            │
└──────────────────┬───────────────────┘   └──────────────────┬───────────────────┘
                   │                                          │
                   └─────────────────────┬────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │         TREE-SHAP & XGBOOST RISK FUSION      │
                  │  • Dual-Regime Calm vs Storm Modulation      │
                  │  • Odisha Zero-Casualty SOP Resource Planner │
                  └──────────────────────────────────────────────┘
```

---

## 3. Core Formulations

### 3.1 Kinematic Advection & Parabolic Recurvature
The moving cyclone eye position $(\phi(t), \lambda(t))$ is integrated over time step $\Delta t$:
$$\Delta \phi = \frac{v_{\text{trans}} \cdot \cos(\theta(t))}{111.12}, \quad \Delta \lambda = \frac{v_{\text{trans}} \cdot \sin(\theta(t))}{111.12 \cdot \cos(\phi(t))}$$

Above the subtropical ridge inflection latitude ($19.8^\circ\text{N}$), the trajectory experiences clockwise parabolic recurvature toward West Bengal/Bangladesh:
$$\theta(t) = \theta_0 + \gamma \cdot \max(0, \phi(t) - 19.8) \cdot t^{1.15}$$

### 3.2 Dynamic Coastline Intersection (Landfall Pinpointing)
The engine traces the forward trajectory $\vec{r}(t)$ against the geographic coordinates of all coastal districts ($d_{\text{coast}} \le 15\text{ km}$). The minimum geodesic distance determines the exact landfall target district and hour ($\text{ETL}$):
$$\text{LandfallTarget} = \arg\min_{D \in \text{Coastal}} \left( \min_{t \in [0, 48\text{h}]} \text{Haversine}(\vec{r}(t), \vec{r}_D) \right)$$

### 3.3 Asymmetric Modified Rankine Vortex Profile
Northern Hemisphere counter-clockwise rotation superimposes the forward translation vector onto the right-front quadrant (Dangerous Semicircle):
$$V_{\text{effective}}(r, \theta) = V_{\text{Rankine}}(r) + v_{\text{trans}} \cdot \sin(\theta - \theta_{\text{track}}) \cdot \left(\frac{R_{\max}}{\max(R_{\max}, r)}\right)^{0.5}$$
where:
$$V_{\text{Rankine}}(r) = \begin{cases} V_{\max} \left(0.35 + 0.65 \left(\frac{r}{R_{\max}}\right)^{0.8}\right) & r \le R_{\max} \\ V_{\max} \left(\frac{R_{\max}}{r}\right)^{0.5} & r > R_{\max} \end{cases}$$

### 3.4 Kaplan-DeMaria Post-Landfall Overland Decay
Upon landfall ($t > \text{ETL}$), loss of oceanic latent heat and surface friction reduces core winds exponentially:
$$V_{\max}(t_{\text{post}}) = V_{\text{background}} + (V_{\text{landfall}} - V_{\text{background}}) \cdot e^{-\alpha \cdot t_{\text{post}}}$$
where $\alpha = 0.095\text{ hr}^{-1}$ and $V_{\text{background}} = 15.0\text{ kt}$.

### 3.5 Rapid Intensification (RI) Index (NOAA SHIPS / INCOIS TCHP Formulation)
RI is defined by WMO/IMD as a wind increase $\ge 30\text{ kt}$ within a 24-hour window:
$$\text{RI}_{\text{score}} = 0.25 \cdot f(\text{SST}) + 0.25 \cdot f(\text{TCHP}) + 0.20 \cdot f(\text{VWS}) + 0.20 \cdot \rho_{\text{cloud}} + 0.10 \cdot (1 - \epsilon_{\text{organ}})$$
- **TCHP:** Tropical Cyclone Heat Potential $> 80\text{ kJ/cm}^2$ indicates deep upper-ocean thermal energy.
- **VWS:** Vertical Wind Shear $< 12\text{ kt}$ provides an uninhibited convective chimney.

---

## 4. 50-Member Monte Carlo Probabilistic Ensemble

To provide operational certainty and eliminate single-point blindspots, IDMAP generates a 50-member perturbation ensemble:

1. **Perturbation Distributions:**
   - Steering Heading: $\Delta \theta \sim \mathcal{N}(0, \sigma_\theta = 4.8^\circ)$
   - Translation Speed: $\Delta v \sim \mathcal{N}(0, \sigma_v = 2.4\text{ km/h})$
   - Core Intensity: $\Delta V_{\max} \sim \mathcal{N}(0, \sigma_V = 5.5\text{ kt})$

2. **Per-District Probability Thresholds:**
   - **Gale Wind Probability ($P \ge 34\text{ kt}$)**: Early marine alert and artisanal fishing suspension.
   - **Storm Wind Probability ($P \ge 48\text{ kt}$)**: Mandatory tree pruning, power grid shutdown, and kutcha house alerts.
   - **Hurricane Wind Probability ($P \ge 64\text{ kt}$)**: Immediate mandatory zero-casualty evacuation to Multipurpose Cyclone Shelters (MCS).
   - **Coastal Surge Inundation ($P \ge 1.0\text{ m}$)**: Coastal dike breach preparation and saline embankment reinforcement.

---

## 5. Advanced Physical Extensions Specification

To bridge the remaining operational error margins ($15-25\text{ km}$ track error and $\pm 5\text{ kt}$ intensity error), IDMAP is designed to incorporate four specialized sub-engines:

### 5.1 3D Atmospheric Environmental Steering (NWP Mass-Weighted Integration)
* **Problem Solved:** Abrupt stalls, sharp turns, or westerly trough capture.
* **Data Sources:** Open-Meteo Pressure-Levels API, ECMWF IFS Open Data, NOAA GFS 0.25° GRIB2.
* **Mathematical Formula:**
  $$\vec{V}_{\text{steer}} = \frac{\sum_{p \in \{850, 700, 500, 300, 200\}} w(p) \cdot \vec{V}_{\text{env}}(p)}{\sum w(p)}$$
  * Weights: $w_{850} = 0.15, w_{700} = 0.25, w_{500} = 0.35, w_{300} = 0.15, w_{200} = 0.10$.
* **Integration:** Dynamically modulates instantaneous heading $\theta(t)$ and translation speed $v_{\text{trans}}(t)$ at every numerical integration step.

---

### 5.2 Eyewall Replacement Cycle (ERC) & Double-Rankine Vortex
* **Problem Solved:** Catastrophic intensity dips followed by 2x expansion of outer damage footprint in severe storms ($V_{\max} > 85\text{ kt}$).
* **Data Sources:** INSAT-3D/3DR TIR-1 (10.8 µm) & Microwave Convective Morphology.
* **Mathematical Formula:**
  $$V_{\text{ERC}}(r) = (1 - w_{\text{erc}}(t)) \cdot V_{\text{Rankine}}(r, R_{\max 1}) + w_{\text{erc}}(t) \cdot V_{\text{Rankine}}(r, R_{\max 2})$$
  * $R_{\max 1} \approx 20-30\text{ km}$ (contracting inner core).
  * $R_{\max 2} \approx 65-85\text{ km}$ (expanding secondary outer eyewall).
  * $w_{\text{erc}}(t) \in [0, 1]$ ramps over the 12–18 hour contraction cycle.

---

### 5.3 Doppler Weather Radar (DWR) Assimilation ($< 350\text{ km}$)
* **Problem Solved:** Satellite parallax offset and cloud-top obscuration during terminal 18-hour approach.
* **Data Sources:** IMD / MOSDAC Gopalpur DWR & Paradip DWR (Reflectivity $Z$, Radial Velocity $V_r$).
* **Mathematical Formula:**
  1. **Eye Center Localization:** Hough Circle Transform on radar-silent core ($Z < 20\text{ dBZ}$) surrounded by eyewall ($Z \ge 45\text{ dBZ}$).
  2. **Doppler Dipole Wind Extraction:**
     $$V_{\text{surface\_gust}} = 1.25 \times \frac{|V_{r,\max}| + |V_{r,\min}|}{2}$$
  3. **Kalman Filter Nudging:** Weights radar eye coordinates ($R = 4\text{ km}^2$) against kinematic advection ($Q = 25\text{ km}^2$) to pin landfall location within $\pm 4\text{ km}$.

---

### 5.4 Subsurface Ocean Cold-Wake Dynamics (Price-Weller-Pinkel 1D Mixing)
* **Problem Solved:** Over-intensification of slow-moving or stalling storms over the Bay of Bengal.
* **Data Sources:** INCOIS Mixed Layer Depth ($H_{\text{mld}}$ in meters) & Tropical Cyclone Heat Potential (TCHP).
* **Mathematical Formula:**
  $$\Delta T_{\text{sst}} = -C_{\text{ocean}} \cdot \frac{V_{\max}^2}{v_{\text{trans}} \cdot H_{\text{mld}}}$$
  * $C_{\text{ocean}} \approx 0.0035$ (empirical thermal coupling coefficient).
  * Dynamic SST capping: $T_{\text{effective}} = T_{\text{sst}} - \Delta T_{\text{sst}}$.
  * Fed into Emanuel's Maximum Potential Intensity (MPI) thermodynamic limit to prevent false runaway intensification.

---

## 6. Phased Implementation Roadmap

| Phase | Innovation | Data Source | Forecast Gain |
| :--- | :--- | :--- | :--- |
| **Phase 1 (Completed)** | 50-Member Monte Carlo Ensemble & TCHP Integration | Open-Meteo, INCOIS, NASA GIBS | Calibrated probabilistic strike envelopes & consensus |
| **Phase 2 (Completed)** | Dynamic Coastline Trajectory Intersection & Sector Mapping | Haversine Geodesics, Odisha Nodes | Zero hardcoded landfall labels; 100% path synchrony |
| **Phase 3** | 3D NWP Pressure-Level Environmental Steering Flow | Open-Meteo Pressure Levels / GFS | Eliminates sudden recurvature & stalling track errors |
| **Phase 4** | Double-Rankine Eyewall Replacement (ERC) Model | INSAT-3DR Microwave / Thermal IR | Predicts wind radius broadening in Category 3+ cyclones |
| **Phase 5** | IMD Gopalpur & Paradip DWR Radar Data Assimilation | MOSDAC Radar NetCDF / MaxZ | Sub-5 km landfall precision in terminal 18 hours |
| **Phase 6** | 1D PWP Ocean Cold Wake & Dynamic MPI Capping | INCOIS Mixed Layer Depth ($H_{\text{mld}}$) | Prevents over-intensification on slow-moving tracks |

---

## 7. Verification and API Reference

All operational forecast APIs in IDMAP expose the dynamic probabilistic ensemble and trajectory intersection payload under `probabilistic_ensemble`:
* `ensemble_members_count`: Total perturbed simulations ($N=50$)
* `primary_landfall_consensus_pct`: Landfall district percentage split (e.g., `{"Puri": 92, "Ganjam": 8}`)
* `top_landfall_sector`: Dynamically calculated target sector (`Puri / Astranga Sector`)
* `ensemble_confidence_score_pct`: Quantitative consensus percentage (`92%`)
* `probabilistic_district_matrix`: Sorted district breakdown with strike confidence pills (`🔴 HIGH CONFIDENCE`, `🟠 MODERATE`, `🟡 MARGINAL`).
