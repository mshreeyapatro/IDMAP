# Dynamic Forecasting & Spatial Risk Engine: Mathematical & Meteorological Architecture

## Executive Summary
This document provides the complete theoretical foundation, mathematical formulations, algorithmic workflows, and empirical parameter calibrations for the **4-Component Dynamic Cyclone Forecasting and Spatial Risk Engine** deployed across the IDMAP platform for the state of Odisha.

---

## System Architecture Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│               MULTIMODAL INGESTION LAYER                    │
│   • Live Open-Meteo Hourly Weather Telemetry (6 Stations)   │
│   • ISRO MOSDAC / NASA GIBS Live Satellite Pass (PyTorch)   │
│   • TCIR ResNet Intensity Proxy (Vmax_proxy, Anomaly Error) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. 2D TRAJECTORY VECTOR ADVECTION ENGINE                    │
│    • Inputs: (lat0, lon0), Heading θ, Speed v_trans, Step h │
│    • Outputs: Real-time Storm Eye Position (lat_eye, lon_eye)│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. HAVERSINE MOVING EYE GEODESIC ENGINE                     │
│    • Spherical Geodesic: (lat_eye(h), lon_eye(h)) ──> (latD, lonD)
│    • Outputs: Precise Dynamic Distance d_eye(h, D) (30 Dists)│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. MODIFIED RANKINE VORTEX RADIAL WIND PROFILE              │
│    • Core Eyewall (r <= Rmax): Ramping (r / Rmax)^0.8       │
│    • Outer Vortex (r > Rmax): Cyclonic Decay (Rmax / r)^0.5 │
│    • Outputs: Local Wind Speed V_D(h) for Every District    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. KAPLAN-DEMARIA LANDFALL DECAY & XGBOOST/SHAP FUSION      │
│    • Inland Wind Decay: V_max(t) = (V_lf - V_bg)*e^(-α*t)+V_bg
│    • Dynamic Surface Pressure Field: P_surface(h, D)        │
│    • XGBoost Regressor Risk Score & Live SHAP Decomposition │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Dynamic 2D Trajectory Vector Advection with Parabolic Recurvature

### Theoretical Background
Cyclones in the Bay of Bengal initially track Northwestward ($\approx 315^\circ$) along the steering current of the sub-tropical ridge. As they translate north of $19.8^\circ\text{N}$, interaction with the Earth's planetary vorticity gradient (**Beta-drift** $\beta = \frac{2\Omega\cos\phi}{R_E}$) and mid-to-upper tropospheric westerly troughs deflects the system rightward towards the North-North-East ($015^\circ - 045^\circ$, like *Cyclone Fani* and *Amphan*).

### Mathematical Formulation
The engine performs numerical path integration over 15-minute steps ($dt = 0.25\text{ h}$):

$$\frac{d\theta}{dt} = \begin{cases} 
0.0 & \text{if } \text{lat}_{\text{eye}}(t) \le 19.8^\circ\text{N} \\[6pt]
0.40 \cdot \left(\text{lat}_{\text{eye}}(t) - 19.8\right) & \text{if } \text{lat}_{\text{eye}}(t) > 19.8^\circ\text{N} \quad (\text{deg/h})
\end{cases}$$

$$\theta(t + dt) = \theta(t) + \frac{d\theta}{dt} \cdot dt$$

$$\text{lat}_{\text{eye}}(t + dt) = \text{lat}_{\text{eye}}(t) + \frac{v_{\text{trans}} \cdot dt \cdot \cos(\theta(t))}{111.32}$$

$$\text{lon}_{\text{eye}}(t + dt) = \text{lon}_{\text{eye}}(t) + \frac{v_{\text{trans}} \cdot dt \cdot \sin(\theta(t))}{111.32 \cdot \cos\left(\text{lat}_{\text{eye}}(t) \cdot \frac{\pi}{180}\right)}$$

---

## 1B. WMO / IMD Rapid Intensification (RI) Warning Index

### Theoretical Background
The World Meteorological Organization (WMO) and IMD define Rapid Intensification as a max sustained wind increase of $\ge 30\text{ kt}$ in a 24-hour window ($+1.25\text{ kt/hour}$). RI occurs when high ocean heat content ($\text{SST} \ge 29.5^\circ\text{C}$) combines with strong convective organization and low vortex asymmetry.

