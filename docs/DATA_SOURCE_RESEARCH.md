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

## 9) KCYCLE 선수 마스터 preview 수집 계약

- 검증일: 2026-07-13
- 공식 화면:
  - [선수조회](https://www.kcycle.or.kr/racer/info)
  - [선수전적비교](https://www.kcycle.or.kr/racer/compare)
- 인증, 서비스 키, 로그인 세션 없이 공개 응답을 확인했다.

### 실제 요청과 응답 형식

- 기본 선수 목록: `GET https://www.kcycle.or.kr/racer/info`
  - 응답: 전체 페이지 HTML
  - 기본 필터: `retiredYn=N`인 현역선수
- 선수조회 검색/AJAX: `POST /racer/info`
  - 응답: `.layoutContArea`를 교체하는 HTML fragment
  - 공개 검색 필드: `retiredYn`, `racerGrdCd`, `gisu`, `trngPlcCd`, `searchRacer`, `fstLet`
- 선수전적비교 검색: `POST /racer/compare`
  - 응답: HTML fragment
- 비교 선택 갱신: `POST /racer/compare/update`
  - `compareRacerNo`를 사용하며 비교 선수는 화면 스크립트상 최대 3명이다.
- 별도 JSON 목록 API는 확인되지 않았다.

### 목록과 페이지네이션

- 기본 현역 목록은 575개 `a.prsn` 카드가 단일 HTML 응답에 포함됐다.
- 서버 페이지 번호 및 page-size 파라미터는 확인되지 않았다.
- 화면은 초성 그룹과 검색 필터를 사용하며 숫자 페이지네이션은 없다.
- KIP preview 수집기의 `page_size`는 서버 요청값이 아니라 응답에서 정규화할 최대 카드 수이며 1~10으로 제한한다.
- `max_pages`는 1만 허용한다.

### racerNo 및 공개 필드

- `racerNo`: 카드의 `onclick="fnMoveTo('/racer/info', '<8자리 숫자>')"` 두 번째 인수
- 사진 경로: `/player/<racerNo>.jpg`
- 상세 URL: `/racer/info/<racerNo>`
- 선수명: 카드의 `b.name`
- 등급과 기수: 카드의 `span.cate`
- 기본 목록 상태: 현역(`retiredYn=N`), KIP 값 `active`
- 훈련지는 검색 조건으로 공개되지만 기본 카드에는 선수별 값이 포함되지 않아 preview에서는 `unknown`이다.
- 상세 화면에는 출생일, 출신지/출신팀 등의 정보가 공개된다. 초기 preview 수집기는 추가 상세 요청을 하지 않는다.
- `external_id`는 앞자리 0을 보존하는 문자열로 저장하며 숫자 변환, 이름/기수 결합, hash 생성을 금지한다.

### 2026-07-13 소규모 live dry-run

- HTTP 성공: true
- 응답 카드: 575
- 검사/정규화: 첫 10건 / 10건 성공
- `MISSING_EXTERNAL_ID`: 0
- `MISSING_PLAYER_NAME`: 0
- 중복 `racerNo`: 0
- 결과는 Git 무시 대상인 `tmp/kcycle_players_preview.csv`에 기록했다.
- DB insert/update 코드는 없으며 운영 DB를 사용하지 않았다.

### data.go 통계 후보 매칭

현재 data.go live-style fixture는 실명을 제거한 10개 샘플이므로 KCYCLE live preview와의 실데이터 연결성을 검증할 수 없다. 형식적 비교 결과는 다음과 같다.

- `name + period_number`: 유일 후보 0, 후보 없음 10, 복수 후보 0
- `name + grade`: 유일 후보 0, 후보 없음 10, 복수 후보 0
- `name + period_number + grade`: 유일 후보 0, 후보 없음 10, 복수 후보 0
- 10건 모두 이름 단계에서 일치 후보가 없었다.

자동 매칭 전에는 원본 data.go 이름 표기, 기수 숫자 정규화, 시점별 등급 변화, 동명이인, 은퇴선수 포함 여부를 검증해야 한다. 등급은 시점에 따라 변할 수 있으므로 식별키로 사용하면 안 된다.

### robots 및 이용정책

- [robots.txt](https://www.kcycle.or.kr/robots.txt)는 고객 게시판 일부와 스팸 URL 패턴을 제외하고 기본 `Allow: /`를 선언하며 `/racer/info`를 금지하지 않는다.
- [자료무단복제금지](https://www.kcycle.or.kr/customerplaza/terms/reproduction)는 승인 없는 사이트 자료의 상업적 무단 복제·전송·배포를 금지한다.
- 따라서 현재 구현은 최대 10건의 저빈도 개발 preview로 제한한다. 정기·전체·상업적 수집 전에는 KCYCLE 측 이용 승인과 재배포 범위를 별도로 확인해야 한다.

## 10) KCYCLE 외부 선수 staging 저장 정책

- KCYCLE preview CSV는 `external_players` staging 테이블에만 가져온다.
- KCYCLE `racerNo`는 `external_id` 문자열 원문으로 보존하며 앞자리 0을 유지한다.
- 식별 unique 기준은 `(source, external_id)`이다.
- `players` 테이블과 자동 연결하지 않는다.
- 이름+기수 결합값, hash, 임의 번호를 식별자로 생성하지 않는다.
- data.go 통계와 자동 결합하지 않는다.
- CSV CLI는 명시적인 `--dry-run` 또는 `--apply` 선택과 대상 `--database-url`을 요구한다.
- 관리자 API는 staging 조회만 제공하며 생성·수정·삭제는 제공하지 않는다.

### 법적·운영 제한

- live 수집 검증은 최대 10명 preview로 제한한다.
- preview 데이터는 개발 검증 용도다.
- 전체·정기·상용 수집은 KCYCLE 이용 승인과 재배포 범위 확인 전까지 보류한다.
- 선수 사진은 저장하지 않는다.
- 생년월일은 수집하거나 staging에 저장하지 않는다.
- `external_id`는 공식 상세 페이지 식별자를 원형 보존하기 위한 값이다.

## 11) data.go 선수 성적 통계 staging 및 후보 매칭 정책

- data.go 경륜 선수정보 응답은 선수 마스터가 아니라 연도별 선수 성적 통계로 취급한다.
- 실제 응답에는 안정적인 선수 고유번호가 없으므로 `players` 또는 `external_players`에 직접 적재하지 않는다.
- 통계는 `external_player_statistics`에 저장하며 `players`/`external_players` FK를 두지 않는다.
- 내부 자동 증가 PK 외에 이름+기수 결합 ID, hash, 가짜 `player_number`를 생성하지 않는다.

### 실제 XML 매핑

- `stnd_yr` → `standard_year`
- `racer_nm` → `racer_name`
- `period_no` → `period_number`
- `racer_grd_cd` → `grade`
- `run_cnt`, `run_day_tcnt` → 출전 횟수/일수
- `rank1_tcnt`~`rank9_tcnt` → 순위별 횟수
- `elim_tcnt` → 탈락 횟수
- `win_rate`, `high_rate`, `high_3_rate` → 승률 통계
- 누락 통계값은 NULL이며 명시적 0만 0으로 저장한다.

### 잠정 중복 정책

- 잠정키: `(source, standard_year, racer_name, period_number)`
- 2026-07-13 축약 live-style fixture 10행에서는 잠정키 중복이 0건이었다.
- 현재 셸에는 서비스 키가 없어 live 10행을 재호출하지 못했으므로 DB unique 제약은 추가하지 않았다.
- import 서비스가 잠정키로 기존 행을 조회하고 created/updated/skipped를 판정한다.
- period_number 누락 행은 staging에 저장할 수 있지만 후보 매칭에서는 `MISSING_PERIOD_NUMBER`로 분리한다.

### 후보 매칭

- KCYCLE `external_players`와 이름 정확 일치 + 기수 정확 일치만 사용한다.
- fuzzy matching, 한글 이름 변형, 등급 기반 식별은 사용하지 않는다.
- 등급은 `GRADE_MISMATCH` 보조 검증에만 사용하며 시점별로 달라질 수 있어 식별키가 아니다.
- 상태: `UNIQUE_CANDIDATE`, `NO_CANDIDATE`, `MULTIPLE_CANDIDATES`, `MISSING_PERIOD_NUMBER`, `GRADE_MISMATCH`.
- 후보 결과는 읽기 전용 리포트이며 FK 저장, 자동 승인, `players` 연결을 하지 않는다.

### 운영 제한

- live 검증은 서비스 키가 있을 때만 최대 10행·1페이지로 제한한다.
- 운영 DB에는 0006 migration이나 통계 데이터를 자동 적용하지 않는다.
- 서비스 키, 전체 요청 URL, 원본 XML은 로그·오류·리포트에 기록하지 않는다.

## 12) 예측 MVP용 과거 경주 데이터 검토

- 현재 운영 SQLite 데이터는 `races=3`, `entries=15`, `results=8`, `players=13` 수준이라 실제 예측 모델 학습에는 부족하다.
- 완료 상태 경주는 1건뿐이고, 결과가 연결된 출전 행은 8행이다. 결과 누락 출전 행은 7행이다.
- 과거 경주 수집 후보는 다음 공식 출처다.
  - data.go.kr 경륜 `출주표_GW`: <https://www.data.go.kr/data/15107830/openapi.do>
  - data.go.kr 경륜 `경주결과_GW`: <https://www.data.go.kr/data/15107816/openapi.do>
  - KCYCLE 확정출주표: <https://www.kcycle.or.kr/race/card/decision>
  - KCYCLE 통합경주결과: <https://www.kcycle.or.kr/race/result/general>
- 예측 학습 행은 “한 경주의 한 출전 선수” 1행으로 정의한다.
- 경주 전 알 수 없는 현재 경기 최종 순위, 현재 경기 이후 갱신된 누적 통계, 미래 경기 결과는 feature로 사용하지 않는다.
- 공식 출처에서 안정적인 선수 식별자가 확인되지 않는 데이터는 이름, 이름+기수, hash 등으로 가짜 ID를 만들지 않고 preview 또는 staging 구조에만 둔다.
- 초기 학습 readiness 기준은 완료 경주 500건, 유효 출전 행 3,000건, 선수당 과거 경기 중앙값 5건, `result_rank` 누락률 5% 미만이다.
- 기준 미달 시 모델 학습과 예측 확률 생성을 중단하고 `INSUFFICIENT_TRAINING_DATA`로 보고한다.

### data.go.kr 출주표/경주결과 API 명세 확인

2026-07-14 기준 공공데이터포털 OpenAPI 상세 페이지의 Swagger JSON에서 다음을 확인했다.

#### 경륜-출주표_GW

- catalog: <https://www.data.go.kr/data/15107830/openapi.do>
- gateway endpoint: `https://apis.data.go.kr/B551014/SRVC_OD_API_CRA_RACE_ORGAN/TODZ_API_CRA_RACE_ORGAN_I`
- method: `GET`
- format: JSON/XML
- pagination: `pageNo`, `numOfRows`
- required query: `serviceKey`, `resultType`
- optional query: `meet_nm`, `stnd_yr`, `week_tcnt`
- 주요 응답 필드:
  - `meet_nm`: 경륜장명
  - `stnd_yr`: 경기연도
  - `race_ymd`: 경주일자
  - `race_no`: 경주번호
  - `back_no`: 등번호/출전 번호
  - `racer_nm`: 선수명
  - `period_no`: 기수번호
  - `racer_grd_cd`: 등급코드
  - `dptre_tm`: 출발시각
- 문서상 별도 공식 race ID는 확인되지 않았다.
- 문서상 별도 공식 player/racer ID는 확인되지 않았다.
- `back_no`는 출전 번호이며 선수 고유번호로 사용하지 않는다.

#### 경륜-경주결과_GW

- catalog: <https://www.data.go.kr/data/15107816/openapi.do>
- gateway endpoint: `https://apis.data.go.kr/B551014/SRVC_TODZ_CRA_RACE_RESULT/TODZ_API_CRA_RACE_RESULT`
- method: `GET`
- format: JSON/XML
- pagination: `pageNo`, `numOfRows`
- required query: `serviceKey`, `resultType`, `stnd_yr`, `meet_nm`, `week_tcnt`, `day_tcnt`, `race_no`
- 주요 응답 필드:
  - `stnd_yr`: 경기연도
  - `race_ymd`: 경주일자
  - `meet_nm`: 경륜장명
  - `race_no`: 경주번호
  - `rank1`, `rank2`, `rank3`: 1~3위
  - `week_tcnt`: 등록회차수
  - `day_tcnt`: 경기회차수
  - `row_num`: 순번
- 문서상 결과는 1~3위 중심이며 전체 출전 선수별 순위/실격/기권 세부 필드는 확인되지 않았다.
- 문서상 별도 공식 race ID와 player/racer ID는 확인되지 않았다.
- 2026-07-14 live 응답에서 `rank1`, `rank2`, `rank3` 값은 `2***`, `6***`, `5***`처럼 출전번호와 선수명이 결합된 형식이었다.
- `race_ymd`는 `0103`처럼 `MMDD` 형태로 왔고 `stnd_yr=2025`와 결합해 `2025-01-03`으로 정규화한다.
- 원본 result item 1건에서 선수 결과 3건이 정규화된다.
- 4위 이후 필드는 확인되지 않았으므로 결과 API는 `PARTIAL_TOP3_RESULT_SOURCE`로 취급한다.

### 2026-07-14 preview 실행 상태

- 현재 셸에 `DATA_GO_KR_SERVICE_KEY`가 없어 live 호출은 실행하지 않았다.
- `scripts/collect_race_history.py --date-from 2025-01-01 --date-to 2025-01-31 --max-races 10 --dry-run --inspect`
  - `live_called=false`
  - `lineup_item_count=0`
  - `result_item_count=0`
  - issue: `SERVICE_KEY_MISSING`
- 서비스 키가 준비되면 결과 API 특성상 단순 날짜 범위만으로는 결과를 조회할 수 없고, 최소 `--meet-name`, `--year`, `--week-count`, `--day-count`, `--race-number`를 지정해야 한다.

### 식별자 판정

| 대상 | 공식 식별자 | 존재 여부 | 안정성 | 사용 가능 여부 |
| --- | --- | --- | --- | --- |
| race | 문서상 별도 ID 없음. `race_ymd + meet_nm + week_tcnt/day_tcnt + race_no` 자연키 후보만 있음 | `NO_STABLE_IDENTIFIER` | 자연키 후보라 cross-source 검증 필요 | 운영 PK로 직접 사용 금지 |
| player | 출주표/결과 문서상 별도 `racerNo` 없음 | `NO_STABLE_IDENTIFIER` | 이름/기수/등번호는 불충분 | 운영 선수 ID 생성 금지 |
| entry | `back_no`/결과 rank 값의 번호 | `CROSS_SOURCE_MAPPING_REQUIRED` | 경주 내 출전 번호일 가능성이 높음 | 선수 고유번호로 사용 금지 |

## 13) 비배팅 경주 기록 분석 MVP staging

- 경주 기록은 운영 `races`, `entries`, `results`, `players`에 직접 넣지 않고 다음 staging 테이블에 저장한다.
  - `external_races`
  - `external_race_entries`
  - `external_race_results`
- 경주 자연키는 `(source, standard_year, meet_name, week_count, day_count, race_number)`이다.
- 자연키는 공식 ID가 아니며 source 내부 연결용 후보로만 사용한다.
- 출주표 `back_no`는 경주 내 출전 번호로 보존하고 선수 고유번호로 사용하지 않는다.
- 선수 분석은 `player_name + period_number` provisional key를 사용하되 공식 선수 ID라고 표현하지 않는다.
- 제공 API는 기록 분석과 데이터 품질 조회만 수행하며 배당·베팅·예측값을 반환하지 않는다.
