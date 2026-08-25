"""
04 — Diagnostic figures for the Sprint 1 / mentor update.

These are DESIGN and DATA-VALIDITY figures, not results figures. No parking
utilisation has been measured yet — the CoM archives are not downloaded. Each
plot answers a scoping question that determines whether the analysis is viable.

    fig1  intervention timing vs sensor coverage   -> which segments are analysable
    fig2  capacity change, treatment vs control    -> is the panel a valid counterfactual
    fig3  obstruction factor by location type      -> is a single Grattan factor defensible

Run:  python analysis/src/04_figures.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config as C

FIGS = C.OUTPUTS / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
    "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
})
TEAL, CORAL, GREY, AMBER = "#1b7f79", "#d1495b", "#8d99ae", "#e09f3e"


def load():
    d = pd.read_csv(C.PROCESSED / "intervention_dates.csv", dtype={"sid": str})
    d["intervention_date"] = pd.to_datetime(d["intervention_date"])
    d["loc"] = np.select([d.cbd == 1, d.metro == 1, d.regional == 1],
                         ["CBD", "Metro", "Regional"], "?")
    return d


# ---------------------------------------------------------------- fig 1
def fig_timing(d):
    tr = d[d.treatment_or_control == "treatment"].copy()
    tr = tr.sort_values("intervention_date")
    dated = tr.dropna(subset=["intervention_date"]).reset_index(drop=True)
    undated = tr[tr.intervention_date.isna()]

    fig, ax = plt.subplots(figsize=(9, 6.5))
    s_start, s_end = pd.Timestamp(C.SENSOR_START), pd.Timestamp(C.SENSOR_END)

    ax.axvspan(s_start, s_end, color=TEAL, alpha=0.10, zorder=0)
    ax.axvspan(pd.Timestamp(C.COVID_START), pd.Timestamp(C.COVID_END),
               color=CORAL, alpha=0.10, zorder=0)

    colors = {"protected bike lane": TEAL, "pedestrian": AMBER,
              "regional_reallocation": GREY}
    y = np.arange(len(dated))
    for itype, sub in dated.groupby("intervention_type"):
        idx = sub.index.values
        ax.scatter(sub.intervention_date, idx, s=26,
                   color=colors.get(itype, GREY), label=itype,
                   edgecolor="white", linewidth=0.4, zorder=3)

    usable = dated[dated.sensor_usable]
    ax.scatter(usable.intervention_date, usable.index.values, s=115,
               facecolor="none", edgecolor=CORAL, linewidth=1.4, zorder=4,
               label="sensor before/after possible")

    ax.axvline(s_end, color=TEAL, ls="--", lw=1.2, zorder=2)
    ax.text(s_end, len(dated) * 1.005, "  sensors end\n  May 2020",
            color=TEAL, va="bottom", ha="left", fontsize=8, fontweight="bold")
    ax.text(s_start + pd.Timedelta(days=200), len(dated) * 0.965,
            "City of Melbourne sensor archive", color=TEAL, fontsize=8, alpha=0.9)

    ax.set_yticks([])
    ax.set_ylabel(f"96 treatment segments (sorted by date; {len(undated)} undated, not shown)")
    ax.set_xlabel("Intervention date (decoded from financial-year quarter)")
    ax.set_title("Only 11 of 96 treatment segments can be analysed with sensor data\n"
                 "Everything else is imagery-only", loc="left", fontsize=11, fontweight="bold")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    fig.savefig(FIGS / "fig1_intervention_timing_vs_sensor_coverage.png")
    plt.close(fig)


# ---------------------------------------------------------------- fig 2
def fig_capacity(d):
    q = pd.read_csv(C.PROCESSED / "qtr_attributes_filled.csv", dtype=str)
    q["cap"] = pd.to_numeric(q["StreetInScopeOnStreetParkingCap"], errors="coerce")
    q["qdate"] = pd.to_datetime(q["qdate"])
    q["sid"] = pd.to_numeric(q["sid"], errors="coerce").astype("Int64").astype(str)
    q["grp"] = q["sid"].map(d.set_index("sid").treatment_or_control)

    ch = q.dropna(subset=["cap"]).groupby(["sid", "grp"])["cap"].nunique()
    ch = ch.reset_index(name="n")
    rate = ch.groupby("grp").apply(lambda t: 100 * (t.n > 1).mean())

    delta = pd.read_csv(C.OUTPUTS / "capacity_change_from_panel.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))

    ax1.bar(["Control\n(n=204)", "Treatment\n(n=85)"],
            [rate.get("control", 0), rate.get("treatment", 0)],
            color=[GREY, TEAL], width=0.55)
    for i, v in enumerate([rate.get("control", 0), rate.get("treatment", 0)]):
        ax1.text(i, v + 2, f"{v:.1f}%", ha="center", fontweight="bold")
    ax1.set_ylim(0, 108)
    ax1.set_ylabel("% of segments whose recorded capacity\never changes across 105 quarters")
    ax1.set_title("Control capacity is essentially frozen", loc="left",
                  fontsize=10, fontweight="bold")

    bl = delta[delta.itype == "protected bike lane"]["delta"]
    ax2.hist(bl, bins=np.arange(-36, 10, 3), color=TEAL, edgecolor="white", linewidth=0.6)
    ax2.axvline(0, color=GREY, lw=1)
    ax2.axvline(bl.mean(), color=CORAL, ls="--", lw=1.4,
                label=f"mean {bl.mean():+.1f} spaces")
    ax2.set_xlabel("Change in recorded parking spaces (post − pre)")
    ax2.set_ylabel("Protected bike lane segments")
    ax2.set_title(f"{(bl<0).mean()*100:.0f}% lost capacity, {(bl==0).mean()*100:.0f}% unchanged",
                  loc="left", fontsize=10, fontweight="bold")
    ax2.legend(frameon=False, fontsize=8)

    fig.suptitle("IV's capacity field is maintained for treatment sites only — "
                 "it cannot serve as the counterfactual",
                 fontsize=11, fontweight="bold", x=0.5, y=1.04)
    fig.savefig(FIGS / "fig2_capacity_change_validity.png")
    plt.close(fig)


# ---------------------------------------------------------------- fig 3
def fig_obstruction(d):
    c = pd.read_csv(C.OUTPUTS / "segment_kerb_capacity.csv")
    c["loc"] = np.select([c.cbd == 1, c.metro == 1, c.regional == 1],
                         ["CBD", "Metro", "Regional"], "?")
    c["f"] = c.cap_reported / c.cap_geometric
    c = c[c.f.between(0, 1)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2),
                                   gridspec_kw={"width_ratios": [1, 1.25]})

    order = ["CBD", "Metro", "Regional"]
    data = [c.loc[c["loc"] == g, "f"].dropna() for g in order]
    bp = ax1.boxplot(data, tick_labels=[f"{g}\n(n={len(x)})" for g, x in zip(order, data)],
                     patch_artist=True, widths=0.5, showfliers=False,
                     medianprops=dict(color="white", lw=1.6))
    for patch, col in zip(bp["boxes"], [CORAL, TEAL, AMBER]):
        patch.set_facecolor(col)
    ax1.axhline(c.f.median(), color=GREY, ls="--", lw=1.2)
    ax1.text(0.55, c.f.median() + 0.015, f"global {c.f.median():.2f}", color=GREY,
             va="bottom", ha="left", fontsize=8)
    ax1.set_ylabel("Parkable share of kerb\n(IV reported ÷ raw geometric)")
    ax1.set_title("A single factor hides a 2× CBD/Metro gap", loc="left",
                  fontsize=10, fontweight="bold")

    for g, col in zip(order, [CORAL, TEAL, AMBER]):
        s = c[c["loc"] == g]
        ax2.scatter(s.cap_geometric, s.cap_reported, s=16, alpha=0.65,
                    color=col, label=f"{g} (median {s.f.median():.2f})",
                    edgecolor="white", linewidth=0.3)
    lim = np.array([0, c.cap_geometric.quantile(0.99)])
    ax2.plot(lim, lim, color=GREY, ls=":", lw=1, label="1:1 (no obstruction)")
    ax2.plot(lim, lim * c.f.median(), color="black", ls="--", lw=1.2,
             label=f"global factor {c.f.median():.2f}")
    ax2.set_xlim(0, lim[1]); ax2.set_ylim(0, lim[1])
    ax2.set_xlabel("Geometric capacity (kerb length ÷ 6.0 m)")
    ax2.set_ylabel("IV reported capacity (spaces)")
    ax2.set_title("Calibration against IV's consultant counts", loc="left",
                  fontsize=10, fontweight="bold")
    ax2.legend(frameon=False, fontsize=7.5, loc="upper left")

    fig.suptitle("Grattan Appendix D obstruction factor, calibrated on 270 segments",
                 fontsize=11, fontweight="bold", x=0.5, y=1.02)
    fig.savefig(FIGS / "fig3_obstruction_factor_calibration.png")
    plt.close(fig)


def main():
    d = load()
    fig_timing(d)
    fig_capacity(d)
    fig_obstruction(d)
    print("wrote 3 figures to", FIGS)


if __name__ == "__main__":
    main()
