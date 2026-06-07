# Process Window Prototype

Vue3와 FastAPI로 만든 Process Window 분석 프로토타입입니다.

이 저장소는 초보 팀원이 코드 흐름을 빠르게 따라갈 수 있도록 파일 구조를 얕게 유지했습니다. 실제 DB, CatBoost/SHAP 운영 모델, 인증, 배포 자동화는 이후 단계로 남겨두고, 현재 버전은 합성 데이터 기반으로 화면과 분석 흐름을 검증하는 데 집중합니다.

## 주요 기능

- 제품, L1 Feature, L3 Item 선택
- L3별 L1 우선순위 랭킹
- Window 분석 차트
- 월 생산량과 chip 단가를 반영한 월 순효과 Trade-off 분석
- Multi L1 vs L3 교호작용 heatmap과 hotspot 요약
- FastAPI API와 Vue3 화면 분리

## Trade-off 산식

Trade-off 차트의 월 순효과는 아래 기준으로 계산합니다.

```text
월 순효과 = 불량 절감액 - 생산 손실액
불량 절감액 = (baseline bad chip 가치 - SPEC 적용 후 residual bad chip 가치)
생산 손실액 = 월 생산량 * production_loss * chip 단가
```

현재 프로토타입은 wafer 기준 production loss와 chip 기준 defect ppm을 함께 보여주기 때문에, 실제 운영 적용 전에는 재무팀/공정팀과 denominator를 다시 확인해야 합니다.

## 폴더 구조

```text
backend/
  app/
    analysis/          # 순수 Python 분석 로직
    main.py            # FastAPI 엔드포인트
    repository.py      # 데이터 접근 계층
    schemas.py         # 요청/응답 모델
    synthetic_data.py  # 합성 wafer 데이터 생성
  tests/               # unittest 기반 테스트
  run_analysis_demo.py # API 없이 분석 로직만 실행하는 데모

frontend/
  src/
    components/        # 화면 영역별 Vue 컴포넌트
    App.vue            # 전체 레이아웃과 상태 관리
    api.ts             # FastAPI 호출 함수
    types.ts           # 화면에서 쓰는 타입

frontend_static/
  index.html           # npm 없이 확인 가능한 정적 fallback 화면
```

## 실행 방법

백엔드와 프론트엔드를 각각 다른 터미널에서 실행합니다.

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

확인:

```bash
curl http://127.0.0.1:8010/api/health
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

브라우저에서 아래 주소를 엽니다.

```text
http://127.0.0.1:5174/
```

## 검증 명령

백엔드 테스트:

```bash
cd backend
PYTHONPATH=$PWD python -m unittest discover -s tests
```

프론트엔드 빌드와 타입 체크:

```bash
cd frontend
npm run typecheck
npm run build
```

## API 목록

- `GET /api/health`
- `GET /api/catalog`
- `POST /api/rank`
- `POST /api/analyze/single`
- `POST /api/analyze/interaction`

## 코드 읽는 순서

처음 프로젝트를 보는 팀원은 아래 순서로 읽으면 전체 흐름을 가장 쉽게 따라갈 수 있습니다.

1. `backend/app/synthetic_data.py`
2. `backend/app/repository.py`
3. `backend/app/analysis/ranking.py`
4. `backend/app/analysis/window_1d.py`
5. `backend/app/analysis/interaction_2d.py`
6. `backend/app/main.py`
7. `frontend/src/api.ts`
8. `frontend/src/App.vue`

## 현재 한계

- 현재 데이터는 합성 데이터입니다.
- CatBoost/SHAP 기반 랭킹은 운영 데이터 연결 후 확장 예정입니다.
- SPEC, 공정 조건, 장비/PM 이력은 실제 DB 스키마 확정 후 연결해야 합니다.
- 화면은 프로토타입이며, 권한 관리와 운영 배포 설정은 포함하지 않았습니다.
