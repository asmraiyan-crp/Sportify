# ⚡ Sportify — Frontend V2

Modular ReactJS + TypeScript + Tailwind CSS frontend for the Sportify DBMS project.

## Stack
- **React 18** + **TypeScript** (strict mode)
- **Tailwind CSS v4** with custom design tokens
- **Vite 5** build tool + dev proxy to Flask
- **Axios** for Flask API calls (no Supabase on frontend)

## Project Structure

```
src/
├── App.tsx                          # Router only (~55 lines)
├── main.tsx                         # Entry point
├── sportify.css                     # Fonts + scrollbar (Tailwind can't do these)
│
├── types/index.ts                   # All TypeScript interfaces
├── data/index.ts                    # Mock data + constants (swap with axios later)
├── hooks/index.ts                   # useHeroSlider, useMatchFilter, useModal, etc.
│
├── pages/
│   ├── LandingPage.tsx              # Public marketing page (unauthenticated)
│   ├── DashboardPage.tsx            # Main app — 5 tabs: home/matches/standings/players/events
│   └── ProfilePage.tsx              # User profile — 4 tabs: overview/following/activity/settings
│
└── components/
    ├── shared/index.tsx             # Badges, skeletons, FilterTabs, SectionHeader, etc.
    ├── layout/
    │   ├── Navbar.tsx               # Auth-aware top nav
    │   └── Sidebar.tsx              # Quick nav + mini standings + Footer
    ├── hero/HeroSlider.tsx          # Auto-cycling hero with prev/next arrows
    ├── match/MatchCard.tsx          # MatchCard + UpcomingRow + MatchModal
    ├── player/PlayerCard.tsx        # Sport-smart stats, follow button, injury badge
    └── standings/StandingsTable.tsx # Compact + full modes with GD column
```

## Getting Started

```bash
# 1. Install dependencies
npm install

# 2. Start dev server (proxies /api/* to http://localhost:5000)
npm run dev

# 3. Open http://localhost:5173
```

## Connecting to Flask Backend

All data currently comes from `src/data/index.ts` (mock arrays).

To wire a component to your real Flask API, replace the import with an axios call:

```ts
// BEFORE (mock)
import { LIVE_MATCHES } from "../data";

// AFTER (real Flask API)
import { useState, useEffect } from "react";
import axios from "axios";

const [matches, setMatches] = useState([]);
useEffect(() => {
  axios.get("/api/v1/matches/live").then(res => setMatches(res.data));
}, []);
```

### Auth

`App.tsx` has a `handleLogin()` stub:

```ts
const handleLogin = () => {
  // Replace this with your real Flask auth call:
  // const res = await axios.post("/api/v1/auth/login", { email, password });
  // setUser(res.data.user);
  // localStorage.setItem("token", res.data.access_token);
  setUser(MOCK_USER);
  setPage("home");
};
```

Pass the token in Axios headers via an interceptor:

```ts
// src/lib/axios.ts
import axios from "axios";

const api = axios.create({ baseURL: "/api/v1" });

api.interceptors.request.use(config => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
```

## Design Tokens (tailwind.config.js)

| Token | Value | Usage |
|---|---|---|
| `bg-base` | `#0b0b0f` | Page background |
| `bg-card` | `#111118` | Card backgrounds |
| `accent` | `#7c3aed` | Primary purple accent |
| `accent-light` | `#9d5ff0` | Hover states |
| `live` | `#ef4444` | Live status, alerts |
| `soon` | `#eab308` | Upcoming, ratings |
| `win` | `#22c55e` | Won, positive stats |
| `font-display` | Bebas Neue | Scores, hero text |
| `font-heading` | Rajdhani | Section titles, names |
| `font-body` | Inter | Body text, labels |

## Build

```bash
npm run build    # TypeScript check + Vite bundle
npm run preview  # Preview production build locally
```