### Mathematical Formulation
$$\text{RI\_Score} = 0.45 \cdot \left(\frac{\text{SST} - 28.0}{3.0}\right) + 0.35 \cdot \text{CloudDensity}_{\text{sat}} + 0.20 \cdot \left(1.0 - \frac{\text{AnomalyReconError}}{0.10}\right) \in [0.0, 1.0]$$

* **Classification Rule:**
  - $\text{RI\_Score} \ge 0.75 \implies$ `🚨 HIGH PROBABILITY (Surge >=30kt/24h)` $\rightarrow$ Triggers early tactical warnings.
  - $\text{RI\_Score} < 0.75 \implies$ `🟢 LOW / NORMAL INTENSIFICATION`.

---

## 1C. IMD Official Ensemble Cone of Uncertainty ($\pm \sigma(h)$ Track Swarm)

### Theoretical Background
Official IMD / WMO track bulletins define an expanding circular confidence cone along the forecast trajectory to convey track spread and spatial uncertainty:

### Mathematical Formulation
$$R_{\text{cone}}(h) = \begin{cases} 
0.0\text{ km} & \text{at } T+0\text{h} \quad (\text{Exact satellite fix}) \\
\text{round}\left(3.0 \cdot h^{1.02}, 1\right) & \text{for } h > 0\text{h} \quad (\text{Empirical IMD 70% confidence radius})
\end{cases}$$

| Forecast Horizon | IMD 70% Confidence Uncertainty Radius ($R_{\text{cone}}$) |
| :--- | :--- |
| **$T+0\text{h}$** | $\pm 0.0\text{ km}$ |
| **$T+6\text{h}$** | $\pm 18.6\text{ km}$ |
| **$T+12\text{h}$** | $\pm 37.7\text{ km}$ |
| **$T+24\text{h}$** | $\pm 76.4\text{ km}$ |
| **$T+36\text{h}$** | $\pm 115.6\text{ km}$ |
| **$T+48\text{h}$** | $\pm 155.2\text{ km}$ |

---

## 2. Haversine Geodesic Distance & Compass Bearing to Moving Eye

### Theoretical Background
As the cyclone translates across the Bay of Bengal and intersects the coastline, the distance and relative bearing angle from the storm center to each district centroid shift continuously. Accurate spherical trigonometry is essential to evaluate the radial wind field, translation asymmetry, and local storm surge exposure.

### Mathematical Formulation
For any district $D$ with centroid coordinates $(\text{lat}_D, \text{lon}_D)$ and advected cyclone eye coordinates $(\text{lat}_{\text{eye}}(h), \text{lon}_{\text{eye}}(h))$:

$$\Delta \text{lat} = (\text{lat}_D - \text{lat}_{\text{eye}}(h)) \cdot \frac{\pi}{180}$$

$$\Delta \text{lon} = (\text{lon}_D - \text{lon}_{\text{eye}}(h)) \cdot \frac{\pi}{180}$$

$$a = \sin^2\left(\frac{\Delta \text{lat}}{2}\right) + \cos\left(\text{lat}_{\text{eye}}(h) \cdot \frac{\pi}{180}\right) \cdot \cos\left(\text{lat}_D \cdot \frac{\pi}{180}\right) \cdot \sin^2\left(\frac{\Delta \text{lon}}{2}\right)$$

$$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$

$$d_{\text{eye}}(h, D) = R_E \cdot c \quad (\text{where } R_E = 6371.0\text{ km})$$

### Initial Compass Bearing Angle ($\beta$)
$$\beta = \text{atan2}\left(\sin(\Delta \text{lon}) \cdot \cos(\text{lat}_D), \; \cos(\text{lat}_{\text{eye}}) \cdot \sin(\text{lat}_D) - \sin(\text{lat}_{\text{eye}}) \cdot \cos(\text{lat}_D) \cdot \cos(\Delta \text{lon})\right) \pmod{360^\circ}$$

---

## 3. Asymmetric Modified Rankine Vortex Radial Wind Speed Profile

