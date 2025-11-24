# 집품(Zippoom) 리뷰 크롤링

집품 사이트의 매물 정보 및 리뷰 데이터를 크롤링하는 스크립트입니다.

## 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

## 사용법

```bash
python reviewCrawling.py
```

## 수집 데이터

- 매물 기본 정보 (주소, 타입, 가격, 면적)
- 매물 설명
- 리뷰 데이터 (작성자, 내용, 평점, 작성일)

## 출력

`zippoom_data_YYYYMMDD_HHMMSS.json` 형식으로 저장됩니다.
