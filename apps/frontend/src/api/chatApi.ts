// RAG 서비스 응답 인터페이스
export interface ChatResponse {
  answer: string;
  filter_info?: {
    summary: string;
    details: {
      location?: string;
      facilities?: string[];
      deal_type?: string;
      building_type?: string;
      max_deposit?: string;
      max_rent?: string;
      style?: string[];
    };
    search_strategy?: string;
  };
  properties?: any[];
  session_id: string;
}

const isProduction = process.env.NODE_ENV === 'production';
const RAG_BASE_URL = isProduction
  ? 'https://goziphouse.com/rag'
  : (process.env.NEXT_PUBLIC_RAG_URL || 'http://localhost:8001');

export const sendChatQuestion = async (question: string, sessionId?: string): Promise<ChatResponse> => {
  try {
    const response = await fetch(`${RAG_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        session_id: sessionId || undefined
      }),
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending chat question:', error);
    throw error;
  }
};
