# CityVision Frontend

React + Vite dashboard for the ANPR platform: GIS map, vehicle trajectory
search, traffic analytics, alerts and camera management.

## Stack

- React 19 + React Router v7
- Leaflet + react-leaflet (map, trajectory polylines, heatmap via `leaflet.heat`)
- Recharts (charts)
- Axios (API client with JWT auth + silent token refresh)

## Structure

```text
src/
├── components/
│   ├── Layout.jsx, ProtectedRoute.jsx
│   ├── Map/CityMap.jsx        -- shared Leaflet map (cameras, trajectory, alerts, heatmap)
│   ├── Camera/                -- CameraStatusBadge
│   ├── Alert/                 -- AlertCard
│   └── Analytics/             -- StatCard, HourlyTrafficChart, CameraTrafficChart
├── pages/
│   ├── Login.jsx
│   ├── Dashboard.jsx          -- stats + map + recent alerts + hourly chart
│   ├── VehicleSearch.jsx      -- plate search -> trajectory list + map
│   ├── Analytics.jsx          -- filters + charts + heatmap + route/speed tables
│   ├── Alerts.jsx             -- alert feed (polled) + blacklist management
│   └── Cameras.jsx            -- camera list + add camera (shows API key once)
├── context/AuthContext.jsx    -- JWT storage, current user, role helpers
├── hooks/useAuth.js
├── services/api.js            -- axios instance + all backend endpoint calls
└── theme.js                   -- validated categorical/status color palette
```

## Setup

```powershell
cd D:\Programs\Projects\Hackathon\CityVision\frontend
npm install
copy .env.example .env
```

`.env` just needs `VITE_API_URL` pointing at the Step 1 Django backend
(defaults to `http://127.0.0.1:8000`).

**Backend CORS**: make sure `backend/.env`'s `CORS_ALLOWED_ORIGINS`
includes `http://localhost:5173` (Vite's default port) -- already set
up if you're using this repo's `backend/.env.example` as a base.

## Running

```powershell
npm run dev
```

Open `http://localhost:5173`. Log in with a Django user created via
`python manage.py createsuperuser` (or the admin panel) -- VIEWER role
can read everything, OPERATOR/ADMIN can also create cameras and manage
the blacklist, ADMIN-only can regenerate a camera's API key.

## Notes on real-time-ness

Alerts currently refresh via polling (every 15s on the Dashboard and
Alerts pages), not a WebSocket push. Step 7 (Django Channels) replaces
the polling with a live push without changing this UI -- the alert list
just starts updating instantly instead of on a timer.

## Verified

Driven end-to-end with a headless Playwright browser against the real
Step 1/5 backend (MySQL + real multi-camera test data): login, Dashboard
(stat cards, camera markers + a real blacklist alert marker on the map,
hourly chart), Vehicle Search (real 5-stop cross-camera trajectory for
`TN07EF4321` rendered as a polyline), Analytics (categorical bar charts,
heatmap centered correctly on the highest-traffic camera), Alerts
(status filters, blacklist panel), and Cameras (camera table, add-camera
form) -- all five pages, zero browser console errors.
