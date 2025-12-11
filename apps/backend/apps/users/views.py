from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.utils import timezone

from .models import (
    User, LoginHistory, SearchHistory, ListingViewHistory,
    Wishlist, WishlistHistory, PreferenceSurvey
)
from .serializers import (
    UserSerializer, GoogleLoginSerializer, PreferenceSurveySerializer,
    SearchHistorySerializer, ListingViewHistorySerializer,
    WishlistSerializer, LoginHistorySerializer, EmailPasswordLoginSerializer
)


class GoogleLoginView(APIView):
    """
    구글 로그인/회원가입 처리
    - NextAuth에서 구글 인증 후 백엔드로 전송
    - 신규 사용자면 생성, 기존 사용자면 로그인
    - JWT 토큰 발급
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        name = serializer.validated_data['name']
        image = serializer.validated_data.get('image', '')
        google_id = serializer.validated_data['googleId']

        # 사용자 조회 또는 생성
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'google_id': google_id,
                'profile_image': image,
                'first_name': name.split()[0] if name else '',
                'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                'is_new_user': True,
            }
        )

        if created:
            user.set_unusable_password()
            user.save()
        else:
            # 기존 사용자 정보 업데이트
            user.profile_image = image
            user.google_id = google_id
            user.save()

        # 로그인 이력 저장
        LoginHistory.objects.create(
            user=user,
            action='login',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # JWT 토큰 발급
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'isNewUser': user.is_new_user,
            'surveyCompleted': user.survey_completed,
        }, status=status.HTTP_200_OK)

    def get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CurrentUserView(APIView):
    """현재 로그인한 사용자 정보 조회/삭제"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def delete(self, request):
        user_email = request.user.email
        request.user.delete()
        return Response(
            {
                'message': '계정이 삭제되었습니다.',
                'email': user_email
            },
            status=status.HTTP_200_OK
        )


class UpdateUserView(APIView):
    """사용자 정보 수정"""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PreferenceSurveyView(APIView):
    """선호도 설문 조회/제출"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """사용자가 마지막으로 제출한 설문 정보 조회"""
        latest_survey = PreferenceSurvey.objects.filter(
            user=request.user
        ).order_by('-created_at').first()

        data = None
        priorities = {}
        if latest_survey:
            data = PreferenceSurveySerializer(latest_survey).data
            priorities = latest_survey.priorities

        return Response({
            'survey': data,
            'priorities': priorities,
            'job': request.user.job_type,
            'surveyCompleted': request.user.survey_completed,
        })

    def post(self, request):
        # 설문 저장
        survey = PreferenceSurvey.objects.create(
            user=request.user,
            priorities=request.data.get('priorities', {})
        )

        # 사용자 상태 업데이트
        user = request.user
        user.survey_completed = True
        user.is_new_user = False
        user.job_type = request.data.get('job', '')
        user.save()

        return Response({
            'message': '선호도 설문이 완료되었습니다.',
            'survey': PreferenceSurveySerializer(survey).data,
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class SearchHistoryView(APIView):
    """검색 이력 조회/생성"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """최근 검색 이력 20개 조회"""
        histories = SearchHistory.objects.filter(user=request.user)[:20]
        serializer = SearchHistorySerializer(histories, many=True)
        return Response(serializer.data)

    def post(self, request):
        """검색 이력 저장"""
        history = SearchHistory.objects.create(
            user=request.user,
            search_conditions=request.data.get('search_conditions', {}),
            result_count=request.data.get('result_count', 0)
        )
        return Response(
            SearchHistorySerializer(history).data,
            status=status.HTTP_201_CREATED
        )


class ListingViewHistoryView(APIView):
    """매물 조회 이력 저장"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """매물 조회 이력 저장"""
        history = ListingViewHistory.objects.create(
            user=request.user,
            listing_id=request.data.get('listing_id'),
            view_duration=request.data.get('view_duration'),
            scroll_depth=request.data.get('scroll_depth')
        )
        return Response(
            ListingViewHistorySerializer(history).data,
            status=status.HTTP_201_CREATED
        )


class WishlistView(APIView):
    """찜 목록 조회/추가"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """찜 목록 조회"""
        wishlists = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(wishlists, many=True)
        return Response(serializer.data)

    def post(self, request):
        """찜 추가"""
        listing_id = request.data.get('listing_id')

        # 찜 추가 (이미 있으면 가져오기)
        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            listing_id=listing_id,
            defaults={'memo': request.data.get('memo', '')}
        )

        # 찜 이력 저장
        if created:
            WishlistHistory.objects.create(
                user=request.user,
                listing_id=listing_id,
                action='add'
            )

        return Response(
            WishlistSerializer(wishlist).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class WishlistDetailView(APIView):
    """찜 목록 개별 삭제"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, listing_id):
        """찜 삭제"""
        try:
            wishlist = Wishlist.objects.get(user=request.user, listing_id=listing_id)
            wishlist.delete()

            # 찜 삭제 이력 저장
            WishlistHistory.objects.create(
                user=request.user,
                listing_id=listing_id,
                action='remove'
            )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Wishlist.DoesNotExist:
            return Response(
                {'error': '찜 목록에 없는 매물입니다.'},
                status=status.HTTP_404_NOT_FOUND
            )


class LogoutView(APIView):
    """로그아웃"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 로그아웃 이력 저장
        LoginHistory.objects.create(
            user=request.user,
            action='logout',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # TODO: JWT 토큰 블랙리스트 처리 (Redis 사용)

        return Response({'message': '로그아웃되었습니다.'})

    def get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class EmailPasswordLoginView(APIView):
    """이메일/비밀번호 로그인"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailPasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request=request, username=email, password=password)
        bypass_password = False

        if user is None:
            user_obj = User.objects.filter(email=email).first()
            if user_obj and user_obj.google_id and not user_obj.has_usable_password():
                user = user_obj
                bypass_password = True
            else:
                return Response(
                    {'detail': '이메일 또는 비밀번호가 올바르지 않습니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        LoginHistory.objects.create(
            user=user,
            action='login',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'isNewUser': user.is_new_user,
            'surveyCompleted': user.survey_completed,
        })

    def get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
