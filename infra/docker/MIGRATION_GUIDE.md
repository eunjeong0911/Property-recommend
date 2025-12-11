# Requirements 통합 마이그레이션 가이드

## 변경 사항

모든 Python 의존성 파일이 `infra/docker/` 폴더로 통합되었습니다.

### 이전 구조
```
requirements.txt
apps/backend/requirements.txt
apps/rag/requirements.txt
apps/reco/requirements.txt
analytics/requirements.txt
dataCrawling/피터팬 매물 데이터/requirements.txt
```

### 새로운 구조
```
infra/docker/
├── requirements.txt          # 🎯 모든 의존성 통합!
├── backend.Dockerfile
├── rag.Dockerfile
├── reco.Dockerfile
├── analytics.Dockerfile
├── scripts.Dockerfile
└── crawling.Dockerfile
```

**모든 Python 패키지가 하나의 `requirements.txt` 파일로 통합되었습니다.**

## 사용 방법

### 기존 방식 (더 이상 필요 없음)
```bash
# ❌ 이제 필요 없습니다
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 새로운 방식
```bash
# ✅ Docker만 사용하면 됩니다
docker-compose up
```

## 서비스별 실행

### 메인 서비스 (항상 실행)
```bash
docker-compose up
```
- postgres, neo4j, redis
- backend, rag, reco, frontend

### Analytics (선택적)
```bash
docker-compose --profile analytics up analytics
```
Jupyter Notebook: http://localhost:8888

### Scripts (선택적)
```bash
docker-compose --profile scripts run scripts python your_script.py
```

### Crawling (선택적)
```bash
docker-compose --profile crawling run crawling python your_crawler.py
```

## 의존성 추가 방법

1. `infra/docker/requirements.txt` 파일 수정
2. Docker 이미지 재빌드:
   ```bash
   docker-compose build <service-name>
   # 또는 모든 서비스
   docker-compose build
   ```
3. 서비스 재시작:
   ```bash
   docker-compose up -d <service-name>
   ```

## 장점

✅ **가상환경 불필요**: venv 설치/활성화 과정 제거  
✅ **중앙 관리**: 모든 의존성이 한 곳에서 관리됨  
✅ **일관성**: 모든 개발자가 동일한 환경 사용  
✅ **격리**: 각 서비스가 독립적인 컨테이너에서 실행  
✅ **재현성**: Docker 이미지로 환경 완벽 재현  

## 문제 해결

### 의존성이 설치되지 않는 경우
```bash
# 캐시 없이 재빌드
docker-compose build --no-cache <service-name>
```

### 컨테이너 내부에서 명령 실행
```bash
docker-compose exec <service-name> bash
```

### 로그 확인
```bash
docker-compose logs <service-name>
```
