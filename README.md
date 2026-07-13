# Keirin Intelligence Platform (KIP)

KIP는 경륜 데이터를 로컬에서 관리·분석하기 위한 **Phase 1 로컬 MVP**입니다. FastAPI, SQLite, Alembic과 Flutter Web으로 구성되어 있으며 상용 배포가 완료된 제품은 아닙니다.

현재 KCYCLE 선수 마스터와 data.go 선수 성적 통계는 별도 staging 테이블에 저장됩니다. `external_players`와 운영 `players`의 자동 연결, fuzzy matching, 임의 선수번호 생성은 제공하지 않으며 관리자가 읽기 전용 화면에서 품질과 후보를 검토합니다. AI·예측 고도화와 상용 배포는 Phase 1 범위 밖입니다.

## 현재 구성

- FastAPI REST API와 SQLite 로컬 DB
- Alembic head: `0006_external_player_statistics`
- 선수·경주·트랙·출주·결과 및 기본 분석 API
- 관리자 JWT 인증과 CSV 검증/import
- KCYCLE 외부 선수 및 data.go 통계 staging
- 읽기 전용 후보 매칭과 데이터 품질 대시보드
- Flutter Web 일반/관리자 화면

## Backend 실행

Python 가상환경 사용을 권장합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

루트 디렉터리에서 백엔드 검증:

```powershell
python -m compileall backend scripts
python -m unittest
pytest -q
python scripts\smoke_test_phase1.py
```

관리자 계정은 비밀번호를 명령행 인자로 노출하지 않는 스크립트로 생성합니다.

```powershell
python scripts\create_admin.py --email admin@example.com
```

## Flutter Web 실행

```powershell
cd frontend
flutter pub get
flutter run -d chrome --web-port 5001 --dart-define=KIP_API_BASE_URL=http://127.0.0.1:8000
flutter analyze --no-pub
flutter test --no-pub
flutter build web --no-pub
```

`frontend/build/`는 생성 산출물이며 Git에 포함하지 않습니다.

## 관리자 화면

- 로그인: `/admin/login`
- 관리자 홈: `/admin` 또는 `/admin/home`
- CSV import: `/admin/imports`
- 외부 선수: `/admin/external-players`
- 선수 통계: `/admin/external-player-statistics`
- 매칭 후보: `/admin/player-match-candidates`
- 데이터 품질: `/admin/data-quality`

staging과 후보/품질 화면은 읽기 전용입니다. 자동 선수 연결이나 승인 저장 기능은 없습니다.

## 환경변수와 비밀정보

- `DATABASE_URL`: Backend DB 연결 문자열. 로컬 기본값은 Backend 실행 위치 기준 `sqlite:///./kip.db`입니다.
- `DATA_GO_KR_SERVICE_KEY`: data.go 수집 명령에서만 사용합니다.
- `KIP_API_BASE_URL`: Flutter가 호출할 Backend URL입니다.
- `CORS_ORIGINS`: 허용할 로컬 Web origin 목록입니다.
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: 관리자 JWT 설정입니다.
- `CSV_IMPORT_MAX_BYTES`: 관리자 CSV 업로드 제한입니다.

서비스 키와 운영 비밀값은 소스, 문서, 로그에 저장하지 않습니다. 코드의 기본 JWT secret은 로컬 개발 전용이므로 운영 환경에서는 반드시 충분히 강한 별도 `JWT_SECRET_KEY`를 주입해야 합니다. `.env`, SQLite DB, DB 백업, 로그, `tmp/`, Flutter build는 Git ignore 대상입니다.

## Docker 상태

`docker-compose.yml`과 Dockerfile 구성은 존재하지만 Phase 1 최종 점검에서는 Docker Desktop을 실제 실행해 검증하지 않았습니다. 따라서 Docker 배포 완료 상태로 간주하지 않습니다.

```powershell
docker compose up --build
```

Docker를 사용하기 전 환경변수, 영구 볼륨, 운영 비밀정보와 백업 정책을 별도로 검토해야 합니다.

## 주의

`scripts/reset_demo_db.py`는 로컬 데모 DB 재구축용입니다. 운영 DB에 실행하지 마십시오. 전체·정기 외부 데이터 수집은 이용 승인과 운영 정책 확인 전까지 보류합니다.

최종 검증 결과와 운영 전 체크 항목은 [Phase 1 Release Checklist](docs/PHASE1_RELEASE_CHECKLIST.md)를 참고하십시오.
