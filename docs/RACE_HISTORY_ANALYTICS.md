# KIP 비배팅 경주 기록 분석 MVP

## 범위

이 문서는 배당·베팅·예측을 제외한 공식 경륜 기록 분석 MVP를 설명한다.

포함:

- 공식 출주표 preview
- 공식 경주결과 preview
- 과거 기록 staging 저장
- 선수 후보별 과거 성적 통계
- 경기장별 결과 분석
- 데이터 품질 점검

제외:

- 배당 수집
- 베팅 조합
- 가치베팅
- AI 모델 학습
- 순위 예측
- 운영 `players/races/entries/results` 자동 연결

## 공식 endpoint

### 출주표

- catalog: <https://www.data.go.kr/data/15107830/openapi.do>
- endpoint: `https://apis.data.go.kr/B551014/SRVC_OD_API_CRA_RACE_ORGAN/TODZ_API_CRA_RACE_ORGAN_I`
- method: `GET`
- 필수: `serviceKey`, `resultType`
- 선택: `pageNo`, `numOfRows`, `meet_nm`, `stnd_yr`, `week_tcnt`

### 경주결과

- catalog: <https://www.data.go.kr/data/15107816/openapi.do>
- endpoint: `https://apis.data.go.kr/B551014/SRVC_TODZ_CRA_RACE_RESULT/TODZ_API_CRA_RACE_RESULT`
- method: `GET`
- 필수: `serviceKey`, `resultType`, `stnd_yr`, `meet_nm`, `week_tcnt`, `day_tcnt`, `race_no`
- 선택: `pageNo`, `numOfRows`
- 2026-07-14 live 확인 구조:
  - 원본 `item` 1건이 한 경주의 결과를 의미한다.
  - `rank1`, `rank2`, `rank3` 필드가 각각 1~3위를 의미한다.
  - live 예시는 `rank1=2***`, `rank2=6***`, `rank3=5***`처럼 `출전번호+선수명` 결합값이었다.
  - 4위 이후 순위 필드는 확인되지 않았다.
  - 별도 `racerNo`, `external_player_id`, 공식 `external_race_id`는 확인되지 않았다.
  - 따라서 이 결과 API는 현재 `PARTIAL_TOP3_RESULT_SOURCE`로 판정한다.

## CLI 모드

출주표만:

```powershell
python scripts\collect_race_history.py `
  --mode lineup `
  --date-from 2025-01-01 `
  --date-to 2025-01-31 `
  --meet-name 광명 `
  --year 2025 `
  --week-count 1 `
  --max-races 10 `
  --dry-run `
  --inspect
```

결과만:

```powershell
python scripts\collect_race_history.py `
  --mode result `
  --date-from 2025-01-01 `
  --date-to 2025-01-31 `
  --meet-name 광명 `
  --year 2025 `
  --week-count 1 `
  --day-count 1 `
  --race-number 1 `
  --dry-run `
  --inspect
```

## 자연키와 식별자

경주 staging 자연키:

- `source`
- `standard_year`
- `meet_name`
- `week_count`
- `day_count`
- `race_number`

이 값은 공식 race ID가 아니라 source 내부 자연키다.

선수 후보키:

- `player_name`
- `period_number`

이 값은 분석용 provisional key이며 공식 선수 ID가 아니다. 이름만으로 합치지 않고, 이름+기수도 운영 선수번호로 사용하지 않는다.

`back_no`는 경주 내 출전 번호이며 선수 ID로 저장하지 않는다.

## staging 테이블

- `external_races`
- `external_race_entries`
- `external_race_results`

운영 테이블 `races`, `entries`, `results`, `players`는 변경하지 않는다.

## 결과 상태

- `FINISHED`
- `WITHDRAWN`
- `DISQUALIFIED`
- `DID_NOT_START`
- `UNKNOWN_RESULT_STATUS`

숫자 순위는 정수로 저장하고, 특수 상태를 임의 숫자로 변환하지 않는다.

## top3 전용 결과 소스 제한

data.go.kr `경륜-경주결과_GW`는 현재 확인된 구조상 상위 3명만 제공한다.

허용:

- 우승 횟수
- 2위 횟수
- 3위 횟수
- top3 횟수
- top3 선수 분포
- 경기별 상위 3명 기록

금지:

- 전체 평균 순위
- 전체 결과 등록률
- 완료 출전 수를 전체 순위 데이터처럼 해석
- 4위 이하 선수를 결과 누락으로 간주

전체 순위 분석은 KCYCLE 통합경주결과 등 별도 전체 결과 출처가 확인된 뒤 구현한다.

## 분석 API

- `GET /api/v1/analytics/history/summary`
- `GET /api/v1/analytics/history/players`
- `GET /api/v1/analytics/history/players/{name}`
- `GET /api/v1/analytics/history/tracks`
- `GET /api/v1/admin/race-history-data-quality`

관리자 품질 API는 관리자 인증이 필요하다.

## 현재 검증 상태

- Codex 실행 환경에는 `DATA_GO_KR_SERVICE_KEY`가 없어 live 호출은 수행하지 못했다.
- 임시 SQLite DB `backend/kip_history_test.db`에서 0007 migration, dry-run, 첫 apply, 두 번째 apply를 검증했다.
- 첫 apply: external race 1건, entry 2건, result 2건 생성
- 두 번째 apply: 신규 생성 0, 기존 데이터 skipped
- 운영 `backend/kip.db`는 변경하지 않았다.

## 전체 수집 전 확인사항

- 경주가 실제 존재하는 `meet_nm`, `stnd_yr`, `week_tcnt`, `day_tcnt`, `race_no` 조합
- 결과 API의 rank 필드가 실제로 번호+이름 형식인지
- 기권·실격·미출주가 어떤 문자열로 오는지
- data.go 이용 승인과 전체·정기 수집 허용 범위
