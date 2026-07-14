# KIP 핵심 예측 MVP 메모

## 현재 데이터 준비도

- 현재 운영 SQLite 데이터는 경주 3건, 출전 15행, 결과 8행 수준이다.
- 완료 상태 경주는 1건뿐이며, 결과가 연결된 출전 행은 8행이다.
- 이 데이터로 모델을 학습하거나 정확도를 주장하지 않는다.

## 최소 학습 행

학습 데이터의 한 행은 “한 경주의 한 출전 선수”다.

필수 컬럼:

- `race_date`
- `track_code`
- `race_number`
- `player_id`, `player_number`, `player_name`
- `entry_number`
- `grade`
- `period_number`
- `result_rank`

경주 전 알 수 있는 특성만 사용한다.

- 최근 5경기 출전 수, 평균 순위, 우승 수, 3위 이내 수
- 최근 10경기 평균 순위
- 경기장별 과거 출전 수와 평균 순위
- 최근 경기 이후 경과일
- 과거 기록 존재 여부

현재 경기 결과, 현재 경기 이후 누적 통계, 미래 경기 결과는 feature로 사용하지 않는다.

## 데이터 준비도 기준

초기 기준:

- 완료 경주 500건 이상
- 결과가 있는 유효 출전 행 3,000건 이상
- 선수당 과거 경기 중앙값 5건 이상
- result_rank 누락률 5% 미만

기준 미달 시 상태는 `INSUFFICIENT_TRAINING_DATA`이며, 모델 파일과 예측 확률을 만들지 않는다.

## 공식 과거 데이터 후보

- data.go.kr 경륜 `출주표_GW`: <https://www.data.go.kr/data/15107830/openapi.do>
- data.go.kr 경륜 `경주결과_GW`: <https://www.data.go.kr/data/15107816/openapi.do>
- KCYCLE 확정출주표: <https://www.kcycle.or.kr/race/card/decision>
- KCYCLE 통합경주결과: <https://www.kcycle.or.kr/race/result/general>

공식 출처에서 안정적인 선수 식별자가 확인되지 않은 데이터는 운영 `players/races/results` 테이블에 바로 넣지 않고 preview 또는 staging으로 유지한다.

## 현재 구현

- `backend/app/ml/dataset_builder.py`: 운영 DB를 읽어 누수 방지 학습 CSV와 report 생성
- `backend/app/ml/trainer.py`: 충분한 데이터가 있을 때만 기준 모델을 실행하는 readiness gate
- `backend/app/ml/predictor.py`: 모델 준비 전 `not_ready` 응답
- `GET /api/v1/analytics/races/{race_id}/prediction`: 현재 환경에서는 `INSUFFICIENT_TRAINING_DATA`
- `scripts/collect_race_history.py`: 최대 10경주 preview 수집기. 서비스 키와 확정 endpoint가 없으면 live 호출 없이 명확히 중단
- `scripts/build_training_dataset.py`: `tmp/training_dataset.csv`, `tmp/training_dataset_report.json` 생성
- `scripts/train_baseline_model.py`: 데이터 부족 시 학습 거부

## 2026-07-14 과거 출주·결과 수집 병목

- 현재 다음 병목은 모델 코드가 아니라 과거 출주표·경주결과 데이터 확보와 식별자 검증이다.
- 공공데이터포털 문서 기준 출주표 endpoint는 `SRVC_OD_API_CRA_RACE_ORGAN/TODZ_API_CRA_RACE_ORGAN_I`이다.
- 공공데이터포털 문서 기준 경주결과 endpoint는 `SRVC_TODZ_CRA_RACE_RESULT/TODZ_API_CRA_RACE_RESULT`이다.
- 문서상 출주표/결과 모두 별도 공식 race ID와 player ID가 확인되지 않았다.
- 날짜+경기장+회차+일차+경주번호는 자연키 후보일 뿐 공식 ID가 아니다.
- `back_no`는 출전 번호로 취급하며 선수 고유번호로 사용하지 않는다.
- ID 확정 전에는 운영 `races`, `entries`, `results`, `players` 테이블에 과거 데이터를 적재하지 않는다.
- 현재 셸에는 `DATA_GO_KR_SERVICE_KEY`가 없어 live preview는 실행하지 않았고 `SERVICE_KEY_MISSING`으로 중단했다.

## 운영 제한

- 배당, 베팅 조합, 가치베팅, 적중 보장 표현은 구현하지 않는다.
- 운영 DB는 읽기 전용으로 사용한다.
- 모델 산출물은 `artifacts/models/`에 생성하되 Git에는 포함하지 않는다.
