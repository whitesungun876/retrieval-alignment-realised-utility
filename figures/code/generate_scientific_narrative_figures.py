#!/usr/bin/env python3
"""Generate figures for the evidence-matched thesis narrative."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT = Path(
    "/Users/lola/Documents/dimensional/thesis/manuscript_revision_robustness/"
    "scientific_narrative_figures"
)
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#172B4D"
TEXT = "#334155"
LINE = "#475569"
BLUE = "#D9EAF7"
ORANGE = "#FCE8D5"
GREEN = "#DFF2E8"
PURPLE = "#E8E2F3"


def card(ax, xy, width, height, face, heading, lines):
    x, y = xy
    ax.add_patch(
        FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            linewidth=1.6, edgecolor=LINE, facecolor=face,
        )
    )
    ax.text(
        x + width / 2, y + height * 0.84, heading,
        ha="center", va="center", fontsize=14, fontweight="bold", color=NAVY,
    )
    for index, (value, size, weight, colour) in enumerate(lines):
        ax.text(
            x + width / 2, y + height * (0.64 - index * 0.14), value,
            ha="center", va="center", fontsize=size, fontweight=weight, color=colour,
        )


def arrow(ax, start, end):
    ax.add_patch(
        FancyArrowPatch(
            start, end, arrowstyle="-|>", mutation_scale=18,
            linewidth=1.8, color=LINE,
        )
    )


def graphical_abstract():
    fig, ax = plt.subplots(figsize=(15, 7.2))
    ax.set_xlim(0, 1.5)
    ax.set_ylim(0, 0.72)
    ax.axis("off")

    ax.text(
        0.75, 0.685, "Why did retrieved experience help?",
        ha="center", va="center", fontsize=23, fontweight="bold", color=NAVY,
    )
    ax.text(
        0.75, 0.645,
        "Three sequential studies, each frozen before its own outcomes",
        ha="center", va="center", fontsize=12, color=TEXT,
    )

    card(
        ax, (0.045, 0.27), 0.40, 0.30, BLUE, "1  Main study",
        [
            ("Raw package vs empty block", 11, "normal", TEXT),
            ("R−N  +20.59 pp", 18, "bold", NAVY),
            ("D changed 673/675 sources", 10.5, "normal", TEXT),
            ("Internal criterion saturated as designed", 10.2, "normal", TEXT),
            ("D−R  +0.89 pp  [−1.78, +3.63]", 11, "bold", NAVY),
        ],
    )
    card(
        ax, (0.555, 0.27), 0.36, 0.30, ORANGE, "2  Assignment follow-up",
        [
            ("Same successful-source vector", 10.5, "normal", TEXT),
            ("semantic vs permuted assignment", 10.5, "normal", TEXT),
            ("R2−P  +1.375 pp", 18, "bold", NAVY),
            ("95% CI [−1.25, +4.06]", 11, "normal", TEXT),
            ("equivalent within ±5 pp", 11, "bold", "#8A4B08"),
        ],
    )
    card(
        ax, (1.025, 0.27), 0.43, 0.30, PURPLE, "3  Active-control follow-up",
        [
            ("Concrete coherent trajectory (P)", 10.5, "normal", TEXT),
            ("vs paired abstract scaffold (C)", 10.5, "normal", TEXT),
            ("P−C  +20.06 pp", 18, "bold", NAVY),
            ("95% CI [+17.13, +23.06]", 11, "normal", TEXT),
            ("not a pure replay-verification effect", 10.5, "bold", "#5B3B76"),
        ],
    )
    arrow(ax, (0.445, 0.42), (0.555, 0.42))
    arrow(ax, (0.915, 0.42), (1.025, 0.42))

    ax.add_patch(
        FancyBboxPatch(
            (0.19, 0.075), 1.12, 0.115,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            linewidth=1.6, edgecolor="#2F6B4F", facecolor=GREEN,
        )
    )
    ax.text(
        0.75, 0.145,
        "Evidence-matched conclusion",
        ha="center", va="center", fontsize=12, fontweight="bold", color="#244F3B",
    )
    ax.text(
        0.75, 0.105,
        "Concrete trajectory content carried substantial utility relative to the abstract scaffold;",
        ha="center", va="center", fontsize=11.5, color=NAVY,
    )
    ax.text(
        0.75, 0.078,
        "the tested internal alignment criterion and target-specific assignment added little in this saturated bank.",
        ha="center", va="center", fontsize=11.5, color=NAVY,
    )

    fig.savefig(
        OUT / "graphical_abstract_scientific_narrative.png",
        dpi=250, bbox_inches="tight", facecolor="white",
    )
    plt.close(fig)


def manipulation_and_outcome():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.1))

    axes[0].bar(["D vs R"], [99.7], color="#4C9ABC", width=0.55)
    axes[0].set_ylim(0, 105)
    axes[0].set_ylabel("Targets with a different selected source (%)")
    axes[0].set_title("Manipulation activation")
    axes[0].text(0, 101, "673/675", ha="center", fontsize=12, fontweight="bold")

    point, low, high = 0.89, -1.78, 3.63
    axes[1].errorbar(
        point, 0, xerr=[[point - low], [high - point]],
        fmt="o", markersize=9, capsize=6, linewidth=2.3, color="#4C9ABC",
    )
    axes[1].axvline(0, color="#333333", linestyle="--", linewidth=1.4)
    axes[1].set_xlim(-4, 5)
    axes[1].set_ylim(-0.65, 0.65)
    axes[1].set_yticks([0], ["D−R"])
    axes[1].set_xlabel("Terminal-success difference (percentage points; 95% CI)")
    axes[1].set_title("External realised utility")
    axes[1].text(point, 0.22, "+0.89 pp", ha="center", fontsize=11, fontweight="bold")

    for axis in axes:
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(labelsize=10)

    fig.suptitle(
        "The de-lexicalised intervention activated, but its terminal-success increment was small",
        fontsize=14,
    )
    fig.tight_layout()
    fig.savefig(
        OUT / "figure_5_1_manipulation_and_outcome.png",
        dpi=300, bbox_inches="tight", facecolor="white",
    )
    plt.close(fig)


if __name__ == "__main__":
    graphical_abstract()
    manipulation_and_outcome()
