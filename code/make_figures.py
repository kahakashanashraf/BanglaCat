"""Regenerate the figures of the revised BanglaCAT data article from the V2 release files.

Usage:
    python make_figures.py <release_dir> <figure_dir>

Fig. 1  Level-1 and Level-2 label distribution, training vs. test (percentages, counts labelled)
Fig. 2  Character-length distribution of context and target reply, training vs. test
Fig. 3  Test-set composition by source and Level-1 class
Fig. 4  Data-construction pipeline
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

REL, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

TRAIN_C, TEST_C = "#2a78d6", "#eb6834"      # categorical slots 1, 2
NONTOX_C, TOX_C = "#1baf7a", "#eda100"      # categorical slots 3, 4
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "savefig.dpi": 600, "savefig.bbox": "tight", "figure.facecolor": "white",
})

rd = lambda f: pd.read_csv(REL / "data" / f, keep_default_na=False, encoding="utf-8-sig")
train, test = rd("banglacat_train_bn.csv"), rd("banglacat_test_bn.csv")
SUBTYPES = ["Insult", "Mockery / Ridicule", "Harassment", "Profanity", "Sexual Harassment / Objectification",
            "Hate Speech", "Incitement / Encouragement of Harm", "Dehumanization", "Identity Attack",
            "Toxic Endorsement / Agreement", "Threat"]


# ---------------------------------------------------------------- Fig. 1
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.6), gridspec_kw={"width_ratios": [1, 2.6]})
cls = ["Non-toxic", "Toxic"]
x = np.arange(2)
w = 0.38
for off, df, c, name in ((-w / 2, train, TRAIN_C, "Training"), (w / 2, test, TEST_C, "Test")):
    n = df.level_1_class.value_counts().reindex(cls).values
    p = 100 * n / n.sum()
    bars = a1.bar(x + off, p, w * 0.92, color=c, label=f"{name} (n = {n.sum():,})")
    for b, k, v in zip(bars, n, p):
        a1.text(b.get_x() + b.get_width() / 2, v + 1, f"{k:,}", ha="center", va="bottom", fontsize=7, color=INK2)
a1.set_xticks(x, cls)
a1.set_ylabel("Share of partition (%)")
a1.set_ylim(0, 68)
a1.set_title("(a) Level-1")
a1.yaxis.grid(True, color=GRID, lw=0.6)
a1.set_axisbelow(True)

y = np.arange(len(SUBTYPES))[::-1]
h = 0.38
for off, df, c in ((h / 2, train, TRAIN_C), (-h / 2, test, TEST_C)):
    tox = df[df.level_1_class == "Toxic"]
    n = tox.toxicity_type.value_counts().reindex(SUBTYPES, fill_value=0).values
    p = 100 * n / n.sum()
    bars = a2.barh(y + off, p, h * 0.92, color=c)
    for b, k, v in zip(bars, n, p):
        a2.text(v + 0.4, b.get_y() + b.get_height() / 2, f"{k:,}", va="center", fontsize=6.5, color=INK2)
a2.set_yticks(y, SUBTYPES, fontsize=7.5)
a2.set_xlabel("Share of Toxic items in partition (%)")
a2.set_xlim(0, 42)
a2.set_title("(b) Level-2 toxic subtype")
a2.xaxis.grid(True, color=GRID, lw=0.6)
a2.set_axisbelow(True)
fig.legend(*a1.get_legend_handles_labels(), loc="upper center", ncol=2, frameon=False,
           bbox_to_anchor=(0.5, 1.04), fontsize=8.5)
fig.text(0.99, -0.02, "Bar labels give item counts.", ha="right", fontsize=7, color=INK2)
fig.tight_layout()
fig.savefig(OUT / "fig1_label_distribution.png")
plt.close(fig)

# ---------------------------------------------------------------- Fig. 2
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
for ax, col, title in ((axes[0], "context", "(a) Context"), (axes[1], "target_reply", "(b) Target reply")):
    tr_len, te_len = train[col].str.len(), test[col].str.len()
    hi = int(np.percentile(pd.concat([tr_len, te_len]), 99))
    bins = np.linspace(0, hi, 46)
    for s, c, name in ((tr_len, TRAIN_C, "Training"), (te_len, TEST_C, "Test")):
        ax.hist(s.clip(upper=hi), bins=bins, density=True, histtype="step", lw=2, color=c,
                label=f"{name} (median {int(s.median())})")
        ax.axvline(s.median(), color=c, lw=1, ls=(0, (3, 2)))
    ax.set_title(title)
    ax.set_xlabel("Length (characters)")
    ax.set_ylabel("Density")
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=7.5)
fig.text(0.99, -0.03, "Values above the 99th percentile are pooled in the last bin; dashed lines mark medians.",
         ha="right", fontsize=7, color=INK2)
fig.tight_layout()
fig.savefig(OUT / "fig2_length_distribution.png")
plt.close(fig)

# ---------------------------------------------------------------- Fig. 3
srcs = ["facebook", "youtube", "news portal"]
names = {"facebook": "Facebook\n(post or parent comment)", "youtube": "YouTube\n(post or parent comment)",
         "news portal": "News portals\n(headline or post title)"}
ct = pd.crosstab(test.source, test.level_1_class).reindex(srcs)
fig, ax = plt.subplots(figsize=(6.4, 2.4))
yy = np.arange(len(srcs))[::-1]
left = np.zeros(len(srcs))
for cl, c in (("Non-toxic", NONTOX_C), ("Toxic", TOX_C)):
    v = ct[cl].values
    ax.barh(yy, v, 0.6, left=left, color=c, label=cl, edgecolor="white", linewidth=2)
    for yi, l, k, tot in zip(yy, left, v, ct.sum(axis=1).values):
        ax.text(l + k / 2, yi, f"{k:,} ({100 * k / tot:.0f}%)", ha="center", va="center", fontsize=7.5, color=INK)
    left += v
for yi, tot in zip(yy, left):
    ax.text(tot + 12, yi, f"n = {int(tot):,}", va="center", fontsize=7.5, color=INK2)
ax.set_yticks(yy, [names[s] for s in srcs], fontsize=8)
ax.set_xlabel("Test items")
ax.set_xlim(0, left.max() * 1.15)
ax.xaxis.grid(True, color=GRID, lw=0.6)
ax.set_axisbelow(True)
ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.45, 1.2), fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "fig3_test_source_composition.png")
plt.close(fig)

# ---------------------------------------------------------------- Fig. 4 (pipeline)
fig, ax = plt.subplots(figsize=(7.4, 8.2))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")
BLUE_F, ORNG_F, GREY_F = "#eaf2fc", "#fdeee7", "#f3f3f1"
LINE_H, PAD_TOP, PAD_BOT, GAP = 2.45, 4.6, 1.6, 3.2


def box(xc, ytop, wd, title, body, fc, ec):
    """Draw a box whose height follows its line count; return its bottom y."""
    ht = PAD_TOP + LINE_H * (body.count("\n") + 1) + PAD_BOT
    ax.add_patch(FancyBboxPatch((xc - wd / 2, ytop - ht), wd, ht, boxstyle="round,pad=0,rounding_size=1.2",
                                fc=fc, ec=ec, lw=1.2))
    ax.text(xc, ytop - 1.4, title, ha="center", va="top", fontsize=8, fontweight="bold", color=INK)
    ax.text(xc, ytop - PAD_TOP, body, ha="center", va="top", fontsize=7, color=INK2, linespacing=1.45)
    return ytop - ht


def arrow(x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.1,
                                                                    shrinkA=0, shrinkB=0))


review = "Three independent human reviewers:\nAgree/Disagree + corrected Level-1/Level-2"
LEFT = [("1. Candidate generation", "Claude Sonnet 5\n19,454 context–reply candidates"),
        ("2. Label review", review),
        ("3. Majority vote (2 of 3, joint label)", "19,453 accepted (549 labels changed)\n1 item without majority excluded"),
        ("Training set", "19,453 pairs\n9,861 Non-toxic / 9,592 Toxic")]
RIGHT = [("1. Collection (25 Jun – 25 Aug 2026)", "2,330 public context–reply pairs\nFacebook, YouTube, news portals"),
         ("2. Round 1: three annotators (blind)", "2,142 resolved by 2-of-3 majority\n188 without majority"),
         ("3. Round 2: three new annotators (blind)", "186 resolved; 2 pooled over six votes\n1 resolved, 1 tied and excluded"),
         ("Test set", "2,322 pairs (6 duplicates and 1 lost text removed)\n1,038 Non-toxic / 1,284 Toxic")]
ax.text(25, 99.5, "Training partition (synthetic)", ha="center", va="top", fontsize=9, fontweight="bold", color=TRAIN_C)
ax.text(75, 99.5, "Test partition (real social media)", ha="center", va="top", fontsize=9, fontweight="bold", color=TEST_C)
bottoms = []
for xc, items, fc, ec in ((25, LEFT, BLUE_F, TRAIN_C), (75, RIGHT, ORNG_F, TEST_C)):
    y = 95
    for i, (t, b) in enumerate(items):
        if i:
            arrow(xc, y + GAP, xc, y)
        y = box(xc, y, 46, t, b, fc, ec) - GAP
    bottoms.append(y + GAP)
ytop = min(bottoms) - 5
for xc, yb in zip((25, 75), bottoms):
    arrow(xc, yb, xc, ytop)
yend = box(50, ytop, 96, "Integrity checks, English translation and public release (Mendeley Data V2)",
    "NFC normalisation; no exact train–test overlap; six test duplicates removed\n"
    "English translation: Google Translate + rule-based corrections (labels unchanged)\n"
    "Released: Bangla and English files, individual votes, code and SHA-256 checksums", GREY_F, INK2)
ax.set_ylim(yend - 1, 100)
fig.savefig(OUT / "fig4_pipeline.png")
plt.close(fig)
print("figures written to", OUT)
