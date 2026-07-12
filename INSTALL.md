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

6. Create an admin account for write access.

```bash
python ../scripts/create_admin.py --email admin@example.com
```

7. Create a new migration from the current SQLAlchemy models.

```bash
alembic revision --autogenerate -m "description"
```

8. Load sample data and reset the local demo database when needed.

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
- `JWT_SECRET_KEY=dev-only-local-secret-key-for-kip-demo-2026`
- `JWT_ALGORITHM=HS256`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `CSV_IMPORT_MAX_BYTES=5242880`

## Notes

- The project is currently a local MVP demo.
- The demo database is SQLite-based and rebuilt by `scripts/reset_demo_db.py`.
- Do not use the demo reset flow against a production PostgreSQL database.
- Read APIs are public, but create/update/delete APIs require an admin JWT.
- Admin CSV uploads use `POST /api/v1/admin/imports/{import_type}` with `multipart/form-data`.
- Use `python scripts/create_admin.py --email admin@example.com` after a reset to create the first admin.
- Example login request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"your-password\"}"
```

Admin CSV upload example:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/admin/imports/players?dry_run=true" \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@samples/players.csv"
```

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
