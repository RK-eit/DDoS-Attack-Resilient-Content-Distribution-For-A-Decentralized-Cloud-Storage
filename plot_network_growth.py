"""
plot_network_growth.py
Figure: network growth to robustness (Fig. 2b of DDoS_Resilient_DCS_v3).

This is Question A.3 of Kundu et al. (ICPADS 2023) answered comparatively:
at the fixed attack budget C = 360,000 that breaks Storj, how many vetted
nodes must the network hold before P(E_FX) <= 0.001?

Kundu et al. report N_v >= 31,525 for Storj.  Our own sweep, using the
budget-optimal adversary allocation (all 308 unvetted nodes first, then
the remaining budget on vetted nodes), gives a slightly smaller figure;
the difference is the allocation rounding already noted in Sec. V-G and
does not affect any conclusion.

Run:  python3 plot_network_growth.py    ->  fig_network.pdf / .png
Requires: mpmath, matplotlib
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpmath import mp, mpf, binomial

mp.dps = 50

Nu, cv, cu = 308, 50, 1
M = mpf("2.375e9")
C_FIXED = 360000
STORJ = (80, 29, 76, 4)
OURS = (120, 40, 114, 6)


def hyper_pmf(N, K, n, k):
    if k < 0 or k > n or k > K or (n - k) > (N - K):
        return mpf(0)
    return binomial(K, k) * binomial(N - K, n - k) / binomial(N, n)


def seg_loss(t, d, tv, tu, Nv_, NvA, Nu_, NuA):
    tau = t - d + 1
    px = [hyper_pmf(Nv_, NvA, tv, x) for x in range(tv + 1)]
    py = [hyper_pmf(Nu_, NuA, tu, y) for y in range(tu + 1)]
    return sum(px[x] * py[z - x]
               for z in range(tau, t + 1)
               for x in range(max(0, z - tu), min(z, tv) + 1))


def PEFX(Nv_, cfg, r, C=C_FIXED):
    t, d, tv, tu = cfg
    NuA = min(Nu, C // cu)
    NvA = min(Nv_, (C - cu * NuA) // cv)
    p = seg_loss(t, d, tv, tu, Nv_, int(NvA), Nu, int(NuA))
    return (1 - (1 - p) ** M) if r == 1 else min(mpf(1), M * p ** r)


def crossing_Nv(cfg, r, target, lo, hi, it=18):
    for _ in range(it):
        mid = (lo + hi) // 2
        if PEFX(mid, cfg, r) > target:
            lo = mid
        else:
            hi = mid
    return hi


CURVES = [
    ("Storj $(80,29)$",           STORJ, 1, "#4C4C4C", "-",  "s"),
    ("$(120,40)$, $r{=}1$",        OURS, 1, "#0072B2", "--", "o"),
    ("Proposed, $r_{\\min}{=}3$",  OURS, 3, "#D55E00", "-",  "^"),
]

nvs = list(range(25500, 36001, 700))
print("computing network-growth sweep ...")
series = []
for label, cfg, r, col, ls, mk in CURVES:
    ys = [float(PEFX(nv, cfg, r)) for nv in nvs]
    series.append((label, ys, col, ls, mk))
    print(f"  {label:28s} done")

nv_storj = crossing_Nv(STORJ, 1, mpf("0.001"), 25500, 60000)
p_ours_now = PEFX(25500, OURS, 3)
print(f"\n  Storj reaches P<=0.001 at N_v = {nv_storj:,}")
print(f"  Proposed at N_v = 25,500 already: P <= {mp.nstr(p_ours_now, 3)}")

plt.rcParams.update({
    "font.family": "serif", "font.size": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.0,
    "axes.linewidth": 0.6, "pdf.fonttype": 42,
})
fig, ax = plt.subplots(figsize=(3.42, 1.92))

ax.axhline(0.001, color="#2E7D32", lw=0.7, ls=":", zorder=1)
for label, ys, col, ls, mk in series:
    ax.semilogy(nvs, ys, ls=ls, color=col, lw=1.1, marker=mk, ms=2.6,
                mfc="none", mew=0.7, label=label, zorder=3)

# Curve bands in log10:  Storj -0.4..-5.8 | r=1 -6.7..-15.6 | r=3 -39..-66.
# The band -18..-36 is empty; both labels and the legend live there, with the
# labels on the LEFT half and the legend on the RIGHT half so their bounding
# boxes are horizontally disjoint.
ax.plot([nv_storj], [0.001], marker="*", ms=7, color="#B00020", zorder=6)
ax.annotate(f"Storj needs\n$N_v\\!=\\!{nv_storj:,}$",
            xy=(nv_storj, 1e-3), xytext=(25400, 1e-22),
            fontsize=6, ha="left", va="center",
            arrowprops=dict(arrowstyle="->", lw=0.55, color="#B00020"))
ax.plot([25500], [float(p_ours_now)], marker="*", ms=7,
        color="#D55E00", zorder=6)
ax.annotate("proposed robust\nalready",
            xy=(25500, float(p_ours_now)), xytext=(25400, 1e-32),
            fontsize=6, ha="left", va="center",
            arrowprops=dict(arrowstyle="->", lw=0.55, color="#D55E00"))

ax.set_xlabel("vetted nodes $N_v$")
ax.set_ylabel("$\\mathbb{P}(E_{F_X})$ at $C=3.6\\times10^{5}$")
ax.set_xlim(25000, 36200)
ax.set_xticks([26000, 28000, 30000, 32000, 34000, 36000])
ax.set_ylim(1e-70, 6)
ax.set_yticks([1e0, 1e-14, 1e-28, 1e-42, 1e-56, 1e-70])
ax.grid(True, lw=0.3, color="#DDDDDD", zorder=0)
ax.set_axisbelow(True)
ax.legend(loc="center right", frameon=False, borderpad=0.15,
          handlelength=1.5, labelspacing=0.2,
          bbox_to_anchor=(1.005, 0.60))

import figcheck; figcheck.report(fig, "fig_network")
fig.tight_layout(pad=0.3)
fig.savefig("fig_network.pdf", bbox_inches="tight", pad_inches=0.03)
fig.savefig("fig_network.png", dpi=220, bbox_inches="tight", pad_inches=0.03)
print("\nwrote fig_network.pdf / fig_network.png")
