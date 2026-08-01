"""
verify_table2_v3.py
Verification of every numerical entry in Table II (tab:security) of
DDoS_Resilient_DCS_v3, which reports the boundary-completed r_min = 3 design.

Every entry depends on the redundancy profile only through r_min.  This script
re-derives r_min by enumeration from the construction of Sec. III-D rather than
assuming it, so that the table is checked against the design as specified.

Run:  python3 verify_table2_v3.py
Requires: mpmath
"""
from mpmath import mp, mpf, binomial
import math

mp.dps = 60

_RESULTS = []


def check(label, computed, paper, tol=5e-3):
    c, p = mpf(computed), mpf(paper)
    ok = (c == p) if p == 0 else (abs(c - p) / abs(p) <= tol)
    _RESULTS.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:42s} "
          f"computed={mp.nstr(c, 6):>12s}  paper={mp.nstr(p, 6):>12s}")


def hyper_pmf(N, K, n, k):
    if k < 0 or k > n or k > K or (n - k) > (N - K):
        return mpf(0)
    return binomial(K, k) * binomial(N - K, n - k) / binomial(N, n)


def seg_loss(t, d, tv, tu, Nv, NvA, Nu, NuA):
    tau = t - d + 1
    px = [hyper_pmf(Nv, NvA, tv, x) for x in range(tv + 1)]
    py = [hyper_pmf(Nu, NuA, tu, y) for y in range(tu + 1)]
    return sum(px[x] * py[z - x]
               for z in range(tau, t + 1)
               for x in range(max(0, z - tu), min(z, tv) + 1))


def profile(n, boundary="new"):
    """Enumerate the redundancy profile of the construction.

    boundary = "none" -> D_Sub u D_Super            (Eq. 10 profile)
               "new"  -> D_Sub u D_Super u D_Bnd    (Eq. 12 profile)
    """
    k = math.ceil(n / 2)
    d_sub = [(i, n - k + i) for i in range(1, k + 1)]
    d_sub = [(a, b) for (a, b) in d_sub if a != b]
    d_sup = [(i, i + 1) for i in range(1, n)]
    d_bnd = {"none": [], "new": [(1, n)]}[boundary]
    objs = list(dict.fromkeys(d_sub + d_sup + d_bnd))
    c = {i: 0 for i in range(1, n + 1)}
    for a, b in objs:
        c[a] += 1
        c[b] += 1
    return objs, [c[i] for i in range(1, n + 1)]


# reference configuration
Nv, Nu, NvA, NuA = 25500, 308, 7194, 300
pS = seg_loss(80, 29, 76, 4, Nv, NvA, Nu, NuA)
pC = seg_loss(120, 40, 114, 6, Nv, NvA, Nu, NuA)
M = mpf("2.375e9")
n = 63

rho_v, rho_u = mpf(NvA) / Nv, mpf(NuA) / Nu
EZ_S = 76 * rho_v + 4 * rho_u
EZ_C = 114 * rho_v + 6 * rho_u

objs, prof = profile(n, "new")
r_min = min(prof)

print("=" * 74)
print("TABLE II  --  Security comparison at attack budget C = 360,000")
print("=" * 74)
print(f"\n  r_min re-derived by enumeration from the construction: {r_min}")
ok = (r_min == 3)
_RESULTS.append(ok)
print(f"  [{'PASS' if ok else 'FAIL'}] table header claims r_min = 3\n")

print("  Adversarial nodes: 7,194 vetted + 300 unvetted (both protocols)")
check("Exp. pieces controlled, Storj (of 80)", EZ_S, "25.34")
check("Exp. pieces controlled, ours  (of 120)", EZ_C, "38.01")
check("Gap to threshold, Storj (52 - E[Z])", 52 - EZ_S, "26.66")
check("Gap to threshold, ours  (81 - E[Z])", 81 - EZ_C, "42.99")
check("P(concat. seg. loss) = p_C", pC, "6.83e-17")
check("P(orig. segment loss), Storj = p_S", pS, "2.14e-10")
check("P(orig. segment loss), ours <= p_C^r_min", pC**r_min, "3.19e-49")
check("P(E_FX), Storj = 1-(1-p_S)^M", 1 - (1 - pS) ** M, "0.399")
check("P(E_FX), ours <= M p_C^r_min", M * pC**r_min, "7.57e-40")

print("\n  Parenthetical in Sec. V-G (without the boundary object):")
objs0, prof0 = profile(n, "none")
check("P(E_FX) <= M p_C^2", M * pC**min(prof0), "1.11e-23")

print("\n  Robustness verdict (threshold P(E_FX) <= 0.001):")
for name, val in (("Storj", 1 - (1 - pS) ** M), ("ours", M * pC**r_min)):
    verdict = "robust" if val <= mpf("0.001") else "not robust"
    expect = "not robust" if name == "Storj" else "robust"
    ok = verdict == expect
    _RESULTS.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:6s}: {verdict:11s} "
          f"(paper: {expect})")

print("\n" + "=" * 74)
print(f"  {sum(_RESULTS)}/{len(_RESULTS)} checks passed")
print("=" * 74)
