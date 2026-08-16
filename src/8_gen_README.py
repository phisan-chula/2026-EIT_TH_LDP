import json
import sqlite3
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Target columns for final output
TARGET_COLUMNS = [
    "ISO_1", "HASC_1", "NAME_1", "POP_Coverage(%)", "Samples", 
    "LDP", "CM_CP", "area_sqkm", "EW_km", "NS_km"
]

PATHS = {
    "gadm_csv": Path("OUTPUT_PROV/gadm41_THA.csv"),
    "logs_dir": Path("OUTPUT_SAMPL"),
    "sqlite_db": Path("OUTPUT_LDP/LDP_Province.sqlite"),
    "out_csv": Path("OUTPUT_LDP/ProvinceLDP.csv"),
    "readme": Path("../README.md")
}

# ==========================================
# PIPELINE FUNCTIONS
# ==========================================

def read_gadm_data(csv_path: Path) -> pd.DataFrame:
    """Reads the GADM province CSV file into a pandas DataFrame."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    return pd.read_csv(csv_path)

def parse_single_log(log_path: Path, hasc: str) -> Dict[str, Any]:
    """Parses a single pipeline log file for MSL stats, JSONL metadata, and Sample counts."""
    # Initialize all potential target columns to ensure they are never "lost"
    row_data = {
        "HASC_1": hasc, 
        "MSL_min_mean_max": None, 
        "Samples": None,
        "POP_Coverage(%)": None,
        "EW_km": None,
        "NS_km": None,
        "area_sqkm": None
    }
    
    try:
        with log_path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Extract MSL stats
                if line.startswith("Points MSL min/mean/max [m.]"):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        row_data["MSL_min_mean_max"] = parts[1].strip()
                
                # Extract LDP and Coverage metadata
                elif line.startswith('{"meta": "LDP_Definition"') or line.startswith('{"meta": "Coverage_Analysis"'):
                    try:
                        data = json.loads(line)
                        # Normalize keys if the JSON outputs them slightly differently than TARGET_COLUMNS
                        if "POP_Coverage" in data and "POP_Coverage(%)" not in data:
                            data["POP_Coverage(%)"] = data["POP_Coverage"]
                        if "EW" in data and "EW_km" not in data:
                            data["EW_km"] = data["EW"]
                        if "NS" in data and "NS_km" not in data:
                            data["NS_km"] = data["NS"]
                            
                        row_data.update(data)
                    except json.JSONDecodeError:
                        logging.warning(f"Failed to parse JSON in {log_path.name}")
                        
                # Extract Samples from the data table row
                elif line.startswith(hasc):
                    parts = line.split()
                    
                    # Try to capture tail-end metrics just in case they print here instead of JSON
                    if len(parts) >= 6:
                        try:
                            if pd.isna(row_data.get("NS_km")): row_data["NS_km"] = parts[-1]
                            if pd.isna(row_data.get("EW_km")): row_data["EW_km"] = parts[-2]
                            if pd.isna(row_data.get("area_sqkm")): row_data["area_sqkm"] = parts[-3]
                        except Exception:
                            pass

                    if len(parts) >= 4:
                        try:
                            # Parse integer and reformat with thousand comma
                            samples_val = int(parts[3].replace(',', ''))
                            row_data["Samples"] = f"{samples_val:,}"
                        except ValueError:
                            row_data["Samples"] = parts[3]
                        
    except Exception as e:
        logging.error(f"Failed to read log file {log_path}: {e}")

    return row_data

def parse_all_pipeline_logs(hasc_series: pd.Series, base_dir: Path) -> pd.DataFrame:
    """Iterates through all province identifiers and extracts log data."""
    parsed_data = []

    for hasc in hasc_series:
        folder_name = hasc.replace('.', '_')
        log_path = base_dir / folder_name / f"{folder_name}_pipeline.log"
        
        if not log_path.exists():
            logging.warning(f"Log file missing for {hasc}: {log_path}")
            continue

        row_data = parse_single_log(log_path, hasc)
        parsed_data.append(row_data)

    return pd.DataFrame(parsed_data)

def export_sqlite(df: pd.DataFrame, output_path: Path) -> None:
    """Writes the merged DataFrame to a standard SQLite database."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(output_path) as conn:
            df.to_sql("LDP_Province", conn, if_exists="replace", index=False)
        logging.info(f"Saved SQLite database: {output_path}")
    except Exception as e:
        logging.error(f"Failed to save SQLite database: {e}")

