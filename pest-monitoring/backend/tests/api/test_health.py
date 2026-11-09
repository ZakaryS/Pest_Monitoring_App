"""Health check used by App Service and the release pipeline smoke tests."""
import pytest
from django.db import OperationalError


@pytest.mark.django_db
def test_health_check_reports_ok(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "up"


@pytest.mark.django_db
def test_health_check_reports_build_version(client, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "1234")

    assert client.get("/healthz").json()["version"] == "1234"


@pytest.mark.django_db
def test_health_check_ignores_allowed_hosts(client):
    # App Service probes from an internal IP that is not in ALLOWED_HOSTS
    response = client.get("/healthz", HTTP_HOST="10.0.0.5")

    assert response.status_code == 200


@pytest.mark.django_db
def test_health_check_returns_503_when_database_is_down(client, monkeypatch):
    def fail():
        raise OperationalError("database is unavailable")

    monkeypatch.setattr("config.health.connection.ensure_connection", fail)
    response = client.get("/healthz")

    assert response.status_code == 503
    assert response.json()["database"] == "down"


@pytest.mark.django_db
def test_other_paths_are_not_affected(client):
    assert client.get("/api/species/").status_code == 200


def test_cors_allows_upload_token_header(settings):
    assert "x-upload-token" in settings.CORS_ALLOW_HEADERS
