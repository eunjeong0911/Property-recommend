/**
 * 이미지 URL 유틸리티
 * 외부 이미지 URL을 백엔드 프록시를 통해 로드
 */

const PROXY_DOMAINS = ['ic.zigbang.com'];

/**
 * 이미지 URL을 프록시 URL로 변환
 * Zigbang 등의 hotlink protection을 우회하기 위해 백엔드 프록시 사용
 */
export function getProxiedImageUrl(imageUrl: string): string {
    if (!imageUrl) return imageUrl;

    // 이미 프록시 URL이면 그대로 반환
    if (imageUrl.includes('/api/proxy-image/')) {
        return imageUrl;
    }

    // 프록시가 필요한 도메인인지 확인
    const needsProxy = PROXY_DOMAINS.some(domain => imageUrl.includes(domain));

    if (needsProxy) {
        // 백엔드 프록시를 통해 이미지 로드
        const encodedUrl = encodeURIComponent(imageUrl);
        return `/api/proxy-image/?url=${encodedUrl}`;
    }

    return imageUrl;
}

/**
 * 이미지 URL 배열을 프록시 URL로 변환
 */
export function getProxiedImageUrls(imageUrls: string[]): string[] {
    return imageUrls.map(getProxiedImageUrl);
}
