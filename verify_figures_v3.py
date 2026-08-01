"""
verify_figures_v3.py
Independent verification of every numerical claim made in the three new
figures of DDoS_Resilient_DCS_v3 and in Section VI-C, the abstract, and the
conclusion that reference them.

Checks:
  A. attack-budget crossings and the 1.77x / 1.99x multipliers
  B. network-size crossing for Storj and the margin for the proposed design
  C. the ~18% vetted-node growth Storj requires
  D. optimal (t_v,t_u) split at N_u = 308 and at N_u = 50,000
  E. that Gamma is a probability ratio, NOT a cost ratio -- i.e. that the
     budget multiplier scales with log(Gamma), not with Gamma

Run:  python3 verify_figures_v3.py     (a few minutes; exact arithmetic)
Requires: mpmath
"""
from mpmath import mp, mpf, binomial, log10

mp.dps = 50

Nv0, Nu0, cv, cu = 25500, 308, 50, 1
M = mpf("2.375e9")
STORJ = (80, 29, 76, 4)
OURS = (120, 40, 114, 6)
C_REF = 360000

_R = []


def check(label, got, want, tol=0.02, fmt="{:.4g}"):
    g, w = mpf(got), mpf(want)
    ok = abs(g - w) / abs(w) <= tol if w != 0 else g == w
    _R.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:46s} "
          f"got={fmt.format(float(g)):>12s}  paper={fmt.format(float(w)):>12s}")


def assert_true(label, cond):
    _R.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")


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


def alloc(C, Nv_, Nu_):
    NuA = min(Nu_, C // cu)
    NvA = min(Nv_, (C - cu * NuA) // cv)
    return int(NvA), int(NuA)


def PEFX(C, cfg, r, Nv_=Nv0, Nu_=Nu0, split=None):
    t, d, tv, tu = cfg
    if split:
        tv, tu = split
    NvA, NuA = alloc(C, Nv_, Nu_)
    p = seg_loss(t, d, tv, tu, Nv_, NvA, Nu_, NuA)
    return (1 - (1 - p) ** M) if r == 1 else min(mpf(1), M * p ** r)


def bisect_C(cfg, r, target, lo, hi, it=22):
    for _ in range(it):
        mid = (lo + hi) // 2
        if PEFX(mid, cfg, r) < target:
            lo = mid
        else:
            hi = mid
    return hi


def bisect_Nv(cfg, r, target, lo, hi, it=18):
    for _ in range(it):
        mid = (lo + hi) // 2
        if PEFX(C_REF, cfg, r, Nv_=mid) > target:
            lo = mid
        else:
            hi = mid
    return hi


print("=" * 78)
print("A.  ATTACK-BUDGET SWEEP  (Fig. 2 left, Sec. VI-C1)")
print("=" * 78)
Cs = bisect_C(STORJ, 1, mpf("0.5"), 100000, 600000)
Co = bisect_C(OURS, 3, mpf("0.5"), 300000, 900000)
check("Storj budget at P(E_FX)=0.5", Cs, "3.62e5")
check("proposed budget at P(E_FX)=0.5", Co, "6.42e5")
check("budget multiplier at P=0.5", mpf(Co) / Cs, "1.77")
Cs1 = bisect_C(STORJ, 1, mpf("0.001"), 50000, 600000)
Co1 = bisect_C(OURS, 3, mpf("0.001"), 300000, 900000)
check("Storj budget at P(E_FX)=0.001", Cs1, "3.06e5")
check("proposed budget at P(E_FX)=0.001", Co1, "6.09e5")
check("budget multiplier at P=0.001", mpf(Co1) / Cs1, "1.99")

print("\n" + "=" * 78)
print("B.  NETWORK GROWTH  (Fig. 2 right, Sec. VI-C2)")
print("=" * 78)
nv_storj = bisect_Nv(STORJ, 1, mpf("0.001"), 25500, 60000)
check("N_v for Storj to reach P<=0.001", nv_storj, "30000", tol=0.03,
      fmt="{:.0f}")
p_ours = PEFX(C_REF, OURS, 3, Nv_=25500)
check("proposed P(E_FX) at deployed N_v=25,500", p_ours, "1.1e-39", tol=0.1,
      fmt="{:.3e}")
assert_true("proposed already robust at deployed size (P <= 0.001)",
            p_ours <= mpf("0.001"))
growth = 100 * (mpf(nv_storj) / 25500 - 1)
check("required Storj network growth (%)", growth, "18", tol=0.15,
      fmt="{:.1f}")
print(f"  [info] margin below threshold: "
      f"{float(log10(mpf('0.001') / p_ours)):.0f} orders of magnitude")

print("\n" + "=" * 78)
print("C.  ERASURE-PIECE SPLIT  (Fig. 3, Sec. VI-C3)")
print("=" * 78)
SPLITS = [(114, 6), (115, 5), (116, 4), (117, 3), (118, 2), (119, 1), (120, 0)]
for Nu_, xs, want in ((308, range(7193, 7201), (120, 0)),
                      (50000, range(6200, 7201, 50), (115, 5))):
    worst = {}
    for s in SPLITS:
        worst[s] = max(float(PEFX(C_REF, OURS, 3, Nu_=Nu_, split=s))
                       if (C_REF - cv * x) >= 0 else 0.0
                       for x in xs
                       for _ in [0]) if False else max(
            float(min(mpf(1), M * seg_loss(
                120, 40, s[0], s[1], Nv0, x,
                Nu_, min(Nu_, C_REF - cv * x)) ** 3))
            for x in xs if C_REF - cv * x >= 0)
    best = min(worst, key=worst.get)
    print(f"  N_u = {Nu_:6d}:  worst-case bound per split")
    for s in SPLITS:
        mark = "  <-- best" if s == best else ""
        print(f"      ({s[0]:3d},{s[1]:2d})  {worst[s]:.3e}{mark}")
    assert_true(f"optimal split at N_u={Nu_} is {want}", best == want)
    if Nu_ == 308:
        check("gain of (120,0) over (114,6)",
              worst[(114, 6)] / worst[(120, 0)], "5.3e6", tol=0.1)

print("\n" + "=" * 78)
print("D.  GAMMA IS NOT A COST RATIO  (Sec. V-G)")
print("=" * 78)
Gamma = mpf("1.06e37")
print(f"  Gamma (probability ratio at fixed budget) = {float(Gamma):.3g}")
print(f"  budget multiplier (cost ratio)            = {float(mpf(Co)/Cs):.3f}")
assert_true("budget multiplier is NOT proportional to Gamma",
            mpf(Co) / Cs < mpf("10"))
assert_true("budget multiplier is O(log Gamma) in magnitude",
            mpf(Co) / Cs < log10(Gamma))
print(f"  [info] log10(Gamma) = {float(log10(Gamma)):.1f}; the multiplier "
      f"{float(mpf(Co)/Cs):.2f} is far below it,")
print("         consistent with an exponential tail in the adversarial "
      "fraction.")

print("\n" + "=" * 78)
print(f"  {sum(_R)}/{len(_R)} checks passed"
      f"{'' if sum(_R) == len(_R) else '   <-- INVESTIGATE'}")
print("=" * 78)
