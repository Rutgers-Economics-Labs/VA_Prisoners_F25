import pandas as pd
import csv
import io

# --- CONFIGURATION ---
INPUT_FILE = 'industry.csv' 

# NAICS codes for "Second Chance" friendly industries
TARGET_SECTORS = {
    '23': 'Construction',
    '31': 'Manufacturing', 
    '32': 'Manufacturing',
    '33': 'Manufacturing',
    '48': 'Transportation/Logistics',
    '49': 'Transportation/Logistics', 
    '562': 'Waste Management'
}

def clean_employment_num(val):
    if pd.isna(val) or val == '':
        return 0
    if isinstance(val, str):
        # Remove commas, spaces, quotes
        clean_str = val.replace(',', '').replace(' ', '').replace('"', '').strip()
        if not clean_str: return 0
        return int(float(clean_str))
    return int(val)

# --- 1. ROBUST FILE LOADER (Fixes the UTF-16/0xff error) ---
def load_data(filepath):
    # List of likely encodings for government/Excel files
    encodings = ['utf-16', 'utf-16le', 'utf-8', 'latin1', 'cp1252']
    # List of likely separators
    separators = ['\t', ',']
    
    for enc in encodings:
        for sep in separators:
            try:
                # print(f"Trying encoding: {enc} with separator: {repr(sep)}...")
                df = pd.read_csv(filepath, sep=sep, encoding=enc, on_bad_lines='skip', engine='python')
                
                # Validation: Does it look like real data?
                # Check if we have more than 1 column and typical column names exist
                if df.shape[1] > 1 and any("Area" in c for c in df.columns):
                    print(f"SUCCESS! Loaded with encoding: {enc} and separator: {repr(sep)}")
                    return df
            except Exception:
                continue
    
    raise ValueError("Could not decode file. Please open 'qcew_data.csv' in Excel and save as 'CSV UTF-8'.")

try:
    # Load the data using the safe loader
    df = load_data(INPUT_FILE)
    print(f"Successfully loaded {len(df)} rows.")

    # --- 2. IDENTIFY COLUMNS ---
    # Robust search for columns
    area_col = next((c for c in df.columns if "Area" in c and "Type" not in c), None)
    industry_col = next((c for c in df.columns if "Industry" in c and "Code" in c), None)
    own_col = next((c for c in df.columns if "Ownership" in c), None)
    
    # Find Employment Column
    emp_col = next((c for c in df.columns if "Average Employment" in c), None)
    if not emp_col:
        emp_col = next((c for c in df.columns if "Employment" in c), None)

    if not all([area_col, industry_col, emp_col]):
        print("ERROR: Could not identify required columns. Found:", df.columns.tolist())
        exit()

    print(f"Columns: Area='{area_col}', Industry='{industry_col}', Emp='{emp_col}'")

    # --- 3. ANALYZE DATA ---
    results = {}

    for index, row in df.iterrows():
        area = row[area_col]
        industry_str = str(row[industry_col])
        emp_count = clean_employment_num(row[emp_col])
        
        # OWNERSHIP FILTER: 
        # Ensure we don't double count. We want "Aggregate" or "Total" for the sums.
        if own_col:
            ownership = str(row[own_col])
            # If it's a specific industry row (not 00000), we usually want "Private" or "Aggregate"
            # But simpler logic: If "Total Government" or "Federal" etc, skip it to avoid duplicates
            # if we are just looking for general job availability. 
            # Ideally, look for "Total Government" + "Private" = Total. 
            # Or just look for "Aggregate of all types".
            if "Aggregate" not in ownership and "Total" not in ownership:
                if "00000" in industry_str: 
                    # If this is the Grand Total row, strictly require Aggregate
                     continue

        # Init Results Dict
        if area not in results:
            results[area] = {'total_jobs': 0, 'second_chance_jobs': 0, 'top_sectors': {}}

        # CHECK 1: Total Jobs (Code 00000 or 10)
        if industry_str.startswith("00") or industry_str.startswith("10 "):
            # Only update total if it's the aggregate ownership
            if own_col and "Aggregate" in str(row[own_col]):
                results[area]['total_jobs'] = max(results[area]['total_jobs'], emp_count)
            elif not own_col:
                results[area]['total_jobs'] = max(results[area]['total_jobs'], emp_count)
            continue 

        # CHECK 2: Second Chance Sector?
        naics_code = industry_str.split(' ')[0].split('-')[0]
        
        sector_name = None
        for prefix, name in TARGET_SECTORS.items():
            if naics_code.startswith(prefix):
                sector_name = name
                break
        
        if sector_name:
            results[area]['second_chance_jobs'] += emp_count
            if sector_name not in results[area]['top_sectors']:
                results[area]['top_sectors'][sector_name] = 0
            results[area]['top_sectors'][sector_name] += emp_count

    # --- 4. OUTPUT ---
    print("\n" + "="*50)
    print("VIRGINIA COUNTY JOB ANALYSIS")
    print("="*50)
    
    js_output = "const countyJobData = {\n"
    
    for area, data in sorted(results.items()):
        total = data['total_jobs']
        sc_jobs = data['second_chance_jobs']
        
        # If total is 0 (missing aggregate row), approximate it using the sum of what we found (risky but better than 0)
        if total == 0 and sc_jobs > 0:
            total = sc_jobs # Fallback
            
        share = round((sc_jobs / total * 100), 1) if total > 0 else 0
        dominant_sector = max(data['top_sectors'], key=data['top_sectors'].get) if data['top_sectors'] else "None"
        
        clean_key = area.replace(" County", "").replace(" City", "")
        
        print(f"{area}: {sc_jobs}/{total} ({share}%) - Top: {dominant_sector}")
        
        js_output += f'    "{clean_key}": {{ jobs: {sc_jobs}, total_jobs: {total}, share: {share}, top_sector: "{dominant_sector}" }},\n'

    js_output += "};"
    
    print("\n" + "-"*30)
    print("COPY THIS FOR YOUR WEBSITE:")
    print("-"*30)
    print(js_output)

except Exception as e:
    print(f"Critical Error: {e}")
    import traceback
    traceback.print_exc()