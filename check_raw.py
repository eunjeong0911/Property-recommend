path = r"C:\dev\study\eunjeong\SKN18-FINAL-1TEAM\data\raw\부동산중개업자정보.csv"

try:
    with open(path, "rb") as f:
        raw = f.read(200)
    
    print("Raw bytes:", raw)
    print("Decoded utf-8:", raw.decode("utf-8", errors="replace"))
except Exception as e:
    print(f"Error: {e}")
