import pandas as pd

# -----------------------------
# Step 1: Load your existing CSV
# -----------------------------
input_file = "ppi_va_county.csv"   # <-- change if needed
df = pd.read_csv(input_file)

# -----------------------------
# Step 2: Standardize column names
#    (adjust these if your column names differ)
# -----------------------------
df.columns = [
    "FIPS",
    "County",
    "Incarcerated",
    "Census_population",
    "Total_population",
    "Incarceration_rate_per_100k"
]

# Ensure the incarcerated column is numeric
df["Incarcerated"] = pd.to_numeric(df["Incarcerated"], errors="coerce")

# -----------------------------
# Step 3: Compute county share
# -----------------------------
total_incarcerated = df["Incarcerated"].sum()
df["County_pct"] = df["Incarcerated"] / total_incarcerated

# -----------------------------
# Step 4: Apply VADOC population
# -----------------------------
VADOC_TOTAL = 22885
df["Estimated_Returnees"] = df["County_pct"] * VADOC_TOTAL
df["Estimated_Returnees"] = df["Estimated_Returnees"].round(2)

# -----------------------------
# Step 5: Save final CSV
# -----------------------------
output_file = "ppi_va_with_returnees.csv"
df.to_csv(output_file, index=False)

print("Done! Saved as:", output_file)
print(df.head())
