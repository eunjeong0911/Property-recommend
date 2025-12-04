@echo off
echo ======================================
echo 챗봇 테스트
echo ======================================
echo.

echo 1. RAG 서비스 헬스체크...
echo --------------------------------------
curl -s http://localhost:8001/health
echo.
echo.

echo 2. 챗봇 질문 테스트...
echo --------------------------------------
echo.

echo 질문 1: 홍대입구역 근처 매물 추천해줘
curl -X POST http://localhost:8001/query -H "Content-Type: application/json" -d "{\"question\": \"홍대입구역 근처 매물 추천해줘\"}"
echo.
echo.

echo 질문 2: 강남역 주변 원룸 찾아줘
curl -X POST http://localhost:8001/query -H "Content-Type: application/json" -d "{\"question\": \"강남역 주변 원룸 찾아줘\"}"
echo.
echo.

echo ======================================
echo 테스트 완료!
echo ======================================
echo.
echo 브라우저에서 확인:
echo - 프론트엔드: http://localhost:3000
echo - 백엔드 Admin: http://localhost:8000/admin/
echo - Neo4j Browser: http://localhost:7474
echo.
pause
