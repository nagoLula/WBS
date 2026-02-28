"""Generate a PDF mind map for the secure clinical communication program."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

def _child_list_factory() -> list["OutlineNode"]:
    return []


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "outline.json"
OUTPUT_DIR = ROOT / "output"
DEFAULT_PDF = OUTPUT_DIR / "secure-clinical-communication.pdf"
DEFAULT_MD = OUTPUT_DIR / "secure-clinical-communication.md"
DEFAULT_ASCII = OUTPUT_DIR / "WBS_diagram"


@dataclass
class OutlineNode:
    """Simple tree node that keeps drawing metadata."""

    title: str
    code: str | None = None
    children: list["OutlineNode"] = field(default_factory=_child_list_factory)
    parent: OutlineNode | None = None
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
        default=None,
        help="Path for the exported artifact (defaults per format).",
    )
    parser.add_argument(
        "--format",
        choices=["pdf", "markdown", "ascii"],
        default="pdf",
        help="Choose between a PDF mind map, markdown outline, or ASCII tree.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Resolution used for the exported diagram.",
    )
    return parser.parse_args()


def load_outline() -> dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as source:
        return json.load(source)


def build_tree(raw: dict[str, Any], depth: int = 0, parent: OutlineNode | None = None) -> OutlineNode:
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
    fig: Any = Figure(figsize=(11, 11))
    FigureCanvasAgg(fig)
    ax: Any = fig.add_subplot(111)
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


def export_markdown(root: OutlineNode, output_path: Path) -> None:
    lines = [f"# {root.label}", ""]

    def _walk(node: OutlineNode, depth: int, bucket: list[str]) -> None:
        indent = "    " * depth
        bucket.append(f"{indent}- {node.label}")
        for child in node.children:
            _walk(child, depth + 1, bucket)

    for child in root.children:
        _walk(child, 0, lines)

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_ascii(root: OutlineNode, output_path: Path) -> None:
    lines = [root.label]
    children = root.children
    if children:
        lines.append("│")

    for idx, child in enumerate(children):
        _walk_ascii(child, prefix="", is_last=idx == len(children) - 1, bucket=lines)
        if idx < len(children) - 1:
            lines.append("│")
            lines.append("")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _walk_ascii(node: OutlineNode, *, prefix: str, is_last: bool, bucket: list[str]) -> None:
    connector = "└──" if is_last else "├──"
    bucket.append(f"{prefix}{connector} {node.label}")
    if not node.children:
        return

    child_prefix = f"{prefix}{'    ' if is_last else '│   '}"
    for idx, child in enumerate(node.children):
        _walk_ascii(child, prefix=child_prefix, is_last=idx == len(node.children) - 1, bucket=bucket)


def _draw_node(ax: Any, node: OutlineNode) -> None:
    x, y = node.coords
    if node.depth == 0:
        ax.scatter([x], [y], s=1400, color="#0b3954", zorder=2)  # type: ignore[attr-defined]
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

    ax.scatter([x], [y], s=marker_size, color=color, alpha=0.95, zorder=2)  # type: ignore[attr-defined]
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
    output_path = args.output
    if output_path is None:
        if args.format == "pdf":
            output_path = DEFAULT_PDF
        elif args.format == "markdown":
            output_path = DEFAULT_MD
        else:
            output_path = DEFAULT_ASCII
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "pdf":
        layout_tree(root)
        draw_mind_map(root, output_path, dpi=args.dpi)
    elif args.format == "markdown":
        export_markdown(root, output_path)
    else:
        export_ascii(root, output_path)

    try:
        rel_path = output_path.relative_to(ROOT)
    except ValueError:
        rel_path = output_path
    print(f"Diagram exported to {rel_path}")


if __name__ == "__main__":
    main()
