# 프로젝트 문서

이 폴더에는 프로젝트의 모든 기술 문서가 포함되어 있습니다.

## 📋 목차

### 아키텍처 및 설계
- [architecture.md](./architecture.md) - 전체 시스템 아키텍처
- [erd.md](./erd.md) - 데이터베이스 ERD
- [graph_schema.md](./graph_schema.md) - Neo4j 그래프 스키마
- [폴더구조.md](./폴더구조.md) - 프로젝트 폴더 구조

### API 및 백엔드
- [api_spec.md](./api_spec.md) - API 명세서
- [API_TEST_RESULTS.md](./API_TEST_RESULTS.md) - API 테스트 결과 및 매물 상세정보 DB 연동
- [backend_readme.md](./backend_readme.md) - 백엔드 개발 가이드

### 기능 구현
- [FILTER_FEATURE.md](./FILTER_FEATURE.md) - 매물 필터링 기능 구현 가이드
- [DATA_STATISTICS.md](./DATA_STATISTICS.md) - 매물 데이터 통계 및 분석
- [README_CHATBOT.md](./README_CHATBOT.md) - 챗봇 기능 가이드

### 배포 및 운영
- [DOCKER_DEPLOYMENT_GUIDE.md](./DOCKER_DEPLOYMENT_GUIDE.md) - Docker 배포 가이드
- [neo4j_data_import_guide.md](./neo4j_data_import_guide.md) - Neo4j 데이터 임포트 가이드

### 개발 환경
- [가상환경.md](./가상환경.md) - Python 가상환경 설정
- [구글로그인관련.txt](./구글로그인관련.txt) - Google OAuth 설정

## 🚀 빠른 시작

### 1. 개발 환경 설정
프로젝트 루트의 [START_FOR_DEVELOPER.md](../START_FOR_DEVELOPER.md)를 참고하세요.

### 2. 주요 기능 이해
- **매물 필터링**: [FILTER_FEATURE.md](./FILTER_FEATURE.md)
- **API 연동**: [API_TEST_RESULTS.md](./API_TEST_RESULTS.md)
- **데이터 분석**: [DATA_STATISTICS.md](./DATA_STATISTICS.md)

### 3. 배포
- **Docker 배포**: [DOCKER_DEPLOYMENT_GUIDE.md](./DOCKER_DEPLOYMENT_GUIDE.md)
- **데이터 임포트**: [neo4j_data_import_guide.md](./neo4j_data_import_guide.md)

## 📊 최근 업데이트 (2024-12-08)

### 새로 추가된 문서
1. **API_TEST_RESULTS.md** - 매물 상세정보 DB 연동 완료
   - PostgreSQL 데이터 구조 분석
   - 가격 파싱 로직 (만원 단위)
   - 모든 필드 매핑 완료

2. **FILTER_FEATURE.md** - 매물 필터링 기능 구현
   - 서울 25개 구 필터
   - 거래유형 필터 (매매, 전세, 월세, 단기임대, 미분류)
   - 건물유형 필터
   - 검색 기능

3. **DATA_STATISTICS.md** - 매물 데이터 통계
   - 총 9,914개 매물 분석
   - 거래유형별 분포
   - 지역별 분포
   - 필터 조합별 매물 수

## 🔧 기술 스택

### 백엔드
- Django 4.2
- Django REST Framework
- PostgreSQL (pgvector)
- Neo4j 5.15
- Redis

### 프론트엔드
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS

### AI/ML
- LangChain
- OpenAI API
- 추천 시스템

## 📝 문서 작성 가이드

새로운 문서를 추가할 때는 다음 형식을 따라주세요:

```markdown
# 문서 제목

## 개요
간단한 설명

## 주요 내용
상세 설명

## 예시
코드 예시 또는 사용 방법

## 참고 자료
관련 문서 링크
```

## 🤝 기여하기

문서 개선이나 오류 수정은 언제든 환영합니다!

1. 문서 수정
2. 이 README.md 업데이트 (필요시)
3. 커밋 및 푸시

## 📞 문의

문서 관련 문의사항은 팀 채널을 통해 연락주세요.
