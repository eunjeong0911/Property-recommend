"""
이미지 프록시 뷰
외부 이미지 URL을 프록시하여 hotlink protection 우회
"""
import requests
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from urllib.parse import unquote


@require_http_methods(["GET"])
@cache_page(60 * 60 * 24)  # 24시간 캐시
def proxy_image(request):
    """
    외부 이미지를 프록시하여 반환
    
    Usage: /api/proxy-image/?url=https://ic.zigbang.com/ic/items/47382502/1.jpg
    """
    image_url = request.GET.get('url')
    
    if not image_url:
        return HttpResponseBadRequest("Missing 'url' parameter")
    
    # URL 디코딩
    image_url = unquote(image_url)
    
    # 허용된 도메인 체크 (보안)
    allowed_domains = ['ic.zigbang.com', 'img.peterpanz.com', 'cdn.peterpanz.com']
    if not any(domain in image_url for domain in allowed_domains):
        return HttpResponseBadRequest("Invalid image domain")
    
    try:
        # 외부 이미지 요청 (referrer 없이)
        response = requests.get(
            image_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
            timeout=10,
            stream=True
        )
        response.raise_for_status()
        
        # 이미지 반환
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        django_response = HttpResponse(response.content, content_type=content_type)
        
        # 캐시 헤더 추가
        django_response['Cache-Control'] = 'public, max-age=86400'  # 24시간
        
        return django_response
        
    except requests.RequestException as e:
        return HttpResponseBadRequest(f"Failed to fetch image: {str(e)}")
