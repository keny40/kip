# Phase 1 Release Checklist

검증일: 2026-07-13  
범위: 로컬 SQLite MVP 통합 검증. 실제 서버/Docker/외부 API live 수집은 제외.

## A. 완료 기능

- [x] SQLite 모델과 Alembic `0001`~`0006`
- [x] 선수, 경주, 트랙, 출주, 결과 API
- [x] 기본 경주·트랙·선수 분석 API
- [x] 관리자 JWT 인증과 권한 검사
- [x] CSV 검증, dry-run 및 import
- [x] Flutter Web 일반 화면과 관리자 화면
- [x] KCYCLE 선수 마스터 `external_players` staging
- [x] data.go 연도별 선수 통계 `external_player_statistics` staging
- [x] 이름+기수 기반 읽기 전용 후보 매칭 리포트
- [x] 관리자 데이터 품질 요약 API와 Flutter 대시보드

## B. 최종 검증 결과

| 항목 | 결과 |
|---|---|
| `python -m compileall backend scripts` | 통과 |
| `python -m unittest` | 96개 통과 |
| `pytest -q` | 96개 통과 |
| `flutter analyze --no-pub` | 문제 없음 |
| `flutter test --no-pub` | 46개 통과 |
| `flutter build web --no-pub` | 성공 |
| 빈 DB → Alembic head | `0006_external_player_statistics` 성공 |
| Alembic `0006 → 0005 → 0006` | 성공, 임시 DB 삭제 확인 |
| `scripts/smoke_test_phase1.py` | Public 7개·Admin read-only 4개 및 인증/쓰기 보호 통과 |
| CSV smoke | 선수 10행·외부 선수 1행 dry-run, 오류 1행 거부, DB 불변 |

## C. 현재 로컬 데이터

운영 `backend/kip.db`를 SQLite read-only 모드로 확인했습니다.

| 항목 | 값 |
|---|---:|
| Alembic revision | `0006_external_player_statistics` |
| players | 13 |
| races | 3 |
| tracks | 3 |
| external_players | 10 |
| external_player_statistics | 10 |
| users / admin users | 1 / 1 |

현재 후보 집계는 유일 후보 0, 후보 없음 10, 복수 후보 0, 기수 미확인 0, 등급 불일치 0입니다. 품질 집계에서는 외부 선수 region `unknown` 10건과 통계 run count NULL/비정상 1건이 확인되었습니다. 외부 선수/통계 잠정키 중복은 각각 0건입니다. 실제 선수명과 external ID는 이 문서에 기록하지 않습니다.

## D. 운영 전 보류

- [ ] PostgreSQL 전환과 migration 검증
- [ ] 실제 서버 배포와 HTTPS/TLS
- [ ] 비밀정보 관리 서비스 또는 안전한 secret injection
- [ ] 운영 DB 자동 백업·복구 훈련
- [ ] 로그·메트릭·알림 모니터링
- [ ] 전체·정기 KCYCLE/data.go 수집 이용 승인
- [ ] 대용량 수집·조회·후보 집계 성능 검증
- [ ] 일반 회원가입과 결제·구독
- [ ] 모바일 스토어 배포
- [ ] Docker Desktop 실제 실행 및 compose 통합 검증
- [ ] `scripts/bootstrap.ps1` 로컬 bootstrap 자동화

## E. 데이터 연결 제한

- `external_players`와 `players` 자동 연결 없음
- 이름과 기수를 조합한 가짜 `player_number` 또는 external ID 생성 없음
- fuzzy matching 없음
- data.go 통계는 안정적인 선수번호가 없어 staging에만 저장
- 후보 매칭과 데이터 품질 화면은 read-only이며 승인 저장 없음

## F. 알려진 경고와 제한

- Python 테스트에서 Starlette의 `python_multipart` import 전환 관련 PendingDeprecationWarning이 발생합니다.
- Flutter Web build에서 CupertinoIcons 폰트가 assets에 없다는 비차단 경고가 발생합니다.
- Web 외부 링크 구현은 조건부 import에서 deprecated `dart:html`을 사용하며 향후 `package:web` 전환 검토가 필요합니다.
- Docker 구성 파일은 존재하지만 이번 점검에서 Docker Desktop을 실제 실행하지 않았습니다.
- `backend/app/core/config.py`의 JWT secret 기본값은 개발 전용입니다. 운영에서는 기본값 사용을 금지합니다.

## 실행·배포 직전 확인

- [ ] 작업 트리와 배포 커밋 확정
- [ ] 운영 전용 `DATABASE_URL`, `JWT_SECRET_KEY`, CORS 설정 주입
- [ ] 서비스 키가 파일·로그·CI 출력에 없는지 재확인
- [ ] `alembic upgrade head` 대상 DB와 백업 확인
- [ ] Backend health와 관리자 로그인 smoke 실행
- [ ] Flutter API base URL과 HTTPS origin 확인
- [ ] Docker를 사용할 경우 별도 compose 검증 완료

Phase 1은 **로컬 MVP 범위에서 완료 가능**합니다. 상용 운영 준비 완료를 의미하지 않으며 D 항목 해결 전 실제 서비스 배포를 보류합니다.
