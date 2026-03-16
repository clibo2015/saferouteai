# SafeRouteAI — Pitch Deck Technical Content
# Huawei Developer Competition — Spark Infinity

---

## SLIDE: Project Overview (Page 2 of template)

| Field | Content |
|---|---|
| Project Name | SafeRouteAI |
| Technical Field | PaaS, EI (Edge Intelligence), Mobile, Database |
| Technologies | FastAPI, React, Capacitor, Huawei Map Kit, Huawei ECS, Huawei OBS, Huawei ModelArts, Neon PostgreSQL, Nginx, JWT Authentication |
| Keywords | Safety Navigation, Crime Hotspot Detection, Real-time Hazard Alerts, AI Route Optimization, Edge AI, Mobile App |
| Applicable Fields | Smart City, Public Safety, Transportation, Mobile Applications |

**Description (200 words):**

SafeRouteAI is a real-time safety navigation mobile application built on Huawei Cloud infrastructure. It addresses a critical gap in existing navigation solutions — the absence of safety intelligence. Current navigation apps like Google Maps and Waze optimize for speed and distance but ignore crime hotspots, hazard zones, and real-time safety risks.

SafeRouteAI solves this by combining real crime data, user-reported hazards, and AI-powered route analysis to recommend the safest path to a destination. The app displays a live safety heatmap, highlights danger zones, and alerts users before they enter high-risk areas.

The system is built as a production-ready Android application backed by a Python FastAPI server deployed on Huawei ECS, with Huawei Map Kit powering the mapping layer, Huawei OBS for data storage, and Huawei ModelArts configured for AI model training. The database runs on Neon PostgreSQL with full user authentication, journey history, and personalized safety preferences.

Target users are everyday drivers, ride-hailing drivers, delivery personnel, and commuters in high-crime urban areas — particularly in South Africa where road safety and crime remain significant concerns.

---

## SLIDE: Technical Architecture — Overview (Page 6 of template)

### Key Technologies and Their Roles

**Huawei Cloud ECS (Elastic Cloud Server)**
- Hosts the entire backend application
- Ubuntu 22.04 LTS, Singapore region (ap-southeast-1)
- Runs Nginx as reverse proxy and FastAPI/Uvicorn as the application server
- Both services managed by systemd for auto-restart and boot persistence

**Huawei Map Kit**
- Powers all mapping functionality in the Android app
- Renders safety heatmaps, hazard markers, and danger zones
- Provides geocoding (address to coordinates) and route display
- Integrated via AppGallery Connect with production API keys

**Huawei OBS (Object Storage Service)**
- Stores crime dataset CSV files and trained ML model artifacts
- Used as the data source for the safety scoring engine
- Bucket: saferoute-data

**Huawei ModelArts**
- Configured for AI/ML model training pipeline
- Training jobs defined for safety prediction model
- Model artifacts stored in OBS and loaded by the inference engine

**Neon PostgreSQL (Serverless Database)**
- Stores user accounts, journey history, and hazard reports
- Serverless architecture scales automatically with usage
- SSL-encrypted connection with connection pooling

**FastAPI (Python Backend)**
- RESTful API with 15+ endpoints
- JWT-based authentication system
- Real-time safety data processing
- Route optimization engine
- Hazard crowdsourcing system

**React + Capacitor (Mobile Frontend)**
- React web app compiled to native Android APK via Capacitor
- Custom UI components: Dashboard, Navigation Screen, Hazard HUD, Onboarding
- HTTPS-only communication enforced

---

## SLIDE: Technical Architecture — Solution Deployment (Page 7 of template)

### Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│                   USER DEVICE                        │
│         Android App (React + Capacitor)              │
│         Huawei Map Kit SDK                           │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS (TLS 1.2+)
                       │ saferouteai.duckdns.org:443
┌──────────────────────▼──────────────────────────────┐
│              HUAWEI CLOUD ECS                        │
│         Region: ap-southeast-1 (Singapore)           │
│  ┌─────────────────────────────────────────────┐    │
│  │  Nginx (Port 443) — SSL Termination          │    │
│  │  Let's Encrypt Certificate                   │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │ Proxy                          │
│  ┌──────────────────▼──────────────────────────┐    │
│  │  FastAPI + Uvicorn (Port 8004)               │    │
│  │  - Authentication Service (JWT)              │    │
│  │  - Route Optimization Engine                 │    │
│  │  - Hazard Detection Service                  │    │
│  │  - Map Kit Integration Layer                 │    │
│  │  - Safety Scoring Engine                     │    │
│  └──────────┬───────────────────┬──────────────┘    │
│             │                   │                    │
└─────────────┼───────────────────┼────────────────────┘
              │                   │
