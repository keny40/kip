# SQLite 로컬 UAT 체크리스트

## 실행 기준

- 테스트 날짜: 2026-07-13 (Asia/Seoul)
- Git branch/commit: `main` / `7098e89a31d77c10cfe0acfe5a90938f6333e3e7`
- 시작 시점 `HEAD`, 로컬 `origin/main`, 원격 `origin/main`: 동일
- 시작 시점 working tree: clean
- UAT 데이터베이스: `backend/kip_uat.db`
- 운영 데이터베이스 `backend/kip.db`: 읽기 전용 사전/사후 검증에만 사용
- Docker, PostgreSQL, data.go, KCYCLE 네트워크: 사용하지 않음

## 데이터베이스 보호 및 준비

운영 DB를 파일 복사하여 UAT DB를 만들었다. 관리자 생성 전 복사본의 크기와
SHA-256은 운영 DB와 동일했다.

| 항목 | 운영 DB 작업 전 | 운영 DB 작업 후 |
| --- | ---: | ---: |
| 파일 크기 | 307,200 bytes | 307,200 bytes |
| 수정 시각(ns) | 1783913012562283900 | 1783913012562283900 |
| SHA-256 | `0fb4d598f0991e227627cd2ab91b6f42b6076a9168b5256d751c04f9bb713772` | 동일 |
| Alembic revision | `0006_external_player_statistics` | 동일 |
| players | 13 | 13 |
| tracks | 3 | 3 |
| races | 3 | 3 |
| entries | 15 | 15 |
| results | 8 | 8 |
| external_players | 10 | 10 |
| external_player_statistics | 10 | 10 |
| users / admins | 1 / 1 | 1 / 1 |

UAT DB에서만 임시 관리자 1명을 추가했다. 최종 UAT DB의 선수·경주·staging
건수는 운영 DB와 같고 users/admins만 각각 2명이다. 자격 증명은 환경변수로만
전달했으며 테스트 후 런타임 자격 증명 파일과 환경변수를 제거했다.

## 실행 방법

현재 PowerShell 세션에 `KIP_UAT_ADMIN_EMAIL`과
`KIP_UAT_ADMIN_PASSWORD`를 안전하게 주입한 뒤 실행한다. 값을 명령 기록,
문서, Git 추적 파일에 넣지 않는다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_sqlite_uat.ps1
```

기본 주소:

- Backend: `http://127.0.0.1:8000`
- Flutter Web: `http://127.0.0.1:5001`
- Backend 작업 디렉터리에서 DB URL: `sqlite:///./kip_uat.db`

스크립트는 UAT DB 경로를 검증하고, UAT 관리자 준비, Backend health 대기,
Flutter release web build, 정적 web server 실행 순서로 동작한다. 다른 포트를
사용하려면 `-BackendPort`와 `-FlutterPort`를 전달한다.

