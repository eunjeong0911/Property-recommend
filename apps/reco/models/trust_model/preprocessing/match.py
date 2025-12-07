# vworld + peterpanz + 부동산중개업자정보 matching code
# 거래완료/등록매물/총매물수 를 직원 수대로 정수 분배해서 "원래 컬럼"에 덮어쓰기
import os
import numpy as np
import pandas as pd

# ─────────────────────────
# 1. 경로 설정
# ─────────────────────────

PROJECT_ROOT = os.getcwd()  # 프로젝트 루트에서 실행한다고 가정
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

PATH_SEOUL = os.path.join(DATA_DIR, "seoul_broker_clean.csv")    # 사무소 단위 clean
PATH_INFO  = os.path.join(DATA_DIR, "부동산중개업자정보.csv")      # 직원/근무자 정보
OUTPUT_PATH_MERGED = os.path.join(DATA_DIR, "seoul_broker_merged.csv")

print("📂 DATA_DIR   :", DATA_DIR)
print("📄 PATH_SEOUL :", PATH_SEOUL)
print("📄 PATH_INFO  :", PATH_INFO)
print("💾 OUTPUT     :", OUTPUT_PATH_MERGED)


# ─────────────────────────
# 2. 직원별 정수 분배 함수
#    - 등록번호별로 groupby
#    - 사무소 합계(total)를 직원 수(n=행 수)로 나누되
#      합계를 그대로 유지하도록 몫/나머지 분배
#    - 예: total=7, n=3 → [3, 2, 2]
#    - ❗ 새 컬럼 만들지 않고, col 자체에 덮어씀
# ─────────────────────────
def split_counts_overwrite(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    df   : 직원 포함된 merged DataFrame
    col  : 사무소 단위 합계 컬럼명 (예: '거래완료')
    동작 :
      - 등록번호 그룹별로 정수 분배된 값을 계산해서
        df[col] 값 자체를 덮어쓴다.
      - 등록번호별로 col을 다시 합치면 원래 합계와 동일해야 한다.
    """

    def _assign(group: pd.DataFrame) -> pd.DataFrame:
        total = group[col].iloc[0]

        # NaN 이면 그대로 NaN
        if pd.isna(total):
            group[col] = np.nan
            return group

        try:
            total_int = int(total)
        except Exception:
            # 숫자 변환 안 되면 그냥 NaN
            group[col] = np.nan
            return group

        n = len(group)  # 이 등록번호에 해당하는 직원(행) 수
        if n <= 0:
            group[col] = np.nan
            return group

        base = total_int // n   # 기본 몫
        extra = total_int % n   # 나머지

        vals = [base] * n
        for i in range(extra):
            vals[i] += 1  # 앞에서부터 1씩 분배

        group[col] = vals
        return group

    return df.groupby("등록번호", group_keys=False).apply(_assign)


# ─────────────────────────
# 3. 매칭 및 전처리 메인 함수
# ─────────────────────────
def merge_broker_info():
    # 1) 데이터 읽기
    seoul = pd.read_csv(PATH_SEOUL, encoding="utf-8-sig", dtype={"등록번호": str})
    info  = pd.read_csv(PATH_INFO,  encoding="utf-8-sig", dtype={"등록번호": str})

    print("📦 seoul (clean, 사무소 단위) shape:", seoul.shape)
    print("📦 info  (부동산중개업자정보, 직원 단위 가정) shape:", info.shape)

    # 2) 사무소 + 직원 정보 merge (등록번호 기준)
    merged = seoul.merge(info, on="등록번호", how="left")
    print("🔗 after seoul+info merge shape:", merged.shape)

    # 3) 거래/매물 관련 컬럼들을
    #    → 직원 수대로 정수 분배해서 "원래 컬럼"에 덮어쓰기
    count_cols = ["거래완료", "등록매물", "총매물수"]
    for col in count_cols:
        if col in merged.columns:
            print(f"⚙️  직원 단위 정수 분배 후 원 컬럼 덮어쓰기: {col}")
            merged = split_counts_overwrite(merged, col)
            merged[col] = merged[col].astype("Int64")  # 정수형(NA 허용)으로 정리

    # 4) 필요 없다고 판단되는 컬럼 정리 (있으면 삭제, 없으면 무시)
    drop_cols = ["법정동명", "법정동코드", "사업자상호", "데이터기준일자"]
    merged = merged.drop(columns=drop_cols, errors="ignore")

    print("✅ 최종 merged shape:", merged.shape)
    print(merged.head(5))

    # 5) sanity check: 합계 보존 여부 확인 (콘솔 출력용)
    try:
        print("\n🔍 합계 비교 (clean vs merged, 등록번호 기준 재집계)")

        # clean 기준 합계
        clean_sum = seoul[count_cols].sum()
        print("[clean 합계]")
        print(clean_sum)

        # merged에서 등록번호 기준으로 다시 합쳐본 합계
        merged_sum = (
            merged.groupby("등록번호")[count_cols]
                  .sum()
                  .sum()
        )
        print("\n[merged 합계 (등록번호 기준 재집계 후 전체 합산)]")
        print(merged_sum)

    except Exception as e:
        print("⚠️ 합계 비교 중 오류 발생:", e)

    # 6) 저장
    merged.to_csv(OUTPUT_PATH_MERGED, index=False, encoding="utf-8-sig")
    print("\n💾 저장 완료 →", OUTPUT_PATH_MERGED)


# ─────────────────────────
# 4. 실행 엔트리포인트
# ─────────────────────────
if __name__ == "__main__":
    merge_broker_info()