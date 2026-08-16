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

# Updated target columns to match the requested order
TARGET_COLUMNS = [
    "ISO_1", "HASC_1", "NAME_1", "POP_Coverage(%)", "Samples", 
    "LDP", "CM_CP", "area_sqkm", "EW_km", "NS_km"
]

PATHS = {
    "gadm_csv": Path("OUTPUT_PROV/gadm41_THA.csv"),
    "logs_dir": Path("OUTPUT_SAMPL"),
    "sqlite_db": Path("OUTPUT_LDP/LDP_Province.sqlite"),
    "out_csv": Path("OUTPUT_LDP/ProvinceLDP.csv"),
    "readme": Path("README.md")
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
    row_data = {"HASC_1": hasc, "MSL_min_mean_max": None, "Samples": None}
    
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
                        row_data.update(json.loads(line))
                    except json.JSONDecodeError:
                        logging.warning(f"Failed to parse JSON in {log_path.name}")
                        
                # Extract Samples from the data table row
                elif line.startswith(hasc):
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            # Parse integer and reformat with thousand comma
                            samples_val = int(parts[3].replace(',', ''))
                            row_data["Samples"] = f"{samples_val:,}"
                        except ValueError:
                            # Fallback if parsing fails
                            row_data["Samples"] = parts[3]
                        
    except Exception as e:
        logging.error(f"Failed to read log file {log_path}: {e}")

    return row_data

def parse_all_pipeline_logs(hasc_series: pd.Series, base_dir: Path) -> pd.DataFrame:
    """Iterates through all province identifiers and extracts log data."""
    parsed_data = []

    for hasc in hasc_series:
        # Normalize folder name format (e.g., "TH.AC" -> "TH_AC")
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

def highlight_low_coverage(val: Any) -> str:
    """Formats coverage percentage with colored emojis based on thresholds:
    - 0-70%: 🔴 Red
    - 70-80%: 🟡 Yellow
    - 80-100%: 🟢 Green
    """
    if pd.isna(val):
        return str(val)
    
    try:
        num_val = float(val)
    except (ValueError, TypeError):
        return str(val)
        
    if 0 <= num_val < 70:
        return f'🔴 {num_val}'
    elif 70 <= num_val < 80:
        return f'🟡 {num_val}'
    elif 80 <= num_val <= 100:
        return f'🟢 {num_val}'
        
    return str(num_val)

def export_summary_files(df: pd.DataFrame, csv_path: Path, readme_path: Path) -> None:
    """Exports sorted raw CSV and a GitHub-flavored Markdown README with banner and links."""
    available_cols = [col for col in TARGET_COLUMNS if col in df.columns]
    df_out = df[available_cols].copy()

    # Sort ascending FIRST so that both the CSV and README are ordered correctly
    if "POP_Coverage(%)" in df_out.columns:
        df_out["POP_Coverage(%)"] = pd.to_numeric(df_out["POP_Coverage(%)"], errors='coerce')
        df_out = df_out.sort_values(by="POP_Coverage(%)", ascending=False)

    # 1. Export standard CSV (Natively sorted, no HTML, no emojis)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(csv_path, index=False)
    logging.info(f"Saved CSV: {csv_path}")

    # 2. Format and Export README.md
    df_md = df_out.copy()

    if "POP_Coverage(%)" in df_md.columns:
        # Apply the emoji warning for the Markdown table only
        df_md["POP_Coverage(%)"] = df_md["POP_Coverage(%)"].apply(highlight_low_coverage)
        
    # Convert HASC_1 to HTML hyperlink opening in new tab for README
    if "HASC_1" in df_md.columns:
        df_md["HASC_1"] = df_md["HASC_1"].apply(
            lambda x: f"<a href='OUTPUT_LDP/{str(x).replace('.', '_')}/{str(x).replace('.', '_')}_OnePage.pdf' target='_blank'>{x}</a>" if pd.notna(x) else x
        )

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

    # Step 1: Read reference
    logging.info(f"Reading GADM reference data from {PATHS['gadm_csv']}...")
    df_gadm = read_gadm_data(PATHS['gadm_csv'])

    # Steps 2-4: Parse logs
    logging.info("Parsing pipeline logs for metadata and stats...")
    df_logs = parse_all_pipeline_logs(df_gadm['HASC_1'], PATHS['logs_dir'])

    # Merge data
    if not df_logs.empty:
        df_merged = pd.merge(df_gadm, df_logs, on="HASC_1", how="left")
    else:
        logging.warning("No log data extracted. Proceeding with base GADM data only.")
        df_merged = df_gadm.copy()

    # Steps 5-6: Exports
    export_sqlite(df_merged, PATHS['sqlite_db'])
    export_summary_files(df_merged, PATHS['out_csv'], PATHS['readme'])
    
    logging.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
