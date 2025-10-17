import pdfplumber
import pandas as pd

PDF_PATH = "communityrecidivismreport_fy2020starters_final.pdf"

RECIDIVATING_COMMUNITY_STARTERS_TITLE = "Recidivating FY2020 Community Starters: Employment During Follow-up Period"
RECIDIVATING_COMMUNITY_STARTERS_CSV_PATH = "data/recidivating_fy2020_community_starters_employment.csv"

PAGE_START = 9
PAGE_END = 103

IMAGE_TABLE_PAGE_NUMBERS = [11, 12]

def extract_section(lines, data_line, keywords, next_section_keyword, other_keyword=True):
    final_keywords = keywords.copy()
    if other_keyword:
        final_keywords = keywords + [None]
    
    section_data = [0] * len(final_keywords)
    index = 0
    while data_line < len(lines) and next_section_keyword not in lines[data_line]:
        count = lines[data_line].strip().split()[1].replace(",", "")
        if not count.isnumeric():
            data_line += 1
            continue
        for i, keyword in enumerate(final_keywords):
            if keyword == None or keyword in lines[data_line]:
                section_data[i] = count
                break
        
        index += 1 
        data_line += 1

    if index > len(final_keywords):
        raise ValueError("Warning: More lines than expected in section.")
    
    data_line += 1

    section_data.append(data_line)

    return section_data

def extract_data(pdf):

    data_list = []

    for i, page in enumerate(pdf.pages):
        text = page.extract_text()

        if i < PAGE_START or i > PAGE_END or not text:
            continue

        if i in IMAGE_TABLE_PAGE_NUMBERS:
            continue
        
        lines = text.splitlines()[:-1]
        title = lines[0].strip()

        if title == RECIDIVATING_COMMUNITY_STARTERS_TITLE:
            table = page.extract_table()
            df = pd.DataFrame(table)
            columns = ["Community Supervision Location", "Unemployed", "Unemployed %", "Employed <47%", "Employed <47% (%)", "Employed 47–77%", "Employed 47–77% (%)", "Employed >77%", "Employed >77% (%)"]
            df.columns = columns
            df = df.iloc[2:-1]
            df.to_csv(RECIDIVATING_COMMUNITY_STARTERS_CSV_PATH, index=False)
            continue

        second_line = lines[1].strip() if len(lines) > 1 else ""

        if second_line == "Starters" or second_line == "Supervisees":
            title += " " + second_line

        including_locations = ""

        if "includes" in second_line.lower():
            including_locations = second_line.split("includes")[-1].strip()
        else:
            third_line = lines[2].strip() if len(lines) > 2 else ""
            if "includes" in third_line.lower():
                including_locations = third_line.split("includes")[-1].strip()

        if including_locations.endswith(")"):
            including_locations = including_locations[:-1].strip()

        district_name, group_type = "", ""

        if "–" in title:
            district_name = title.split("–")[0].strip()
            group_type = title.split("–")[1].strip()
        else:
            district_name = "FY2020"
            group_type = title.replace(" FY2020 ", " ").strip()

        # print(f"{district_name} - {group_type} - {including_locations}")

        data_line = 1
        while not lines[data_line][2].isnumeric():
            data_line += 1

        total_count = lines[data_line].strip().split()[1].replace(",", "")

        while "Gender" not in lines[data_line]:
            data_line += 1

        gender_keywords = ["Male", "Female"]
        term_keywords = ["one term", "two terms", "three terms"]
        offense_keywords = ["Violent", "Property", "Drug"]
        age_keywords = ["younger than age 30", "ages 30 and 44", "ages 45 and 54"]
        supervision_keywords = ["Low", "Medium", "High", "Elevated"]
        multiple_drug_keywords = ["opioids and cocaine", "negative for opioids or cocaine", "opioids only", "cocaine only", "not tested for opioids or cocaine"]
        meth_keywords = ["positive"]
        compas_keywords = ["Low", "Medium", "High"]
        gang_keywords = ["had a known gang affiliation"]

        data_line += 1
        male_count, female_count, other_gender_count, data_line = extract_section(lines, data_line, gender_keywords, "Criminal History")
        one_term_count, two_term_count, three_term_count, zero_term_count, data_line = extract_section(lines, data_line, term_keywords, "DOC")
        violent_count, property_count, drug_count, other_offense_count, data_line = extract_section(lines, data_line, offense_keywords, "Age")
        age_below_30_count, age_30_44_count, age_45_54_count, age_55_above_count, data_line = extract_section(lines, data_line, age_keywords, "Supervision")
        low_supervision_count, medium_supervision_count, high_supervision_count, elevated_supervision_count, no_supervision_count, data_line = extract_section(lines, data_line, supervision_keywords, "Multiple Drugs")
        opiod_and_cocaine_count, negative_for_opiod_or_cocaine_count, opoid_only_count, cocaine_only_count, no_opoid_cocaine_test_count, no_drug_test_count, data_line = extract_section(lines, data_line, multiple_drug_keywords, "Meth")
        positive_meth_count, negative_meth_count, data_line = extract_section(lines, data_line, meth_keywords, "COMPAS")
        low_compas_count, medium_compas_count, high_compas_count, no_compas_count, data_line = extract_section(lines, data_line, compas_keywords, "Gang")
        gang_count, no_gang_count, data_line = extract_section(lines, data_line, gang_keywords, "Employment")
        
        data = {
            "District": district_name,
            "Group Type": group_type,
            "Including Locations": including_locations,
            "Total Count": total_count,
            "Male Count": male_count,
            "Female Count": female_count,
            "Other Gender Count": other_gender_count,
            "One Term Count": one_term_count,
            "Two Term Count": two_term_count,
            "Three Term Count": three_term_count,
            "Zero Term Count": zero_term_count,
            "Violent Offense Count": violent_count,
            "Property Offense Count": property_count,
            "Drug Offense Count": drug_count,
            "Other Offense Count": other_offense_count,
            "Age Below 30 Count": age_below_30_count,
            "Age 30-44 Count": age_30_44_count,
            "Age 45-54 Count": age_45_54_count,
            "Age 55 and Above Count": age_55_above_count,
            "Low Supervision Count": low_supervision_count,
            "Medium Supervision Count": medium_supervision_count,
            "High Supervision Count": high_supervision_count,
            "Elevated Supervision Count": elevated_supervision_count,
            "No Supervision Count": no_supervision_count,
            "Opiod and Cocaine Count": opiod_and_cocaine_count,
            "Negative for Opiod or Cocaine Count": negative_for_opiod_or_cocaine_count,
            "Opiod Only Count": opoid_only_count,
            "Cocaine Only Count": cocaine_only_count,
            "No Opiod Cocaine Test Count": no_opoid_cocaine_test_count,
            "No Drug Test Count": no_drug_test_count,
            "Positive Meth Count": positive_meth_count,
            "Negative Meth Count": negative_meth_count,
            "Low COMPAS Count": low_compas_count,
            "Medium COMPAS Count": medium_compas_count,
            "High COMPAS Count": high_compas_count,
            "No COMPAS Count": no_compas_count,
            "Gang Affiliation Count": gang_count,
            "No Gang Affiliation Count": no_gang_count
        }

        data_list.append(data)

    df = pd.DataFrame(data_list)
    df.to_csv("data/recidivating_fy2020_community_starters_summary.csv", index=False)
    print("Data extraction complete. CSV file saved.")

if __name__ == "__main__":
    with pdfplumber.open(PDF_PATH) as pdf:
        extract_data(pdf)