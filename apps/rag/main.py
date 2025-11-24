from fastapi import FastAPI
from graphs.listing_rag_graph import create_rag_graph

app = FastAPI(title="RAG System")

graph = create_rag_graph()

@app.post("/query")
async def query(question: str):
    result = await graph.ainvoke({"question": question})
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
