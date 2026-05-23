# Phase 2: Django Main App + DRF + Admin

## Plan Overview
Bootstrap Django main app with PostgreSQL models, DRF REST API, JWT auth, Redis cache, and Admin.

**Service Boundary:**
- Django owns: ORM, admin, auth, REST endpoints consumed by frontend/clients
- FastAPI owns: async data ingestion, scheduling — writes nothing to Postgres yet (Phase 3 bridge)

**Architecture:**
```
services/django/
  ├─ manage.py
  ├─ footylens/              ← project config
  │   ├─ settings.py
  │   ├─ urls.py
  │   └─ wsgi.py
  ├─ matches/                ← Competition + Match models
  │   ├─ models.py
  │   ├─ serializers.py
  │   ├─ views.py
  │   ├─ admin.py
  │   └─ urls.py
  ├─ teams/                  ← Team + Player models
  │   ├─ models.py
  │   ├─ serializers.py
  │   ├─ views.py
  │   ├─ admin.py
  │   └─ urls.py
  ├─ standings/              ← Standing + TableEntry models
  │   ├─ models.py
  │   ├─ serializers.py
  │   ├─ views.py
  │   ├─ admin.py
  │   └─ urls.py
  └─ accounts/               ← Custom User (AbstractUser)
      ├─ models.py
      └─ admin.py
```

**DB Schema:**

`matches.Competition`
- id (int, PK — Football-Data.org id)
- name, code, area_name, area_code, emblem_url

`matches.Match`
- id (int, PK — Football-Data.org id)
- competition (FK), utc_date, status, matchday, stage
- home_team (FK → teams.Team), away_team (FK → teams.Team)
- score_home_ft, score_away_ft, score_home_ht, score_away_ht
- last_updated (auto_now)

`teams.Team`
- id (int, PK — Football-Data.org id)
- name, short_name, tla, founded, crest_url, venue, area_name, area_code

`teams.Player`
- id (int, PK — Football-Data.org id)
- team (FK), name, nationality, position, shirt_number, date_of_birth

`standings.Standing`
- competition (FK), season_start_date, season_end_date, type (TOTAL/HOME/AWAY), stage
- last_updated (auto_now), unique_together (competition, type, stage)

`standings.TableEntry`
- standing (FK), team (FK), position, played_games, won, draw, lost, points
- goals_for, goals_against, goal_difference

**Endpoint Contracts:**
- GET /api/competitions/             → list all competitions
- GET /api/competitions/{id}/        → competition detail
- GET /api/matches/                  → list matches (filters: competition, status, matchday)
- GET /api/matches/{id}/             → match detail
- GET /api/teams/                    → list teams (filter: competition)
- GET /api/teams/{id}/               → team detail with players
- GET /api/standings/                → list standings (filters: competition, type)
- GET /api/standings/{id}/           → standing with full table
- POST /api/auth/token/              → obtain JWT pair
- POST /api/auth/token/refresh/      → refresh access token

---

## Tasks

### 1. Create branch + project structure
- [x] `git checkout -b phase-2-django`
- [ ] `mkdir -p services/django`
- [ ] `django-admin startproject footylens services/django`
- [ ] Create apps: matches, teams, standings, accounts

### 2. Dependencies
- [ ] Create `services/django/requirements.txt`
- [ ] Install: django, djangorestframework, psycopg2-binary, django-environ, djangorestframework-simplejwt, redis, django-redis
- [ ] Create `.env.django.example`

### 3. Configure settings.py
- [ ] PostgreSQL connection (footylens_db)
- [ ] DRF + JWT auth config
- [ ] Redis cache backend
- [ ] INSTALLED_APPS, MIDDLEWARE

### 4. Define models
- [ ] matches: Competition, Match
- [ ] teams: Team, Player
- [ ] standings: Standing, TableEntry
- [ ] accounts: User (AbstractUser)

### 5. Run migrations
- [ ] `python manage.py makemigrations`
- [ ] `python manage.py migrate`
- [ ] `python manage.py createsuperuser`

### 6. Django Admin
- [ ] CompetitionAdmin, MatchAdmin
- [ ] TeamAdmin, PlayerAdmin (inline)
- [ ] StandingAdmin (TableEntry inline), TableEntryAdmin

### 7. DRF serializers + viewsets
- [ ] CompetitionSerializer, MatchSerializer (nested teams)
- [ ] TeamSerializer (with nested PlayerSerializer)
- [ ] StandingSerializer (with nested TableEntrySerializer)

### 8. Wire up URLs
- [ ] Project urls.py: include app urls + auth
- [ ] Each app urls.py: router registration

### 9. Verify
- [ ] `python manage.py runserver 8002`
- [ ] GET /api/matches/ → 200 (empty list)
- [ ] GET /admin/ → admin login page
- [ ] GET /api/auth/token/ → schema correct

### 10. Commit
- [ ] `feat: bootstrap Django app with models, DRF, and admin`

---

## Notes
