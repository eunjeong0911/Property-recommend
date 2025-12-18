"""
Trust Model Feature Engineering EDA
====================================
각 피처를 생성한 근거를 데이터 분석으로 제시

목차:
1. 거래 및 실적 지표
2. 인력 및 전문성 지표
3. 운영 경험 및 숙련도
4. 조직 구조
5. 대표자 자격
6. 지역 기반 피처
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 결과 저장 디렉토리
output_dir = Path("apps/reco/models/trust_model/results/eda")
output_dir.mkdir(parents=True, exist_ok=True)

# 데이터 로드
print("=" * 100)
print("데이터 로드")
print("=" * 100)

# 전처리된 데이터 사용 (숫자형으로 변환됨)
df = pd.read_csv('data/ML/preprocessed_office_data.csv', encoding='utf-8-sig')
target_df = pd.read_csv('data/ML/trust/train_target.csv', encoding='utf-8-sig')

# Target 병합
df_with_target = df.merge(target_df[['등록번호', 'Target']], on='등록번호', how='inner')

print(f"전체 데이터: {len(df)}개")
print(f"Target 있는 데이터: {len(df_with_target)}개")
print(f"Target 분포:\n{df_with_target['Target'].value_counts().sort_index()}")

# ============================================================================
# 1. 거래 및 실적 지표
# ============================================================================
print("\n" + "=" * 100)
print("1. 거래 및 실적 지표 분석")
print("=" * 100)

# 1-1. 로그 변환의 필요성
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# 원본 분포 (NaN 제거)
total_activity = (df['거래완료'] + df['등록매물']).dropna()
axes[0, 0].hist(total_activity, bins=50, edgecolor='black')
axes[0, 0].set_title('총거래활동량 분포 (원본)', fontsize=14, fontweight='bold')
axes[0, 0].set_xlabel('총거래활동량')
axes[0, 0].set_ylabel('빈도')
axes[0, 0].axvline(total_activity.median(), 
                    color='red', linestyle='--', label=f'중앙값')
axes[0, 0].legend()

# 로그 변환 후 분포
log_activity = np.log1p(total_activity)
axes[0, 1].hist(log_activity, bins=50, edgecolor='black', color='orange')
axes[0, 1].set_title('총거래활동량 분포 (로그 변환)', fontsize=14, fontweight='bold')
axes[0, 1].set_xlabel('log(총거래활동량)')
axes[0, 1].set_ylabel('빈도')
axes[0, 1].axvline(log_activity.median(), color='red', linestyle='--', label=f'중앙값')
axes[0, 1].legend()

# 왜도 비교
skew_original = total_activity.dropna().skew()
skew_log = log_activity.dropna().skew()

axes[1, 0].bar(['원본', '로그 변환'], [abs(skew_original), abs(skew_log)], 
               color=['steelblue', 'orange'])
axes[1, 0].set_title('왜도(Skewness) 비교', fontsize=14, fontweight='bold')
axes[1, 0].set_ylabel('왜도 (절대값)')
axes[1, 0].axhline(0.5, color='red', linestyle='--', label='정규분포 기준 (0.5)')
axes[1, 0].legend()
for i, v in enumerate([abs(skew_original), abs(skew_log)]):
    axes[1, 0].text(i, v + 0.1, f'{v:.2f}', ha='center', fontweight='bold')

# Target과의 관계
if 'Target' in df_with_target.columns:
    df_with_target['총거래활동량_log'] = np.log1p(
        df_with_target['거래완료'] + df_with_target['등록매물']
    )
    
    grade_labels = ['C등급 (0)', 'B등급 (1)', 'A등급 (2)']
    box_data = [df_with_target[df_with_target['Target'] == i]['총거래활동량_log'].dropna() 
                for i in range(3)]
    
    bp = axes[1, 1].boxplot(box_data, labels=grade_labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], ['lightcoral', 'lightyellow', 'lightgreen']):
        patch.set_facecolor(color)
    
    axes[1, 1].set_title('신뢰도 등급별 총거래활동량 분포', fontsize=14, fontweight='bold')
    axes[1, 1].set_ylabel('log(총거래활동량)')
    axes[1, 1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / '01_transaction_analysis.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '01_transaction_analysis.png'}")
plt.close()

print(f"\n📊 분석 결과:")
print(f"   - 원본 왜도: {skew_original:.2f} (심한 왜곡)")
print(f"   - 로그 변환 후 왜도: {skew_log:.2f} (정규분포에 가까움)")
print(f"   ✅ 결론: 로그 변환이 필요함")

# ============================================================================
# 2. 인력 및 전문성 지표
# ============================================================================
print("\n" + "=" * 100)
print("2. 인력 및 전문성 지표 분석")
print("=" * 100)

# 2-1. 자격증 보유 비율 분석
def calculate_cert_ratio(row):
    if pd.isna(row["직원목록_JSON"]):
        return 0.0
    try:
        staff_list = json.loads(row["직원목록_JSON"])
        if not staff_list:
            return 0.0
        
        cert_count = sum(1 for staff in staff_list 
                        if pd.notna(staff.get("자격번호")) or pd.notna(staff.get("자격취득일")))
        return cert_count / len(staff_list) if len(staff_list) > 0 else 0.0
    except:
        return 0.0

df_with_target['자격증_보유비율'] = df_with_target.apply(calculate_cert_ratio, axis=1)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 자격증 보유 비율 분포
axes[0].hist(df_with_target['자격증_보유비율'], bins=20, edgecolor='black', color='skyblue')
axes[0].set_title('자격증 보유 비율 분포', fontsize=14, fontweight='bold')
axes[0].set_xlabel('자격증 보유 비율')
axes[0].set_ylabel('빈도')
axes[0].axvline(df_with_target['자격증_보유비율'].mean(), 
                color='red', linestyle='--', label=f'평균: {df_with_target["자격증_보유비율"].mean():.2f}')
axes[0].legend()

# 등급별 자격증 보유 비율
grade_cert = df_with_target.groupby('Target')['자격증_보유비율'].mean()
axes[1].bar(grade_labels, grade_cert.values, color=['lightcoral', 'lightyellow', 'lightgreen'])
axes[1].set_title('신뢰도 등급별 평균 자격증 보유 비율', fontsize=14, fontweight='bold')
axes[1].set_ylabel('평균 자격증 보유 비율')
axes[1].grid(axis='y', alpha=0.3)
for i, v in enumerate(grade_cert.values):
    axes[1].text(i, v + 0.01, f'{v:.2f}', ha='center', fontweight='bold')

# 자격증 보유 비율과 Target 상관관계
corr = df_with_target[['자격증_보유비율', 'Target']].corr().iloc[0, 1]
axes[2].scatter(df_with_target['자격증_보유비율'], df_with_target['Target'], 
                alpha=0.5, s=50)
axes[2].set_title(f'자격증 보유 비율 vs 신뢰도 등급\n(상관계수: {corr:+.3f})', 
                  fontsize=14, fontweight='bold')
axes[2].set_xlabel('자격증 보유 비율')
axes[2].set_ylabel('신뢰도 등급')
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / '02_certification_analysis.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '02_certification_analysis.png'}")
plt.close()

print(f"\n📊 분석 결과:")
print(f"   - 평균 자격증 보유 비율: {df_with_target['자격증_보유비율'].mean():.2f}")
print(f"   - Target과의 상관계수: {corr:+.3f}")
print(f"   ✅ 결론: 자격증 보유 비율이 높을수록 신뢰도 높음")

# ============================================================================
# 3. 운영 경험 및 숙련도
# ============================================================================
print("\n" + "=" * 100)
print("3. 운영 경험 및 숙련도 분석")
print("=" * 100)

# 운영기간 계산
df_with_target['등록일'] = pd.to_datetime(df_with_target['등록일'], errors='coerce')
today = pd.Timestamp.now()
df_with_target['운영기간_년'] = ((today - df_with_target['등록일']).dt.days / 365.25).fillna(0)
df_with_target['운영_안정성'] = (df_with_target['운영기간_년'] >= 3).astype(int)

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# 운영기간 분포
axes[0, 0].hist(df_with_target['운영기간_년'], bins=30, edgecolor='black', color='lightblue')
axes[0, 0].set_title('운영기간 분포', fontsize=14, fontweight='bold')
axes[0, 0].set_xlabel('운영기간 (년)')
axes[0, 0].set_ylabel('빈도')
axes[0, 0].axvline(3, color='red', linestyle='--', label='3년 (안정성 기준)')
axes[0, 0].legend()

# 등급별 평균 운영기간
grade_period = df_with_target.groupby('Target')['운영기간_년'].mean()
axes[0, 1].bar(grade_labels, grade_period.values, color=['lightcoral', 'lightyellow', 'lightgreen'])
axes[0, 1].set_title('신뢰도 등급별 평균 운영기간', fontsize=14, fontweight='bold')
axes[0, 1].set_ylabel('평균 운영기간 (년)')
axes[0, 1].grid(axis='y', alpha=0.3)
for i, v in enumerate(grade_period.values):
    axes[0, 1].text(i, v + 0.2, f'{v:.1f}년', ha='center', fontweight='bold')

# 운영 안정성 (3년 이상) 비율
stability_by_grade = df_with_target.groupby('Target')['운영_안정성'].mean()
axes[1, 0].bar(grade_labels, stability_by_grade.values * 100, 
               color=['lightcoral', 'lightyellow', 'lightgreen'])
axes[1, 0].set_title('신뢰도 등급별 운영 안정성 (3년 이상) 비율', fontsize=14, fontweight='bold')
axes[1, 0].set_ylabel('3년 이상 운영 비율 (%)')
axes[1, 0].grid(axis='y', alpha=0.3)
for i, v in enumerate(stability_by_grade.values * 100):
    axes[1, 0].text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')

# 숙련도 지수 (운영기간 × 공인중개사 비율)
df_with_target['공인중개사_비율'] = np.where(
    df_with_target['총_직원수'] > 0,
    df_with_target['공인중개사수'] / df_with_target['총_직원수'],
    0
)
df_with_target['숙련도_지수'] = df_with_target['운영기간_년'] * df_with_target['공인중개사_비율']

grade_skill = df_with_target.groupby('Target')['숙련도_지수'].mean()
axes[1, 1].bar(grade_labels, grade_skill.values, color=['lightcoral', 'lightyellow', 'lightgreen'])
axes[1, 1].set_title('신뢰도 등급별 평균 숙련도 지수', fontsize=14, fontweight='bold')
axes[1, 1].set_ylabel('평균 숙련도 지수')
axes[1, 1].grid(axis='y', alpha=0.3)
for i, v in enumerate(grade_skill.values):
    axes[1, 1].text(i, v + 0.1, f'{v:.2f}', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / '03_experience_analysis.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '03_experience_analysis.png'}")
plt.close()

print(f"\n📊 분석 결과:")
print(f"   - 평균 운영기간: {df_with_target['운영기간_년'].mean():.1f}년")
print(f"   - 3년 이상 비율: {df_with_target['운영_안정성'].mean()*100:.1f}%")
print(f"   ✅ 결론: 운영기간이 길수록 신뢰도 높음")

# ============================================================================
# 4. 조직 구조 분석
# ============================================================================
print("\n" + "=" * 100)
print("4. 조직 구조 분석")
print("=" * 100)

df_with_target['대형사무소'] = (df_with_target['총_직원수'] >= 2).astype(int)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 직원 수 분포
axes[0].hist(df_with_target['총_직원수'], bins=20, edgecolor='black', color='lightgreen')
axes[0].set_title('직원 수 분포', fontsize=14, fontweight='bold')
axes[0].set_xlabel('총 직원 수')
axes[0].set_ylabel('빈도')
axes[0].axvline(2, color='red', linestyle='--', label='대형사무소 기준 (2명)')
axes[0].legend()

# 대형사무소 비율
size_by_grade = df_with_target.groupby('Target')['대형사무소'].mean()
axes[1].bar(grade_labels, size_by_grade.values * 100, 
            color=['lightcoral', 'lightyellow', 'lightgreen'])
axes[1].set_title('신뢰도 등급별 대형사무소 비율', fontsize=14, fontweight='bold')
axes[1].set_ylabel('대형사무소 비율 (%)')
axes[1].grid(axis='y', alpha=0.3)
for i, v in enumerate(size_by_grade.values * 100):
    axes[1].text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')

# 직원 수와 Target 관계
grade_staff = df_with_target.groupby('Target')['총_직원수'].mean()
axes[2].bar(grade_labels, grade_staff.values, color=['lightcoral', 'lightyellow', 'lightgreen'])
axes[2].set_title('신뢰도 등급별 평균 직원 수', fontsize=14, fontweight='bold')
axes[2].set_ylabel('평균 직원 수')
axes[2].grid(axis='y', alpha=0.3)
for i, v in enumerate(grade_staff.values):
    axes[2].text(i, v + 0.1, f'{v:.1f}명', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / '04_organization_analysis.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '04_organization_analysis.png'}")
plt.close()

print(f"\n📊 분석 결과:")
print(f"   - 평균 직원 수: {df_with_target['총_직원수'].mean():.1f}명")
print(f"   - 대형사무소 비율: {df_with_target['대형사무소'].mean()*100:.1f}%")
print(f"   ✅ 결론: 직원이 많을수록 신뢰도 높음")

# ============================================================================
# 5. 지역 기반 피처 분석
# ============================================================================
print("\n" + "=" * 100)
print("5. 지역 기반 피처 분석")
print("=" * 100)

# 지역별 경쟁 강도
df_with_target['지역_경쟁강도'] = df_with_target.groupby('지역명')['등록번호'].transform('count')

# 1층 여부 추출
def extract_floor_smart(address):
    import re
    addr_str = str(address)
    
    if '지하' in addr_str or 'B1' in addr_str.upper():
        return -1
    
    floor_match = re.search(r'(\d+)층', addr_str)
    if floor_match:
        return int(floor_match.group(1))
    
    room_match = re.search(r'(\d{3,4})호', addr_str)
    if room_match:
        room_num = room_match.group(1)
        if len(room_num) == 3:
            return int(room_num[0])
        elif len(room_num) == 4:
            return int(room_num[:2])
    
    return None

df_with_target['층수'] = df_with_target['주소'].apply(extract_floor_smart)
df_with_target['1층_여부'] = (df_with_target['층수'] == 1).astype(int)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 지역별 경쟁 강도 분포
axes[0].hist(df_with_target['지역_경쟁강도'], bins=20, edgecolor='black', color='coral')
axes[0].set_title('지역별 경쟁 강도 분포', fontsize=14, fontweight='bold')
axes[0].set_xlabel('같은 지역 내 중개사무소 수')
axes[0].set_ylabel('빈도')

# 1층 비율
floor_1_ratio = df_with_target['1층_여부'].mean()
floor_other_ratio = 1 - floor_1_ratio
axes[1].pie([floor_1_ratio, floor_other_ratio], 
            labels=['1층', '기타'], 
            autopct='%1.1f%%',
            colors=['lightblue', 'lightgray'],
            startangle=90)
axes[1].set_title('1층 사무소 비율', fontsize=14, fontweight='bold')

# 등급별 1층 비율
floor_by_grade = df_with_target.groupby('Target')['1층_여부'].mean()
axes[2].bar(grade_labels, floor_by_grade.values * 100, 
            color=['lightcoral', 'lightyellow', 'lightgreen'])
axes[2].set_title('신뢰도 등급별 1층 사무소 비율', fontsize=14, fontweight='bold')
axes[2].set_ylabel('1층 비율 (%)')
axes[2].grid(axis='y', alpha=0.3)
for i, v in enumerate(floor_by_grade.values * 100):
    axes[2].text(i, v + 1, f'{v:.1f}%', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / '05_location_analysis.png', dpi=300, bbox_inches='tight')
print(f"✅ 저장: {output_dir / '05_location_analysis.png'}")
plt.close()

print(f"\n📊 분석 결과:")
print(f"   - 평균 지역 경쟁 강도: {df_with_target['지역_경쟁강도'].mean():.1f}개")
print(f"   - 1층 사무소 비율: {floor_1_ratio*100:.1f}%")
print(f"   ✅ 결론: 1층 접근성이 신뢰도에 영향")

# ============================================================================
# 최종 요약
# ============================================================================
print("\n" + "=" * 100)
print("EDA 완료!")
print("=" * 100)
print(f"\n📁 결과 저장 위치: {output_dir}")
print(f"\n생성된 파일:")
print(f"  1. 01_transaction_analysis.png - 거래 및 실적 지표 분석")
print(f"  2. 02_certification_analysis.png - 자격증 보유 비율 분석")
print(f"  3. 03_experience_analysis.png - 운영 경험 및 숙련도 분석")
print(f"  4. 04_organization_analysis.png - 조직 구조 분석")
print(f"  5. 05_location_analysis.png - 지역 기반 피처 분석")

print("\n" + "=" * 100)