### Theoretical Background
Tropical cyclones exhibit distinct wind structures: inside the Radius of Maximum Winds ($R_{\max}$), winds increase rapidly within the eyewall; outside $R_{\max}$, tangential velocities decay cyclonically with radial distance $r$.

Furthermore, in the Northern Hemisphere (Bay of Bengal), cyclones rotate **counter-clockwise**. Consequently, winds in the **Right-Front Quadrant (Dangerous Semicircle)** combine the rotational velocity with the storm forward translation speed, whereas winds in the Left Quadrant oppose forward motion. The engine implements the **Schwerdt / Miyazaki vortex translation asymmetry formulation**.

### Mathematical Formulation
Given the Radius of Maximum Winds $R_{\max} \approx 35.0\text{ km}$, core maximum sustained wind $V_{\max}(h)$, steering heading $\theta_{\text{heading}}$, and translation speed $v_{\text{trans}}\text{ (kt)}$:

$$r = \max\left(1.0, d_{\text{eye}}(h, D)\right)$$

#### 1. Base Symmetric Vortex:
$$V_{\text{symmetric}}(r) = \begin{cases} 
V_{\max}(h) \cdot \left[ 0.35 + 0.65 \cdot \left( \dfrac{r}{R_{\max}} \right)^{0.8} \right] & \text{for } r \le R_{\max} \quad (\text{Eyewall Ramping}) \\[10pt]
V_{\max}(h) \cdot \left( \dfrac{R_{\max}}{r} \right)^{0.5} & \text{for } r > R_{\max} \quad (\text{Outer Vortex Decay})
\end{cases}$$

#### 2. Translation Vector Asymmetry Correction:
$$\Delta V_{\text{asym}}(r, \beta) = v_{\text{trans}} \cdot \sin\left(\beta - \theta_{\text{heading}}\right) \cdot \left( \frac{R_{\max}}{\max(R_{\max}, r)} \right)^{0.5}$$

$$V_D(r, \beta) = \max\left(V_{\text{ambient}}, \; V_{\text{symmetric}}(r) + \Delta V_{\text{asym}}(r, \beta)\right)$$

### Dynamic Kinetic Wind Pressure
Dynamic wind force on structures $q$ ($\text{N/m}^2$) is computed using standard fluid dynamics:

$$v_{\text{ms}} = V_D(r, \beta) \cdot 0.514444 \quad (\text{m/s})$$

$$q = \frac{1}{2} \cdot \rho_{\text{air}} \cdot (v_{\text{ms}})^2 \quad \left(\text{with } \rho_{\text{air}} = 1.225\text{ kg/m}^3\right)$$

---

## 3B. Jelesnianski / SLOSH Coastal Storm Surge & Tidal Inundation Model

### Theoretical Background
The Bay of Bengal features an exceptionally shallow continental shelf that amplifies coastal surge heights. The model computes peak surge height $S_{\text{surge}}$ (in meters) for all coastal nodes ($d_{\text{coast}} \le 25\text{ km}$) fusing the **Inverse Barometer Sea Surface Rise** with the **Onshore Wind Stress Surge**.

### Mathematical Formulation
$$\Delta P = \max(0.0, \; 1013.25 - P_{\text{surface}}(h, D)) \quad (\text{hPa})$$

$$h_{\text{baro}} = \Delta P \cdot 0.01 \quad (\approx 1\text{ cm sea level rise per 1 hPa drop})$$

$$h_{\text{wind}} = 0.00055 \cdot (V_D)^2 \cdot \max\left(0.25, \; \cos\left(\beta - 315^\circ\right)\right)$$

$$S_{\text{surge}} = \left( h_{\text{baro}} + h_{\text{wind}} \right) \cdot \exp\left(-\frac{d_{\text{coast}}}{15.0}\right) \quad (\text{m})$$

### Surge Alert Classification:
- $S_{\text{surge}} \ge 3.0\text{ m}$: `🌊 EXTREME SURGE (>3.0m)` $\rightarrow$ Mandatory Sea-Wall Evacuation
- $1.8\text{ m} \le S_{\text{surge}} < 3.0\text{ m}$: `🌊 HIGH SURGE (1.8-3.0m)` $\rightarrow$ Low-Lying Coastal Inundation
- $0.8\text{ m} \le S_{\text{surge}} < 1.8\text{ m}$: `🌊 MODERATE SURGE (0.8-1.8m)` $\rightarrow$ High-Tide Caution
- $S_{\text{surge}} < 0.8\text{ m}$ or $d_{\text{coast}} > 25\text{ km}$: `🟢 INLAND / NIL SURGE`

