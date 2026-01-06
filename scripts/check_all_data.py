"""
전체 데이터 적재 상태 체크 스크립트
"""
import os
import psycopg2

def check_all_data():
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'realestate'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres')
    )
    cur = conn.cursor()
    
    print("=" * 70)
    print("📊 전체 데이터 적재 상태 체크")
    print("=" * 70)
    
    # 1. Land 테이블
    print("\n[1] Land (매물) 테이블")
    cur.execute("SELECT COUNT(*) FROM land")
    land_count = cur.fetchone()[0]
    print(f"   - 총 매물 수: {land_count:,}개")
    
    if land_count > 0:
        cur.execute("SELECT building_type, COUNT(*) FROM land GROUP BY building_type ORDER BY COUNT(*) DESC")
        print("   - 건물유형별:")
        for row in cur.fetchall():
            print(f"     • {row[0]}: {row[1]:,}개")
        
        cur.execute("SELECT deal_type, COUNT(*) FROM land GROUP BY deal_type ORDER BY COUNT(*) DESC")
        print("   - 거래유형별:")
        for row in cur.fetchall():
            print(f"     • {row[0]}: {row[1]:,}개")
    
    # 2. LandBroker 테이블 (중개사)
    print("\n[2] LandBroker (중개사) 테이블")
    cur.execute("SELECT COUNT(*) FROM landbroker")
    broker_count = cur.fetchone()[0]
    print(f"   - 총 중개사 수: {broker_count:,}개")
    
    if broker_count > 0:
        # Trust Score 분포
        cur.execute("""
            SELECT trust_score, COUNT(*) 
            FROM landbroker 
            WHERE trust_score IS NOT NULL 
            GROUP BY trust_score 
            ORDER BY trust_score
        """)
        trust_scores = cur.fetchall()
        if trust_scores:
            print("   - 신뢰도 등급 분포:")
            for row in trust_scores:
                print(f"     • {row[0]}등급: {row[1]:,}개")
        else:
            print("   - ⚠️ 신뢰도 등급 없음 (trust_score가 NULL)")
        
        # Trust Score NULL 개수
        cur.execute("SELECT COUNT(*) FROM landbroker WHERE trust_score IS NULL")
        null_trust = cur.fetchone()[0]
        print(f"   - 신뢰도 미평가: {null_trust:,}개")
        
        # 매물과 연결된 중개사
        cur.execute("SELECT COUNT(DISTINCT landbroker_id) FROM land WHERE landbroker_id IS NOT NULL")
        linked_brokers = cur.fetchone()[0]
        print(f"   - 매물과 연결된 중개사: {linked_brokers:,}개")
    
    # 3. 가격 분류 결과 테이블
    print("\n[3] Price Classification (가격 평가) 테이블")
    try:
        cur.execute("SELECT COUNT(*) FROM price_classification_results")
        price_count = cur.fetchone()[0]
        print(f"   - 총 평가 수: {price_count:,}개")
        
        if price_count > 0:
            cur.execute("""
                SELECT 예측_레이블_한글, COUNT(*) 
                FROM price_classification_results 
                GROUP BY 예측_레이블_한글 
                ORDER BY COUNT(*) DESC
            """)
            print("   - 가격 등급 분포:")
            for row in cur.fetchall():
                print(f"     • {row[0]}: {row[1]:,}개")
    except Exception as e:
        print(f"   - ⚠️ 테이블 없음 또는 오류: {e}")
    
    # 4. Land 테이블의 가격 분류 컬럼 확인
    print("\n[4] Land 테이블 가격 분류 컬럼 확인")
    try:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'land' 
            AND column_name IN ('price_class', 'price_label', 'price_classification')
        """)
        price_cols = cur.fetchall()
        if price_cols:
            for col in price_cols:
                cur.execute(f"SELECT COUNT(*) FROM land WHERE {col[0]} IS NOT NULL")
                count = cur.fetchone()[0]
                print(f"   - {col[0]}: {count:,}개 (NOT NULL)")
        else:
            print("   - ⚠️ 가격 분류 컬럼 없음")
    except Exception as e:
        print(f"   - 오류: {e}")
    
    # 5. Land 이미지
    print("\n[5] Land Image (매물 이미지) 테이블")
    cur.execute("SELECT COUNT(*) FROM land_image")
    image_count = cur.fetchone()[0]
    print(f"   - 총 이미지 수: {image_count:,}개")
    
    cur.execute("SELECT COUNT(DISTINCT land_id) FROM land_image")
    lands_with_images = cur.fetchone()[0]
    print(f"   - 이미지 있는 매물: {lands_with_images:,}개")
    
    # 6. Elasticsearch 인덱스 확인 (별도)
    print("\n[6] 기타 테이블")
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    print(f"   - 사용자 수: {user_count:,}개")
    
    cur.execute("SELECT COUNT(*) FROM wishlists")
    wishlist_count = cur.fetchone()[0]
    print(f"   - 찜 목록: {wishlist_count:,}개")
    
    # 7. 매물-중개사 연결 상태
    print("\n[7] 매물-중개사 연결 상태")
    cur.execute("SELECT COUNT(*) FROM land WHERE landbroker_id IS NOT NULL")
    linked_lands = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM land WHERE landbroker_id IS NULL")
    unlinked_lands = cur.fetchone()[0]
    print(f"   - 중개사 연결된 매물: {linked_lands:,}개")
    print(f"   - 중개사 미연결 매물: {unlinked_lands:,}개")
    
    # 8. 신뢰도 등급별 매물 수
    print("\n[8] 신뢰도 등급별 매물 수")
    cur.execute("""
        SELECT lb.trust_score, COUNT(l.land_id)
        FROM land l
        JOIN landbroker lb ON l.landbroker_id = lb.landbroker_id
        WHERE lb.trust_score IS NOT NULL
        GROUP BY lb.trust_score
        ORDER BY lb.trust_score
    """)
    for row in cur.fetchall():
        print(f"   - {row[0]}등급 중개사 매물: {row[1]:,}개")
    
    print("\n" + "=" * 70)
    print("✅ 데이터 체크 완료")
    print("=" * 70)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_all_data()
