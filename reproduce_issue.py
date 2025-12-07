import pandas as pd

path = r"C:\dev\study\eunjeong\SKN18-FINAL-1TEAM\data\raw\부동산중개업자정보.csv"
encodings = ["utf-8", "cp949", "euc-kr", "utf-16", "latin1"]

for enc in encodings:
    try:
        print(f"Testing {enc}...")
        df = pd.read_csv(path, encoding=enc, nrows=5)
        print(f"SUCCESS with {enc}!")
        print(df.columns.tolist())
        break
    except Exception as e:
        print(f"Failed {enc}: {e}")