---

## 3C. IMD / NOAA 24-Hour Accumulated Rainfall Potential Model ($R_{\text{pot}}$)

### Theoretical Background
Inland flood damage is governed by precipitation intensity and translation speed (slower-moving storms deposit dramatically higher rainfall accumulation). The engine uses the standard tropical cyclone rainfall potential formulation:

### Mathematical Formulation
$$R_{24\text{h}} = \left( \frac{1.6 \cdot V_{\max}(h)}{\max(7.0, \; v_{\text{trans, kmh}})} \right) \cdot 24.0 \cdot 0.45 \cdot \exp\left(-\frac{d_{\text{eye}}(h, D)}{180.0}\right) + R_{\text{ambient}} \quad (\text{mm})$$

### Rainfall Alert Thresholds:
- $R_{24\text{h}} \ge 204.5\text{ mm}$: `🔴 Extremely Heavy Rain (>204mm)`
- $115.6\text{ mm} \le R_{24\text{h}} < 204.5\text{ mm}$: `🟠 Heavy to Very Heavy Rain (115-204mm)`
- $64.5\text{ mm} \le R_{24\text{h}} < 115.6\text{ mm}$: `🟡 Heavy Rain (64-115mm)`
- $R_{24\text{h}} < 64.5\text{ mm}$: `🟢 Moderate / Light Rain (<64mm)`

---

## 4. Post-Landfall Intensity Decay (Kaplan-DeMaria Law) & XGBoost Risk Fusion

### Theoretical Background
Upon crossing the coastline, frictional dissipation and deprivation of oceanic latent heat flux cause rapid exponential degradation of storm intensity. The **Kaplan-DeMaria empirical decay model** (standardized by IMD / NHC) accurately reproduces this overland deceleration.

### Mathematical Formulation
For time horizon step $h$ and estimated landfall time $t_{\text{landfall}}$:

#### Pre-Landfall / Approaching Phase ($h \le t_{\text{landfall}}$):
$$V_{\max}(h) = V_{\text{landfall}} \cdot \left( 0.45 + 0.55 \cdot \frac{h}{\max(1.0, t_{\text{landfall}})} \right)$$

$$P_{\text{central}}(h) = P_{\text{base}} - (P_{\text{base}} - P_{\text{min, lf}}) \cdot \left(\frac{h}{\max(1.0, t_{\text{landfall}})}\right)$$

#### Post-Landfall Phase ($h > t_{\text{landfall}}$):
$$t_{\text{post}} = h - t_{\text{landfall}}$$

$$V_{\max}(t_{\text{post}}) = (V_{\text{landfall}} - V_{\text{background}}) \cdot e^{-\alpha \cdot t_{\text{post}}} + V_{\text{background}}$$

*Calibrated parameters:*
- $\alpha = 0.095\text{ hr}^{-1}$ (Decay rate constant)
- $V_{\text{background}} = 15.0\text{ kt}$ (Residual depression vortex baseline)

### Surface Pressure Field Modeling
Local barometric pressure $P_{\text{surface}}(h, D)$ at district $D$:

$$P_{\text{surface}}(h, D) = P_{\text{central}}(h) + \left(1012.0 - P_{\text{central}}(h)\right) \cdot \left(1 - e^{-0.012 \cdot d_{\text{eye}}(h, D)}\right)$$

### XGBoost & SHAP Risk Regressor
The complete dynamic feature vector $\mathbf{X}_D(h)$ is passed into the trained XGBoost Regressor:

$$\mathbf{X}_D(h) = \begin{bmatrix}
V_D(h) & (\text{Rankine local wind in knots}) \\
d_{\text{eye}}(h, D) & (\text{Haversine distance to eye in km}) \\
\text{Population}_D & (\text{Census 2011 district population}) \\
P_{\text{surface}}(h, D) & (\text{Local surface pressure in hPa}) \\
\text{ReconError}_{\text{sat}} & (\text{Autoencoder cloud wall reconstruction error})
\end{bmatrix}$$

