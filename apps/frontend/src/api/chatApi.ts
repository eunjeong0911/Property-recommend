export const sendChatQuestion = async (question: string, sessionId?: string): Promise<string> => {
  try {
    // Use relative path to leverage Next.js rewrites (proxies to RAG service)
    const response = await fetch('/rag/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        session_id: sessionId || undefined  // 세션 ID 전달
      }),
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const data = await response.json();
    // The RAG service returns { "answer": "..." } or similar structure based on the graph output
    // Based on generate_node.py, it returns state["answer"]
    // The main.py returns the result of graph.ainvoke, which is the final state.
    // So data will be the full state object. We need to extract 'answer'.
    return data.answer || "죄송합니다. 답변을 찾을 수 없습니다.";
  } catch (error) {
    console.error('Error sending chat question:', error);
    throw error;
  }
};
