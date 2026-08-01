"""Detect text-vs-text and text-vs-data collisions in a matplotlib figure."""
import numpy as np
from matplotlib.text import Text as _Text, Annotation as _Annotation

def report(fig, name="figure"):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    problems = []
    for ax in fig.axes:
        texts = [t for t in ax.texts if t.get_text().strip()]
        # include annotation texts and tick labels
        ticks = ax.get_xticklabels() + ax.get_yticklabels()
        leg = ax.get_legend()
        legtexts = leg.get_texts() if leg else []
        allt = [(t, t.get_text()) for t in texts + ticks + legtexts]
        boxes = []
        for t, s in allt:
            try:
                # For annotations, Annotation.get_window_extent() also covers
                # the leader arrow.  A leader deliberately points AT a curve,
                # so we measure the text box only.
                if isinstance(t, _Annotation):
                    b = _Text.get_window_extent(t, renderer=r)
                else:
                    b = t.get_window_extent(renderer=r)
            except Exception:
                continue
            if b.width <= 0 or b.height <= 0:
                continue
            boxes.append((s, b))
        # text vs text
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                s1, b1 = boxes[i]; s2, b2 = boxes[j]
                if b1.overlaps(b2):
                    ov = (min(b1.x1, b2.x1) - max(b1.x0, b2.x0))
                    if ov > 0.5:
                        problems.append(f"TEXT/TEXT  '{s1}' <-> '{s2}' "
                                        f"(overlap {ov:.1f}px)")
        # text vs plotted data (exclude tick labels, which live outside axes)
        datapts = []
        for ln in ax.get_lines():
            xd, yd = ln.get_xdata(), ln.get_ydata()
            if len(xd) == 0:
                continue
            pts = ax.transData.transform(np.column_stack([xd, yd]))
            datapts.append((ln.get_label(), pts))
        for s, b in boxes:
            if any(s == tl.get_text() for tl in ticks):
                continue
            for lbl, pts in datapts:
                if lbl.startswith("_"):
                    continue
                inside = ((pts[:, 0] > b.x0) & (pts[:, 0] < b.x1) &
                          (pts[:, 1] > b.y0) & (pts[:, 1] < b.y1)).sum()
                if inside:
                    problems.append(f"TEXT/DATA  '{s}' sits on curve "
                                    f"'{lbl}' ({inside} pts)")
    if problems:
        print(f"  [LAYOUT] {name}: {len(problems)} issue(s)")
        for p in problems:
            print("     -", p)
    else:
        print(f"  [LAYOUT] {name}: clean - no text/text or text/data overlap")
    return problems
