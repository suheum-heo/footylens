# Phase 1: FastAPI Service Bootstrap

## Plan Overview
Bootstrap FastAPI data collection service with Football-Data.org client and rate-limited endpoints.

**Key Constraints:**
- Football-Data.org free tier: 10 calls/min → rate limiting mandatory
- Pydantic validation at boundary (trust nothing from external APIs)
- Service boundary: FastAPI owns data ingestion + analytics async endpoints only
- No Django ORM at this stage

**Architecture:**
```
services/fastapi/
  ├─ main.py (FastAPI app initialization)
  ├─ routers/
  │   ├─ matches.py (GET /api/matches?competition=PL&matchday=1)
  │   ├─ standings.py (GET /api/standings?competition=PL)
  │   └─ teams.py (GET /api/teams?competition=PL)
  ├─ models/
  │   └─ football_data.py (Football-Data.org response DTOs)
  ├─ schemas/
  │   └─ responses.py (Pydantic response schemas)
  ├─ services/
  │   └─ football_data_client.py (HTTP client + rate limiting)
  └─ core/
      └─ config.py (settings, env vars)
```

---

## Tasks

### 1. Create Project Structure
- [ ] Create `services/fastapi/` directory tree
- [ ] Create `__init__.py` files
- [ ] Create `.gitkeep` in empty dirs

### 2. Setup Dependencies
- [ ] Create `services/fastapi/requirements.txt` with: fastapi, uvicorn, httpx, pydantic, apscheduler, python-dotenv
- [ ] Create `.env.example` at repo root (with FOOTBALL_DATA_API_KEY placeholder)

### 3. Implement Core Configuration
- [ ] Create `core/config.py` with Settings class (API key, rate limits, base URL)
- [ ] Add environment variable loading via python-dotenv

### 4. Implement Football-Data.org API Client
- [ ] Create `services/football_data_client.py` with:
  - RateLimitedClient class (httpx-based, 10 req/min)
  - Methods: get_matches(), get_standings(), get_teams()
  - Error handling + retry logic
  - Type hints throughout

### 5. Create Pydantic Models & Schemas
- [ ] Create `models/football_data.py` (DTOs from Football-Data.org responses)
- [ ] Create `schemas/responses.py` (API response contracts)
- [ ] Validate incoming data (handle null/missing fields)

### 6. Create FastAPI Routers
- [ ] Create `routers/matches.py` (GET /api/matches)
- [ ] Create `routers/standings.py` (GET /api/standings)
- [ ] Create `routers/teams.py` (GET /api/teams)
- [ ] Include dependency injection for client + config
- [ ] Add query parameter validation

### 7. Create main.py
- [ ] Initialize FastAPI app
- [ ] Register all routers
- [ ] Add health check endpoint (GET /health)

### 8. Verification
- [ ] Run: `uvicorn main:app --reload`
- [ ] Test each endpoint manually (curl or browser)
- [ ] Verify rate limiting behavior
- [ ] Check error responses

### 9. Commit
- [ ] `git add .`
- [ ] `git commit -m "feat: bootstrap FastAPI service with football-data client"`
- [ ] `git push`

---

## Progress
- [ ] All tasks completed