def format_coverage_link(row) -> str:
    """Formats coverage percentage linking to PDF, keeping the emoji outside the HTML tag."""
    val = row['POP_Coverage(%)']
    hasc = row['HASC_1']
    
    if pd.isna(val) or pd.isna(hasc):
        return str(val)
    
    try:
        num_val = float(val)
    except (ValueError, TypeError):
        return str(val)
        
    if 0 <= num_val < 70:
        emoji = '🔴'
    elif 70 <= num_val < 80:
        emoji = '🟡'
    elif 80 <= num_val <= 100:
        emoji = '🟢'
    else:
        emoji = ''
        
    hasc_safe = str(hasc).replace('.', '_')
    pdf_url = f"https://github.com/phisan-chula/2026-EIT_TH_LDP/blob/main/src/OUTPUT_LDP/{hasc_safe}/{hasc_safe}_OnePage.pdf"
    
    # Emoji stays outside, number is wrapped in the anchor tag
    link = f"<a href='{pdf_url}' target='_blank'>{num_val}</a>"
    return f"{emoji} {link}".strip()

def format_hasc_anchor(row) -> str:
    """Creates a GitHub anchor link pointing to the QAQC Test Line section."""
    hasc = row['HASC_1']
    name = row['NAME_1']
    
    if pd.isna(hasc) or pd.isna(name):
        return str(hasc)
        
    # Match the GitHub markdown slug generation for: "### 🧭 Province: {NAME_1} ({HASC_1})"
    name_clean = str(name).lower().replace(' ', '-')
    hasc_clean = str(hasc).lower().replace('.', '')
    slug = f"-province-{name_clean}-{hasc_clean}"
    
    url = f"https://github.com/phisan-chula/2026-EIT_TH_LDP/tree/main/src/OUTPUT_LDP#{slug}"
    return f"<a href='{url}' target='_blank'>{hasc}</a>"

def export_summary_files(df: pd.DataFrame, csv_path: Path, readme_path: Path) -> None:
    """Exports sorted raw CSV and a GitHub-flavored Markdown README with banner and links."""
    available_cols = [col for col in TARGET_COLUMNS if col in df.columns]
    df_out = df[available_cols].copy()

    # Sort ascending FIRST so that both the CSV and README are ordered correctly
    if "POP_Coverage(%)" in df_out.columns:
        # Strip any accidental '%' string characters so pd.to_numeric doesn't turn them into NaNs
        clean_pop = df_out["POP_Coverage(%)"].astype(str).str.replace('%', '', regex=False)
        df_out["POP_Coverage(%)"] = pd.to_numeric(clean_pop, errors='coerce')
        df_out = df_out.sort_values(by="POP_Coverage(%)", ascending=False)

    # 1. Export standard CSV (Natively sorted, no HTML, no emojis)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(csv_path, index=False)
    logging.info(f"Saved CSV: {csv_path}")

    # 2. Format and Export README.md
    df_md = df_out.copy()

    # Step A: Format Coverage with PDF Link (must happen before we alter HASC_1)
    if "POP_Coverage(%)" in df_md.columns and "HASC_1" in df_md.columns:
        df_md["POP_Coverage(%)"] = df_md.apply(format_coverage_link, axis=1)

    # Step B: Format HASC_1 as the Anchor Link
    if "HASC_1" in df_md.columns and "NAME_1" in df_md.columns:
        df_md["HASC_1"] = df_md.apply(format_hasc_anchor, axis=1)

    readme_banner = """<div align="center">

<table width="100%">
  <tr>
    <td align="center" width="50%"><img src="Publication/SMST_logo.jpg" alt="SMST Logo" width="120"/></td>
    <td align="center" width="50%"><img src="Publication/APCP_logo.jpg" alt="APAC Logo" width="120"/></td>
  </tr>
</table>

# Thailand Low Distortion Map Coordinate System (TH-LDP)

### **Release Candidate 1 (RC-1, Aug 2026)**

*A collaborative initiative by **SMST** & **APAC***

</div>

---

## Provincial LDP: Aggregate Population Coverage Within the ±20 ppm Limit

*(Table is sorted by population coverage. Performance indicators: 🟢 80-100%, 🟡 70-80%, 🔴 <70%)*

"""

    try:
        with readme_path.open('w', encoding='utf-8') as f:
            f.write(readme_banner)
            f.write(df_md.to_markdown(index=False, tablefmt="github"))
        logging.info(f"Generated README: {readme_path}")
    except Exception as e:
        logging.error(f"Failed to write README.md: {e}")

# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    logging.info("Starting log parsing pipeline...")

    logging.info(f"Reading GADM reference data from {PATHS['gadm_csv']}...")
    df_gadm = read_gadm_data(PATHS['gadm_csv'])

    logging.info("Parsing pipeline logs for metadata and stats...")
    df_logs = parse_all_pipeline_logs(df_gadm['HASC_1'], PATHS['logs_dir'])

    if not df_logs.empty:
        df_merged = pd.merge(df_gadm, df_logs, on="HASC_1", how="left")
    else:
        logging.warning("No log data extracted. Proceeding with base GADM data only.")
        df_merged = df_gadm.copy()

    export_sqlite(df_merged, PATHS['sqlite_db'])
    export_summary_files(df_merged, PATHS['out_csv'], PATHS['readme'])
    
    logging.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
