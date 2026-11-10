# Backend image, deployed to Azure App Service for Containers (Part 3, Task 2)
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt requirements-azure.txt ./
RUN pip install --upgrade pip && pip install -r requirements-azure.txt

COPY . .
# Strip Windows line endings in case the script was checked out on Windows
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh \
    && DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

# Run as a non-root user. SQLite (test/demo database) lives in /app, so the user must own it.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1
CMD ["./entrypoint.sh"]