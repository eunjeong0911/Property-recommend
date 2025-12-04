import os
import pickle

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # trust_model 디렉토리 경로
MODEL_DIR = os.path.join(BASE_DIR, "models")           # trust_model/models/

def apply_clustering(df):
    print("\n" + "="*60)
    print("🎯 [4단계] KMeans 클러스터링")
    print("="*60)

    df = df.copy()
    
    # 데이터 누수 방지: 거래성사율 제외
    features = df[["거래완료", "일평균거래", "총매물수", "등록매물"]]

    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    
    # 클러스터링 전 스케일링 (중요!)
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    kmeans = KMeans(n_clusters=3, random_state=42)  # 4개 → 3개로 조정
    df["cluster"] = kmeans.fit_predict(features_scaled)

    n_clusters = len(df["cluster"].unique())
    print(f"✅ 클러스터링 완료 ({n_clusters}개 클러스터)")
    
    # 클러스터별 통계
    for i in range(n_clusters):
        cluster_data = df[df["cluster"] == i]
        print(f"\n   [클러스터 {i}] {len(cluster_data)}개")
        print(f"      - 평균 거래완료: {cluster_data['거래완료'].mean():.0f}건")
        print(f"      - 평균 총매물수: {cluster_data['총매물수'].mean():.0f}건")
        print(f"      - 평균 일평균거래: {cluster_data['일평균거래'].mean():.2f}건")

    # cluster_temp = 클러스터 평균 rule_score
    cluster_temp = df.groupby("cluster")["rule_score"].mean()
    df["cluster_temp"] = df["cluster"].map(cluster_temp)

    print(f"\n✅ 클러스터 온도(cluster_temp) 생성 완료")
    print(f"   - 평균: {df['cluster_temp'].mean():.2f}")

    # 폴더 자동 생성
    os.makedirs(MODEL_DIR, exist_ok=True)

    save_path = os.path.join(MODEL_DIR, "kmeans.pkl")

    # 모델 저장 (스케일러도 함께 저장)
    with open(save_path, "wb") as f:
        pickle.dump(kmeans, f)
    
    scaler_path = os.path.join(MODEL_DIR, "kmeans_scaler.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    print(f"\n💾 모델 저장 완료")
    print(f"   - KMeans: {save_path}")
    print(f"   - Scaler: {scaler_path}")
    return df
