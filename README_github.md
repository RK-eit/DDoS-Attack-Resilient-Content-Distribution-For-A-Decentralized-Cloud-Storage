# DDoS Attack Resilient Content Distribution for Decentralized Cloud Storage

Verification scripts and figure-generating code for the paper

> R. Kundu, "DDoS Attack Resilient Content Distribution for Decentralized Cloud
> Storage," in *Proc. IEEE EdgeCom 2026*, to appear.


The paper proposes a matrix-based concatenated content distribution for
decentralized cloud storage (DCS) that removes the single-segment-erasure
vulnerability of Storj identified in [Kundu, Gehrmann and Kihl, ICPADS 2023],
and evaluates it against Storj on the same attack-budget, network-size and
erasure-piece-split sweeps as that analysis. Every number printed in the
paper's evaluation figures and in Table II can be regenerated from this
repository.

## Contents

| File | Produces / checks |
|---|---|
| `make_figure.py` | Fig. 1 — targeted-attack cost vs. raw storage expansion |
| `plot_budget_sweep.py` | Fig. 2 (left) — attack-budget sweep |
| `plot_network_growth.py` | Fig. 2 (right) — network growth to robustness |
| `plot_tvtu_optimization.py` | Fig. 3 — erasure-piece split optimization |
| `verify_table2_v3.py` | Every entry of Table II (13 checks) |
| `verify_figures_v3.py` | Every number in Figs. 2–3 and Section VI-C (15 checks) |
| `figcheck.py` | Text-overlap detector imported by the plot scripts |
| `requirements.txt` | Python dependencies |
| `LICENSE` | MIT |

All scripts must sit in one flat directory: the plot scripts `import figcheck`.

## Reproducing the results

```bash
pip install -r requirements.txt

python3 verify_table2_v3.py          # expected: 13/13 checks passed
python3 verify_figures_v3.py         # expected: 15/15 checks passed  (a few minutes)

python3 make_figure.py               # writes fig_pareto.pdf
python3 plot_budget_sweep.py         # writes fig_budget.pdf
python3 plot_network_growth.py       # writes fig_network.pdf
python3 plot_tvtu_optimization.py    # writes fig_tvtu.pdf
```

Each verification script prints a `[PASS]` / `[FAIL]` line per claim against
the value printed in the paper, followed by a pass count. All probabilities
are evaluated exactly in high-precision arithmetic (`mpmath`, 50–60 decimal
digits); nothing below 1e-10 is computed in floating point.

Each plot script ends with a `[LAYOUT]` line from `figcheck.py`, which measures
the rendered text bounding boxes and reports any text/text or text/data
collision. All four currently report `clean`.

## Model parameters

The reference configuration follows Kundu et al. (ICPADS 2023):
N_v = 25,500 vetted and N_u = 308 unvetted nodes, cost ratio c_v/c_u = 50,
attack budget C = 360,000, M = 2.375 × 10⁹ segments. Storj uses the
Reed–Solomon parameters (t, d) = (80, 29) with piece split (76, 4); the
proposed protocol uses (120, 40) with split (114, 6). These constants are set
at the top of each script.

## Citation

```bibtex
@inproceedings{kundu2026ddos,
  author    = {Kundu, Rohon},
  title     = {{DDoS} Attack Resilient Content Distribution for
               Decentralized Cloud Storage},
  booktitle = {Proc. IEEE EdgeCom},
  year      = {2026},
  note      = {to appear}
}
```

## Intellectual property and disclosure

The content distribution mechanism analysed in the paper is covered by a
granted Swedish patent (PRV, SE 2451199-0) and a PCT international application
(WO 2026/114955). This repository contains the numerical evaluation and
figure-generating code only, released under the MIT License; the license
grants no rights under those patents.

Portions of the paper's prose and this verification code were drafted with
the assistance of Claude (Anthropic), as disclosed in the paper's
acknowledgment. The author has executed every script and is solely
responsible for the content.

## Contact

Rohon Kundu — Department of Electrical and Information Technology, Lund
University — rohon.kundu@eit.lth.se
