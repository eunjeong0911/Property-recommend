import sys
print(f"Python executable: {sys.executable}")
try:
    import pandas as pd
    print(f"Pandas version: {pd.__version__}")
    print("Pandas import successful!")
except ImportError as e:
    print(f"Pandas import failed: {e}")
