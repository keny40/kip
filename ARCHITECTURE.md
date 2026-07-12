# Architecture

## 목표

KIP는 경륜 데이터를 수집, 저장, 분석, 예측, 시각화하는 SaaS 플랫폼입니다.

## 레이어

### Frontend

- Flutter Web
- Flutter Android
- Flutter iOS
- 화면, 위젯, 상태관리, 라우팅, API 호출 계층으로 분리

### Backend

- FastAPI
- Python 3.12
- API, 도메인 서비스, 저장소, 워커, 수집기, 분석, 대시보드, 알림, 결제, 관리자 기능으로 분리

### Data

- PostgreSQL 16
- SQLAlchemy 2.x
- Alembic

### Infra

- Redis
- Celery
- Local Storage

## 현재 스켈레톤 원칙

- 실제 AI 로직은 넣지 않음
- 실제 크롤링은 넣지 않음
- 실제 예측은 넣지 않음
- 각 모듈은 향후 확장을 위한 최소 구조만 제공
