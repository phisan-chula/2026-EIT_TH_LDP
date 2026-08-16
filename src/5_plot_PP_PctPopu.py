import argparse
import concurrent.futures
import copy
import importlib
import io
import sys
import matplotlib.pyplot as plt
import pandas as pd

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

# Dynamically import module starting with a digit
analyse_ldp = importlib.import_module("4_analyse_ldp")
LDP_Design = analyse_ldp.LDP_Design


def worker_process(offset, args_dict, province, prov_data):
    """Standalone worker function executed in parallel across offsets."""
    args = argparse.Namespace(**args_dict)
    args.OFFSET_PP = offset
    current_prov_data = copy.deepcopy(prov_data)

    # [CRITICAL FIX]: Force PP_MSL to "AUTO" so LDP_Design applies the offset 
    # against the True Mean MSL rather than a hardcoded PP_MSL from the TOML.
    current_prov_data["PP_MSL"] = "AUTO"

    # Suppress internal stdout from LDP_Design
    trap = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = trap
    try:
        ldp = LDP_Design(args, province, current_prov_data)
    finally:
        sys.stdout = old_stdout

    # Compute coverage metrics
    if "POP" in ldp.dfPP.columns:
        df_valid = ldp.dfPP[(ldp.dfPP.CSF_ppm >= -20) & (ldp.dfPP.CSF_ppm <= 20)]
        valid_points = len(df_valid)
        valid_pop = df_valid["POP"].sum()

        pt_pct = (valid_points / ldp.INITIAL_POINTS * 100) if ldp.INITIAL_POINTS > 0 else 0.0
        pop_pct = (valid_pop / ldp.INITIAL_POP * 100) if ldp.INITIAL_POP > 0 else 0.0

        if valid_points > 0:
            csf_min = df_valid["CSF_ppm"].min()
            csf_mean = df_valid["CSF_ppm"].mean()
            csf_max = df_valid["CSF_ppm"].max()
        else:
            csf_min = csf_mean = csf_max = 0.0
    else:
        valid_points = valid_pop = 0
        pt_pct = pop_pct = 0.0
        csf_min = csf_mean = csf_max = 0.0

    return {
        "MSL_PP": ldp.MSL_PP,
        "HAE_PP": ldp.HAE_PP,
        "Province": ldp.PROV_CODE,
        "Total_Pts": ldp.INITIAL_POINTS,
        "Valid_Pts": valid_points,
        "Pt_Coverage(%)": pt_pct,
        "Total_POP": ldp.INITIAL_POP,
        "Valid_POP": valid_pop,
        "POP_Coverage(%)": pop_pct,
        "CSF_Lower_ppm": csf_min,
        "CSF_Mean_ppm": csf_mean,
        "CSF_Upper_ppm": csf_max,
        "_OFFSET": offset,
        "_TRUE_MEAN_MSL": ldp.dfPP.MSL.mean(),
        "_RESULT_PATH": ldp.RESULT,
        "_FILE_CODE": ldp.FILE_CODE,
    }


def resolve_msl_params(prov_code: str, prov_data: dict, args: argparse.Namespace, true_mean_msl: float):
    """Resolves upper MSL, lower MSL, and step parameters prioritizing TOML POPU_PLOT over CLI args/defaults."""
    popu_plot = prov_data.get("POPU_PLOT")

    if isinstance(popu_plot, list) and len(popu_plot) == 3:
        upper_msl = float(popu_plot[0])
        lower_msl = float(popu_plot[1])
        step = float(popu_plot[2])
        print(f"[{prov_code}] POPU_PLOT found in TOML. Overriding MSL bounds: Upper={upper_msl}, Lower={lower_msl}, Step={step}")
        return upper_msl, lower_msl, step

    if popu_plot is not None:
        print(f"[{prov_code}] WARNING: POPU_PLOT must be an array of 3 values [upper, lower, step]. Falling back to CLI/defaults.")

    upper_msl = args.upper_msl if args.upper_msl is not None else true_mean_msl + 100.0
    lower_msl = args.lower_msl if args.lower_msl is not None else true_mean_msl - 200.0
    step = args.step

    return upper_msl, lower_msl, step


def validate_msl_bounds(prov_code: str, upper_msl: float, lower_msl: float, true_mean_msl: float) -> bool:
    """Validates MSL boundary conditions."""
    if upper_msl <= true_mean_msl:
        print(f"ERROR for {prov_code}: upper_msl ({upper_msl}) must be greater than mean MSL ({true_mean_msl:.2f} m).")
        return False
    if lower_msl >= true_mean_msl:
        print(f"ERROR for {prov_code}: lower_msl ({lower_msl}) must be less than mean MSL ({true_mean_msl:.2f} m).")
        return False
    if lower_msl >= upper_msl:
        print(f"ERROR for {prov_code}: lower_msl ({lower_msl}) must be lower than upper_msl ({upper_msl}).")
        return False
    return True


