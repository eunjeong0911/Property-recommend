"""
데이터 Import 검증 스크립트

PostgreSQL과 Neo4j의 데이터를 확인하여 정상적으로 import되었는지 검증합니다.
"""

import os
import sys
from pathlib import Path

# Add data_import to path
sys.path.insert(0, str(Path(__file__).parent / 'data_import'))

from config import Config
from database import Database
import psycopg2
from neo4j import GraphDatabase

def check_postgres():
    """PostgreSQL 데이터 확인"""
    print("\n" + "="*60)
    print("PostgreSQL 확인")
    print("="*60)
    
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            dbname=os.getenv("POSTGRES_DB", "realestate"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        cursor = conn.cursor()
        
        # 전체 개수
        cursor.execute("SELECT COUNT(*) FROM land;")
        total = cursor.fetchone()[0]
        print(f"  ✓ land 테이블: {total:,}개 레코드")
        
        # 건물형태별 개수
        cursor.execute("""
            SELECT building_type, COUNT(*) 
            FROM land 
            GROUP BY building_type 
            ORDER BY COUNT(*) DESC;
        """)
        print("\n  건물형태별:")
        for building_type, count in cursor.fetchall():
            print(f"    - {building_type}: {count:,}개")
        
        # 거래유형별 개수
        cursor.execute("""
            SELECT deal_type, COUNT(*) 
            FROM land 
            WHERE deal_type IS NOT NULL
            GROUP BY deal_type 
            ORDER BY COUNT(*) DESC;
        """)
        print("\n  거래유형별:")
        for deal_type, count in cursor.fetchall():
            print(f"    - {deal_type}: {count:,}개")
        
        cursor.close()
        conn.close()
        
        return total > 0
        
    except Exception as e:
        print(f"  ❌ PostgreSQL 오류: {e}")
        return False


def check_neo4j():
    """Neo4j 데이터 확인"""
    print("\n" + "="*60)
    print("Neo4j 확인")
    print("="*60)
    
    try:
        driver = Database.get_driver()
        
        with driver.session() as session:
            # 노드 개수
            print("\n  노드 개수:")
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """)
            
            node_counts = {}
            for record in result:
                node_type = record["type"]
                count = record["count"]
                node_counts[node_type] = count
                print(f"    ✓ {node_type}: {count:,}개")
            
            # Property 노드 구조 확인
            print("\n  Property 노드 구조 확인:")
            result = session.run("""
                MATCH (p:Property)
                RETURN keys(p) as fields
                LIMIT 1
            """)
            record = result.single()
            if record:
                fields = record["fields"]
                print(f"    필드: {fields}")
                if "address" in fields:
                    print("    ⚠️  경고: Property 노드에 address 필드가 있습니다!")
                    print("    → Neo4j에는 id, latitude, longitude, location만 있어야 합니다.")
                else:
                    print("    ✅ 정상: address 필드 없음 (PostgreSQL에서 조회)")
            
            # 관계 개수
            print("\n  관계(Edge) 개수:")
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship, count(r) as count
                ORDER BY count DESC
                LIMIT 15
            """)
            
            for record in result:
                rel_type = record["relationship"]
                count = record["count"]
                print(f"    ✓ {rel_type}: {count:,}개")
            
            # 검증
            property_count = node_counts.get("Property", 0)
            return property_count > 0
            
    except Exception as e:
        print(f"  ❌ Neo4j 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_data_consistency():
    """PostgreSQL과 Neo4j 데이터 일관성 확인"""
    print("\n" + "="*60)
    print("데이터 일관성 확인")
    print("="*60)
    
    try:
        # PostgreSQL 매물 ID 목록
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            dbname=os.getenv("POSTGRES_DB", "realestate"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        cursor = conn.cursor()
        cursor.execute("SELECT land_num FROM land LIMIT 100;")
        postgres_ids = {str(row[0]) for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        
        # Neo4j Property ID 목록
        driver = Database.get_driver()
        with driver.session() as session:
            result = session.run("MATCH (p:Property) RETURN p.id as id LIMIT 100;")
            neo4j_ids = {str(record["id"]) for record in result}
        
        # 일치 확인
        matching = postgres_ids & neo4j_ids
        print(f"  PostgreSQL 샘플: {len(postgres_ids)}개")
        print(f"  Neo4j 샘플: {len(neo4j_ids)}개")
        print(f"  일치하는 ID: {len(matching)}개")
        
        if len(matching) > 50:
            print("  ✅ 데이터 일관성 정상")
            return True
        else:
            print("  ⚠️  경고: 일치하는 ID가 적습니다")
            return False
            
    except Exception as e:
        print(f"  ❌ 일관성 확인 오류: {e}")
        return False


def main():
    print("="*60)
    print("데이터 Import 검증 시작")
    print("="*60)
    
    postgres_ok = check_postgres()
    neo4j_ok = check_neo4j()
    consistency_ok = verify_data_consistency()
    
    print("\n" + "="*60)
    print("검증 결과")
    print("="*60)
    
    if postgres_ok:
        print("  ✅ PostgreSQL: 정상")
    else:
        print("  ❌ PostgreSQL: 문제 있음")
    
    if neo4j_ok:
        print("  ✅ Neo4j: 정상")
    else:
        print("  ❌ Neo4j: 문제 있음")
    
    if consistency_ok:
        print("  ✅ 데이터 일관성: 정상")
    else:
        print("  ⚠️  데이터 일관성: 확인 필요")
    
    print("="*60)
    
    if postgres_ok and neo4j_ok:
        print("\n🎉 모든 데이터가 정상적으로 import되었습니다!")
    else:
        print("\n⚠️  일부 데이터에 문제가 있습니다. 위 내용을 확인하세요.")


if __name__ == "__main__":
    main()
