"""
plot_tvtu_optimization.py
Figure: erasure-piece split optimization (Fig. 3 of DDoS_Resilient_DCS_v3).

This repeats, for the proposed protocol's (t,d) = (120,40), the study that
Kundu et al. (ICPADS 2023, Figs. 2-3) performed for Storj's (80,29): given
a fixed attack budget, is the deployed vetted/unvetted split of erasure
pieces optimal, and does the answer change with the size of the unvetted
population?

Following their presentation, the x-axis is the number of vetted
adversarial nodes (N_v)_A admissible under the budget constraint
    C = c_v (N_v)_A + c_u (N_u)_A,  c_v = 50, c_u = 1, C = 360,000,
with (N_u)_A taking up the residual budget.  One curve per split
(t_v, t_u), t_v + t_u = 120.

Panel (a): N_u = 308      (the deployed network of [5])
Panel (b): N_u = 50,000   (a hypothetical large unvetted population)

Run:  python3 plot_tvtu_optimization.py  ->  fig_tvtu.pdf / .png
Requires: mpmath, matplotlib
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpmath import mp, mpf, binomial

mp.dps = 50

Nv, cv, cu = 25500, 50, 1
M = mpf("2.375e9")
C = 360000
T, D = 120, 40
R = 3                      # r_min of the completed design


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


def PEFX(tv, tu, NvA, Nu_):
    NuA = min(Nu_, C - cv * NvA)
    if NuA < 0:
        return None
    p = seg_loss(T, D, tv, tu, Nv, int(NvA), Nu_, int(NuA))
    return min(mpf(1), M * p ** R)


SPLITS = [(114, 6), (115, 5), (116, 4), (117, 3), (118, 2), (119, 1),
          (120, 0)]
COLS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9",
        "#000000"]

PANELS = [
    ("(a)  $N_u = 308$ (deployed)", 308,
     list(range(7193, 7201))),
    ("(b)  $N_u = 50{,}000$", 50000,
     list(range(6200, 7201, 50))),
]

plt.rcParams.update({
    "font.family": "serif", "font.size": 8, "axes.labelsize": 8,
    "axes.titlesize": 8, "xtick.labelsize": 6.5, "ytick.labelsize": 7,
    "legend.fontsize": 6.5, "axes.linewidth": 0.6, "pdf.fonttype": 42,
})
fig, axes = plt.subplots(1, 2, figsize=(7.0, 1.88))

best = {}
for ax, (title, Nu_, xs) in zip(axes, PANELS):
    print(f"computing panel: {title}")
    worst_of = {}
    for (tv, tu), col in zip(SPLITS, COLS):
        ys, xx = [], []
        for NvA in xs:
            v = PEFX(tv, tu, NvA, Nu_)
            if v is not None:
                xx.append(NvA)
                ys.append(float(v))
        worst_of[(tv, tu)] = max(ys)
        ax.semilogy(xx, ys, lw=1.1, color=col,
                    label=f"$({tv},{tu})$")
        print(f"   (t_v,t_u)=({tv},{tu})  max P = {max(ys):.3e}")
    b = min(worst_of, key=worst_of.get)
    best[Nu_] = (b, worst_of[b])
    print(f"   -> best split: {b}  (min of max P = {worst_of[b]:.3e})\n")
    ax.set_title(title, pad=4)
    ax.set_xlabel("vetted adversarial nodes $(N_v)_A$")
    if Nu_ == 308:
        ax.set_xlim(7192.7, 7200.3); ax.set_xticks([7193, 7195, 7197, 7199])
    else:
        ax.set_xlim(6180, 7220); ax.set_xticks([6300, 6600, 6900, 7200])
    ax.grid(True, lw=0.3, color="#DDDDDD", zorder=0)
    ax.set_axisbelow(True)

axes[0].set_ylabel("$\\mathbb{P}(E_{F_X})$ bound")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=7, frameon=False,
           bbox_to_anchor=(0.5, -0.03), columnspacing=1.1,
           handletextpad=0.4, title="$(t_v,t_u)$", title_fontsize=6.5)

fig.tight_layout(rect=[0, 0.13, 1, 1], pad=0.4)
import figcheck; figcheck.report(fig, "plot_tvtu_optimization.py")
fig.savefig("fig_tvtu.pdf", bbox_inches="tight", pad_inches=0.02)
fig.savefig("fig_tvtu.png", dpi=200, bbox_inches="tight", pad_inches=0.02)
print("wrote fig_tvtu.pdf / fig_tvtu.png")
for Nu_, (b, v) in best.items():
    print(f"  N_u={Nu_:6d}: optimal split {b}, worst-case bound {v:.3e}")
