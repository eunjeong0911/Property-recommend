# 데이터 임포트 실시간 모니터링 스크립트
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "데이터 임포트 모니터링" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

while ($true) {
    Clear-Host
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "데이터 임포트 실시간 모니터링" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Write-Host "[Neo4j 노드 현황]" -ForegroundColor Yellow
    docker exec -i skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p password123 "MATCH (n) RETURN labels(n)[0] as type, count(n) as count ORDER BY count DESC;"
    
    Write-Host "`n[Neo4j 관계 현황]" -ForegroundColor Yellow
    docker exec -i skn18-final-1team-neo4j-1 cypher-shell -u neo4j -p password123 "MATCH ()-[r]->() RETURN type(r) as relationship, count(r) as count ORDER BY count DESC LIMIT 10;"
    
    Write-Host "`n[PostgreSQL 데이터 현황]" -ForegroundColor Yellow
    docker exec -i skn18-final-1team-postgres-1 psql -U postgres -d realestate -c "SELECT COUNT(*) as total_listings FROM listings;"
    
    Write-Host "`n마지막 업데이트: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host "Ctrl+C를 눌러 종료하세요`n" -ForegroundColor Gray
    
    Start-Sleep -Seconds 5
}
