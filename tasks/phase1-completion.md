# Phase 1 Completion: Scheduler + Caching

## Plan Overview
Add APScheduler for background data fetching and in-memory TTL-based cache to reduce API calls against the 10 calls/min free tier limit.

**Architecture:**
```
services/fastapi/
  ├─ core/
  │   ├─ config.py (existing)
  │   └─ cache.py (NEW) - TTL cache with dict + timestamp
  ├─ services/
  │   ├─ football_data_client.py (existing)
  │   └─ scheduler.py (NEW) - AsyncIOScheduler + background jobs
  ├─ routers/
  │   └─ cache_status.py (NEW) - GET /api/cache/status
  └─ main.py (UPDATED) - wire scheduler startup/shutdown
```

**Cache Strategy:**
- Key format: `{data_type}:{params_hash}` (e.g., "matches:PL", "standings:PL")
- TTL: 1hr (60m) for matches/standings/teams, 24hr (1440m) for historical
- Stale-on-expire behavior: return stale if fresh fetch fails

**Scheduler Jobs:**
1. `fetch_pl_matches` — Every 1hr, fetch PL matches (status=SCHEDULED,LIVE,FINISHED)
2. `fetch_standings` — Every 1hr, fetch PL standings
3. `fetch_historical` — Daily at 00:00, fetch historical matchday data (all comps)

**Verification:**
- Start server → scheduler registered
- Hit `/api/cache/status` → see cache state
- Hit `/api/matches` → should serve from cache (no API call)
- Hit `/api/standings` → should serve from cache
- Wait for cache expiry or manually expire, verify fresh fetch

---

## Tasks

### 1. Create cache.py
- [ ] Create `core/cache.py`
- [ ] CacheEntry dataclass (data, timestamp, ttl_minutes)
- [ ] SimpleCache class with:
  - `get(key)` — return data if not expired, None if stale
  - `set(key, data, ttl_minutes)`
  - `clear(key)`
  - `status()` — return dict of all cache entries with expiry info

### 2. Create scheduler.py
- [ ] Create `services/scheduler.py`
- [ ] SchedulerService class with AsyncIOScheduler
- [ ] Methods:
  - `start()` — start scheduler
  - `stop()` — stop scheduler
  - `add_job(job_id, job_func, trigger, ...)` — register job
- [ ] Background job functions:
  - `fetch_pl_matches_job()` — fetch PL matches, cache
  - `fetch_standings_job()` — fetch PL standings, cache
  - `fetch_historical_job()` — fetch all competitions historical data, cache

### 3. Create cache_status router
- [ ] Create `routers/cache_status.py`
- [ ] `GET /api/cache/status` — return cache state
- [ ] Response: count, entries list with keys, data size, expiry times

### 4. Update main.py
- [ ] Import SchedulerService, CacheService
- [ ] Create scheduler/cache instances
- [ ] Add @app.on_event("startup") to start scheduler
- [ ] Add @app.on_event("shutdown") to stop scheduler

### 5. Update routers to use cache
- [ ] matches.py: check cache before API call, update on fresh fetch
- [ ] standings.py: check cache before API call, update on fresh fetch
- [ ] teams.py: check cache before API call, update on fresh fetch

### 6. Verification
- [ ] Run server
- [ ] Confirm scheduler jobs registered (logs)
- [ ] Call `/api/cache/status` — should show empty initially
- [ ] Call `/api/matches?competition=PL` — triggers job, caches response
- [ ] Call `/api/cache/status` — should show matches cache entry
- [ ] Call `/api/matches` again — should serve from cache (no API logs)

### 7. Commit
- [ ] `git add .`
- [ ] `git commit -m "feat: add scheduler and in-memory cache to FastAPI service"`
- [ ] `git push`

---

## Progress
- [ ] All tasks completed
