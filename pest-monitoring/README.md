# Pest Monitoring (PestPatrol)

A crowdsourced app for reporting and monitoring rodent and bird pest activity. MTU Software Development Tools group project.

| Part | Technology | Folder |
|---|---|---|
| Frontend | Angular 20 (TypeScript) | `frontend/` |
| Backend API | Django 5.2 + Django REST Framework (Python 3.12) | `backend/` |
| Database | SQLite locally and in CI, Azure SQL Database in Azure | `backend/config/settings.py` |
| CI pipeline | Azure Pipelines | `azure-pipelines.yml` |
| Design docs | Azure DevOps wiki (Tasks 1–9) | wiki |
| CI/CD pipeline | Azure Pipelines + SonarCloud | `azure-pipelines.yml`, `pipelines/templates/` |

More detail:

* [Architecture and design patterns](docs/ARCHITECTURE.md)
* [Branching strategy and branch policies](docs/BRANCHING.md) (Part 2, Task 1)
* [IDE set-up and daily Git routine](docs/IDE-SETUP.md) (Part 2, Task 1)
* [Code quality and testing](docs/CODE-QUALITY.md) (Part 2, Tasks 3 and 4)
* [Sprint 1 backlog and work-item links](docs/SPRINT-1-BACKLOG.md) (Part 2, Task 2)

---

## Quick start

### 1. Backend (Django API on http://localhost:8000)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

python manage.py makemigrations reference accounts sightings alerts   # first time only, then commit the files
python manage.py migrate
python manage.py seed_reference_data      # districts, pest species, tags
python manage.py createsuperuser          # for the admin site at /admin/
python manage.py runserver
```

> **First time only:** the `migrations/` folders are empty on purpose. The first person to set up the project runs
> `makemigrations` and commits the generated files. The pipeline step *Check migrations are committed* fails until
> this is done.

### 2. Frontend (Angular on http://localhost:4200)

```bash
cd frontend
npm install                 # creates package-lock.json - commit it
npm start                   # proxies /api to the Django server
```

The map pages use Azure Maps only when `azureMapsKey` is set in `frontend/src/environments/environment.ts`. Without a key, the forms use latitude/longitude fields and the map page shows the list view. **Never commit a real key.**

### 3. Run the tests

```bash
cd backend && pytest --cov                          # backend unit + API tests with coverage
cd frontend && npm test                             # frontend unit tests (Karma, opens Chrome)
cd frontend && npm run test:ci                      # same, headless, as in the pipeline
```

---

## What is in Sprint 1

| User story | Backend | Frontend |
|---|---|---|
| US-01 Sign in (Entra ID) | Token check in `accounts/authentication.py`, `GET /api/me/` | Sprint 2: MSAL Angular |
| US-02 Submit pest sighting | `POST /api/sightings/`, rules in `domain/validation.py` | 3-step form `features/report/` |
| US-03 Attach a photo | `POST /api/sightings/<id>/photo/`, `domain/images.py` (JPG/PNG ≤ 10 MB, GPS removed) | Photo picker in step 1 |
| US-04 View pest map | `GET /api/map/` (GeoJSON) | `features/map/` with Azure Maps |
| US-05 Filter pest map | `?species_id=&family=&genus=&days=&bbox=` | Filter bar on the map page |
| US-06 Receive pest alert | `python manage.py check_pest_levels`, `domain/alerts.py`, `GET /api/notifications/` | Sprint 2: Alerts screen |
| Worker review | `PATCH /api/sightings/<id>/review/`, `GET /api/sightings/all/` | Sprint 2: worker screens |
| Resident dashboard | `GET /api/sightings/mine/` | `features/my-reports/` |

## API summary

| Method | URL | Who |
|---|---|---|
| GET | `/api/species/`, `/api/tags/`, `/api/districts/` | Anyone |
| POST | `/api/sightings/` | Anyone (anonymous reports need `contact_email`) |
| GET | `/api/sightings/mine/` | Signed-in user |
| GET | `/api/sightings/<id>/` | Reporter or worker |
| POST | `/api/sightings/<id>/photo/` | Reporter, worker, or anonymous reporter with `X-Upload-Token` |
| PATCH | `/api/sightings/<id>/review/` | Worker |
| GET | `/api/sightings/all/?status=&priority=` | Worker |
| GET | `/api/map/` | Anyone (public map shows reviewed sightings, positions rounded to about 100 m) |
| GET | `/api/notifications/` · POST `/api/notifications/<id>/read/` | Signed-in user |
| GET/PATCH | `/api/me/` | Signed-in user |