┌─────────────▼──────┐  ┌────────▼───────────────────┐
│  Neon PostgreSQL   │  │  Huawei OBS                 │
│  (Serverless DB)   │  │  (Object Storage)           │
│  - Users           │  │  - Crime datasets (CSV)     │
│  - Journeys        │  │  - ML model artifacts       │
│  - Hazard Reports  │  │  - Training data            │
└────────────────────┘  └────────────────────────────┘
                                  │
                        ┌─────────▼──────────────────┐
                        │  Huawei ModelArts           │
                        │  (AI Training Platform)     │
                        │  - Safety prediction model  │
                        │  - Crime pattern analysis   │
                        └────────────────────────────┘
```

### Service Flow — User Navigation Request

1. User opens SafeRouteAI app on Android device
2. App authenticates user via `POST /api/v1/auth/login` → JWT token issued
3. App requests safety heatmap via `GET /api/v1/map/safety-heatmap`
4. Backend queries crime dataset from OBS + user hazard reports from Neon DB
5. Safety scoring engine calculates risk scores per geographic zone
6. Heatmap data returned to app → Huawei Map Kit renders visual overlay
7. User enters destination → `POST /api/v1/optimize-route` called
8. Route optimization engine evaluates multiple paths against safety scores
9. Safest route returned → displayed on Huawei Map Kit with turn-by-turn guidance
10. Hazard HUD activates when user enters flagged zones
11. Journey saved to Neon DB on completion via `POST /api/v1/journeys`

---

## SLIDE: Technical Architecture — Huawei Cloud Services Used

| Huawei Cloud Service | Role in SafeRouteAI | Status |
|---|---|---|
| ECS (Elastic Cloud Server) | Backend hosting, Nginx + FastAPI | ✅ Active |
| Huawei Map Kit | Mapping, geocoding, route display | ✅ Active |
| OBS (Object Storage) | Crime data storage, ML model storage | ✅ Active |
| ModelArts | AI model training pipeline | ✅ Configured |
| AppGallery Connect | Android app registration, Map Kit API keys | ✅ Active |
| VPC + Security Groups | Network isolation, firewall rules | ✅ Active |

### Technology Maturity Assessment

- **FastAPI**: Production-grade Python framework, used by major tech companies
- **Huawei Map Kit**: Official Huawei SDK, production-ready with global coverage
- **Neon PostgreSQL**: Serverless PostgreSQL, fully managed with 99.9% uptime SLA
- **Capacitor**: Maintained by Ionic team, used by thousands of production apps
- **Let's Encrypt SSL**: Industry standard, trusted by all major browsers and Android
- **systemd process management**: Linux standard, battle-tested for production services

---

## SLIDE: Functions (Page 9 of template)

### Core Functions

**1. Real-Time Safety Heatmap**
- Color-coded risk visualization overlaid on live map
- Powered by crime hotspot data processed through the safety scoring engine
- Updates dynamically as user moves through the map

**2. Safe Route Optimization**
- Analyzes multiple route options between origin and destination
- Scores each route based on crime data, hazard reports, and time of day
- Returns the route with the highest safety score, not just the fastest

**3. Hazard HUD (Heads-Up Display)**
- Activates automatically when entering flagged zones
- Displays real-time alerts: crime hotspots, user-reported incidents, danger zones
- Non-intrusive overlay that doesn't obstruct navigation

**4. Crowdsourced Hazard Reporting**
- Users report incidents in real-time via `POST /api/v1/map/report-hazard`
- Reports include location, hazard type, severity, and description
- Aggregated into the safety scoring engine for all users

**5. User Authentication & Journey History**
- Secure account creation and login with JWT tokens
- Full journey history with safety scores per trip
- Personalized safety preferences per user

**6. Edge AI Driver Behavior Analysis**
- On-device AI processor analyzes driving patterns
- Detects anomalies that may indicate unsafe conditions
- Runs locally on device for low latency

### Advantages Over Existing Products

| Feature | Google Maps | Waze | SafeRouteAI |
|---|---|---|---|
| Traffic routing | ✅ | ✅ | ✅ |
| Safety-based routing | ❌ | ❌ | ✅ |
| Crime hotspot overlay | ❌ | ❌ | ✅ |
| Real-time hazard HUD | ❌ | Partial | ✅ |
| AI safety scoring | ❌ | ❌ | ✅ |
| Offline-capable | Partial | ❌ | Planned |

---

## SLIDE: Innovations (Page 10 of template)

### Technical Innovations

**1. Safety-First Route Optimization**
Existing navigation apps treat safety as secondary to speed. SafeRouteAI inverts this — the primary optimization variable is safety score, with travel time as a secondary factor. This is a novel approach in the navigation space.

**2. Huawei Map Kit + AI Safety Layer Integration**
The project demonstrates a novel integration pattern: Huawei Map Kit's mapping capabilities combined with a custom AI safety scoring engine running on Huawei ECS. The safety heatmap is computed server-side and rendered client-side as a Map Kit overlay — a pattern not available in any existing Huawei Map Kit reference implementation.

**3. Crowdsourced + Algorithmic Hybrid Safety Model**
The safety scoring engine combines two data sources: static crime hotspot data (processed from real South African crime statistics) and dynamic user-reported hazards. This hybrid model improves accuracy over time as more users contribute data.

**4. Edge AI on Mobile**
The EdgeAIProcessor runs locally on the Android device, analyzing driver behavior without sending raw sensor data to the server. This reduces latency, preserves privacy, and works in low-connectivity environments.

**5. Production-Grade Architecture on Minimal Budget**
The entire system — ECS, OBS, ModelArts, Map Kit, SSL, database — runs in production with auto-restart, HTTPS, and automated certificate renewal. This demonstrates that enterprise-grade safety infrastructure can be built cost-effectively using Huawei Cloud services.

### Technical Breakthroughs

- First known implementation of Huawei Map Kit with a real-time AI safety heatmap overlay
- Real South African crime data (SAPS statistics) integrated into a live navigation system
- Full production deployment on Huawei Cloud with zero manual intervention required after setup


---

## SLIDE: Project Introduction

### Project Background

South Africa has one of the highest crime rates in the world. According to SAPS (South African Police Service) statistics, over 2.8 million crimes were reported in 2023 alone — including carjackings, robberies, and violent incidents that frequently occur on public roads. Despite this, the navigation tools most people rely on daily (Google Maps, Waze) were built to solve a traffic problem, not a safety problem. They have no awareness of crime hotspots, no ability to warn a driver before entering a dangerous area, and no mechanism for communities to share real-time safety information with each other.

SafeRouteAI was built to fill that gap. The project started from a simple observation: people in high-crime urban areas already mentally avoid certain roads at certain times — they just have no tool that does this for them automatically. SafeRouteAI makes that safety intelligence accessible, data-driven, and real-time.

---

### Key Features

**Safety Heatmap**
A live color-coded overlay on the map showing risk levels across geographic zones. Green = low risk, yellow = moderate, red = high risk. Powered by real SAPS crime statistics and user-reported incidents.

**Safe Route Optimization**
When a user enters a destination, the app evaluates multiple route options and returns the one with the highest safety score — not just the fastest. Safety is the primary optimization variable.

**Hazard HUD (Heads-Up Display)**
A non-intrusive overlay that activates automatically when the user enters a flagged zone. Displays the type of hazard, severity, and distance — without blocking the navigation view.

**Crowdsourced Hazard Reporting**
Users can report incidents in real-time: carjackings, road blocks, accidents, suspicious activity. Reports are immediately factored into the safety scores for all other users in the area.

**User Authentication & Journey History**
Secure accounts with full journey history, safety scores per trip, and personalized preferences. Users can review past routes and see which areas they've traveled through.

**Edge AI Driver Behavior Analysis**
An on-device AI processor monitors driving patterns and detects anomalies that may indicate unsafe conditions — running locally on the device for low latency and privacy.

---

### Problems Solved

| Problem | How SafeRouteAI Solves It |
|---|---|
| Drivers unknowingly enter high-crime areas | Safety heatmap and proactive hazard alerts warn users before they enter |
| No real-time community safety sharing | Crowdsourced hazard reporting lets users warn each other instantly |
| Navigation apps ignore crime data | Route optimization engine uses real SAPS crime statistics as primary input |
| Reactive safety (you find out after the fact) | Proactive alerts trigger before the user reaches a flagged zone |
| Safety data is siloed and inaccessible | Aggregated, visualized, and surfaced directly in the navigation interface |

---

### Application Scenarios

**Daily Commuters**
A commuter driving to work can see at a glance which roads have elevated risk that morning, and get an alternative route suggestion before they even start driving.

**Ride-Hailing & Delivery Drivers**
Uber, Bolt, and food delivery drivers operate in unfamiliar areas at all hours. SafeRouteAI gives them a safety layer that their employer's app doesn't provide — reducing exposure to carjackings and robberies.

**Tourists & Visitors**
People unfamiliar with a city have no intuition for which areas to avoid. SafeRouteAI provides that local knowledge automatically, without requiring the user to know the city.

**Emergency Situations**
If a user needs to leave an area quickly, the app can calculate the safest exit route in real time, factoring in current hazard reports from other users.

**Fleet & Logistics Management**
Companies managing vehicle fleets can use the API to route drivers through safer corridors, reducing insurance risk and improving driver safety.

---

### Target Users

**Primary Users**
- Drivers in South African urban areas (Johannesburg, Cape Town, Durban, Pretoria)
- Ride-hailing drivers (Uber, Bolt, inDrive)
- Food and parcel delivery drivers

**Secondary Users**
- Daily commuters who drive to work
- Tourists and visitors unfamiliar with local areas
- Parents tracking family members' routes

**Enterprise Users (Future)**
- Logistics and fleet companies
- Insurance companies (safety-based premium models)
- Municipal governments and law enforcement (aggregated safety data)

**Market Context**
South Africa has approximately 12 million registered vehicles and one of the highest smartphone penetration rates on the continent. The ride-hailing market alone is growing at over 15% annually. SafeRouteAI targets a market that is large, underserved by existing tools, and acutely aware of the safety problem the app solves.
