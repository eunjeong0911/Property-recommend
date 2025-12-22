"""OpenAI Embedding Service (Singleton Pattern)"""
import os
from typing import List, Optional

from openai import OpenAI


class EmbeddingService:
    """OpenAI 임베딩 서비스 (싱글톤)
    
    text-embedding-3-large 모델을 사용하여 3072차원 벡터를 생성합니다.
    """
    
    _instance: Optional['EmbeddingService'] = None
    _client: Optional[OpenAI] = None
    
    MODEL = "text-embedding-3-large"
    DIMENSIONS = 3072
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def client(self) -> OpenAI:
        """OpenAI 클라이언트 (lazy initialization)"""
        if self._client is None:
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client
    
    def embed_text(self, text: str) -> List[float]:
        """단일 텍스트 임베딩
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            3072차원 임베딩 벡터
        """
        response = self.client.embeddings.create(
            model=self.MODEL,
            input=text,
            dimensions=self.DIMENSIONS
        )
        return response.data[0].embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """배치 텍스트 임베딩 (최대 100개)
        
        Args:
            texts: 임베딩할 텍스트 리스트
            
        Returns:
            3072차원 임베딩 벡터 리스트
        """
        response = self.client.embeddings.create(
            model=self.MODEL,
            input=texts,
            dimensions=self.DIMENSIONS
        )
        return [item.embedding for item in response.data]
    
    @classmethod
    def get_instance(cls) -> 'EmbeddingService':
        """싱글톤 인스턴스 반환"""
        return cls()
