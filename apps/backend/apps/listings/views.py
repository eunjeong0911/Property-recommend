from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Land
from .serializers import LandSerializer

class LandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Land.objects.all()
    serializer_class = LandSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['land_num', 'address']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 지역 필터 (부분 일치)
        address = self.request.query_params.get('address', None)
        if address:
            queryset = queryset.filter(address__icontains=address)
        
        # 거래유형 필터
        deal_type = self.request.query_params.get('deal_type', None)
        if deal_type:
            if deal_type == '단기임대':
                # 단기임대는 deal_type에 "단기임대"가 포함된 모든 매물
                queryset = queryset.filter(deal_type__icontains='단기임대')
            elif deal_type == '미분류':
                # 미분류는 deal_type이 NULL이거나 빈 문자열인 매물
                from django.db.models import Q
                queryset = queryset.filter(Q(deal_type__isnull=True) | Q(deal_type=''))
            else:
                # 매매, 전세, 월세는 정확히 일치
                queryset = queryset.filter(deal_type=deal_type)
        
        # 건물유형 필터 (정확히 일치)
        building_type = self.request.query_params.get('building_type', None)
        if building_type:
            queryset = queryset.filter(building_type=building_type)
        
        return queryset
