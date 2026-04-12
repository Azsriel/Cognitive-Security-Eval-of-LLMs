# effectiveness_analysis.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
PIPELINE_CSV = "summary.csv"
RAW_CSV      = "summary_raw.csv"
OUTPUT_DIR   = "analysis_output/output"

LABEL_ORDER  = ["benign", "ccs1", "ccs2", "ccs3", "ccs4", "ccs5", "ccs6", "ccs7"]

Path(OUTPUT_DIR).mkdir(exist_ok=True)

# ── LABEL NAMES (pull from CSV directly, no hardcoding needed) ────────────────
def load_summary(path: str) -> pd.DataFrame:
    for enc in ["utf-8", "windows-1252", "latin-1"]:
        try:
            df = pd.read_csv(path, encoding=enc)
            df["label"] = df["label"].str.strip().str.lower()
            df = df[df["label"] != "all"]
            df = df.set_index("label")
            return df
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Could not decode {path}")

pipeline = load_summary(PIPELINE_CSV)
raw      = load_summary(RAW_CSV)

# Pull vulnerability names directly from the CSV instead of hardcoded dict
labels = [l for l in LABEL_ORDER if l in pipeline.index and l in raw.index]
pipeline = pipeline.loc[labels]
raw      = raw.loc[labels]

# Use vulnerability column from CSV as display names
LABEL_NAMES = pipeline["vulnerability"].to_dict()
display_labels = [LABEL_NAMES.get(l, l) for l in labels]

# ── METRIC CALCULATIONS ───────────────────────────────────────────────────────

def verdict_rates(df: pd.DataFrame) -> pd.DataFrame:
    total = df["total"].replace(0, np.nan)   # lowercase
    return pd.DataFrame({
        "pass_rate" : df["PASS"] / total,
        "warn_rate" : df["WARN"] / total,
        "fail_rate" : df["FAIL"] / total,
    }, index=df.index)

pipe_rates = verdict_rates(pipeline)
raw_rates  = verdict_rates(raw)

# ── EFFECTIVENESS SCORE ───────────────────────────────────────────────────────
# Formula:
#   PASS=+1, WARN=0.5, FAIL=-1 (weighted verdicts)
#   score = (PASS - FAIL) / Total  → range [-1, +1]
#   effectiveness = pipeline_score - raw_score  → range [-2, +2]
#
# Overcompensation penalty:
#   If pipeline WARN+FAIL rate > raw WARN+FAIL rate, the pipeline made things
#   worse. This is captured naturally — effectiveness will be negative.
#   We also compute an overcompensation flag explicitly for the heatmap.

def weighted_score(df: pd.DataFrame) -> pd.Series:
    total = df["total"].replace(0, np.nan)   # lowercase
    return (df["PASS"] - (df["FAIL"] + 0.5*df["WARN"])) / total

pipe_score = weighted_score(pipeline)
raw_score  = weighted_score(raw)
effectiveness = pipe_score - raw_score

# Overcompensation: pipeline is worse than raw on WARN+FAIL combined
pipe_bad = pipe_rates["warn_rate"] + pipe_rates["fail_rate"]
raw_bad  = raw_rates["warn_rate"]  + raw_rates["fail_rate"]
overcompensation = (pipe_bad - raw_bad).clip(lower=0)  # only positive = worse

# ── SUMMARY TABLE ─────────────────────────────────────────────────────────────
print("\n── Effectiveness Analysis ──\n")
print(f"{'Label':<8} {'Vulnerability':<26} "
      f"{'Raw Score':>10} {'Pipe Score':>11} "
      f"{'Effect.':>9} {'Overcomp.':>10}")
print("─" * 80)

for lbl in labels:
    print(
        f"{lbl:<8} {LABEL_NAMES.get(lbl, lbl):<26} "
        f"{raw_score[lbl]:>10.3f} {pipe_score[lbl]:>11.3f} "
        f"{effectiveness[lbl]:>9.3f} {overcompensation[lbl]:>10.3f}"
    )

print("─" * 80)
print(f"\nMean effectiveness : {effectiveness.mean():.3f}")
print(f"Mean overcompensation: {overcompensation.mean():.3f}\n")

# ── BUILD HEATMAP DATA ────────────────────────────────────────────────────────
# Rows = metrics, Cols = vulnerability labels
display_labels = [LABEL_NAMES.get(l, l) for l in labels]

heatmap_data = pd.DataFrame({
    "PASS Rate (Raw)"      : raw_rates.loc[labels, "pass_rate"].values,
    "WARN Rate (Raw)"      : raw_rates.loc[labels, "warn_rate"].values,
    "FAIL Rate (Raw)"      : raw_rates.loc[labels, "fail_rate"].values,
    "PASS Rate (Pipeline)" : pipe_rates.loc[labels, "pass_rate"].values,
    "WARN Rate (Pipeline)" : pipe_rates.loc[labels, "warn_rate"].values,
    "FAIL Rate (Pipeline)" : pipe_rates.loc[labels, "fail_rate"].values,
    "Effectiveness Score"  : effectiveness.loc[labels].values,
    "Overcompensation"     : overcompensation.loc[labels].values,
}, index=display_labels).T  # rows=metrics, cols=vulnerabilities

# ── PLOT 1: MAIN HEATMAP ──────────────────────────────────────────────────────
fig, axes = plt.subplots(
    3, 1, figsize=(14, 14),
    gridspec_kw={"height_ratios": [3, 3, 2]}
)
fig.suptitle("CCS Pipeline Effectiveness Analysis", fontsize=15, fontweight="bold", y=0.98)

