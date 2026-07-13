# KIP SQLite Windows 데모 배포

## 목적과 패키징 방식

이 패키지는 Windows 10/11 단일 PC에서 KIP SQLite MVP를 시연하기 위한 로컬
배포물이다. Backend는 Python 3.11 이상이 설치된 PC에서 전용 `.venv`를 만드는
방식을 사용한다.

PyInstaller 단일 EXE는 Alembic migration 리소스, SQLAlchemy 동적 import,
bcrypt/uvicorn 바이너리 의존성, Flutter 정적 자산을 별도로 묶어야 하므로 현재
단계에서는 재현성과 장애 진단성이 낮다. Embeddable Python은 Python 재배포 및
보안 업데이트 책임이 커진다. 따라서 검증 가능한 requirements 고정 버전과 venv가
가장 단순한 선택이다.

## 빌드

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_sqlite_demo_package.ps1
```

출력은 `dist/kip-sqlite-demo/`와 전달용 `dist/kip-sqlite-demo.zip`이며
`dist/`는 Git ignored다. 빌더는 다음만 포함한다.

- FastAPI application과 Alembic 0001~0006
- 데모용 최소 Python requirements
- Flutter Web release build
- synthetic sample CSV 및 별도 `data/kip_demo.db`
- 설치, 관리자 설정, 시작, 종료, 초기화, 검증 도구

운영 `backend/kip.db`, `.env`, Git metadata, service key, 고정 JWT secret,
source map과 Flutter WebAssembly symbol table은 복사하지 않는다. symbol table은
브라우저 오류 symbolication용이며 데모 실행에는 필요하지 않다.

## 패키지 구조

```text
kip-sqlite-demo/
  backend/              FastAPI, Alembic, demo requirements
  frontend/             Flutter Web release 정적 파일
  data/                 kip_demo.db 및 사용자 reset backup
  samples/              synthetic 기본 CSV
  scripts/              관리자, reset, 정적 검증, frontend proxy
  logs/                 실행 로그
  runtime/              실행 중 PID
  install_demo.ps1/cmd
  start_demo.ps1/cmd
  stop_demo.ps1/cmd
  README_FIRST.txt
  VERSION
```

`.venv`는 최초 `install_demo.cmd` 실행 시 패키지 내부에 생성되며 배포 빌드에는
포함하지 않는다.

## 데이터 정책

`create_sqlite_demo_db.py`는 대상 경로를 `data/kip_demo.db`로 고정하고
`backend/kip.db`를 거부한다. 빈 DB에 Alembic head를 적용한 후 sample 경주 데이터와
가상 외부 선수 10명, 가상 통계 10건을 넣는다. 관리자와 비밀번호는 포함하지 않는다.

reset은 실행 중인 데모를 거부하고 사용자가 정확히 `RESET`을 입력해야 한다.
기존 DB는 `data/backups/`에 timestamp 사본을 만든 후 교체한다.

## 실행과 포트

1. `install_demo.cmd`
2. `powershell -ExecutionPolicy Bypass -File scripts\setup_admin.ps1`
3. `start_demo.cmd`
4. 종료 시 `stop_demo.cmd`

기본 Backend/Frontend 포트는 8000/5001이다. `KIP_BACKEND_PORT`와
`KIP_FRONTEND_PORT`로 변경한다. Flutter는 release build 시 현재 origin을 사용하고,
포함된 정적 서버가 `/api/`를 선택한 Backend 포트로 proxy하므로 재빌드가 필요 없다.

포트가 사용 중이면 launcher는 실패하며 해당 프로세스를 종료하지 않는다.

## 관리자와 JWT

관리자 비밀번호는 대화형 hidden 입력 또는 테스트 시 명시적으로 설정한
`KIP_DEMO_ADMIN_PASSWORD` 환경변수로만 전달된다. DB에는 passlib bcrypt hash만
저장한다. 같은 이메일의 활성 관리자가 있으면 중복 생성하지 않는다.

JWT secret은 start마다 메모리에서 무작위 생성하며 파일에 저장하지 않는다.
따라서 재시작하면 기존 로그인 세션은 만료된다.

## 로그

- `logs/backend.log`, `backend.error.log`
- `logs/frontend.log`, `frontend.error.log`
- `logs/launcher.log`
- 최초 설치만 `logs/install.log`

각 실행 로그는 start 시 5 MiB를 넘으면 `.1` 하나로 회전한다. access log는 끄고,
frontend log는 method와 path만 남기며 Authorization, 비밀번호, JWT, DB URL을
기록하지 않는다. 패키지 전용 Backend runner는 처리되지 않은 예외를 일반 500과
`UNEXPECTED_SERVER_ERROR` 코드로 축약하여 traceback과 내부 SQL을 기록하지 않는다.
debug mode는 사용하지 않는다.

## 검증

정적 검증:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_demo_package.ps1
```

실행 중 health, 정적 웹, proxy public API 검증:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_demo_package.ps1 -Running
```

검증은 revision 0006, 주요 테이블, FK, 필수 파일, 운영 DB 부재, `.env`/`.git` 및
source map 부재를 확인한다.

## 전달과 제한

폴더 전체를 ZIP으로 전달할 수 있다. 수신 PC는 Python 3.11 이상과 첫 설치 시
PyPI 접근이 필요하다. Windows SmartScreen 또는 PowerShell 실행 정책이 조직 정책으로
차단된 환경에서는 IT 관리자의 허용이 필요할 수 있다.

이 패키지는 로컬 단일 사용자 테스트용이다. Windows Service, TLS, 외부 접속,
동시 다중 사용자, 자동 백업, 운영 모니터링은 제공하지 않는다.

## 2026-07-13 검증 결과

- 원본 `compileall`: 통과
- Backend `unittest`: 96개 통과
- Backend `pytest`: 96 passed, PostgreSQL integration 1 skipped
- Flutter analyze: 이슈 0건
- Flutter test: 47개 통과
- Flutter release web build: 성공
- 빈 DB migration 0001~0006 및 synthetic seed: 성공
- 패키지 전용 venv 최초 설치: 성공
- health, frontend, same-origin proxy API: 모두 200
- 관리자 생성, 로그인, staging 3개 화면, 데이터 품질, 로그아웃: 성공
- 재시작 후 관리자와 DB 유지: 성공
- stop 후 8000/5001 listen 없음
- 포트 충돌 시 기존 listener 보존 및 launcher 실패: 성공
- `C:\KIP 테스트\...` 경로와 8100/5101 대체 포트: 성공
- reset backup 생성과 새 demo DB 재생성: 성공
- ZIP 추출 후 정적 검증: 성공
- 운영 `backend/kip.db` 크기, mtime, SHA-256, revision, 행 수: 작업 전후 동일

최종 폴더는 약 28.8 MiB, ZIP은 약 10.9 MiB다. `.venv`는 포함하지 않으므로
수신 PC의 최초 설치 후 실제 사용 폴더 크기는 Python 의존성만큼 증가한다.
