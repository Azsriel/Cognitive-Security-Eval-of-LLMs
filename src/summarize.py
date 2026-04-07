# summarize.py

import pandas as pd
from pathlib import Path

def load_csv(path: str) -> pd.DataFrame:
    """Try UTF-8, then Windows-1252, then Latin-1 as final fallback."""
    for encoding in ["utf-8", "windows-1252", "latin-1"]:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Could not decode {path} with any known encoding.")

LABEL_NAMES = {
    "benign" : "Benign",
    "ccs1"   : "Authority",
    "ccs2"   : "Context_Poisoning",
    "ccs3"   : "Goal_Conflict",
    "ccs4"   : "Role_Confusion",
    "ccs5"   : "False_Premise",
    "ccs6"   : "Cognitive_Overload",
    "ccs7"   : "Emotional_Manipulation"
}

VERDICTS = ["PASS", "WARN", "FAIL", "UNKNOWN"]

def summarize_results(
    results_csv : str,
    summary_csv : str = "summary.csv",
    label_col   : str = "label",
    verdict_col : str = "verdict"
) -> pd.DataFrame:
    """
    Reads the pipeline results CSV and outputs PASS/WARN/FAIL
    counts per CCS class to console and a summary CSV.

    Args:
        results_csv : Path to the pipeline output CSV
        summary_csv : Path to save the summary CSV
        label_col   : Column name for the CCS label
        verdict_col : Column name for the verifier verdict

    Returns:
        Summary DataFrame
    """
    df = load_csv(results_csv)
    #df = pd.read_csv(results_csv, encoding="windows-1252")

    # Normalize columns
    df[label_col]   = df[label_col].str.strip().str.lower()
    df[verdict_col] = df[verdict_col].str.strip().str.upper()

    classes = [c for c in LABEL_NAMES if c in df[label_col].unique()]

    # ── BUILD SUMMARY ─────────────────────────────────────────────────────────
    rows = []
    for cls in classes:
        subset       = df[df[label_col] == cls]
        total        = len(subset)
        verdict_counts = subset[verdict_col].value_counts()

        row = {
            "label"         : cls,
            "vulnerability" : LABEL_NAMES[cls],
            "total"         : total,
        }
        for v in VERDICTS:
            row[v] = int(verdict_counts.get(v, 0))

        rows.append(row)

    # ── TOTALS ROW ────────────────────────────────────────────────────────────
    totals = {
        "label"         : "ALL",
        "vulnerability" : "Combined",
        "total"         : sum(r["total"] for r in rows),
    }
    for v in VERDICTS:
        totals[v] = sum(r[v] for r in rows)
    rows.append(totals)

    summary = pd.DataFrame(rows)

    # ── CONSOLE OUTPUT ────────────────────────────────────────────────────────
    print("\n── CCS Verdict Summary ──\n")
    print(f"{'Label':<8} {'Vulnerability':<26} {'Total':>6} {'PASS':>6} {'WARN':>6} {'FAIL':>6} {'UNKNOWN':>8}")
    print("─" * 72)

    for _, row in summary.iterrows():
        is_total = row["label"] == "ALL"
        if is_total:
            print("─" * 72)
        print(
            f"{row['label']:<8} "
            f"{row['vulnerability']:<26} "
            f"{int(row['total']):>6} "
            f"{int(row['PASS']):>6} "
            f"{int(row['WARN']):>6} "
            f"{int(row['FAIL']):>6} "
            f"{int(row['UNKNOWN']):>8}"
        )

    print()

    # ── SAVE CSV ──────────────────────────────────────────────────────────────
    summary.to_csv(summary_csv, index=False)
    print(f"Summary saved to: {summary_csv}\n")

    return summary


if __name__ == "__main__":
    summarize_results(results_csv = "output_final.csv",summary_csv = "summary.csv")
    summarize_results(results_csv = "output_final_normal.csv",summary_csv = "summary_raw.csv")