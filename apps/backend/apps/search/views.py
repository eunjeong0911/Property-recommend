from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import UserSearchLog
import logging

logger = logging.getLogger(__name__)

class UserSearchLogView(APIView):
    """
    사용자 검색 로그 저장 API
    POST /api/search/log
    """
    permission_classes = [AllowAny]  # 내부 서비스(RAG) 호출 허용

    def post(self, request):
        try:
            data = request.data
            
            # 필수 필드 확인
            if 'session_id' not in data or 'query' not in data:
                return Response(
                    {"error": "Missing required fields (session_id, query)"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 로그 생성
            log = UserSearchLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_id=data.get('session_id'),
                query=data.get('query'),
                filters=data.get('filters', {}),
                search_strategy=data.get('search_strategy', 'rag'),
                result_count=data.get('result_count', 0),
                search_duration_ms=data.get('search_duration_ms', 0)
            )

            return Response(
                {"status": "success", "log_id": log.id}, 
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Failed to save search log: {str(e)}")
            return Response(
                {"error": "Internal Server Error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
