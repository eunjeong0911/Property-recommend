import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
import os


class ZippoomCrawler:
    def __init__(self):
        self.base_url = "https://zippoom.com"
        self.data = []
        
    async def crawl_property(self, url: str):
        """특정 매물 페이지 크롤링"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                print(f"크롤링 시작: {url}")
                
                # 메인 페이지 먼저 방문 (세션/쿠키 확보)
                print("메인 페이지 방문 중...")
                await page.goto("https://zippoom.com", wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                
                # 목표 URL로 이동
                print("매물 페이지로 이동 중...")
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                
                # 페이지 HTML 저장 (디버깅용)
                html_content = await page.content()
                with open('page_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print("페이지 HTML 저장: page_debug.html")
                
                # 스크린샷 저장
                await page.screenshot(path='page_screenshot.png', full_page=True)
                print("스크린샷 저장: page_screenshot.png")
                
                # 페이지 전체 텍스트 출력
                body_text = await page.locator('body').text_content()
                print(f"\n=== 페이지 텍스트 미리보기 ===")
                print(body_text[:500] if body_text else "텍스트 없음")
                print("=" * 50)
                
                # 기본 매물 정보 추출
                property_data = await self.extract_property_info(page)
                
                # 리뷰 데이터 추출
                reviews = await self.extract_reviews(page)
                property_data['reviews'] = reviews
                property_data['total_reviews'] = len(reviews)
                
                self.data.append(property_data)
                print(f"\n크롤링 완료!")
                print(f"- 주소: {property_data.get('address', 'Unknown')}")
                print(f"- 리뷰 수: {len(reviews)}개")
                
            except Exception as e:
                print(f"에러 발생: {str(e)}")
                import traceback
                traceback.print_exc()
                
            finally:
                await browser.close()
                
    async def extract_property_info(self, page):
        """매물 기본 정보 추출"""
        data = {
            'url': page.url,
            'crawled_at': datetime.now().isoformat()
        }
        
        print("\n=== 매물 정보 추출 중 ===")
        
        try:
            # 모든 h1, h2, h3 태그 확인
            headings = await page.locator('h1, h2, h3').all()
            for i, heading in enumerate(headings):
                text = await heading.text_content()
                print(f"제목 {i+1}: {text.strip() if text else 'None'}")
            
            # 주소 정보 (다양한 셀렉터 시도)
            selectors_to_try = [
                'h1', 'h2', 
                '[class*="address"]', '[class*="Address"]',
                '[class*="location"]', '[class*="Location"]',
                '[class*="title"]', '[class*="Title"]'
            ]
            
            for selector in selectors_to_try:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        text = await element.text_content()
                        if text and text.strip():
                            data['address'] = text.strip()
                            print(f"✓ 주소 발견 ({selector}): {text.strip()}")
                            break
                except:
                    continue
            
            # 전체 텍스트에서 정보 추출
            all_text = await page.locator('body').text_content()
            data['page_text'] = all_text[:1000] if all_text else None  # 처음 1000자만
            
        except Exception as e:
            print(f"매물 정보 추출 중 에러: {str(e)}")
            
        return data
    
    async def extract_reviews(self, page):
        """리뷰 데이터 추출"""
        reviews = []
        
        print("\n=== 리뷰 추출 중 ===")
        
        try:
            # 페이지 끝까지 스크롤
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            # 다양한 리뷰 셀렉터 시도
            review_selectors = [
                '[class*="review"]',
                '[class*="Review"]',
                '[class*="comment"]',
                '[class*="Comment"]',
                '[class*="feedback"]',
                '[class*="Feedback"]',
                'article',
                '[role="article"]',
                '.review-item',
                '.comment-item'
            ]
            
            review_elements = []
            found_selector = None
            
            for selector in review_selectors:
                elements = await page.locator(selector).all()
                if elements and len(elements) > 0:
                    print(f"✓ '{selector}' 셀렉터로 {len(elements)}개 요소 발견")
                    review_elements = elements
                    found_selector = selector
                    break
            
            if not review_elements:
                print("⚠ 리뷰 요소를 찾을 수 없습니다.")
                # 모든 div 확인
                all_divs = await page.locator('div').all()
                print(f"전체 div 개수: {len(all_divs)}")
                return reviews
            
            # 각 리뷰 추출
            for idx, element in enumerate(review_elements):
                try:
                    review_data = {'index': idx + 1}
                    
                    # 요소의 전체 텍스트
                    full_text = await element.text_content()
                    review_data['raw_text'] = full_text.strip() if full_text else None
                    
                    # 다양한 하위 요소 시도
                    try:
                        # 작성자
                        for author_sel in ['[class*="author"]', '[class*="user"]', '[class*="name"]', 'strong', 'b']:
                            try:
                                author_elem = element.locator(author_sel).first
                                if await author_elem.count() > 0:
                                    author = await author_elem.text_content()
                                    if author and author.strip():
                                        review_data['author'] = author.strip()
                                        break
                            except:
                                continue
                        
                        # 내용
                        for content_sel in ['p', '[class*="content"]', '[class*="text"]', 'span']:
                            try:
                                content_elem = element.locator(content_sel).first
                                if await content_elem.count() > 0:
                                    content = await content_elem.text_content()
                                    if content and len(content.strip()) > 10:
                                        review_data['content'] = content.strip()
                                        break
                            except:
                                continue
                        
                        # 평점
                        for rating_sel in ['[class*="rating"]', '[class*="star"]', '[class*="score"]']:
                            try:
                                rating_elem = element.locator(rating_sel).first
                                if await rating_elem.count() > 0:
                                    rating = await rating_elem.text_content()
                                    if rating:
                                        review_data['rating'] = rating.strip()
                                        break
                            except:
                                continue
                        
                        # 날짜
                        for date_sel in ['[class*="date"]', '[class*="time"]', 'time']:
                            try:
                                date_elem = element.locator(date_sel).first
                                if await date_elem.count() > 0:
                                    date = await date_elem.text_content()
                                    if date:
                                        review_data['date'] = date.strip()
                                        break
                            except:
                                continue
                    except:
                        pass
                    
                    # 최소한 텍스트가 있으면 추가
                    if review_data.get('raw_text') or review_data.get('content'):
                        reviews.append(review_data)
                        print(f"리뷰 {idx+1} 추출 완료")
                        
                except Exception as e:
                    print(f"리뷰 {idx+1} 추출 중 에러: {str(e)}")
                    continue
            
            print(f"총 {len(reviews)}개 리뷰 추출 완료")
                    
        except Exception as e:
            print(f"리뷰 추출 중 에러: {str(e)}")
            import traceback
            traceback.print_exc()
            
        return reviews
    
    def save_to_json(self, filename: str = None):
        """JSON 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"zippoom_data_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        print(f"데이터 저장 완료: {filepath}")
        print(f"총 {len(self.data)}개 매물 크롤링")


async def main():
    """메인 실행 함수"""
    crawler = ZippoomCrawler()
    
    # 크롤링할 URL
    url = "https://zippoom.com/%EB%B6%80%EB%8F%99%EC%82%B0/%EC%84%9C%EC%9A%B8-%EA%B8%88%EC%B2%9C%EA%B5%AC-%EB%8F%85%EC%82%B0%EB%8F%99-301-12/dhb9bq"
    
    await crawler.crawl_property(url)
    
    # 결과 저장
    crawler.save_to_json()


if __name__ == "__main__":
    asyncio.run(main())
