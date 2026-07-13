# KIP 경륜 데이터 출처 조사

이 문서는 실제 구현 전 단계의 조사 기록이다.  
코드, DB, API, 크롤러는 수정하지 않았다.

## 조사 결론

- 1차 권장 출처는 [KCYCLE 경륜](https://www.kcycle.or.kr/) 공식 사이트다.
- 구조화된 머신 데이터가 필요하면 [공공데이터포털](https://www.data.go.kr/)의 서울올림픽기념국민체육진흥공단 경륜 OpenAPI 군이 더 안정적이다.
- 다만 이번 조사 범위에서 `경주일정`만은 KCYCLE 웹 페이지가 가장 명확했고, `선수정보`, `출주표`, `경주결과`는 data.go.kr OpenAPI가 가장 구조적이었다.
- 따라서 첫 수집기는 `KCYCLE 웹 페이지 + data.go.kr OpenAPI`를 같은 기관 데이터군으로 묶어 보되, 운영 초기는 `KCYCLE`을 기준 화면(source of truth)으로 두는 안이 가장 현실적이다.

## 1) KCYCLE 경륜 공식 사이트

- 사이트: [https://www.kcycle.or.kr/](https://www.kcycle.or.kr/)
- 운영 기관: 서울올림픽기념국민체육진흥공단 경륜경정총괄본부
- 공식성: 공식 사이트로 보인다.
- 데이터 형식: HTML 중심, 일부 화면에 Excel/텍스트 저장 버튼이 있다.
- 로그인 필요 여부: 주요 공개 페이지는 로그인 없이 열람 가능했다. 회원 전용 기능은 별도 로그인 흐름이 있다.
- CAPTCHA: 조사한 공개 페이지에서는 보이지 않았다.
- JavaScript 렌더링: 상호작용은 있으나, 주요 텍스트는 서버 렌더링된 HTML에서 확인 가능했다.
- robots.txt: 공개 크롤링을 기본 허용하고, 일부 고객광장 경로만 제외한다.
  - 확인 내용: `Disallow: /customerplaza/voc/`, `Disallow: /customerplaza/predictreview/`, `Allow: /`
- 이용약관 / 재사용 제한: `자료무단복제금지`와 `이용약관`에서 사이트 자료의 무단 상업 복제를 제한한다.
- 업데이트 시각:
  - `확정출주표`는 금요일/토요일/일요일 전일 19:30 이후 제공.
  - `통합경주결과`는 경주 종료 직후 1~3위와 기록 정보를 안내.
  - `경주일정` 페이지는 연도별 달력과 회차 목록을 제공한다.
- 과거 데이터 범위: 페이지상 연도 선택이 2026년부터 1994년까지 노출된다.
- 요청 빈도 제한: 공식 제한값은 확인하지 못했다.
- 고유 식별자:
  - 선수 상세 페이지 URL이 `/racer/info/{player_id}` 형태다.
  - 경주는 `연도 / 회차 / 일차 / 경주번호` 조합으로 식별할 수 있다.
- 데이터 누락/형식 변경 위험:
  - HTML 구조 변경에 민감하다.
  - 공지/출주표/결과 화면은 컬럼 재배치 가능성이 있다.

### KCYCLE에서 확인한 주요 화면

- 경주일정: [https://www.kcycle.or.kr/race/schedule](https://www.kcycle.or.kr/race/schedule)
- 확정출주표: [https://www.kcycle.or.kr/race/card/decision](https://www.kcycle.or.kr/race/card/decision)
- 통합경주결과: [https://www.kcycle.or.kr/race/result/general](https://www.kcycle.or.kr/race/result/general)
- 선수조회: [https://www.kcycle.or.kr/racer/info](https://www.kcycle.or.kr/racer/info)
- 선수 상세 예시: [https://www.kcycle.or.kr/racer/info/20180004](https://www.kcycle.or.kr/racer/info/20180004)

### KCYCLE에서 확인된 필드 예시

- 선수 상세:
  - 선수번호
  - 이름
  - 등급
  - 기수
  - 출생년도
  - 신장/체중
  - 흡연 여부
  - 고등학교/대학교
  - 출신지/출신팀
  - 최신입상내역
  - 경주 기록정보
- 확정출주표:
  - 선수정보
  - 기어배수
  - 200m 기록
  - 훈련지
  - 승률, 연대율, 삼연대율
  - 입상/출전 횟수
  - 입상전법
  - 등급조정
  - 최근 3회 평균득점
  - 최근 3회 성적순위
  - 선행/젖히기/추입/마크
- 경주결과:
  - 1~3위
  - 배당률
  - 경주기록

## 2) 공공데이터포털 data.go.kr OpenAPI

- 사이트: [https://www.data.go.kr/](https://www.data.go.kr/)
- 운영 기관: 서울올림픽기념국민체육진흥공단
- 공식성: 공공데이터포털에 등록된 공식 OpenAPI다.
- 데이터 형식: REST API, JSON + XML
- 로그인 필요 여부:
  - 문서 열람은 가능하다.
  - 실제 활용은 공공데이터포털 회원 가입과 활용신청, API 키 발급이 필요하다.
- CAPTCHA: 조사한 문서 페이지에서는 보이지 않았다.
- JavaScript 렌더링: 문서 페이지는 일반 HTML로 읽혔다.
- robots.txt: Googlebot에 대해 일부 데이터셋/게시판 경로가 차단되어 있다.
- 이용약관 / 재사용 제한:
  - 개별 API 페이지에 `이용허락범위 제한 없음`이 표기되어 있다.
- 업데이트 시각:
  - `선수정보`, `출주표_GW`, `경주결과_GW`는 실시간 업데이트로 표기된다.
- 과거 데이터 범위:
  - 연도/회차 기반으로 장기 이력이 존재한다.
  - 일부 데이터는 2022년 이후 갱신 주기 변경 안내가 있다.
- 요청 빈도 제한:
  - 개발계정 10,000 트래픽이 표기된다.
  - 운영계정은 활용사례 등록 시 증액 신청 가능으로 안내된다.
- 고유 식별자:
  - 선수번호가 제공된다.
  - 경주는 경주일/시행처/회차/경주번호 조합으로 식별 가능하다.
- 데이터 누락/형식 변경 위험:
  - API 필드 추가/변경은 상대적으로 적지만, 명세 갱신은 확인이 필요하다.

### 조사한 OpenAPI

- 선수정보: [https://www.data.go.kr/data/15107844/openapi.do](https://www.data.go.kr/data/15107844/openapi.do)
- 출주표_GW: [https://www.data.go.kr/data/15107830/openapi.do](https://www.data.go.kr/data/15107830/openapi.do)
- 경주결과_GW: [https://www.data.go.kr/data/15107816/openapi.do](https://www.data.go.kr/data/15107816/openapi.do)
- 홈페이지 자료실 정보: [https://www.data.go.kr/data/15107871/openapi.do](https://www.data.go.kr/data/15107871/openapi.do)

### API별 요약

#### 경륜-선수정보

- 형식: REST, JSON/XML
- 업데이트: 실시간
- 제공 필드 예시:
  - 선수번호
  - 이름
  - 등급
  - 출전회수
  - 출전일수
  - 순위별 입상 횟수
  - 승률, 연대율, 삼연대율
  - 실격/포기 횟수
  - 전법 관련 지표
  - 기어배수
  - 일부 생체 정보
- 참고:
  - 2022년부터 월별에서 연별 갱신으로 바뀌었다는 안내가 있다.

#### 경륜-출주표_GW

- 형식: REST, JSON/XML
- 업데이트: 실시간
- 제공 필드 예시:
  - 최근 3회전 성적
  - 시행처(경주장)
  - 경주일자
  - 선수별 주요 통계
- 참고:
  - 출주표 항목은 KCYCLE의 `racecard` 안내와 연계된다고 안내한다.

#### 경륜-경주결과_GW

- 형식: REST, JSON/XML
- 업데이트: 실시간
- 제공 필드 예시:
  - 경주일
  - 시행처
  - 회차
  - 경주번호
  - 1~3위 입상 선수 번호/이름
  - 승식별 배당률
  - 매출액

#### 경륜-홈페이지 자료실 정보

- 형식: REST, JSON/XML
- 업데이트: 실시간 성격의 자료실 정보
- 제공 필드 예시:
  - 경륜스타트사진목록
  - 일반/이벤트 경주 동영상
  - 자료실 정보
  - 기획프로그램
  - 연간경주일정
  - 경륜뉴스

## 3) 조사한 기타 공식 보조 페이지

- 선수 등급 기준 안내: [https://www.kcycle.or.kr/guide/about/basic](https://www.kcycle.or.kr/guide/about/basic)
- 훈련지 변경 공지: [https://www.kcycle.or.kr/racer/state/trainingsitechange](https://www.kcycle.or.kr/racer/state/trainingsitechange)
- 경륜 기초/전법 안내: [https://www.kcycle.or.kr/guide/learn/racetactics](https://www.kcycle.or.kr/guide/learn/racetactics)
- 자료무단복제금지: [https://www.kcycle.or.kr/customerplaza/terms/reproduction](https://www.kcycle.or.kr/customerplaza/terms/reproduction)
- 이용약관: [https://www.kcycle.or.kr/customerplaza/terms/use](https://www.kcycle.or.kr/customerplaza/terms/use)

## 4) 신뢰성 평가

- KCYCLE 공식 사이트
  - 장점: 한 도메인에서 일정, 출주표, 결과, 선수 상세를 모두 볼 수 있다.
  - 장점: 공개 페이지는 로그인 없이 접근 가능했다.
  - 장점: robots.txt가 공개 페이지 수집을 크게 막지 않는다.
  - 단점: HTML 레이아웃 변경에 취약하다.
- data.go.kr OpenAPI
  - 장점: JSON/XML 구조화가 잘 되어 있다.
  - 장점: 실시간 업데이트와 트래픽 정보가 명시되어 있다.
  - 장점: 선수/출주표/결과는 구조적으로 수집하기 쉽다.
  - 단점: 이번 조사에서 `경주일정` 전용 API는 명확히 확인하지 못했다.

## 5) 우선 사용 권장 출처

### 1차 수집기 권장안

- 우선 도메인: [KCYCLE 경륜](https://www.kcycle.or.kr/)
- 이유:
  - 일정/출주표/결과/선수상세를 한 도메인에서 확인할 수 있다.
  - 첫 수집기의 운영 범위를 단순하게 유지할 수 있다.
  - schedule/result/profile을 한 흐름으로 묶기 쉽다.

### 2차 보강안

- 구조화 검증용 보강 출처: [공공데이터포털 경륜 OpenAPI](https://www.data.go.kr/)
- 이유:
  - 선수/출주표/결과는 JSON/XML로 처리하기 쉽다.
  - HTML 파서보다 유지보수가 쉽다.

## 6) 미확인 사항

- 실제 API 호출 시의 정확한 인증 방식과 키 전달 파라미터는 추후 구현 전에 다시 확인해야 한다.
- KCYCLE 사이트의 내부 비공개 API 구조는 조사하지 않았다.
- CAPTCHA가 운영 구간에서 간헐적으로 나타나는지 여부는 확인하지 못했다.
- 요청 빈도 제한의 실제 서버 반응은 아직 측정하지 않았다.

## 7) data.go.kr 경륜 선수정보 실제 응답 계약

- 검증일: 2026-07-13
- 호출 범위: `stnd_yr=2025`, `pageNo=1`, `numOfRows=10`, XML, dry-run
- 공공데이터 설명과 실제 XML 사이에 선수 식별 필드 차이가 확인됐다.
- 실제 10개 item에서 확인한 필드:
  - `stnd_yr`
  - `racer_nm`
  - `period_no`
  - `racer_grd_cd`
  - `run_cnt`
  - `rank1_tcnt`
  - `rank2_tcnt`
  - `rank3_tcnt`
  - `win_rate`
  - `high_rate`
  - `high_3_rate`
- 실제 응답에는 `racer_no`가 없었다.
- 따라서 10건 모두 `MISSING_PLAYER_NUMBER`, 정규화 성공 0건이었다.
- 과거 문서의 “고유 선수 3명/중복 7건” 및 “`racer_no` 중복 제거 live 검증” 표현은 잘못된 fixture에 근거한 것이므로 폐기한다.
- 중복 판정 전에 필수 선수번호 검증에서 실패하므로 실제 중복 건수는 확인할 수 없다.

### 식별 및 적재 정책

- `period_no`는 공식 화면의 기수번호이며 선수 고유번호가 아니다.
- `period_no`는 요청 필터 및 선수 기수 데이터로만 취급하고 `players.player_number`에 매핑하지 않는다.
- `racer_nm` 단독 또는 `racer_nm + period_no`로 `players`를 upsert하지 않는다.
- 이름 해시, 문자열 결합, 행 번호 등으로 가짜 선수번호를 생성하지 않는다.
- `racer_no`가 없으면 `MISSING_PLAYER_NUMBER`로 거부하며 DB import를 시작하지 않는다.
- 이름이 없으면 `MISSING_PLAYER_NAME`으로 거부한다.
- grade/region/status 미확인 값은 `unknown` 정책을 유지한다.
- 현재 API는 연도별 선수 성적 통계 staging 데이터 원천으로는 사용할 수 있지만 선수 마스터 직접 적재에는 사용할 수 없다.
- 선수 마스터의 고유 식별키 출처가 확정될 때까지 `player_number` 매핑은 보류한다.

## 8) KCYCLE 공개 선수 페이지 식별자 소규모 조사

- 조사일: 2026-07-13
- 범위: [선수조회](https://www.kcycle.or.kr/racer/info), [선수전적비교](https://www.kcycle.or.kr/racer/compare), 선수 3명 및 상세 1건
- 공개 식별자 후보 필드명: `racerNo`
- 형식: 8자리 숫자. 예시는 `1999****`, `2021****`, `2024****`처럼 마스킹한다.
- 획득 위치:
  - 선수조회 카드의 `onclick`: `fnMoveTo('/racer/info', '<racerNo>')`
  - 상세 URL: `/racer/info/<racerNo>`
  - 상세 화면 hidden input: `name="racerNo"`
  - 선수전적비교 카드의 `onclick`: `fnAddRacer('<racerNo>')`
- 표본 3명에서 선수조회와 선수전적비교 화면의 값이 각각 동일했고, 상세 URL과 hidden input도 같은 값을 유지했다.
- 따라서 KCYCLE `racerNo`는 이름+기수보다 안정적인 공식 상세 ID 후보로 판단한다. 다만 data.go.kr 통계 item과 이 ID를 직접 연결하는 공개 필드는 이번 조사에서 확인하지 못했다.

### 대체 식별정책 비교

- A. KCYCLE `racerNo`
  - 장점: 공식 공개 화면 여러 곳에서 동일하게 유지되는 상세 식별자다.
  - 권장: 원형을 보존하는 `external_id`가 가장 안전하다. 기존 `player_number`로 사용할지는 전체 선수 및 과거 데이터 안정성 검증 후 결정한다.
- B. `racer_nm + period_no` staging 자연키
  - 장점: 현재 data.go.kr 통계 item만으로 구성할 수 있다.
  - 제한: `players.player_number`로 사용하거나 문자열을 합쳐 가짜 번호를 만들면 안 된다.
  - 표본 3명에서는 충돌이 없었지만, 이름 변경·동명이인·과거/현재 선수 범위까지 유일하다는 공식 보장은 확인하지 못했다.
  - 권장: 선수 마스터와 분리된 연도별 통계 staging 테이블에서만 잠정 키로 사용한다.

현재 권장 순서는 A의 KCYCLE `racerNo`와 data.go.kr 통계 행 사이의 공식 연결 가능성을 먼저 조사하고, 연결이 확인되기 전에는 B를 staging 범위로만 제한하는 것이다.
