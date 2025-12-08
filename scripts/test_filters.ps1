# 필터링 테스트 스크립트

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "매물 필터링 API 테스트" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000/api/listings/lands/"

# 1. 전체 매물 수
Write-Host "[1] 전체 매물 수 확인" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri $baseUrl -Method Get
    $total = if ($response.results) { $response.results.Count } else { $response.Count }
    Write-Host "✓ 전체 매물: $total 개`n" -ForegroundColor Green
} catch {
    Write-Host "✗ API 연결 실패: $_`n" -ForegroundColor Red
    exit 1
}

# 2. 월세 필터
Write-Host "[2] 월세 필터 테스트" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "${baseUrl}?deal_type=월세" -Method Get
    $count = if ($response.results) { $response.results.Count } else { $response.Count }
    Write-Host "✓ 월세 매물: $count 개" -ForegroundColor Green
    if ($count -gt 0) {
        $sample = if ($response.results) { $response.results[0] } else { $response[0] }
        Write-Host "  샘플: ID=$($sample.id), 가격=$($sample.price), 유형=$($sample.transaction_type)`n" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ 월세 필터 실패: $_`n" -ForegroundColor Red
}

# 3. 전세 필터
Write-Host "[3] 전세 필터 테스트" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "${baseUrl}?deal_type=전세" -Method Get
    $count = if ($response.results) { $response.results.Count } else { $response.Count }
    Write-Host "✓ 전세 매물: $count 개" -ForegroundColor Green
    if ($count -gt 0) {
        $sample = if ($response.results) { $response.results[0] } else { $response[0] }
        Write-Host "  샘플: ID=$($sample.id), 가격=$($sample.price), 유형=$($sample.transaction_type)`n" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ 전세 필터 실패: $_`n" -ForegroundColor Red
}

# 4. 매매 필터
Write-Host "[4] 매매 필터 테스트" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "${baseUrl}?deal_type=매매" -Method Get
    $count = if ($response.results) { $response.results.Count } else { $response.Count }
    Write-Host "✓ 매매 매물: $count 개" -ForegroundColor Green
    if ($count -gt 0) {
        $sample = if ($response.results) { $response.results[0] } else { $response[0] }
        Write-Host "  샘플: ID=$($sample.id), 가격=$($sample.price), 유형=$($sample.transaction_type)`n" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ 매매 필터 실패: $_`n" -ForegroundColor Red
}

# 5. 단기임대 필터
Write-Host "[5] 단기임대 필터 테스트" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "${baseUrl}?deal_type=단기임대" -Method Get
    $count = if ($response.results) { $response.results.Count } else { $response.Count }
    Write-Host "✓ 단기임대 매물: $count 개" -ForegroundColor Green
    if ($count -gt 0) {
        $sample = if ($response.results) { $response.results[0] } else { $response[0] }
        Write-Host "  샘플: ID=$($sample.id), 가격=$($sample.price), 유형=$($sample.transaction_type)`n" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ 단기임대 매물이 없습니다. 백엔드 재시작이 필요할 수 있습니다.`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ 단기임대 필터 실패: $_`n" -ForegroundColor Red
}

# 6. 미분류 필터
Write-Host "[6] 미분류 필터 테스트" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "${baseUrl}?deal_type=미분류" -Method Get
    $count = if ($response.results) { $response.results.Count } else { $response.Count }
    Write-Host "✓ 미분류 매물: $count 개" -ForegroundColor Green
    if ($count -gt 0) {
        $sample = if ($response.results) { $response.results[0] } else { $response[0] }
        Write-Host "  샘플: ID=$($sample.id), 가격=$($sample.price), 유형=$($sample.transaction_type)`n" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ 미분류 매물이 없습니다. 백엔드 재시작이 필요할 수 있습니다.`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ 미분류 필터 실패: $_`n" -ForegroundColor Red
}

# 7. 복합 필터 (강남구 + 월세)
Write-Host "[7] 복합 필터 테스트 (강남구 + 월세)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "${baseUrl}?address=강남구&deal_type=월세" -Method Get
    $count = if ($response.results) { $response.results.Count } else { $response.Count }
    Write-Host "✓ 강남구 월세 매물: $count 개" -ForegroundColor Green
    if ($count -gt 0) {
        $sample = if ($response.results) { $response.results[0] } else { $response[0] }
        Write-Host "  샘플: ID=$($sample.id), 가격=$($sample.price), 주소=$($sample.address)`n" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ 복합 필터 실패: $_`n" -ForegroundColor Red
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "테스트 완료" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "⚠ 단기임대나 미분류 필터가 작동하지 않으면:" -ForegroundColor Yellow
Write-Host "   1. 백엔드를 재시작하세요: cd apps\backend; uv run python manage.py runserver" -ForegroundColor Gray
Write-Host "   2. 코드 변경사항이 적용되었는지 확인하세요`n" -ForegroundColor Gray
