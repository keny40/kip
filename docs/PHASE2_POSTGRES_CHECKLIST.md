# Phase 2 PostgreSQL Compatibility Checklist

검토일: 2026-07-13  
현재 결론: 코드와 Compose 기반 준비 완료, 실제 Docker/PostgreSQL 실행 검증은 환경 부재로 보류.

## 1. DB 의존성 조사

| 항목 | 결과 및 PostgreSQL 영향 |
|---|---|
| Integer PK/autoincrement | SQLAlchemy `Integer primary_key` 사용. PostgreSQL identity/sequence 생성 여부를 integration에서 확인하도록 함 |
| Boolean | 모델은 `Boolean`. `0004`의 SQLite식 `is_active = 1`을 portable Boolean 조건으로 수정 |
| Datetime | `DateTime(timezone=True)`이나 `created_at/updated_at`은 ORM client-side UTC default. PostgreSQL은 aware datetime, SQLite는 timezone 정보 보존이 제한적 |
| Decimal/Numeric | 통계 비율 `Numeric(8,3)` 등 사용. PostgreSQL에서 `Decimal`과 scale을 검증하도록 함 |
| Unique/index | 명명된 unique와 일반 index 사용. `source + external_id` constraint/index를 inspector로 확인 |
| Foreign key | entries/results의 CASCADE/RESTRICT는 portable. SQLite는 PRAGMA로 FK를 켜며 PostgreSQL은 항상 강제 |
| nullable/default | staging unknown 기본값 일부는 migration server default, timestamp는 client default |
| raw SQL | migration의 SELECT/UPDATE/trim/COALESCE는 portable. `reset_demo_db.py`의 `PRAGMA foreign_key_check`만 SQLite 전용 |
| SQLite 파일 작업 | reset, backup, 일부 dry-run은 SQLite 파일 복사 전용. PostgreSQL seed에는 사용하지 않음 |
| INSERT OR REPLACE | 발견되지 않음 |
| 테스트 | 기본 API/migration 테스트는 빠른 임시 SQLite에 의존. 별도 opt-in PostgreSQL marker 추가 |

## 2. 수정 사항

- `0004_admin_auth`: `is_active = 1` 제거
- Compose에 PostgreSQL 16, healthcheck, named volume, dependency condition 추가
- Backend entrypoint를 DB 종류와 무관한 `alembic upgrade head` 방식으로 변경
- PostgreSQL/SQLite 공용 Phase 2 seed 추가; SQLite 파일 복사 사용 안 함
- `psycopg[binary] 3.2.1`은 기존 Backend requirements에 이미 포함
- PostgreSQL integration marker와 destructive opt-in guard 추가
- SQL/dump/backup 파일 Git/Docker build 제외
- hardcoded password와 미사용 Redis가 있던 중복 `docker/docker-compose.yml` 제거; 루트 Compose를 단일 기준으로 사용

## 3. Integration 검증 범위

`tests/integration/test_postgres_phase2.py`가 disposable PostgreSQL에서 다음을 확인합니다.

- public schema 초기화 후 `0001 → 0006`
- 주요 테이블, unique constraint와 index
- `0006 → 0005 → 0006`
- track/player/race/entry/result, 관리자, 외부 선수, 통계 seed
- external ID `00123456`, period `01`, standard year 문자열 보존
- Numeric `100.000`, timezone-aware collected timestamp
- ORM timestamp 기본값, Boolean, PK 생성
- FK CASCADE/RESTRICT
- health/login/public/admin API, 401/403/405
- PostgreSQL CSV dry-run과 행 수 불변

필수 환경변수:

```text
POSTGRES_TEST_DATABASE_URL=postgresql+psycopg://...
KIP_ALLOW_POSTGRES_TEST_RESET=1
```

환경변수가 없으면 기본 `pytest`에서 skip됩니다.

## 4. 실제 검증 결과

| 항목 | 상태 |
|---|---|
| Compose YAML 정적 파싱 | 통과 |
| SQLite 빈 DB migration `0001 → 0006` | 통과 |
| 공용 Phase 2 seed의 SQLite 임시 DB 실행 | 통과: tracks 3, players 10, races 3, entries 15, results 8, 외부/통계/관리자 각 1 |
| `python -m unittest` | 96개 통과 |
| 기본 `pytest -q` | 96개 통과, PostgreSQL integration 1개 의도적 skip |
| Phase 1 API/CSV smoke | 통과 |
| psycopg import | 현재 환경 3.3.3 성공; pinned Docker requirement 3.2.1 |
| Docker CLI/Desktop | 사용 불가 |
| `docker compose config/build/up/ps/logs/down -v` | 미검증 |
| PostgreSQL migration/downgrade/upgrade | 미검증 |
| PostgreSQL seed/API smoke/타입 | 미검증 |

미검증 항목을 성공으로 간주하지 않습니다.

## 5. 보안·운영 체크

- [x] `.env` Git ignore
- [x] `.env.example`은 placeholder만 포함
- [x] DB/dump/backup/log Git ignore
- [x] Backend entrypoint가 DATABASE_URL이나 password를 출력하지 않음
- [x] seed가 관리자 비밀번호를 출력하지 않음
- [x] data.go 서비스 키를 Compose에 전달하지 않음
- [x] JWT example은 운영 사용 금지 문서화
- [ ] 실제 Docker logs에서 비밀값 미노출 확인
- [ ] 운영 secret manager 연동
- [ ] pg_dump/pg_restore 실제 복구 훈련

## 6. 전환 판정

SQLite 로컬 개발은 그대로 유지됩니다. PostgreSQL용 migration/seed/integration/Compose 실행 기반은 준비됐지만 실제 PostgreSQL이 없는 환경에서는 전환 준비 완료로 확정할 수 없습니다. Docker가 가능한 환경에서 3절 integration과 Compose health를 모두 통과해야 최종 준비 완료입니다.
