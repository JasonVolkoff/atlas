# Atlas

A map-based housing intelligence platform, capable of displaying housing metrics over set periods time

## Stack

- **Frontend**: Nuxt 3 + Vue 3 + TypeScript + Mapbox GL JS
- **Backend**: Django 5 + Django REST Framework + PostgreSQL/PostGIS
- **Infrastructure**: Docker Compose (local dev), AWS (production)

## Prerequisites

- A [Mapbox access token](https://account.mapbox.com/access-tokens/) (free tier works)

## Quick Start

1. **Clone and configure environment:**

```bash
cp .env.example .env
# Edit .env and add your MAPBOX_TOKEN
```

2. **Start all services:**

```bash
docker compose up --build
```

This starts PostgreSQL/PostGIS, Redis, the Django backend (port 8000), and the Nuxt frontend (port 3000).

3. **Import geographic boundaries (first time only):**

```bash
docker compose exec backend python manage.py import_geographies
```

This downloads Census TIGER/Line shapefiles (~500MB) and imports ~33,000 ZCTA and ~3,200 county boundaries. Takes 5-10 minutes.

4. **Import housing data (first time only):**

```bash
docker compose exec backend python manage.py import_zhvi
```

This downloads Zillow ZHVI data and imports ~8 million data points. Takes 5-15 minutes.

5. **Open the app:** [http://localhost:3000](http://localhost:3000)

## Project Structure

```
atlas/
  backend/          Django API (geography, housing, data_pipeline apps)
  frontend/         Nuxt 3 app (map explorer, composables, stores)
  docker-compose.yml
```

See the plan document for full architecture details.

## Development

**Backend only (without Docker):**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Requires PostgreSQL with PostGIS and GDAL installed locally.

**Frontend only (without Docker):**

```bash
cd frontend
npm install
npm run dev
```
