#!/usr/bin/env python3
"""
데이터 Import 검증 스크립트
Neo4j와 PostgreSQL에 데이터가 제대로 들어갔는지 확인합니다.
"""

import os
import sys
from neo4j import GraphDatabase
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def verify_neo4j():
    """Neo4j 데이터 검증"""
    print("\n" + "=" * 70)
    print("Neo4j 데이터 검증")
    print("=" * 70)
    
    try:
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "neo4j"))
        )
        
        with driver.session() as session:
            # 매물 수
            result = session.run("MATCH (p:Property) RETURN count(p) as count")
            property_count = result.single()["count"]
            print(f"✓ 매물 (Property): {property_count:,}개")
            
            # 지하철역 수
            result = session.run("MATCH (s:SubwayStation) RETURN count(s) as count")
            subway_count = result.single()["count"]
            print(f"✓ 지하철역 (SubwayStation): {subway_count:,}개")
            
            # 버스정류장 수
            result = session.run("MATCH (b:BusStation) RETURN count(b) as count")
            bus_count = result.single()["count"]
            print(f"✓ 버스정류장 (BusStation): {bus_count:,}개")
            
            # 편의점 수
            result = session.run("MATCH (c:ConvenienceStore) RETURN count(c) as count")
            convenience_count = result.single()["count"]
            print(f"✓ 편의점 (ConvenienceStore): {convenience_count:,}개")
            
            # 공원 수
            result = session.run("MATCH (p:Park) RETURN count(p) as count")
            park_count = result.single()["count"]
            print(f"✓ 공원 (Park): {park_count:,}개")
            
            # 병원 수
            result = session.run("MATCH (h:Hospital) RETURN count(h) as count")
            hospital_count = result.single()["count"]
            print(f"✓ 병원 (Hospital): {hospital_count:,}개")
            
            # 약국 수
            result = session.run("MATCH (p:Pharmacy) RETURN count(p) as count")
            pharmacy_count = result.single()["count"]
            print(f"✓ 약국 (Pharmacy): {pharmacy_count:,}개")
            
            # 대학교 수
            result = session.run("MATCH (c:College) RETURN count(c) as count")
            college_count = result.single()["count"]
            print(f"✓ 대학교 (College): {college_count:,}개")
            
            print("\n관계 (Relationships):")
            
            # 지하철역 연결
            result = session.run("MATCH ()-[r:NEAR_SUBWAY]->() RETURN count(r) as count")
            subway_rel_count = result.single()["count"]
            print(f"✓ 매물-지하철역 연결: {subway_rel_count:,}개")
            
            # 버스정류장 연결
            result = session.run("MATCH ()-[r:NEAR_BUS]->() RETURN count(r) as count")
            bus_rel_count = result.single()["count"]
            print(f"✓ 매물-버스정류장 연결: {bus_rel_count:,}개")
            
            # 편의점 연결
            result = session.run("MATCH ()-[r:NEAR_CONVENIENCE]->() RETURN count(r) as count")
            convenience_rel_count = result.single()["count"]
            print(f"✓ 매물-편의점 연결: {convenience_rel_count:,}개")
            
            # 샘플 매물 확인
            print("\n샘플 매물 (처음 3개):")
            result = session.run("""
                MATCH (p:Property)
                RETURN p.id as id, p.name as name, p.address as address
                LIMIT 3
            """)
            for i, record in enumerate(result, 1):
                print(f"  {i}. {record['name']} ({record['id']})")
                print(f"     주소: {record['address']}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"✗ Neo4j 연결 실패: {e}")
        return False


def verify_postgres():
    """PostgreSQL 데이터 검증"""
    print("\n" + "=" * 70)
    print("PostgreSQL 데이터 검증")
    print("=" * 70)
    
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "realestate"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        
        cur = conn.cursor()
        
        # 매물 수
        cur.execute("SELECT COUNT(*) FROM listings")
        listing_count = cur.fetchone()[0]
        print(f"✓ 매물 (listings): {listing_count:,}개")
        
        # 샘플 매물 확인
        print("\n샘플 매물 (처음 3개):")
        cur.execute("""
            SELECT listing_id, title, address
            FROM listings
            LIMIT 3
        """)
        for i, row in enumerate(cur.fetchall(), 1):
            print(f"  {i}. {row[1]} ({row[0]})")
            print(f"     주소: {row[2]}")
        
        # 지역별 매물 수
        print("\n지역별 매물 수:")
        cur.execute("""
            SELECT 
                address_info->>'시도' as 시도,
                COUNT(*) as 매물수
            FROM listings
            WHERE address_info->>'시도' IS NOT NULL
            GROUP BY address_info->>'시도'
            ORDER BY 매물수 DESC
            LIMIT 5
        """)
        for row in cur.fetchall():
            if row[0]:
                print(f"  {row[0]}: {row[1]:,}개")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ PostgreSQL 연결 실패: {e}")
        return False


def main():
    print("\n" + "=" * 70)
    print(" " * 20 + "데이터 Import 검증")
    print("=" * 70)
    
    neo4j_ok = verify_neo4j()
    postgres_ok = verify_postgres()
    
    print("\n" + "=" * 70)
    print("검증 결과")
    print("=" * 70)
    print(f"Neo4j: {'✓ 성공' if neo4j_ok else '✗ 실패'}")
    print(f"PostgreSQL: {'✓ 성공' if postgres_ok else '✗ 실패'}")
    print("=" * 70 + "\n")
    
    if neo4j_ok and postgres_ok:
        print("✓ 모든 데이터가 정상적으로 import되었습니다!")
        sys.exit(0)
    else:
        print("✗ 일부 데이터베이스에 문제가 있습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
