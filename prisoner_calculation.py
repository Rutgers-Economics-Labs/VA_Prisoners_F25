import pandas as pd
import numpy as np

# --- CONFIGURATION ---
INPUT_FILE = 'ppi.csv'
TOTAL_ANNUAL_RELEASES = 12680 

def clean_data_value(x):
    """
    Cleans a value that might be a string with quotes and commas (e.g., '"33,413"')
    and converts it to a float.
    """
    if isinstance(x, str):
        # Remove double quotes, single quotes, and commas
        clean_str = x.replace('"', '').replace("'", "").replace(',', '').strip()
        if clean_str == '': 
            return 0
        return float(clean_str)
    return float(x) if x else 0

try:
    # 1. Load the Data
    # We remove the 'thousands' param and handle cleaning manually to be safe with your quotes
    df = pd.read_csv(INPUT_FILE, on_bad_lines='skip')

    # 2. Identify Columns (Robust Matching)
    # This finds the column even if your CSV has quotes around the header text
    name_col = [c for c in df.columns if "Virginia counties" in c][0]
    
    # We look for "Number of people" to find the prisoner count column
    prisoner_col = [c for c in df.columns if "Number of people" in c][0]
    
    # We look for "Census population" (or "Total population" if you prefer)
    pop_col = [c for c in df.columns if "Census population" in c][0]

    # 3. Clean and Convert Data
    # Apply the cleaning function to ensure "33,413" becomes 33413.0
    df[prisoner_col] = df[prisoner_col].apply(clean_data_value).fillna(0).astype(int)
    df[pop_col] = df[pop_col].apply(clean_data_value).fillna(0).astype(int)

    # 4. Calculate Totals
    total_ppi_population = df[prisoner_col].sum()
    print(f"DEBUG: Found {total_ppi_population} total prisoners in the CSV.")
    print(f"DEBUG: Using VADOC Baseline: {TOTAL_ANNUAL_RELEASES} annual releases.")

    # 5. Generate the JavaScript Object
    js_output = "const countyMockData = {\n"
    
    for index, row in df.iterrows():
        county_name = row[name_col]
        
        # Clean the name for the map ID (e.g., "Accomack County" -> "Accomack")
        # BUT keep "City" if it's an independent city to avoid confusion
        if " County" in county_name:
            clean_name = county_name.replace(" County", "")
        else:
            clean_name = county_name # Keep "City" or other suffixes for independent cities
            # If your map requires "Richmond" instead of "Richmond City", uncomment the line below:
            # clean_name = clean_name.replace(" City", "")

        raw_count = row[prisoner_col]
        census_pop = row[pop_col]
        
        # THE FORMULA: (County Count / Total Count) * 12680
        if total_ppi_population > 0:
            est_annual = int((raw_count / total_ppi_population) * TOTAL_ANNUAL_RELEASES)
        else:
            est_annual = 0

        # Formats the line for your HTML file
        js_output += f'    "{clean_name}": {{ pop: {census_pop}, prisoners: {est_annual} }},\n'

    js_output += "};"

    # 6. Output
    print("-" * 30)
    print("COPY THIS BLOCK INTO YOUR HTML:")
    print("-" * 30)
    print(js_output)

except Exception as e:
    print("Error:", e)
    print("Tip: Make sure the file is named 'ppi.csv' and is in the same folder.")