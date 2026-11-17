# PestPatrol – Pest Monitoring App

A crowdsourced web application for identifying, reporting and monitoring **rodent and avian pest activity**. Residents submit sightings with a location, time, species and an optional photo. Pest control workers review them, and the results are shown on an interactive, filterable map. When activity in a district crosses a threshold, users are alerted.

> MTU Software Development Tools group project.
> <!-- TODO: add team members, module code and lecturer -->

---

## Table of contents

- [Project objectives](#project-objectives)
- [Tech stack](#tech-stack)
- [Repository structure](#repository-structure)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Running the tests](#running-the-tests)
- [Code quality](#code-quality)
- [CI/CD pipeline](#cicd-pipeline)
- [API summary](#api-summary)
- [Sprint 1 user stories](#sprint-1-user-stories)
- [Version control workflow](#version-control-workflow)
- [Further documentation](#further-documentation)

---

## Project objectives

- Allow users to submit pest sightings and capture the relevant details (location, time, species, count, photo).
- Validate and securely process submitted data (photo checks, GPS metadata removed).
- Store sighting and user data.
- Display pest activity geographically on an interactive map.
- Filter pest activity by species, family, genus, date range and area.
- Alert users when pest activity reaches significant levels.
- Develop the application using an Agile approach, managed in Azure DevOps.

The main focus is on rodent pests because of their impact on infrastructure, food storage and public health.

---

## Tech stack

| Part | Technology |
|---|---|
| Frontend | Angular 20 (TypeScript), MapLibre GL JS with OpenFreeMap tiles |
| Backend API | Django 5.2 + Django REST Framework, Python 3.12 |
| Database | SQLite (local and CI), Azure SQL Database (Azure) |
| File storage | Local files (development), Azure Blob Storage (Azure) |
| Authentication | Username/password with API tokens; Microsoft Entra ID token checks when configured |
| Notifications | Azure Notification Hubs |
| Containers | Docker, Azure Container Registry, Azure App Service for Containers |
| Infrastructure as code | Bicep, compiled to ARM templates |
| CI/CD | Azure Pipelines, SonarCloud |
| Project management | Azure DevOps Boards |

---

## Repository structure

```text
Pest_Monitoring_App-main/
├── README.md                  # this file
├── sonar-project.properties   # SonarCloud analysis settings
└── pest-monitoring/
    ├── azure-pipelines.yml    # main CI/CD pipeline
    ├── azure-mirror.yml       # mirrors GitHub to Azure Repos
    ├── backend/               # Django REST API
    │   ├── config/            # settings, URLs, health check
    │   ├── domain/            # pure Python business rules (validation, alerts, images, geo)
    │   ├── accounts/          # users, roles, sign-in
    │   ├── reference/         # districts, pest species, tags (+ seed data)
    │   ├── sightings/         # sightings, photos, review workflow, map
    │   ├── alerts/            # pest alerts and notifications
    │   ├── tests/             # domain and API tests (pytest)
    │   └── Dockerfile
    ├── frontend/              # Angular app
    │   └── src/app/
    │       ├── core/          # API service, auth, guards, map adapter
    │       └── features/      # report, map, my-reports, login
    ├── infra/                 # Bicep templates
    ├── pipelines/templates/   # reusable pipeline steps and stages
    └── docs/                  # architecture, branching, CI/CD, code quality, backlog
```

---

## Getting started

### Prerequisites

- [Python 3.12](https://www.python.org/downloads/)
- [Node.js 22](https://nodejs.org/) and npm
- Git
- Google Chrome (for the frontend tests)
- Docker (optional, only to build the container image)

### 1. Backend – Django API on http://localhost:8000

```bash
cd pest-monitoring/backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements-dev.txt

python manage.py migrate
python manage.py seed_reference_data   # districts, pest species and tags
python manage.py createsuperuser       # admin account for /admin/
python manage.py runserver
```

Check it is running: http://localhost:8000/api/species/ should return a list of species.

### 2. Frontend – Angular app on http://localhost:4200

Open a second terminal:

```bash
cd pest-monitoring/frontend
npm install
npm start          # proxies /api and /media to the Django server
```

Then open http://localhost:4200.

| Page | Route | Notes |
|---|---|---|
| Report a sighting | `/report` | 3-step form, works without signing in |
| Pest activity map | `/map` | Public map with a filter bar |
| My reports | `/my-reports` | Requires sign-in |
| Sign in | `/login` | |

> The map uses free OpenFreeMap tiles, so no API key is needed. To hide the map and use plain latitude/longitude fields instead, set `mapStyleUrl` to `''` in `frontend/src/environments/environment.ts`.

### 3. Run the alert check (optional)

```bash
cd pest-monitoring/backend
python manage.py check_pest_levels
```

This looks for districts where sightings have passed `ALERT_THRESHOLD` and creates alerts and notifications. In Azure it is designed to run on a schedule.

---

## Configuration

The backend reads its settings from environment variables. Copy the example file and edit it:

```bash
cd pest-monitoring/backend
cp .env.example .env      # Windows: copy .env.example .env
```

**Never commit `.env`.** The defaults work for local development.

| Variable | Purpose | Local default |
|---|---|---|
| `DJANGO_DEBUG` | Debug mode | `true` |
| `DJANGO_SECRET_KEY` | Django secret key | `change-me` |
| `DJANGO_ALLOWED_HOSTS` | Allowed host names | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Frontend origin | `http://localhost:4200` |
| `DB_ENGINE` | `sqlite` or `mssql` (Azure SQL) | `sqlite` |
| `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Azure SQL connection | – |
| `ENTRA_TENANT_ID`, `ENTRA_API_AUDIENCE` | Microsoft Entra ID token checks (leave empty locally) | – |
| `AZURE_STORAGE_ACCOUNT`, `AZURE_STORAGE_CONTAINER` | Photo storage in Azure Blob (empty = local files) | `sightings` |
| `ALERT_THRESHOLD` | Sightings needed to raise an alert | `10` |
| `NOTIFICATION_HUB_CONNECTION_STRING`, `NOTIFICATION_HUB_NAME` | Azure Notification Hubs | – |

---

## Running the tests

```bash
# Backend: unit and API tests with coverage (fails under 80%)
cd pest-monitoring/backend
pytest --cov

# Frontend: unit tests in Chrome (Karma + Jasmine)
cd pest-monitoring/frontend
npm test

# Frontend: headless, as in the pipeline
npm run test:ci
```

---

## Code quality

These checks run on every build and can also be run locally from `pest-monitoring/backend`:

| Tool | What it checks | Command |
|---|---|---|
| ruff | Errors, style, security and complexity | `ruff check .` |
| codespell | Spelling mistakes | `codespell .` |
| import-linter | Architecture layers are respected | `lint-imports` |
| radon / xenon | Complexity and maintainability | `radon cc . -a -s` |
| pylint | Duplicate code | `pylint --disable=all --enable=duplicate-code domain` |
| pip-audit | Known vulnerabilities in dependencies | `pip-audit -r requirements.txt` |

Frontend: `npm run lint` (ESLint) and `npm audit`.

SonarCloud analyses the whole repository and the pipeline fails if the quality gate fails. See [CODE-QUALITY.md](pest-monitoring/docs/CODE-QUALITY.md).

---

## CI/CD pipeline

One Azure Pipelines file, `pest-monitoring/azure-pipelines.yml`, runs on every push and pull request to `main` and `develop`.

```text
Build ─┬─ Backend ──────┬─ Container (docker build, smoke test, push to ACR)
       ├─ Frontend ─────┤
       ├─ Infrastructure┘
       └─ SonarCloud (after Backend + Frontend)
Deploy_test   (develop and main)
Deploy_prod   (main only, after approval)
```

- **Backend job:** migrations check, ruff, codespell, import-linter, radon/xenon, pylint, pip-audit, pytest with coverage.
- **Frontend job:** ESLint, Karma tests, npm audit, production build, zip package.
- **Infrastructure job:** lints the Bicep files and compiles them to ARM templates.
- **Container job:** builds the Docker image, runs it and smoke-tests `/healthz` and `/api/species/` before pushing.
- **Deploy stages:** deploy to a test environment, then to production after manual approval.

Reusable steps live in `pipelines/templates/`. See [CI-CD.md](pest-monitoring/docs/CI-CD.md) for details.

---

## API summary

All endpoints are under `/api/`.

| Method | URL | Who |
|---|---|---|
| GET | `/api/species/`, `/api/tags/`, `/api/districts/` | Anyone |
| POST | `/api/login/`, `/api/logout/` | Anyone / signed-in user |
| GET, PATCH | `/api/me/` | Signed-in user |
| POST | `/api/sightings/` | Anyone (anonymous reports need `contact_email`) |
| GET | `/api/sightings/mine/` | Signed-in user |
| GET | `/api/sightings/<id>/` | Reporter or worker |
| POST | `/api/sightings/<id>/photo/` | Reporter, worker, or anonymous reporter with `X-Upload-Token` |
| PATCH | `/api/sightings/<id>/review/` | Worker |
| GET | `/api/sightings/all/?status=&priority=` | Worker |
| GET | `/api/map/?species_id=&family=&genus=&days=&bbox=` | Anyone (reviewed sightings only, positions rounded to about 100 m) |
| GET | `/api/notifications/` | Signed-in user |
| POST | `/api/notifications/<id>/read/` | Signed-in user |
| GET | `/healthz` | Health check |

The Django admin site is at `/admin/`.

---

## Sprint 1 user stories

| User story | Backend | Frontend |
|---|---|---|
| US-01 Sign in | `accounts/authentication.py`, `GET /api/me/` | Login page (MSAL Angular planned for Sprint 2) |
| US-02 Submit pest sighting | `POST /api/sightings/`, rules in `domain/validation.py` | 3-step form in `features/report/` |
| US-03 Attach a photo | `POST /api/sightings/<id>/photo/`, `domain/images.py` (JPG/PNG ≤ 10 MB, GPS removed) | Photo picker in step 1 |
| US-04 View pest map | `GET /api/map/` (GeoJSON) | `features/map/` with MapLibre |
| US-05 Filter pest map | Query filters on `/api/map/` | Filter bar on the map page |
| US-06 Receive pest alert | `check_pest_levels` command, `domain/alerts.py`, `GET /api/notifications/` | Alerts screen planned for Sprint 2 |
| Worker review | `PATCH /api/sightings/<id>/review/`, `GET /api/sightings/all/` | Worker screens planned for Sprint 2 |
| Resident dashboard | `GET /api/sightings/mine/` | `features/my-reports/` |

Full backlog: [SPRINT-1-BACKLOG.md](pest-monitoring/docs/SPRINT-1-BACKLOG.md).

---

## Version control workflow

Git and GitHub manage the source code, and a pipeline mirrors the repository to Azure Repos.

- **`main`** holds the released code; **`develop`** is the integration branch.
- **Feature and documentation branches** are used for all changes.
- **Commits** have short, meaningful messages.
- **Pull requests** are reviewed before merging, where team permissions allow.
- **Fetch and pull** remote changes before pushing.
- **Azure Pipelines** runs code-quality checks, tests, coverage and build verification on every pull request.

See [BRANCHING.md](pest-monitoring/docs/BRANCHING.md) and [IDE-SETUP.md](pest-monitoring/docs/IDE-SETUP.md).

---

## Further documentation

- [Architecture and design patterns](pest-monitoring/docs/ARCHITECTURE.md)
- [Branching strategy and branch policies](pest-monitoring/docs/BRANCHING.md)
- [IDE set-up and daily Git routine](pest-monitoring/docs/IDE-SETUP.md)
- [Code quality and testing](pest-monitoring/docs/CODE-QUALITY.md)
- [CI, CD and release management](pest-monitoring/docs/CI-CD.md)
- [Sprint 1 backlog](pest-monitoring/docs/SPRINT-1-BACKLOG.md)
- Design documents (Tasks 1–9): Azure DevOps wiki

---

## Team

<!-- TODO: fill in -->

## Team

We didn't assign fixed roles. Work was shared out from the Azure DevOps backlog as the project went on.

| Name | Role |
|---|---|
| Padraic Moriarty | Lecture |
| Mari Tarasova | Student |
| Rani Wheeza | Student |
| Philip Dawson-Gariepy | Student |
| Zakary Snyder | Student |