def render_coverage_plot(df_report: pd.DataFrame, prov_data: dict, meta: dict):
    """Generates and exports the SVG coverage plot."""
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(df_report["MSL_PP"], df_report["POP_Coverage(%)"], marker="o", color="b", linestyle="-", linewidth=2, label="Population Coverage")
    ax1.set_ylim(0, 100)
    ax1.set_ylabel("Population Coverage (%)", color="b", fontweight="bold")
    ax1.tick_params(axis="y", labelcolor="b")
    ax1.grid(True, linestyle="--", alpha=0.7)
    ax1.set_xlabel("Project Plane MSL (m)", fontweight="bold")

    true_mean_msl_plot = meta["_TRUE_MEAN_MSL"]
    ax1.axvline(x=true_mean_msl_plot, color="r", linestyle="--", linewidth=2, label=f"Topo MSL ({true_mean_msl_plot:.0f} m)")

    # The green dashed line still reads from the untouched original prov_data 
    if "PP_MSL" in prov_data and str(prov_data["PP_MSL"]).upper() != "AUTO":
        user_msl = float(prov_data["PP_MSL"])
        ax1.axvline(x=user_msl, color="g", linestyle="--", linewidth=2, label=f"LDP PP_MSL ({user_msl:.0f} m)")

    ax1.legend(loc="lower right")

    # Twin X-axis for HAE
    ax2 = ax1.twiny()
    undul_shift = df_report["HAE_PP"].iloc[0] - df_report["MSL_PP"].iloc[0]
    x1_limits = ax1.get_xlim()
    ax2.set_xlim(x1_limits[0] + undul_shift, x1_limits[1] + undul_shift)
    ax2.set_xlabel("Project Plane HAE (m)", fontweight="bold")

    plt.title(f"{meta['Province']}: Population Coverage vs Project Plane Offsets", pad=20, fontsize=14)
    plt.tight_layout()

    out_svg = meta["_RESULT_PATH"] / f"{meta['_FILE_CODE']}_Plot_PP_Popu.svg"
    plt.savefig(out_svg, format="svg")
    plt.close(fig)
    print(f"\n -> Plot saved successfully to: {out_svg}\n")


def process_single_province(province_code: str, args: argparse.Namespace, config_data: dict):
    """Processes pipeline analysis and plotting for a single province."""
    if province_code not in config_data:
        print(f"ERROR: Configuration for '{province_code}' not found in {args.toml}.")
        return

    prov_data = config_data[province_code]

    # Retrieve true mean MSL with baseline execution
    temp_args = copy.deepcopy(args)
    temp_args.OFFSET_PP = 0.0

    trap = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = trap
    try:
        temp_ldp = LDP_Design(temp_args, province_code, prov_data)
    finally:
        sys.stdout = old_stdout

    true_mean_msl = temp_ldp.dfPP.MSL.mean()

    # Resolve MSL range configuration
    upper_msl, lower_msl, step = resolve_msl_params(province_code, prov_data, args, true_mean_msl)

    if not validate_msl_bounds(province_code, upper_msl, lower_msl, true_mean_msl):
        return

    # Calculate relative offsets from absolute MSL targets
    lower_offset = lower_msl - true_mean_msl
    upper_offset = upper_msl - true_mean_msl

    offsets = []
    current_offset = lower_offset
    while current_offset <= upper_offset + (step * 0.01):
        offsets.append(current_offset)
        current_offset += step

    run_args = copy.deepcopy(args)
    run_args.upper_msl = upper_msl
    run_args.lower_msl = lower_msl
    run_args.step = step
    args_dict = vars(run_args)

    records = []
    print(f"[{province_code}] Starting ProcessPoolExecutor with {len(offsets)} offsets to compute (Mean MSL: {true_mean_msl:.2f} m)...")
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(
            worker_process,
            offsets,
            [args_dict] * len(offsets),
            [province_code] * len(offsets),
            [prov_data] * len(offsets),
        )
        for res in results:
            print(f"[{province_code}] OFFSET_PP [{res['_OFFSET']:.2f}] computed successfully.")
            records.append(res)

    df_records = [{k: v for k, v in rec.items() if not k.startswith("_")} for rec in records]
    df_report = pd.DataFrame(df_records)

    formats = ["+.2f", "+.2f", None, ".0f", ".0f", ".2f", ",.0f", ",.0f", ".2f", "+.1f", "+.1f", "+.1f"]
    print(f"\n==================================== LDP Population Coverage Analysis: {province_code} ====================================")
    print(df_report.to_markdown(index=False, floatfmt=formats))
    print("==========================================================================================================================")

    if not df_report.empty:
        render_coverage_plot(df_report, prov_data, records[0])


def main():
    parser = argparse.ArgumentParser(
        prog="5_plot_PP_PctPopu",
        description="Loop over PP MSL values to analyze population coverage and output as a dataframe and plot.",
    )
    parser.add_argument("province", help="HASC_1 province code (e.g., TH.BR) or 'ALL'")
    parser.add_argument("-t", "--toml", default="PROV_LDP.toml", help="TOML file containing province configuration data")
    parser.add_argument("-b", "--bypass", action="store_true", help="Bypass MSL outliers filtering")
    parser.add_argument("--upper_msl", type=float, default=None, help="Upper Project Plane MSL")
    parser.add_argument("--lower_msl", type=float, default=None, help="Lower Project Plane MSL")
    parser.add_argument("--step", type=float, default=20.0, help="PP step, default 20 meter")

    args = parser.parse_args()

    with open(args.toml, "rb") as f:
        config_data = tomllib.load(f)

    if args.province.upper() == "ALL":
        provinces = list(config_data.keys())
        print(f"Found {len(provinces)} provinces in {args.toml}. Processing sequentially...")
        for prov in provinces:
            print(f"\n>>> Processing province: {prov}")
            process_single_province(prov, args, config_data)
        print("All provinces processed successfully.")
    else:
        process_single_province(args.province, args, config_data)


if __name__ == "__main__":
    main()
