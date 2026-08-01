"""
plot_budget_sweep.py
Figure: attack-budget sweep (Fig. 2a of DDoS_Resilient_DCS_v3).

For each attack budget C, the adversary allocates optimally under
    C = c_v (N_v)_A + c_u (N_u)_A ,   c_v/c_u = 50,
then we evaluate the network-wide loss probability P(E_FX):
    Storj / r = 1 :  1 - (1 - p)^M          (exact)
    proposed r>=2 :  min(1, M p^r)          (union bound, Eq. 10)

Answers the operational question the improvement factor Gamma does NOT
answer: how much MORE MONEY must the adversary spend?  Gamma is a
probability ratio at fixed budget; because the hypergeometric tail is
exponential in the adversarial fraction, the budget multiplier is only
logarithmic in Gamma.

Run:  python3 plot_budget_sweep.py      ->  fig_budget.pdf / .png
Requires: mpmath, matplotlib
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpmath import mp, mpf, binomial

mp.dps = 50

Nv, Nu, cv, cu = 25500, 308, 50, 1
M = mpf("2.375e9")
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


def alloc(C, Nv_=Nv, Nu_=Nu):
    """Unvetted nodes cost 50x less, so the adversary buys all of them
    first and spends the remainder on vetted nodes."""
    NuA = min(Nu_, C // cu)
    NvA = min(Nv_, (C - cu * NuA) // cv)
    return int(NvA), int(NuA)


def PEFX(C, cfg, r):
    t, d, tv, tu = cfg
    NvA, NuA = alloc(C)
    p = seg_loss(t, d, tv, tu, Nv, NvA, Nu, NuA)
    return (1 - (1 - p) ** M) if r == 1 else min(mpf(1), M * p ** r)


def crossing(cfg, r, target, lo, hi, it=22):
    for _ in range(it):
        mid = (lo + hi) // 2
        if PEFX(mid, cfg, r) < target:
            lo = mid
        else:
            hi = mid
    return hi


CURVES = [
    ("Storj $(80,29)$",              STORJ, 1, "#4C4C4C", "-",  "s"),
    ("$(120,40)$, no concat. $r{=}1$", OURS, 1, "#0072B2", "--", "o"),
    ("Proposed, $r_{\\min}{=}3$",     OURS, 3, "#D55E00", "-",  "^"),
]

budgets = list(range(120000, 900001, 30000))

print("computing budget sweep ...")
series = []
for label, cfg, r, col, ls, mk in CURVES:
    ys = []
    for C in budgets:
        ys.append(float(PEFX(C, cfg, r)))
    series.append((label, ys, col, ls, mk))
    print(f"  {label:32s} done")

C_storj = crossing(STORJ, 1, mpf("0.5"), 100000, 600000)
C_ours = crossing(OURS, 3, mpf("0.5"), 300000, 900000)
C_storj_rob = crossing(STORJ, 1, mpf("0.001"), 50000, 600000)
C_ours_rob = crossing(OURS, 3, mpf("0.001"), 300000, 900000)
print(f"\n  P=0.5   : Storj C={C_storj:,}  ours C={C_ours:,}  "
      f"ratio {C_ours / C_storj:.3f}x")
print(f"  P=0.001 : Storj C={C_storj_rob:,}  ours C={C_ours_rob:,}  "
      f"ratio {C_ours_rob / C_storj_rob:.3f}x")

plt.rcParams.update({
    "font.family": "serif", "font.size": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.0,
    "axes.linewidth": 0.6, "pdf.fonttype": 42,
})
fig, ax = plt.subplots(figsize=(3.42, 1.92))

# X in units of 1e5 -> single-digit tick labels that cannot collide.
xs = [C / 1e5 for C in budgets]
xs_st, xs_ou = C_storj / 1e5, C_ours / 1e5

ax.axhline(0.5, color="#B00020", lw=0.7, ls=":", zorder=1)
ax.axhline(0.001, color="#2E7D32", lw=0.7, ls=":", zorder=1)
# the two threshold labels are put on OPPOSITE sides so their bounding
# boxes cannot intersect, whatever the decade span of the axis
ax.text(1.08, 0.9, "attack succeeds", fontsize=6, color="#B00020",
        ha="left", va="bottom")
ax.text(8.92, 1.8e-3, "robust", fontsize=6, color="#2E7D32",
        ha="right", va="bottom")

for label, ys, col, ls, mk in series:
    ax.semilogy(xs, ys, ls=ls, color=col, lw=1.1, marker=mk, ms=2.6,
                mfc="none", mew=0.7, label=label, zorder=3)

ax.axvline(xs_st, color="#4C4C4C", lw=0.6, ls="-.", alpha=0.6)
ax.axvline(xs_ou, color="#D55E00", lw=0.6, ls="-.", alpha=0.6)
ax.plot([xs_st], [0.5], marker="*", ms=7, color="#4C4C4C", zorder=6)
ax.plot([xs_ou], [0.5], marker="*", ms=7, color="#D55E00", zorder=6)

# The r=3 curve sweeps the full y-range between the two crossings, so ANY
# horizontal span drawn inside the axes would be crossed by it.  The span is
# therefore drawn ABOVE the axes frame, where no data can reach it.
tr = ax.get_xaxis_transform()   # x in data coords, y in axes fraction
ax.annotate("", xy=(xs_st, 1.045), xytext=(xs_ou, 1.045), xycoords=tr,
            textcoords=tr, annotation_clip=False,
            arrowprops=dict(arrowstyle="<->", lw=0.7, color="black"))
ax.text((xs_st + xs_ou) / 2, 1.10, f"budget $\\times{C_ours / C_storj:.2f}$",
        transform=tr, ha="center", va="bottom", fontsize=6.5, clip_on=False)

ax.set_xlabel("attack budget $C$  ($\\times 10^{5}$)")
ax.set_ylabel("$\\mathbb{P}(E_{F_X})$")
ax.set_xlim(1.0, 9.0)
ax.set_xticks([1, 2, 3, 4, 5, 6, 7, 8, 9])
ax.set_ylim(1e-30, 6)
ax.set_yticks([1e0, 1e-6, 1e-12, 1e-18, 1e-24, 1e-30])
ax.grid(True, lw=0.3, color="#DDDDDD", zorder=0)
ax.set_axisbelow(True)
ax.legend(loc="lower right", frameon=False, borderpad=0.15,
          handlelength=1.5, labelspacing=0.2, borderaxespad=0.25)

import figcheck; figcheck.report(fig, "fig_budget")
fig.tight_layout(pad=0.3)
fig.savefig("fig_budget.pdf", bbox_inches="tight", pad_inches=0.03)
fig.savefig("fig_budget.png", dpi=220, bbox_inches="tight", pad_inches=0.03)
print("\nwrote fig_budget.pdf / fig_budget.png")
