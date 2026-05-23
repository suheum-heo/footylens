# FootyLens — Claude Instructions

## Project Context
- **Goal**: Football match analysis platform — collect, process, and visualize soccer data
- **Stack**: FastAPI (data ingestion/analytics) + Django + DRF (main app/admin) + PostgreSQL + Redis
- **Data Sources**: Football-Data.org, StatsBomb open data, FotMob (optional)
- **Frontend**: Next.js dashboard (Phase 4)
- **Infra**: Docker Compose locally, Railway/Render for deployment
- **Venv**: `source .venv/bin/activate`
- **Timeline**:
  - Phase 1 (2w): FastAPI data collection service
  - Phase 2 (3w): Django main app + DRF + Admin
  - Phase 3 (2w): Analytics layer (xG, pass networks, heatmaps)
  - Phase 4 (1w): Next.js dashboard + Docker + deploy

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- Write specs upfront — endpoint contracts, DB schema, data flow diagrams in comments
- If something breaks or drifts from architecture, STOP and re-plan before proceeding
- Use plan mode for verification steps, not just building

### 2. Architecture Discipline
- FastAPI = async data ingestion, scheduling, analytics endpoints only
- Django = ORM, admin, auth, REST via DRF — no business logic duplication
- Never blur the service boundary without a clear reason and explicit plan update
- If a feature could live in either service, default to Django unless async/performance is the reason

### 3. Self-Improvement Loop
- After ANY correction: update `tasks/lessons.md` with the pattern
- Write rules that prevent the same mistake from recurring
- Review lessons at session start for relevant context

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Validate API responses against raw source data when relevant
- Ask: "Would a backend engineer at StatsBomb or Opta approve this?"
- Run the server, hit the endpoint, confirm the response — then mark done

### 5. Demand Elegance (Balanced)
- For non-trivial endpoints or data transforms: pause and ask "is there a more elegant way?"
- If a solution feels hacky: implement the clean version from the start
- Skip for simple obvious fixes — don't over-engineer
- Pydantic models and Django serializers should be tight, not permissive

### 6. Autonomous Bug Fixing
- When given a broken endpoint or data issue: diagnose and fix. Don't ask for hand-holding
- Point at schema mismatches, type errors, null handling — then resolve
- For Django ORM issues: check migrations before assuming logic bugs
- For FastAPI async issues: check event loop, dependency injection chain first

---

## Task Management

1. **Plan First** — Write plan to `tasks/todo.md` with checkable items
2. **Verify Plan** — Check in before starting implementation
3. **Track Progress** — Mark items complete as you go
4. **Explain Changes** — High-level summary of what changed and why at each step
5. **Document Results** — Add review/notes section to `tasks/todo.md` after each phase
6. **Capture Lessons** — Update `tasks/lessons.md` after any correction

---

## Core Principles

- **Service Boundary First** — Always ask which service owns this feature before writing code
- **No Laziness** — Find root causes in data quality and API issues. No band-aid fixes
- **Minimal Impact** — Changes should only touch what's necessary. Avoid cross-service side effects
- **Data Integrity** — Validate incoming data at the FastAPI boundary with Pydantic. Trust nothing from external APIs
- **Migrations are Sacred** — Never edit a migration file after it's been applied. Make a new one

---

## Git Workflow
- Commit after each meaningful milestone (schema created, endpoint live, EDA complete, etc.)
- Commit message format: `feat: add /matches endpoint` / `fix: null handling in kickoff_time` / `chore: add redis caching to standings`
- Never commit broken code — run the server and verify first
- Always `git push` after committing
- Branch per phase: `phase-1-fastapi`, `phase-2-django`, etc. Merge to `main` at phase completion

---

## Key Reminders
- Football-Data.org free tier: 10 calls/min — always add rate limiting in the scheduler
- StatsBomb open data is file-based (JSON) — batch load, don't poll
- Redis cache TTL: 1hr for standings/fixtures, 24hr for historical match stats
- Django Admin customization is a deliverable — not an afterthought