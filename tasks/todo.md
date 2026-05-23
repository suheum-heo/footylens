# Phase 4: Next.js Dashboard + Docker Compose

## Plan Overview
Build a minimal, data-first Next.js 14 dashboard backed by the FastAPI analytics service.
All data fetching via server components (no client-side fetching / SWR / React Query).

**Architecture:**
```
Browser → Next.js (3000) → FastAPI (8000) → Football-Data.org
                         ↘ [cached in-memory 1h/24h]
```

**Pages:**
- `/`          — PL standings table + last-5 form badges per team
- `/matches`   — Matchday results/fixtures with scores
- `/analytics` — xG horizontal bar chart + top scorers table

**Docker services:**
| Service  | Image              | Port |
|----------|--------------------|------|
| postgres | postgres:16-alpine | 5432 |
| redis    | redis:7-alpine     | 6379 |
| fastapi  | ./services/fastapi | 8000 |
| django   | ./services/django  | 8001 |
| nextjs   | ./services/nextjs  | 3000 |

---

## Tasks

### 1. Scaffold Next.js app
- [x] `npx create-next-app@latest` in services/nextjs/
- [x] Clean boilerplate (remove default page content, globals.css reset)

### 2. Types + API layer
- [x] `types/api.ts` — TypeScript interfaces matching FastAPI schemas
- [x] `lib/api.ts` — Typed fetch functions with `next: { revalidate: 3600 }`

### 3. Layout
- [x] Root layout with sidebar nav (Standings / Matches / Analytics)
- [x] Responsive: sidebar collapses to top nav on mobile

### 4. Pages
- [x] `/` — Standings table with FormBadge component
- [x] `/matches` — Matchday fixtures/results
- [x] `/analytics` — xG chart + top scorers

### 5. Docker Compose
- [x] `docker-compose.yml` at repo root
- [x] Dockerfiles for fastapi and django
- [x] nextjs Dockerfile (multi-stage)
- [x] Health checks on all services

### 6. Verify
- [ ] `docker compose up --build` → all services healthy
- [ ] GET localhost:3000 → standings table renders
- [ ] GET localhost:3000/analytics → xG chart + scorers

### 7. Commit
- [ ] `feat: add Next.js dashboard and Docker Compose`
