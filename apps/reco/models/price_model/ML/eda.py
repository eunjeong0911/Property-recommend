"""
Feature Engineering EDA - Simplified Version
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set font for Korean
try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
except:
    print("Warning: Korean font not available")

# Load data
data_path = Path(r"C:\dev\SKN18-FINAL-1TEAM\data\actual_transaction_price\월세_모델링용(24.08~25.10).csv")

print(f"Loading data from: {data_path}")
df = pd.read_csv(data_path, encoding='utf-8')

# Convert numeric columns
numeric_cols = ['임대면적', '층', '건축년도', '보증금(만원)', '임대료(만원)', 
                '기준금리', 'KORIBOR', 'CD', '무담보콜금리', '기업대출', 
                '전세자금대출', '변동형주택담보대출', '소비자물가']

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"Data loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")

# Create output directory
output_dir = Path("eda_plots")
output_dir.mkdir(exist_ok=True)

# Calculate target variable
avg_rate = df['기준금리'].mean() if '기준금리' in df.columns else 3.5
interest_rate = (avg_rate + 2.0) / 100.0
df['converted_deposit'] = df['보증금(만원)'] + (df['임대료(만원)'] * 12) / interest_rate
df['pyeong'] = df['임대면적'] / 3.3
df['price_per_pyeong'] = df['converted_deposit'] / df['pyeong']

print(f"\nPrice per pyeong statistics:")
print(df['price_per_pyeong'].describe())

# 1. Target distribution
fig, axes = plt.subplots(1, 2, figsize=(15, 5))
axes[0].hist(df['price_per_pyeong'].dropna(), bins=50, edgecolor='black', alpha=0.7)
axes[0].set_xlabel('Price per Pyeong (10K KRW)')
axes[0].set_ylabel('Frequency')
axes[0].set_title('Distribution of Price per Pyeong')

axes[1].boxplot(df['price_per_pyeong'].dropna())
axes[1].set_ylabel('Price per Pyeong (10K KRW)')
axes[1].set_title('Boxplot of Price per Pyeong')
plt.tight_layout()
plt.savefig(output_dir / '01_target_distribution.png', dpi=300, bbox_inches='tight')
print(f"Saved: 01_target_distribution.png")
plt.close()

# 2. Price by district
gu_stats = df.groupby('자치구명')['price_per_pyeong'].agg(['mean', 'median', 'count']).sort_values('mean', ascending=False)
print(f"\nTop 10 districts by price:")
print(gu_stats.head(10))

fig, ax = plt.subplots(figsize=(12, 6))
gu_sorted = gu_stats.sort_values('mean', ascending=True)
ax.barh(range(len(gu_sorted)), gu_sorted['mean'])
ax.set_yticks(range(len(gu_sorted)))
ax.set_yticklabels(gu_sorted.index)
ax.set_xlabel('Average Price per Pyeong (10K KRW)')
ax.set_title('Average Price by District')
plt.tight_layout()
plt.savefig(output_dir / '02_price_by_gu.png', dpi=300, bbox_inches='tight')
print(f"Saved: 02_price_by_gu.png")
plt.close()

# 3. Price by building type
building_stats = df.groupby('건물용도')['price_per_pyeong'].agg(['mean', 'median', 'count'])
print(f"\nPrice by building type:")
print(building_stats)

fig, ax = plt.subplots(figsize=(10, 6))
df.boxplot(column='price_per_pyeong', by='건물용도', ax=ax)
ax.set_xlabel('Building Type')
ax.set_ylabel('Price per Pyeong (10K KRW)')
ax.set_title('Price Distribution by Building Type')
plt.suptitle('')
plt.tight_layout()
plt.savefig(output_dir / '03_price_by_building_type.png', dpi=300, bbox_inches='tight')
print(f"Saved: 03_price_by_building_type.png")
plt.close()

# 4. Price by floor
df_floor = df[df['층'].notna()].copy()
df_floor['floor_bin'] = pd.cut(df_floor['층'], bins=[-10, 0, 3, 6, 11, 70], 
                                labels=['Basement', 'Low', 'Mid', 'Mid-High', 'High'])
floor_stats = df_floor.groupby('floor_bin')['price_per_pyeong'].agg(['mean', 'median', 'count'])
print(f"\nPrice by floor:")
print(floor_stats)

fig, axes = plt.subplots(1, 2, figsize=(15, 5))
axes[0].scatter(df_floor['층'], df_floor['price_per_pyeong'], alpha=0.3, s=10)
axes[0].set_xlabel('Floor')
axes[0].set_ylabel('Price per Pyeong (10K KRW)')
axes[0].set_title('Price vs Floor')

df_floor.boxplot(column='price_per_pyeong', by='floor_bin', ax=axes[1])
axes[1].set_xlabel('Floor Category')
axes[1].set_ylabel('Price per Pyeong (10K KRW)')
axes[1].set_title('Price by Floor Category')
plt.suptitle('')
plt.tight_layout()
plt.savefig(output_dir / '04_price_by_floor.png', dpi=300, bbox_inches='tight')
print(f"Saved: 04_price_by_floor.png")
plt.close()

# 5. Time series
monthly_stats = df.groupby('연월')['price_per_pyeong'].agg(['mean', 'median', 'count'])
print(f"\nMonthly statistics:")
print(monthly_stats)

fig, axes = plt.subplots(2, 1, figsize=(15, 10))
axes[0].plot(monthly_stats.index, monthly_stats['mean'], marker='o', label='Mean')
axes[0].plot(monthly_stats.index, monthly_stats['median'], marker='s', label='Median')
axes[0].set_xlabel('Month')
axes[0].set_ylabel('Price per Pyeong (10K KRW)')
axes[0].set_title('Monthly Price Trend')
axes[0].legend()
axes[0].grid(True, alpha=0.3)
axes[0].tick_params(axis='x', rotation=45)

axes[1].bar(monthly_stats.index, monthly_stats['count'])
axes[1].set_xlabel('Month')
axes[1].set_ylabel('Transaction Count')
axes[1].set_title('Monthly Transaction Volume')
axes[1].tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.savefig(output_dir / '05_time_series.png', dpi=300, bbox_inches='tight')
print(f"Saved: 05_time_series.png")
plt.close()

# 6. Correlation
corr_cols = ['임대면적', '층', '건축년도', '보증금(만원)', '임대료(만원)', 'price_per_pyeong']
if '기준금리' in df.columns:
    corr_cols.append('기준금리')
if 'KORIBOR' in df.columns:
    corr_cols.append('KORIBOR')

corr_matrix = df[corr_cols].corr()
print(f"\nCorrelation with price_per_pyeong:")
print(corr_matrix['price_per_pyeong'].sort_values(ascending=False))

fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
ax.set_title('Correlation Heatmap')
plt.tight_layout()
plt.savefig(output_dir / '06_correlation_heatmap.png', dpi=300, bbox_inches='tight')
print(f"Saved: 06_correlation_heatmap.png")
plt.close()

# 7. District x Building Type
pivot_table = df.pivot_table(values='price_per_pyeong', index='자치구명', 
                              columns='건물용도', aggfunc='mean')
print(f"\nDistrict x Building Type:")
print(pivot_table)

fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
ax.set_title('Average Price by District and Building Type')
ax.set_xlabel('Building Type')
ax.set_ylabel('District')
plt.tight_layout()
plt.savefig(output_dir / '07_gu_building_heatmap.png', dpi=300, bbox_inches='tight')
print(f"Saved: 07_gu_building_heatmap.png")
plt.close()

print(f"\n{'='*60}")
print("EDA Complete!")
print(f"Plots saved to: {output_dir.absolute()}")
print(f"{'='*60}")
