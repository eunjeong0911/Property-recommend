"""
문화 온도 EDA (Exploratory Data Analysis)
도서관 가중치 5점 적용 버전
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from neo4j import GraphDatabase

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# Neo4j 연결 설정
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password123")

# 가중치 설정 (도서관 5점 버전)
WEIGHTS = {
    '영화관': 30,
    '미술관': 30,
    '공연장': 25,
    '박물관/기념관': 15,
    '도서관': 5,      # 10점 → 5점으로 조정
    '기타': 5,
    '문화원': 5,
}


class Neo4jConnector:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    
    def get_culture_data(self, limit=10000):
        """매물별 문화시설 데이터 조회"""
        query = """
        MATCH (p:Property)
        OPTIONAL MATCH (p)-[r:NEAR_CULTURE]->(c:Culture)
        WHERE r.distance <= 500
        WITH p.id as property_id, 
             c.category as category, 
             r.distance as distance,
             count(c) as count
        RETURN property_id, category, distance, count
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return pd.DataFrame([r.data() for r in result])
    
    def get_culture_summary(self, limit=10000):
        """매물별 문화시설 개수 요약"""
        query = """
        MATCH (p:Property)
        OPTIONAL MATCH (p)-[r:NEAR_CULTURE]->(c:Culture)
        WHERE r.distance <= 500
        WITH p.id as property_id, count(c) as culture_count
        RETURN property_id, culture_count
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return pd.DataFrame([r.data() for r in result])
    
    def compare_weights(self, limit=500):
        """가중치 비교 분석 (현재 vs 도서관 5점)"""
        query = """
        MATCH (p:Property)
        WITH p LIMIT $limit
        
        OPTIONAL MATCH (p)-[r:NEAR_CULTURE]->(c:Culture)
        WHERE r.distance <= 500
        WITH p, c, r,
             CASE c.category
                WHEN '영화관' THEN 30 * (1 - r.distance / 500.0)
                WHEN '미술관' THEN 30 * (1 - r.distance / 500.0)
                WHEN '공연장' THEN 25 * (1 - r.distance / 500.0)
                WHEN '박물관/기념관' THEN 15 * (1 - r.distance / 500.0)
                WHEN '도서관' THEN 10 * (1 - r.distance / 500.0)
                ELSE 10 * (1 - r.distance / 500.0)
             END as score_v1,
             CASE c.category
                WHEN '영화관' THEN 30 * (1 - r.distance / 500.0)
                WHEN '미술관' THEN 30 * (1 - r.distance / 500.0)
                WHEN '공연장' THEN 25 * (1 - r.distance / 500.0)
                WHEN '박물관/기념관' THEN 15 * (1 - r.distance / 500.0)
                WHEN '도서관' THEN 5 * (1 - r.distance / 500.0)
                ELSE 5 * (1 - r.distance / 500.0)
             END as score_v2
        
        WITH p.id as property_id,
             sum(score_v1) as total_v1,
             sum(score_v2) as total_v2
        
        RETURN 
            avg(total_v1) as avg_score_current,
            avg(total_v2) as avg_score_library5,
            avg(total_v1 - total_v2) as avg_diff,
            percentileCont(total_v1, 0.5) as median_current,
            percentileCont(total_v2, 0.5) as median_library5,
            max(total_v1) as max_current,
            max(total_v2) as max_library5
        """
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return result.single()
    
    def close(self):
        self.driver.close()


def analyze_distribution(df):
    """분포 분석"""
    print("=" * 60)
    print("📊 문화 온도 EDA 결과")
    print("=" * 60)
    
    print("\n=== 기술 통계 ===")
    print(df['culture_count'].describe())
    
    zero_pct = (df['culture_count'] == 0).mean() * 100
    print(f"\n0개인 매물 비율: {zero_pct:.1f}%")
    print(f"1개 이상 매물 비율: {100-zero_pct:.1f}%")
    
    print("\n=== 분위수별 개수 ===")
    percentiles = [0.5, 0.75, 0.90, 0.95, 0.99]
    for p in percentiles:
        val = df['culture_count'].quantile(p)
        print(f"상위 {(1-p)*100:.0f}% (p{int(p*100)}): {val:.0f}개")


def plot_distribution(df, output_dir=None):
    """분포 시각화"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 히스토그램
    ax1 = axes[0]
    counts = df['culture_count'].value_counts().sort_index()
    ax1.bar(counts.index, counts.values, color='steelblue', edgecolor='black')
    ax1.set_title('매물 주변(500m) 문화시설 개수 분포', fontsize=14)
    ax1.set_xlabel('문화시설 개수')
    ax1.set_ylabel('매물 수')
    ax1.grid(axis='y', alpha=0.3)
    
    # 누적 분포 (CDF)
    ax2 = axes[1]
    sorted_data = df['culture_count'].sort_values()
    unique_vals = sorted_data.unique()
    cdf = [(sorted_data <= x).mean() for x in unique_vals]
    ax2.plot(unique_vals, cdf, marker='o', linewidth=2, markersize=4)
    ax2.set_title('누적 분포 (CDF)', fontsize=14)
    ax2.set_xlabel('문화시설 개수')
    ax2.set_ylabel('누적 비율')
    ax2.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='중위수')
    ax2.axhline(y=0.9, color='orange', linestyle='--', alpha=0.5, label='상위 10%')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_dir:
        output_path = os.path.join(output_dir, "culture_distribution.png")
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"\n📊 그래프 저장됨: {output_path}")
    
    plt.show()


def compare_weight_versions(db):
    """가중치 비교 분석 실행"""
    print("\n" + "=" * 60)
    print("📊 문화 온도 가중치 비교 결과")
    print("=" * 60)
    
    record = db.compare_weights(limit=500)
    
    print(f"\n{'지표':<25} {'현재 (도서관 10점)':<20} {'변경 (도서관 5점)':<20}")
    print("-" * 65)
    print(f"{'평균 점수':<25} {record['avg_score_current']:.2f}{'':<15} {record['avg_score_library5']:.2f}")
    print(f"{'중위수':<25} {record['median_current']:.2f}{'':<15} {record['median_library5']:.2f}")
    print(f"{'최고 점수':<25} {record['max_current']:.2f}{'':<15} {record['max_library5']:.2f}")
    print(f"\n{'평균 차이 (현재 - 변경)':<25} {record['avg_diff']:.2f}점")
    print("=" * 60)


def main():
    print("문화 온도 EDA 분석 시작...")
    
    # Neo4j 연결
    db = Neo4jConnector()
    
    try:
        # 1. 데이터 로드
        print("데이터 로딩 중...")
        df = db.get_culture_summary(limit=10000)
        print(f"분석 대상 매물 수: {len(df)}")
        
        # 2. 분포 분석
        analyze_distribution(df)
        
        # 3. 가중치 비교 분석
        compare_weight_versions(db)
        
        # 4. 시각화
        current_dir = os.path.dirname(os.path.abspath(__file__))
        plot_distribution(df, output_dir=current_dir)
        
    finally:
        db.close()
    
    print("\n✅ 분석 완료!")


if __name__ == "__main__":
    main()
