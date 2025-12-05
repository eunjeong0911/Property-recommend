from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Land
from .serializers import LandSerializer

class LandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Land.objects.all()
    serializer_class = LandSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['address', 'deal_type', 'building_type']
    search_fields = ['land_num', 'address']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Additional custom filtering if needed
        return queryset