종료:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop_sqlite_uat.ps1 -RemoveLogs
```

종료 스크립트는 PID와 command line을 함께 검증하고 이 스크립트가 시작한
프로세스 트리만 종료한다.

## 수동 브라우저 UAT 결과

### 일반 화면

- 오늘의 경주: 2026-07-13 서울 3경주 1건 표시, 상세에서 출전 선수 5명 확인
- 선수: 총 13명 표시, 상세·최근 결과·통계 표시 확인
- 선수 검색/등급/지역/상태 조합: Flutter widget 테스트 및 API 결과로 확인
- 경기장: 3건 표시, 서울 경기장 상세에서 경주 2건·출전 10건·고유 선수 9명 확인
- 분석: 경주 3, 예정/진행/완료 각 1, 선수 13, 결과 8, 경기장 3 표시
- 빈 필터 결과: UAT smoke에서 0건과 정상 응답 확인
- Backend 중단 후 재조회: 재시도 가능한 사용자 안내 표시 확인

### 관리자 화면

- 잘못된 비밀번호: 로그인 실패 문구 표시
- 정상 로그인: admin/active 확인 및 관리자 홈 메뉴 전체 표시
- 외부 선수: 10건, 필터 영역, 상세 dialog, 읽기 전용 구성 확인
- 선수 통계: 10건, NULL은 `-`, 0은 `0`, 상세/필터 UI 확인
- 매칭 후보: 10건 모두 `후보 없음`, 자동 연결·승인 동작 없음
- 데이터 품질: players 13, external players 10, statistics 10,
  후보 없음 10, 연결 가능률 0.0%, region unknown 10,
  invalid/null run count 1, 잠정키 중복 0 확인
- 로그아웃 후 관리자 로그인 화면으로 복귀 확인
- fixture CSV dry-run: UAT 복사본 smoke와 Flutter widget 테스트로 확인;
  실제 apply는 실행하지 않음
- KCYCLE 상세 링크는 dialog에 존재함을 확인했지만 외부 네트워크 호출 금지 때문에
  새 창의 원격 페이지는 열지 않음

### 반응형

- 실제 브라우저: 390px, 768px, 1280px(기본), 1440px에서 확인
- 390px 데이터 품질 화면은 카드 1열, 필터 줄바꿈, 가로 overflow 없음
- 768px 이상은 카드 grid와 필터 배치 정상
- staging DataTable의 좁은 화면 가로 스크롤은 Flutter widget 테스트 통과
- 1024px는 이번 브라우저 세션에서 별도 캡처하지 않았으므로 다음 수동 UAT에서
  재확인 권장

## 인증·오류·쓰기 보호

- 미인증 관리자 API: 401
- 잘못된 JWT: 401
- 일반 사용자 관리자 API: 403
- 존재하지 않는 external player 상세: 404
- 읽기 전용 staging POST: 405
- 잘못된 필터: 200 + 0건
- CSV: dry-run만 수행, 선수 수 불변
- JWT, 관리자 비밀번호, 서비스 키: 화면·로그·문서에 기록하지 않음

## 자동 테스트 결과

| 명령 | 결과 |
| --- | --- |
| `python -m compileall backend scripts` | 통과 |
| `python -m unittest` | 96 tests 통과 |
| `pytest -q` | 96 passed, 1 PostgreSQL test skipped, 1 dependency warning |
| `python scripts/smoke_test_phase1.py` | 통과 |
| `python scripts/smoke_test_sqlite_uat.py` | 통과 |
| `flutter analyze --no-pub` | 이슈 0건 |
| `flutter test --no-pub` | 47 tests 통과 |
| `flutter build web --no-pub` | release web build 통과 |

UAT smoke는 `kip_uat.db`를 OS 임시 디렉터리로 한 번 더 복사한 뒤 수행한다.
public read 7개, admin read 4개, 401/403/404/405, 빈 필터, CSV dry-run을
검증하며 원본 `kip_uat.db`에도 쓰지 않는다.

## 발견 및 수정한 문제

1. Flutter debug web-server가 인앱 브라우저에서 빈 화면으로 남았다.
   UAT 시작 스크립트를 release web build + 로컬 정적 server 방식으로 변경했다.
2. SQLite `Numeric` 비율 값이 API에서 문자열로 반환되어 선수 통계 staging
   화면이 파싱 예외를 냈다. 숫자와 숫자 문자열을 모두 파싱하고 회귀 테스트를 추가했다.
3. Backend 중단 시 public 화면이 `ClientException`과 내부 API URI를 노출했다.
   public 조회 화면은 공통 사용자 안내만 표시하도록 변경했다.
4. UAT 관리자 준비 도구가 기존 UAT 계정의 전달 비밀번호 변경을 반영하지 않았다.
   대상 DB가 정확히 `backend/kip_uat.db`일 때만 해시를 안전하게 갱신하도록 보강했다.

## 보류 및 판정

- 1024px 별도 실제 브라우저 캡처는 보류했다.
- 외부 KCYCLE 상세 페이지 새 창 도착은 외부 네트워크 금지 때문에 확인하지 않았다.
- build 경고: 선언된 Cupertino icon font asset을 찾지 못했다는 경고가 있으나 build는
  성공했다. `pubspec.yaml`을 이번 UAT에서 변경하지 않았다.
- 위 두 수동 항목을 제외한 SQLite 로컬 MVP 핵심 UAT는 통과했다.

## 정리 결과

- Backend/Flutter 종료 확인
- 8000/5001 listen 없음
- PID 파일 및 UAT 로그 삭제
- 런타임 자격 증명 파일과 관련 환경변수 제거
- `backend/kip_uat.db`는 다음 수동 테스트를 위해 유지하며 `*.db` 규칙으로 Git ignored
- `tmp/`, `frontend/build/`, 로그와 PID 파일은 Git ignored
