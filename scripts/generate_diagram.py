"""Generate a PDF mind map for the secure clinical communication program."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "outline.json"
OUTPUT_DIR = ROOT / "output"


@dataclass
class OutlineNode:
    """Simple tree node that keeps drawing metadata."""

    title: str
    code: str | None = None
    children: list["OutlineNode"] = field(default_factory=list)
    parent: "OutlineNode | None" = None
    depth: int = 0
    angle: float = 0.0
    radius: float = 0.0

    @property
    def label(self) -> str:
        return f"{self.code} {self.title}" if self.code else self.title

    @property
    def coords(self) -> tuple[float, float]:
        return (
            self.radius * math.cos(self.angle),
            self.radius * math.sin(self.angle),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "secure-clinical-communication.pdf",
        help="Path for the exported PDF diagram.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution used for the exported diagram.",
    )
    return parser.parse_args()


def load_outline() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as source:
        return json.load(source)


def build_tree(raw: dict, depth: int = 0, parent: OutlineNode | None = None) -> OutlineNode:
    node = OutlineNode(title=raw["title"], code=raw.get("code"), parent=parent, depth=depth)
    node.children = [build_tree(child, depth + 1, node) for child in raw.get("children", [])]
    return node


def layout_tree(root: OutlineNode, radius_step: float = 1.6, spread: float = 1.6) -> None:
    root.angle = math.pi / 2
    root.radius = 0.0
    first_level = root.children
    if not first_level:
        return

    branch_count = len(first_level)
    for idx, child in enumerate(first_level):
        angle = math.pi / 2 - (math.tau * idx / branch_count)
        _assign_branch(child, depth=1, angle=angle, radius_step=radius_step, spread=spread)


def _assign_branch(
    node: OutlineNode,
    *,
    depth: int,
    angle: float,
    radius_step: float,
    spread: float,
) -> None:
    node.depth = depth
    node.angle = angle
    node.radius = depth * radius_step

    child_count = len(node.children)
    if child_count == 0:
        return

    local_spread = spread / (depth + 0.5)
    if child_count == 1:
        child_angles = [angle]
    else:
        step = local_spread / (child_count - 1)
        child_angles = [angle - (local_spread / 2) + step * idx for idx in range(child_count)]

    for idx, child in enumerate(node.children):
        _assign_branch(
            child,
            depth=depth + 1,
            angle=child_angles[idx],
            radius_step=radius_step,
            spread=spread,
        )


def iter_nodes(root: OutlineNode) -> Iterable[OutlineNode]:
    yield root
    for child in root.children:
        yield from iter_nodes(child)


def draw_mind_map(root: OutlineNode, output_path: Path, dpi: int = 300) -> None:
    fig, ax = plt.subplots(figsize=(11, 11))
    ax.axis("off")

    connector_color = "#94a3b8"
    for node in iter_nodes(root):
        if node.parent is None:
            continue
        x0, y0 = node.parent.coords
        x1, y1 = node.coords
        ax.plot([x0, x1], [y0, y1], color=connector_color, linewidth=1.15, zorder=1)

    for node in iter_nodes(root):
        _draw_node(ax, node)

    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", transparent=False)
    plt.close(fig)


def _draw_node(ax: plt.Axes, node: OutlineNode) -> None:
    x, y = node.coords
    if node.depth == 0:
        ax.scatter([x], [y], s=1400, color="#0b3954", zorder=2)
        ax.text(
            x,
            y,
            node.label,
            color="#ffffff",
            fontsize=18,
            weight="bold",
            ha="center",
            va="center",
            zorder=3,
        )
        return

    if node.depth == 1:
        color = "#087e8b"
        marker_size = 220
        font_size = 13
    elif node.depth == 2:
        color = "#1f487e"
        marker_size = 90
        font_size = 11
    else:
        color = "#475569"
        marker_size = 60
        font_size = 10

    ax.scatter([x], [y], s=marker_size, color=color, alpha=0.95, zorder=2)
    offset = 0.3 + 0.08 * node.depth
    text_x = x + offset * math.cos(node.angle)
    text_y = y + offset * math.sin(node.angle)
    ha = "left" if math.cos(node.angle) >= 0 else "right"
    weight = "bold" if node.depth <= 2 else "normal"
    ax.text(
        text_x,
        text_y,
        node.label,
        color=color,
        fontsize=font_size,
        weight=weight,
        ha=ha,
        va="center",
        zorder=3,
    )


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    args = parse_args()
    ensure_output_dir()
    outline = load_outline()
    root = build_tree(outline)
    layout_tree(root)
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    draw_mind_map(root, output_path, dpi=args.dpi)

    try:
        rel_path = output_path.relative_to(ROOT)
    except ValueError:
        rel_path = output_path
    print(f"Diagram exported to {rel_path}")


if __name__ == "__main__":
    main()
