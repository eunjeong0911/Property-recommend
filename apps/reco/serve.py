from fastapi import FastAPI

app = FastAPI(title="Recommendation Service")


@app.get("/health")
async def health():
    """Health check endpoint for ALB/ECS"""
    return {"status": "healthy", "service": "reco"}


@app.post("/recommend")
async def recommend(user_id: int):
    # TODO: Implement recommendation logic
    return {"recommendations": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
