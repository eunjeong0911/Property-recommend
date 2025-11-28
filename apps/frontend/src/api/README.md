# Client API Functions (`src/api`)

이 폴더는 **외부 서버(Django 백엔드 등)와 통신하기 위한 함수들을 모아두는 공간**입니다.

## 📌 역할
- `axios`나 `fetch`를 사용하여 **백엔드 서버(Django)로 API 요청을 보내는 함수**를 정의합니다.
- 이 폴더 안의 파일들은 **클라이언트(브라우저)**에서 실행됩니다.

## 📂 예시
- `user.ts`: `loginUser()`, `getUserProfile()` 등 사용자 관련 API 호출 함수
- `land.ts`: `getLandList()`, `getLandDetail()` 등 매물 관련 API 호출 함수

## ⚠️ 주의
- 여기에 비밀 키(Secret Key)를 적으면 안 됩니다! (브라우저에 노출됨)
- 실제 비즈니스 로직보다는 **데이터 요청과 응답**을 처리하는 데 집중합니다.

---
**비유**: "배달 주문 전화기" (외부 식당(Django)에 주문을 넣는 도구)
