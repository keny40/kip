# PostgreSQL Docker Compose

## 구성

- `postgres`: PostgreSQL 16 Alpine, named volume `kip_postgres_data`, healthcheck
- `backend`: PostgreSQL healthy 이후 Alembic head 적용, 선택적 demo seed, FastAPI healthcheck
- `frontend`: Backend healthy 이후 Flutter Web/Nginx 시작

Backend 소스와 SQLite 파일을 container에 bind mount하지 않습니다. 이미지 build 시 필요한 소스만 복사하며 `.dockerignore`가 DB, dump, backup, log와 Flutter build를 제외합니다.

## 준비와 실행

```powershell
Copy-Item .env.example .env
```

`.env`에서 최소한 다음 값을 교체합니다.

- `POSTGRES_PASSWORD`: URL에서 안전하게 사용할 수 있는 개발용 password
- `DATABASE_URL=postgresql+psycopg://kip:<URL-encoded password>@postgres:5432/kip`
- `JWT_SECRET_KEY`: 충분히 긴 임의값
- `KIP_ADMIN_PASSWORD`: demo 관리자 비밀번호

실제 비밀번호를 Git, 명령 출력, 문서, 로그에 복사하지 않습니다.

```powershell
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail 200 backend postgres
```

접속 기본값:

- PostgreSQL host port: `5433` (`KIP_POSTGRES_PORT`)
- Backend: `http://localhost:8000` (`KIP_BACKEND_PORT`)
- Flutter Web: `http://localhost:5001` (`KIP_FRONTEND_PORT`)

5433/8000/5001이 사용 중이면 `.env`의 포트를 변경합니다. Browser가 호출하는 `KIP_PUBLIC_API_URL`도 Backend 공개 포트와 맞춰야 합니다.

## Migration, seed, integration

Backend entrypoint가 `alembic upgrade head`를 실행합니다. 수동 확인:

```powershell
docker compose exec backend alembic current
docker compose exec backend python /app/scripts/seed_phase2_data.py
```

PostgreSQL integration 테스트는 public schema를 삭제하므로 disposable DB에서만 실행합니다. 먼저 PostgreSQL만 실행하고 host Python 환경에서 실행하는 절차를 권장합니다.

```powershell
docker compose up -d postgres
$env:POSTGRES_TEST_DATABASE_URL='postgresql+psycopg://kip:URL_ENCODED_PASSWORD@127.0.0.1:5433/kip'
$env:KIP_ALLOW_POSTGRES_TEST_RESET='1'
pytest -m postgres_integration -q
Remove-Item Env:POSTGRES_TEST_DATABASE_URL,Env:KIP_ALLOW_POSTGRES_TEST_RESET
docker compose up -d backend frontend
```

기본 `pytest -q`는 PostgreSQL 환경이 없으면 integration 테스트를 skip하고 SQLite 테스트를 계속 실행합니다.

## 종료와 데이터 삭제

```powershell
docker compose down
```

다음 명령은 PostgreSQL 개발 volume을 완전히 삭제합니다.

```powershell
docker compose down -v
```

운영 데이터에는 `down -v`를 사용하지 않습니다.

## 백업과 복구 방향

- 논리 백업: `pg_dump -Fc`를 사용해 container 밖의 보호된 경로에 저장
- 복구: 새 빈 DB에 `pg_restore --clean --if-exists`를 사전 검증 후 실행
- backup 파일과 `.sql`, `.dump`, `.backup`은 Git에 포함하지 않음
- 운영 전 자동화, 암호화, 보존 기간, 정기 복구 훈련을 별도로 설계

## 검증 상태

2026-07-13 점검 환경에는 Docker CLI가 없어 Compose YAML 정적 검토만 수행했습니다. `docker compose config/build/up/ps/logs/down -v`, PostgreSQL migration과 smoke는 실제 성공으로 검증되지 않았습니다.
