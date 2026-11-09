"""Health check for Azure App Service and the pipeline smoke tests (Part 3, Task 2).

This middleware sits first in MIDDLEWARE, so /healthz is answered before the
host check, the HTTPS redirect and the rate limit. App Service probes the app
from an internal address over plain HTTP, and those requests would otherwise be
rejected.
"""
from __future__ import annotations

import os

from django.db import DatabaseError, connection
from django.http import JsonResponse

HEALTH_PATH = "/healthz"


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path != HEALTH_PATH:
            return self.get_response(request)

        # The release pipeline checks "version" to confirm the new build is the one running
        body = {"status": "ok", "database": "up", "version": os.environ.get("APP_VERSION", "dev")}
        try:
            connection.ensure_connection()
        except DatabaseError:
            body.update(status="unavailable", database="down")
            return JsonResponse(body, status=503)
        return JsonResponse(body)
