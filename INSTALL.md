# Install

## Backend

1. Install Python 3.12 and activate your virtual environment.
2. Change into `backend/`.
3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Run the API server.

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

5. Apply database migrations.

```bash
alembic upgrade head
```

6. Create a new migration from the current SQLAlchemy models.

```bash
alembic revision --autogenerate -m "description"
```

7. Load sample data and reset the local demo database when needed.

```bash
python ../scripts/seed_sample_data.py
python ../scripts/reset_demo_db.py
```

## Frontend

1. Install the Flutter SDK.
2. Change into `frontend/`.
3. Fetch packages.

```bash
flutter pub get
```

4. Run the app in Chrome.

```bash
flutter run -d chrome \
  --web-port 5001 \
  --dart-define=KIP_API_BASE_URL=http://127.0.0.1:8000
```

## Environment

- `DATABASE_URL=sqlite:///./backend/kip.db`
- `CORS_ORIGINS=http://localhost:5001,http://127.0.0.1:5001,http://localhost:5000,http://127.0.0.1:5000`

## Notes

- The project is currently a local MVP demo.
- The demo database is SQLite-based and rebuilt by `scripts/reset_demo_db.py`.
- Do not use the demo reset flow against a production PostgreSQL database.

## Docker Demo

Start the full local stack from the project root:

```bash
docker compose up --build
```

This exposes:

- Flutter Web: http://localhost:5001
- FastAPI: http://localhost:8000
- API docs: http://localhost:8000/docs

The Docker demo uses SQLite, keeps the demo database on a mounted host path, and reuses the existing sample-data reset flow when the database is missing.
