# 아키텍처 문서

## 시스템 구성

### Backend (Django)
- 매물 CRUD API
- 유저 로그 수집
- 추천 결과 제공

### RAG System (LangGraph)
- 매물 Q&A
- 상담형 대화

### Recommendation Models
- 신뢰도 평가 모델
- 시세 평가 모델
- 유저 로그 기반 추천

### Frontend (React)
- 검색/필터 UI
- 매물 상세
- 추천 결과 표시
