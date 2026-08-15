#!/usr/bin/env python3
"""Regenerate thesis figures after removing the non-activated graph arm."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT = Path("/Users/lola/Documents/dimensional/thesis/manuscript_revision_robustness/graph_free_figures")
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#172B4D"
TEXT = "#334155"
LINE = "#394B59"
RAW = "#7F7F7F"
DELEX = "#4C9ABC"
NO_MEMORY = "#B7B7B7"


def box(ax, xy, width, height, face, title, lines=(), fontsize=13, title_frac=0.58):
    x, y = xy
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=1.5, edgecolor=LINE, facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height * title_frac, title, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=NAVY)
    for index, value in enumerate(lines):
        ax.text(x + width / 2, y + height * (0.45 - index * 0.15), value,
                ha="center", va="center", fontsize=10, color=TEXT)
    return patch


def arrow(ax, start, end, connectionstyle="arc3"):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=16,
                                linewidth=1.8, color=LINE,
                                connectionstyle=connectionstyle))


def elbow_arrow(ax, points):
    """Draw an orthogonal connector whose final segment has an arrowhead."""
    xs, ys = zip(*points)
    ax.plot(xs[:-1], ys[:-1], color=LINE, linewidth=1.8)
    arrow(ax, points[-2], points[-1])


def graphical_abstract():
    fig, ax = plt.subplots(figsize=(15, 7.2))
    ax.set_xlim(0, 1.5)
    ax.set_ylim(0, 0.72)
    ax.axis("off")
    ax.text(0.75, 0.685, "From retrieval alignment to realised utility",
            ha="center", va="center", fontsize=22, fontweight="bold", color=NAVY)
    ax.text(0.75, 0.645, "Experience retrieval in TextWorldExpress CookingWorld",
            ha="center", va="center", fontsize=12, color="#42526E")

    box(ax, (0.055, 0.39), 0.25, 0.145, "#E9F3FA", "Target cookbook",
        ("Visible recipe", "ingredient-specific operations"), title_frac=0.82)
    box(ax, (0.055, 0.14), 0.25, 0.145, "#F2F2F2", "Frozen memory",
        ("3,121 replay-verified", "successful trajectories"), title_frac=0.82)
    box(ax, (0.39, 0.175), 0.30, 0.335, "#FFF4E5", "Retrieval policy", title_frac=0.88)

    raw = FancyBboxPatch((0.43, 0.365), 0.22, 0.072,
                         boxstyle="round,pad=0.008,rounding_size=0.015",
                         facecolor="#F6C85F", edgecolor="#805B10", linewidth=1.2)
    delex = FancyBboxPatch((0.43, 0.255), 0.22, 0.085,
                           boxstyle="round,pad=0.008,rounding_size=0.015",
                           facecolor="#A9D6E5", edgecolor="#1B6A8C", linewidth=1.2)
    ax.add_patch(raw)
    ax.add_patch(delex)
    ax.text(0.54, 0.405, "Raw Semantic", ha="center", va="center", fontsize=12, color=NAVY)
    ax.text(0.54, 0.382, "BGE-M3 Top-1", ha="center", va="center", fontsize=10, color=TEXT)
    ax.text(0.54, 0.305, "De-lexicalised Semantic", ha="center", va="center", fontsize=11, color=NAVY)
    ax.text(0.54, 0.278, "BGE-M3 Top-1", ha="center", va="center", fontsize=10, color=TEXT)

    box(ax, (0.78, 0.175), 0.27, 0.335, "#EAF7F1", "Selected source", title_frac=0.88)
    ax.text(0.915, 0.418, "Offline exact anonymised", ha="center", fontsize=10, color=TEXT)
    ax.text(0.915, 0.392, "recipe correspondence", ha="center", fontsize=10, color=TEXT)
    ax.text(0.915, 0.33, "6.52% → 100%", ha="center", fontsize=18,
            fontweight="bold", color=NAVY)
    ax.plot([0.825, 1.005], [0.295, 0.295], color="#6B778C", linewidth=1)
    ax.text(0.915, 0.255, "Representation-specific alignment", ha="center", fontsize=10, color=TEXT)
    ax.text(0.915, 0.225, "saturated", ha="center", fontsize=12, color=NAVY)

    box(ax, (1.14, 0.14), 0.305, 0.395, "#F4ECF7", "Agent execution", title_frac=0.88)
    ax.text(1.292, 0.445, "Same policy, prompt, renderer", ha="center", fontsize=10, color=TEXT)
    ax.text(1.292, 0.42, "and 50-step limit", ha="center", fontsize=10, color=TEXT)
    ax.plot([1.185, 1.40], [0.385, 0.385], color="#6B778C", linewidth=1)
    ax.text(1.292, 0.345, "De-lexicalised − Raw Semantic", ha="center", fontsize=10, color=TEXT)
    ax.text(1.292, 0.305, "+0.89 pp", ha="center", fontsize=18, fontweight="bold", color=NAVY)
    ax.text(1.292, 0.275, "95% CI [−1.78, +3.63]", ha="center", fontsize=10, color=TEXT)
    ax.text(1.292, 0.225, "Raw Semantic − No Memory", ha="center", fontsize=10, color=TEXT)
    ax.text(1.292, 0.185, "+20.59 pp", ha="center", fontsize=18, fontweight="bold", color=NAVY)

    arrow(ax, (0.305, 0.462), (0.39, 0.39))
    arrow(ax, (0.305, 0.212), (0.39, 0.30))
    arrow(ax, (0.69, 0.342), (0.78, 0.342))
    arrow(ax, (1.05, 0.342), (1.14, 0.342))

    gap = FancyBboxPatch((0.315, 0.025), 0.87, 0.078,
                         boxstyle="round,pad=0.01,rounding_size=0.018",
                         facecolor="#FFF8D6", edgecolor="#9A7B00", linewidth=1.5)
    ax.add_patch(gap)
    ax.text(0.75, 0.073, "Alignment–utility gap", ha="center", va="center",
            fontsize=13, fontweight="bold", color=NAVY)
    ax.text(0.75, 0.043, "Saturating the study-defined offline metric did not improve terminal success.",
            ha="center", va="center", fontsize=10.5, color=TEXT)
    arrow(ax, (0.915, 0.175), (0.83, 0.103), "arc3,rad=-0.25")
    arrow(ax, (1.292, 0.14), (1.085, 0.103), "arc3,rad=-0.15")
    fig.savefig(OUT / "graphical_abstract_graph_free.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def method_flow():
    fig, ax = plt.subplots(figsize=(12, 9.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9.5)
    ax.axis("off")
    panels = [(0.2, 7.15, 11.6, 2.05), (0.2, 3.45, 11.6, 3.45), (0.2, 0.2, 11.6, 2.95)]
    for x, y, w, h in panels:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                                    facecolor="#F8FAFC", edgecolor="#94A3B8", linewidth=1.5))
    ax.text(0.45, 8.82, "1  OFFLINE PREPARATION", fontsize=17, fontweight="bold", color="#1E3A5F")
    ax.text(0.45, 6.55, "2  TARGET-TIME RETRIEVAL", fontsize=17, fontweight="bold", color="#1E3A5F")
    ax.text(0.45, 2.77, "3  SHARED INTERACTIVE EXECUTION", fontsize=17, fontweight="bold", color="#1E3A5F")

    box(ax, (0.55, 7.65), 1.85, 0.75, "#E8F1FA", "Train-fold", ("tasks",), 12, 0.72)
    box(ax, (2.8, 7.48), 2.4, 1.08, "#E8F1FA", "Replay-verified", ("successful trajectories",), 12, 0.72)
    box(ax, (5.65, 7.65), 2.15, 0.75, "#E8F1FA", "Frozen bank", (), 12)
    box(ax, (8.45, 7.55), 2.75, 0.95, "#E8F1FA", "Raw & de-lexicalised", ("BGE-M3 embeddings",), 12, 0.72)
    arrow(ax, (2.4, 8.02), (2.8, 8.02)); arrow(ax, (5.2, 8.02), (5.65, 8.02)); arrow(ax, (7.8, 8.02), (8.45, 8.02))

    box(ax, (0.55, 4.55), 1.95, 0.9, "#F1F5F9", "Target cookbook", (), 10.5)
    box(ax, (3.15, 5.75), 2.45, 0.62, "#F1F5F9", "N   No memory", (), 12)
    box(ax, (3.15, 4.75), 2.45, 0.62, "#D9EAF7", "R   Raw Top-1", (), 12)
    box(ax, (3.15, 3.75), 2.45, 0.62, "#FCE8D5", "D   De-lex Top-1", (), 12)
    box(ax, (9.45, 5.75), 1.85, 0.62, "#F1F5F9", "Empty block", (), 11)
    box(ax, (7.05, 4.3), 1.85, 0.78, "#E8E2F3", "Selected source", (), 9.5)
    box(ax, (9.45, 4.2), 1.85, 0.98, "#E8E2F3", "Common raw-", ("trajectory renderer",), 9.5, 0.72)
    for end_y in (6.06, 5.06, 4.06): arrow(ax, (2.5, 5.0), (3.15, end_y))
    arrow(ax, (5.6, 6.06), (9.45, 6.06)); arrow(ax, (5.6, 5.06), (7.05, 4.85)); arrow(ax, (5.6, 4.06), (7.05, 4.55))
    arrow(ax, (8.9, 4.69), (9.45, 4.69))

    box(ax, (4.5, 2.05), 3.0, 0.62, "#E7F3EF", "Common agent prompt", (), 12)
    box(ax, (0.8, 0.65), 2.7, 0.72, "#E7F3EF", "Qwen selects action index", (), 9.5)
    box(ax, (4.65, 0.65), 2.7, 0.72, "#E7F3EF", "TextWorldExpress", ("CookingWorld",), 11, 0.72)
    box(ax, (8.5, 0.65), 2.7, 0.72, "#E7F3EF", "Terminal success", ("and process log",), 11, 0.72)
    elbow_arrow(ax, [(11.3, 6.06), (11.58, 6.06), (11.58, 2.36), (7.5, 2.36)])
    arrow(ax, (10.38, 4.2), (6.8, 2.67), "arc3,rad=-0.18")
    arrow(ax, (5.1, 2.05), (3.5, 1.22)); arrow(ax, (3.5, 1.01), (4.65, 1.01)); arrow(ax, (7.35, 1.01), (8.5, 1.01))
    fig.savefig(OUT / "figure_4_1_graph_free.png", dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def alignment_utility():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6))
    colors = [RAW, DELEX]
    axes[0].bar(["R", "D"], [6.52, 100.0], color=colors, width=0.62)
    axes[0].set_ylim(0, 105)
    axes[0].set_ylabel("Exact anonymised-recipe match (%)")
    axes[0].set_title("Offline retrieval alignment")
    for index, value in enumerate([6.52, 100.0]):
        axes[0].text(index, value + 2, f"{value:.1f}", ha="center", fontsize=11)
    axes[1].bar(["N", "R", "D"], [63.33, 83.93, 84.81],
                color=[NO_MEMORY, RAW, DELEX], width=0.62)
    axes[1].set_ylim(0, 100)
    axes[1].set_ylabel("Mean target terminal success (%)")
    axes[1].set_title("Online realised utility")
    for index, value in enumerate([63.33, 83.93, 84.81]):
        axes[1].text(index, value + 2, f"{value:.1f}", ha="center", fontsize=11)
    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=10)
    fig.suptitle("Retrieval alignment and realised utility", fontsize=16)
    fig.tight_layout()
    fig.savefig(OUT / "figure_5_1_graph_free.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def retained_contrasts():
    labels = ["R−N", "D−R"]
    points = [20.59, 0.89]
    lows = [16.89, -1.78]
    highs = [24.22, 3.63]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    y = [1, 0]
    for yi, point, low, high, color in zip(y, points, lows, highs, [RAW, DELEX]):
        ax.errorbar(point, yi, xerr=[[point - low], [high - point]], fmt="o",
                    markersize=8, capsize=5, linewidth=2.2, color=color)
    ax.axvline(0, color="#333333", linestyle="--", linewidth=1.4)
    ax.set_yticks(y, labels)
    ax.set_xlabel("Risk difference (percentage points; 95% target-cluster bootstrap CI)")
    ax.set_title("Prespecified retained main-study contrasts")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_ylim(-0.6, 1.6)
    fig.tight_layout()
    fig.savefig(OUT / "figure_5_2_graph_free.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    graphical_abstract()
    method_flow()
    alignment_utility()
    retained_contrasts()
