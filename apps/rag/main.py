from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graphs.listing_rag_graph import create_rag_graph
from pydantic import BaseModel

app = FastAPI(title="RAG System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = create_rag_graph()

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query(request: QueryRequest):
    result = await graph.ainvoke({"question": request.question})
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
