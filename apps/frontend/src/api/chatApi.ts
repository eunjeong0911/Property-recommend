export const sendChatQuestion = async (question: string, sessionId?: string): Promise<string> => {
  try {
    // RAG 서비스 직접 호출 (로컬: localhost:8001, 프로덕션: Backend Proxy)
    const ragUrl = process.env.NEXT_PUBLIC_RAG_URL || 'http://localhost:8001';
    const response = await fetch(`${ragUrl}/query`, {
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
