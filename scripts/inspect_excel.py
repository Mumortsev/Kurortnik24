
import pandas as pd
import sys

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

try:
    df = pd.read_excel(r"c:\Antigravity\Project\data\template_for_client.xlsx")
    cols = [str(c).encode('ascii', 'replace').decode('ascii') for c in df.columns.tolist()]
    print("Columns:", cols)
    print("\nFirst 5 rows:")
    # Convert to string and replace non-ascii
    print(df.head().to_string().encode('ascii', 'replace').decode('ascii'))
    
    print("\nData types:")
    print(df.dtypes)
except Exception as e:
    print(f"Error: {e}")
