# Stellenbosch Field Test — Huawei-free Runbook

This is the end-to-end plan for putting SafeRouteAI on a real phone in Stellenbosch
without any Huawei Cloud account, credentials, or consent gates.

Runtime stack (locked):

| Need | Choice |
| --- | --- |
| Phone app | Capacitor Android APK (`com.saferoute.ai`) |
| API host | Render free Web Service (HTTPS) |
| Database | Existing Neon Postgres (`DATABASE_URL`) |
| Maps UI | Leaflet + CARTO / OSM tiles |
| Road routing | Public OSRM (`router.project-osrm.org`) |
| Geocoding | Nominatim (OSM) with app User-Agent |
| Storage / ML | Local disk + sklearn/YOLO — no OBS, no ModelArts |
| Test area | Stellenbosch + surrounds (R44, Kayamandi, Cloetesville) |

```
Phone (Capacitor APK) --HTTPS/JWT--> Render FastAPI --asyncpg--> Neon Postgres
        |                                  |
        |-- tiles ---------------------> CARTO / OSM
        |-- routes --------------------> public OSRM
        |-- geocode -------------------> Nominatim
```

## Phase 1 — Huawei removed from the runtime path (done)

- `src/routing_engine.py` fetches geometry from
  `https://router.project-osrm.org/route/v1/driving/{lon},{lat};{lon},{lat}?overview=full&geometries=geojson`
  and keeps the existing per-segment risk scoring.
- `src/opensource_maps.py` provides the Leaflet/OSM map config, Nominatim geocoding,
  Stellenbosch hotspot markers, hazard zones and heatmap data. `src/api.py`
  serves them from `/api/v1/map/*` — no Huawei JS keys are returned.
- `src/config.py` no longer defines or validates any `HUAWEI_*` setting. Missing
  `DATABASE_URL` is a warning, not a boot failure, so maps/routing still work.
- `requirements.txt` no longer installs `huaweicloudsdkcore` / `esdk-obs-python`.
- `frontend/src/services/apiService.js` reads only `REACT_APP_API_URL`; a
  production build throws a clear error if it is missing. The hardcoded
  `http://110.238.78.155:8004` host is gone.
- The GPS-denied fallback and the default map centre are Stellenbosch
  (`-33.9321, 18.8602`), not Johannesburg.
- Loading / onboarding / dashboard footers now say "OpenStreetMap + OSRM" instead
  of "HUAWEI CLOUD". `HuaweiMapComponent.js` and other unused Huawei UI are left
  untouched and are not imported by the navigation screen.

## Phase 2 — Deploy the API on Render + Neon

1. Push the repo to GitHub (Render deploys from the repository root).
2. Create a Render **Web Service** from the repo:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: taken from the root [`Procfile`](Procfile) —
     `uvicorn src.api:app --host 0.0.0.0 --port $PORT`
   - Health check path: `/`
3. Set environment variables in the Render dashboard:

   | Key | Value |
   | --- | --- |
   | `DATABASE_URL` | your Neon connection string (`?sslmode=require`) |
   | `JWT_SECRET` | long random value, e.g. `python -c "import secrets;print(secrets.token_urlsafe(48))"` |
   | `DEMO_MODE` | `false` |
   | `PYTHON_VERSION` | `3.11.9` |
   | `ESKOM_SE_PUSH_KEY` | optional |

   Do **not** set any `HUAWEI_*` variable. `API_HOST` / `API_PORT` are not needed on
   Render because the Procfile binds `$PORT`.
4. Confirm Neon accepts Render egress. Neon projects normally allow all IPs; if an
   allowlist was configured earlier for Huawei, remove/expand it.
5. Smoke-test the deployed service (replace the host):

   ```bash
   BASE=https://<your-service>.onrender.com
   curl -s $BASE/ | jq '.services, .neon_database'
   curl -s $BASE/api/v1/map/config | jq '.map_config.provider'
   curl -s -X POST $BASE/api/v1/map/geocode \
     -H 'Content-Type: application/json' \
     -d '{"address":"Kayamandi, Stellenbosch"}' | jq .
   curl -s -X POST $BASE/api/v1/optimize-route \
     -H 'Content-Type: application/json' \
     -d '{"start_point":{"lat":-33.9338,"lng":18.8604},"end_point":{"lat":-33.9195,"lng":18.8360},"safety_preferences":{"priority":"safety"}}' \
     | jq '.route_data | {total_distance_km, total_time_minutes, segments: (.segments|length)}'
   curl -s -X POST $BASE/api/v1/auth/register \
     -H 'Content-Type: application/json' \
     -d '{"email":"field@example.com","name":"Field","password":"<strong-password>"}' | jq .
   ```

   Expected: `neon_database: true` and `✅ Connected` once `DATABASE_URL` is set;
   503 "Database not available" if it is missing.

**Render free-tier caveat:** the service sleeps after ~15 idle minutes and the first
request can take 30–60 s. `apiService.js` already retries transient failures and
exposes `warmup()`; on field days open the app once and wait for the first ping.

## Phase 3 — Stellenbosch-ready Android APK

```bash
cd frontend
npm ci
REACT_APP_API_URL=https://<your-service>.onrender.com npm run build
npx cap sync android
cd android
./gradlew assembleDebug          # Windows: gradlew.bat assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Notes:

- `frontend/capacitor.config.ts` already uses `appId: com.saferoute.ai`,
  `appName: SafeRouteAI`, `webDir: build`.
- `frontend/android/app/src/main/AndroidManifest.xml` already declares
  `INTERNET`, `ACCESS_FINE_LOCATION` and `ACCESS_COARSE_LOCATION`.
- Use the HTTPS Render URL so cleartext is not required for the API. The manifest's
  `usesCleartextTraffic` setting is only needed for local `http://` testing.
- If browser geolocation proves flaky inside the WebView, add `@capacitor/geolocation`
  and call it from the map/navigation screens — only after a desk test shows a problem.
- Building requires JDK 17+ and the Android SDK. On a machine without them, build the
  APK in Android Studio or install the SDK/command-line tools first.

## Phase 4 — Real-world drive checklist (Stellenbosch)

Routes that exercise the hotspots already shipped in the app:

| Route | Start → end |
| --- | --- |
| CBD loop | Plein / Dorp / Bird / Braak |
| R44 corridor | Merriman / Cloetesville / Jamestown turnoff |
| Kayamandi approach | Helshoogte / taxi rank |

Do one daytime run and one short after-dark run. Do **not** enter high-risk areas
just to test.

Validate on the device:

- [ ] GPS blue dot tracks while moving
- [ ] OSRM route follows real roads (not a straight line)
- [ ] Stellenbosch / Kayamandi hotspot markers appear
- [ ] Route risk score changes when the path skirts hotter spots
- [ ] Login and journey save still work over mobile data against Neon
- [ ] App recovers after a Render cold start (first request may take ~60 s)
- [ ] `/` on the API shows `neon_database: true` and no Huawei fields

## Out of scope for this field test

- Self-hosted OSRM (revisit only if public OSRM rate-limits or ZA coverage fails)
- ModelArts training, OBS buckets, GaussDB, AppGallery Connect
- iOS build
- Offline tile caching (first run assumes mobile data)

## Success criteria

The APK installs on a phone, opens on mobile data in Stellenbosch, produces a
safety-scored route between two real local points, shows local hotspot context and
persists the journey — with no Huawei credentials in `.env` or on Render.
