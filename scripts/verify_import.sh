#!/bin/bash

echo "======================================"
echo "데이터 Import 검증 스크립트"
echo "======================================"
echo ""

echo "1. Neo4j 데이터 확인..."
echo "--------------------------------------"
docker-compose exec -T neo4j cypher-shell -u neo4j -p ${NEO4J_PASSWORD:-neo4j} "MATCH (p:Property) RETURN count(p) as 매물수;" 2>/dev/null || echo "Neo4j 연결 실패"
docker-compose exec -T neo4j cypher-shell -u neo4j -p ${NEO4J_PASSWORD:-neo4j} "MATCH (s:SubwayStation) RETURN count(s) as 지하철역수;" 2>/dev/null || echo "Neo4j 연결 실패"
docker-compose exec -T neo4j cypher-shell -u neo4j -p ${NEO4J_PASSWORD:-neo4j} "MATCH (b:BusStation) RETURN count(b) as 버스정류장수;" 2>/dev/null || echo "Neo4j 연결 실패"
docker-compose exec -T neo4j cypher-shell -u neo4j -p ${NEO4J_PASSWORD:-neo4j} "MATCH ()-[r:NEAR_SUBWAY]->() RETURN count(r) as 지하철연결수;" 2>/dev/null || echo "Neo4j 연결 실패"
echo ""

echo "2. PostgreSQL 데이터 확인..."
echo "--------------------------------------"
docker-compose exec -T postgres psql -U postgres -d realestate -c "SELECT COUNT(*) as 매물수 FROM listings;" 2>/dev/null || echo "PostgreSQL 연결 실패"
echo ""

echo "3. 전체 노드 타입별 개수 (Neo4j)..."
echo "--------------------------------------"
docker-compose exec -T neo4j cypher-shell -u neo4j -p ${NEO4J_PASSWORD:-neo4j} "MATCH (n) RETURN labels(n)[0] as 타입, count(n) as 개수 ORDER BY 개수 DESC;" 2>/dev/null || echo "Neo4j 연결 실패"
echo ""

echo "======================================"
echo "검증 완료!"
echo "======================================"