def draw_heatmap(ax, data, title, cmap, vmin, vmax, fmt=".2f", annotate=True):
    im = ax.imshow(data.values.astype(float), cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(data.columns)))
    ax.set_xticklabels(data.columns, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(range(len(data.index)))
    ax.set_yticklabels(data.index, fontsize=9)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    plt.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
    if annotate:
        for i in range(len(data.index)):
            for j in range(len(data.columns)):
                val = float(data.values[i, j])
                ax.text(j, i, f"{val:{fmt}}", ha="center", va="center",
                        fontsize=8, color="white" if abs(val) > 0.6 else "black")

# Panel 1: Raw verdict rates
raw_panel = heatmap_data.loc[
    ["PASS Rate (Raw)", "WARN Rate (Raw)", "FAIL Rate (Raw)"]
]
draw_heatmap(axes[0], raw_panel,
             "Verdict Rates — Without Pipeline",
             cmap="RdYlGn", vmin=0, vmax=1)

# Panel 2: Pipeline verdict rates
pipe_panel = heatmap_data.loc[
    ["PASS Rate (Pipeline)", "WARN Rate (Pipeline)", "FAIL Rate (Pipeline)"]
]
draw_heatmap(axes[1], pipe_panel,
             "Verdict Rates — With Pipeline",
             cmap="RdYlGn", vmin=0, vmax=1)

# Panel 3: Effectiveness + Overcompensation
eff_panel = heatmap_data.loc[["Effectiveness Score", "Overcompensation"]]
draw_heatmap(axes[2], eff_panel,
             "Effectiveness Score  |  Overcompensation",
             cmap="RdYlGn", vmin=-1, vmax=1)

plt.tight_layout(rect=[0, 0, 1, 0.97])
out1 = f"{OUTPUT_DIR}/effectiveness_heatmap.png"
plt.savefig(out1, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {out1}")

# ── PLOT 2: DELTA HEATMAP ─────────────────────────────────────────────────────
# Shows how much each verdict rate changed from raw → pipeline
delta_data = pd.DataFrame({
    "ΔPASS (Pipeline - Raw)" : (pipe_rates.loc[labels, "pass_rate"]
                                - raw_rates.loc[labels, "pass_rate"]).values,
    "ΔWARN (Pipeline - Raw)" : (pipe_rates.loc[labels, "warn_rate"]
                                - raw_rates.loc[labels, "warn_rate"]).values,
    "ΔFAIL (Pipeline - Raw)" : (pipe_rates.loc[labels, "fail_rate"]
                                - raw_rates.loc[labels, "fail_rate"]).values,
}, index=display_labels).T

fig, ax = plt.subplots(figsize=(14, 5))
draw_heatmap(ax, delta_data,
             "Verdict Rate Delta (Pipeline − Raw)\n"
             "Green = improvement  |  Red = regression",
             cmap="RdYlGn", vmin=-0.5, vmax=0.5)
plt.tight_layout()
out2 = f"{OUTPUT_DIR}/delta_heatmap.png"
plt.savefig(out2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {out2}")

# ── PLOT 3: EFFECTIVENESS BAR CHART ──────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 5))
x      = np.arange(len(labels))
width  = 0.35
colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in effectiveness.values]

bars = ax.bar(x - width/2, effectiveness.values, width,
              color=colors, label="Effectiveness Score", zorder=3)
ax.bar(x + width/2, overcompensation.values, width,
       color="#e67e22", alpha=0.8, label="Overcompensation", zorder=3)

ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax.set_xticks(x)
ax.set_xticklabels(display_labels, rotation=25, ha="right", fontsize=9)
ax.set_ylabel("Score")
ax.set_title("Pipeline Effectiveness and Overcompensation by Vulnerability",
             fontsize=12, fontweight="bold")
ax.legend()
ax.grid(axis="y", alpha=0.3, zorder=0)
ax.set_ylim(-1.2, 1.2)

# Annotate bars
for bar in bars:
    h = bar.get_height()
    ax.annotate(f"{h:.2f}",
                xy=(bar.get_x() + bar.get_width() / 2, h),
                xytext=(0, 4), textcoords="offset points",
                ha="center", fontsize=8)

plt.tight_layout()
out3 = f"{OUTPUT_DIR}/effectiveness_bar.png"
plt.savefig(out3, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {out3}")

# ── EXPORT STATS CSV ──────────────────────────────────────────────────────────
stats_df = pd.DataFrame({
    "label"              : labels,
    "vulnerability"      : [LABEL_NAMES.get(l, l) for l in labels],
    "raw_pass_rate"      : raw_rates.loc[labels, "pass_rate"].values,
    "raw_warn_rate"      : raw_rates.loc[labels, "warn_rate"].values,
    "raw_fail_rate"      : raw_rates.loc[labels, "fail_rate"].values,
    "pipe_pass_rate"     : pipe_rates.loc[labels, "pass_rate"].values,
    "pipe_warn_rate"     : pipe_rates.loc[labels, "warn_rate"].values,
    "pipe_fail_rate"     : pipe_rates.loc[labels, "fail_rate"].values,
    "raw_score"          : raw_score.loc[labels].values,
    "pipeline_score"     : pipe_score.loc[labels].values,
    "effectiveness"      : effectiveness.loc[labels].values,
    "overcompensation"   : overcompensation.loc[labels].values,
})
out4 = f"{OUTPUT_DIR}/effectiveness_stats.csv"
stats_df.to_csv(out4, index=False)
print(f"Saved: {out4}")