# Victoria Urban Planning - Frontend Dashboard

The frontend is a high-performance React 18 single-page application built with Vite, MapLibre GL, and Recharts. It renders interactive geospatial maps, 24-hour sensor telemetry curves, and dynamic evidence matrices communicating the real-world impacts of bike lane construction.

---

## Component Architecture

```
frontend/src/
├── components/
│   ├── Header.jsx                 # Top bar containing tab navigation, Suburb & Street corridor filters, and live quick stat pills
│   ├── Header.module.css          # Glassmorphic header styling & tooltip overlays
│   ├── ExecutiveBriefing.jsx      # Executive briefing view with research verdict, capacity cards, hourly profiles & evidence matrix
│   ├── ExecutiveBriefing.module.css
│   ├── MapContainer.jsx           # MapLibre GL vector map rendering street blocks with dynamic camera bounds
│   ├── MapContainer.module.css
│   ├── ImpactDashboard.jsx        # Sidebar corridor impact assessment, bay removal KPIs & block-level occupancy
│   └── ImpactDashboard.module.css
├── App.jsx                        # Master application state, location dropdown synchronization & data fetching
├── main.jsx                       # React DOM root initializer
└── index.css                      # Global design system tokens, typography & CSS variables
```

---

## Analytical Views & Tabs

1. **`briefing` (Executive Briefing):**
   * Synthesizes empirical findings answering: *"How does parking use change with bike lanes constructed?"*
   * Displays kerbside capacity preserved, average occupancy, surplus vacancy, and the 24-hour occupancy profile.
   * Renders the dynamic **Business Stakeholder Concerns vs Empirical Evidence Matrix** adapting to active filters.

2. **`explorer` (Corridor Map Explorer):**
   * Renders street segments on a MapLibre GL canvas colored by capacity change.
   * Clicking any corridor displays block-level baseline vs post-intervention bay numbers and hourly stay curves in the sidebar.

---

## Development & Build Commands

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Vite development server on port 5000
npm run dev -- --port 5000

# Run Oxlint linting suite
npm run lint

# Compile production build
npm run build
```

---

## Configuration & Environment Variables

Environment variables are auto-generated into `frontend/.env` by `run_app.py` based on values in `config.yaml`:

```env
VITE_API_URL=http://localhost:7000
VITE_BASELINE_YEAR=2013
VITE_POST_YEAR=2014
```
