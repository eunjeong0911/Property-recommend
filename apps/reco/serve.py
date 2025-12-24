"""
Recommendation Service API Server

파이프라인에서 생성된 추천 결과를 제공하는 서비스
- 매일 정해진 시간에 모델 파이프라인이 실행되어 CSV 생성
- 이 서비스는 생성된 결과를 로드하여 제공
"""
import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger


# =============================================================================
# JSON Logging Configuration (Requirements 5.2, 5.3)
# =============================================================================
def setup_json_logging():
    """Configure JSON-formatted logging for CloudWatch Logs compatibility."""
    log_format = os.getenv("LOG_FORMAT", "json")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    handler = logging.StreamHandler(sys.stdout)
    
    if log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={"levelname": "level", "asctime": "timestamp"},
            timestamp=True
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


logger = setup_json_logging()

app = FastAPI(title="Recommendation Service")


# =============================================================================
# CORS Configuration
# =============================================================================
_cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
if _cors_origins_env:
    cors_origins = [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]
else:
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# =============================================================================
# Health Check Endpoints
# =============================================================================
@app.get("/health")
async def health():
    """Health check endpoint for ALB/ECS"""
    return {"status": "healthy", "service": "reco"}


@app.get("/ready")
async def ready():
    """Readiness check - verify model files are available"""
    # TODO: 실제 모델 파일 존재 여부 확인 로직 추가
    return {"status": "ready", "service": "reco"}


# =============================================================================
# Recommendation Endpoints
# =============================================================================
@app.post("/recommend")
async def recommend(user_id: int):
    """
    사용자 추천 결과 반환
    
    파이프라인에서 생성된 CSV 결과를 로드하여 반환
    """
    logger.info("Recommendation request received", extra={"user_id": user_id})
    
    # TODO: 파이프라인에서 생성된 CSV 결과 로드 로직 구현
    # 예: pandas.read_csv("results/recommendations.csv")
    
    return {"recommendations": [], "user_id": user_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
