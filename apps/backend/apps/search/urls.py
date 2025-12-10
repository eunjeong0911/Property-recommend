# =============================================================================
# Search App URL 라우팅
# =============================================================================
#
# 역할: 검색 관련 API URL 패턴 정의
#
# URL 패턴:
# - /api/search/listings/     -> ListingSearchView
# - /api/search/autocomplete/ -> AutocompleteView
# - /api/search/nearby/       -> NearbySearchView
#
# config/urls.py에 include 필요:
#   path('api/search/', include('apps.search.urls'))
# =============================================================================