$$\text{RiskScore}_D(h) = \text{XGBoost}(\mathbf{X}_D(h)) \in [0.0, 1.0]$$

$$\text{RiskScore}_D(h) = \phi_0 + \sum_{i=1}^5 \phi_i(\mathbf{X}_D(h)) \quad (\text{SHAP Additive Attribution})$$

---

## 5. Standard IMD Cyclone Classification Scale

| Sustained Wind Speed ($V_{\max}$) | Category Name | Dynamic Pressure ($q$) |
| :--- | :--- | :--- |
| $< 17\text{ kt}$ ($< 31\text{ km/h}$) | Low Pressure Area (LPA) | $< 40\text{ N/m}^2$ |
| $17 - 27\text{ kt}$ ($31 - 49\text{ km/h}$) | Depression (D) | $40 - 110\text{ N/m}^2$ |
| $28 - 33\text{ kt}$ ($50 - 61\text{ km/h}$) | Deep Depression (DD) | $110 - 170\text{ N/m}^2$ |
| $34 - 47\text{ kt}$ ($62 - 88\text{ km/h}$) | Cyclonic Storm (CS) | $170 - 350\text{ N/m}^2$ |
| $48 - 63\text{ kt}$ ($89 - 117\text{ km/h}$) | Severe Cyclonic Storm (SCS) | $350 - 620\text{ N/m}^2$ |
| $64 - 89\text{ kt}$ ($118 - 166\text{ km/h}$) | Very Severe Cyclonic Storm (VSCS) | $620 - 1260\text{ N/m}^2$ |
| $90 - 119\text{ kt}$ ($167 - 221\text{ km/h}$) | Extremely Severe Cyclonic Storm (ESCS) | $1260 - 2250\text{ N/m}^2$ |
| $\ge 120\text{ kt}$ ($\ge 222\text{ km/h}$) | Super Cyclonic Storm (SuCS) | $\ge 2250\text{ N/m}^2$ |

---

## 6. Verification and Boundary Condition Testing

| Horizon | Condition | Distance to Eye ($d_{\text{eye}}$) | Wind Speed ($V_D$) | Status |
| :--- | :--- | :--- | :--- | :--- |
| $T+0\text{h}$ | Eye at Sea ($19.5^\circ\text{N}, 86.2^\circ\text{E}$) | Puri: $65.3\text{ km}$ | $12.1\text{ kt}$ | Verified |
| $T+0\text{h}$ | Eye at Sea ($19.5^\circ\text{N}, 86.2^\circ\text{E}$) | Ganjam: $160.8\text{ km}$ | $16.6\text{ kt}$ | Verified |
| $T+12\text{h}$ | Advected ($20.6^\circ\text{N}, 85.0^\circ\text{E}$) | Puri: $112.2\text{ km}$ | $13.9\text{ kt}$ | Verified |
| $T+12\text{h}$ | Advected ($20.6^\circ\text{N}, 85.0^\circ\text{E}$) | Ganjam: $116.6\text{ km}$ | $18.2\text{ kt}$ | Verified |
| $T+48\text{h}$ | Inland Overland ($24.0^\circ\text{N}, 81.4^\circ\text{E}$) | All Districts: $>300\text{ km}$ | $15.0\text{ kt}$ (Residual) | Verified |

---

## 7. Code Implementation References
- Core Engine: [`src/forecasting/predictive_engine.py`](file:///c:/Professional/Projects/IDMAP/src/forecasting/predictive_engine.py)
- Unified Live Survey: [`src/agent/unified_survey.py`](file:///c:/Professional/Projects/IDMAP/src/agent/unified_survey.py)
- Frontend Scrubber & Matrix Table: [`frontend/src/components/ForecastView.jsx`](file:///c:/Professional/Projects/IDMAP/frontend/src/components/ForecastView.jsx)
- Spatial Nodes & Centroids: [`data/processed/odisha_district_nodes.csv`](file:///c:/Professional/Projects/IDMAP/data/processed/odisha_district_nodes.csv)
