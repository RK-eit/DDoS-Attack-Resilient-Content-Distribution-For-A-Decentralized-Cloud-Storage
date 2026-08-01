"""
make_figure.py
Regenerates Fig. 1 of "DDoS Attack Resilient Content Distribution For A
Decentralized Cloud Storage" (fig_pareto.pdf).

Plots targeted-attack cost min_i r_i (Proposition 1) against raw storage
expansion, for the six schemes of Table III, under the two regimes of
Hypothesis 1 (piece-level deduplication absent / present).

Design note: all scheme names are carried in a single shared legend below
the panels rather than as inline annotations, so that schemes sitting at
nearly the same coordinates (3x replication at 9.00 G and the regularised
concatenation design at 9.05 G) cannot produce colliding labels.

Run:  python3 make_figure.py        ->  writes fig_pareto.pdf (and .png)
Requires: matplotlib
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ----------------------------------------------------------------------
# Scheme coordinates.  Storage figures and min_i r_i are those reported in
# Table III and Proposition 1 of the paper.
#   name                       storage(G)  min r_i (no dedup)  (dedup)
SCHEMES = [
    ("Storj (deployed)",            2.76, 1, 1, "s", "#4C4C4C"),
    ("$2\\times$ replication",      6.00, 2, 1, "o", "#0072B2"),
    ("$3\\times$ replication",      9.00, 3, 1, "o", "#009E73"),
    ("$4\\times$ replication",     12.00, 4, 1, "o", "#CC79A7"),
    ("Concat., as in (6)",          8.95, 2, 2, "D", "#D55E00"),
    ("Concat., $r_{\\min}=3$ (9)",  9.05, 3, 3, "^", "#E69F00"),
]

PANELS = [
    ("(a) Hypothesis 1 fails: no piece-level deduplication", 2),
    ("(b) Hypothesis 1 holds: piece-level deduplication",    3),
]

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "axes.linewidth": 0.6,
    "pdf.fonttype": 42,
})

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.55), sharey=True)

for ax, (title, col) in zip(axes, PANELS):
    # replication frontier  r = storage / (t/d) = storage / 3
    ax.plot([2.4, 12.6], [0.8, 4.2], ls="--", lw=0.8, color="#999999",
            zorder=1)
    for name, stor, r_nodedup, r_dedup, marker, colour in SCHEMES:
        y = r_nodedup if col == 2 else r_dedup
        # replication drawn as large open markers so that a concatenation
        # marker at nearly the same coordinates stays visible inside it
        if marker == "o":
            ax.plot(stor, y, marker=marker, ms=9, mfc="none", mec=colour,
                    mew=1.4, ls="none", zorder=3)
        else:
            ax.plot(stor, y, marker=marker, ms=5.5, mfc=colour, mec=colour,
                    ls="none", zorder=4)
    ax.set_title(title, pad=5)
    ax.set_xlabel("raw storage expansion factor ($\\times G$)")
    ax.set_xlim(2.0, 13.0)
    ax.set_ylim(0.5, 4.6)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_xticks([2, 4, 6, 8, 10, 12])
    ax.grid(True, lw=0.3, color="#DDDDDD", zorder=0)
    ax.set_axisbelow(True)

axes[0].set_ylabel("targeted-attack cost  $\\min_i r_i$")

handles = []
for name, _, _, _, marker, colour in SCHEMES:
    if marker == "o":
        handles.append(Line2D([], [], marker=marker, ms=7, mfc="none",
                              mec=colour, mew=1.3, ls="none", label=name))
    else:
        handles.append(Line2D([], [], marker=marker, ms=5, mfc=colour,
                              mec=colour, ls="none", label=name))
handles.append(Line2D([], [], ls="--", lw=0.8, color="#999999",
                      label="replication frontier"))

fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
           bbox_to_anchor=(0.5, -0.015), columnspacing=1.6,
           handletextpad=0.5)

fig.tight_layout(rect=[0, 0.155, 1, 1])
fig.savefig("fig_pareto.pdf", bbox_inches="tight", pad_inches=0.02)
fig.savefig("fig_pareto.png", dpi=200, bbox_inches="tight", pad_inches=0.02)
print("wrote fig_pareto.pdf and fig_pareto.png")
