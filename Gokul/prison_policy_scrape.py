import requests
import pandas as pd
from bs4 import BeautifulSoup

# -----------------------------
# 1. Download the web page
# -----------------------------
url = "https://www.prisonpolicy.org/origin/va/2020/county.html"
response = requests.get(url)
response.raise_for_status()

# -----------------------------
# 2. Parse HTML with BeautifulSoup
# -----------------------------
soup = BeautifulSoup(response.text, "html.parser")

# The table we want is the first <table> on the page
table = soup.find("table")

# -----------------------------
# 3. Convert HTML table to DataFrame
# -----------------------------
df = pd.read_html(str(table))[0]

# -----------------------------
# 4. Clean column names (optional)
# -----------------------------
df.columns = [col.strip() for col in df.columns]

# -----------------------------
# 5. Save to CSV
# -----------------------------
output_file = "ppi_va_county.csv"
df.to_csv(output_file, index=False)

print(f"Saved table to {output_file}")
print(df.head())
