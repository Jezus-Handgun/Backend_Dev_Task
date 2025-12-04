from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from .exceptions import LayoutValidationError
from .models import Joint, LayoutResult, Mount, Panel


def RenderLayout(
    layout: LayoutResult,
    panels: Sequence[Panel],
    rafters: Sequence[float],
    output_path: Path | None = None,
    show_plot: bool = False,
) -> None:
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError as error:
        raise LayoutValidationError(
            "matplotlib is required for plotting. Install with 'pip install .[viz]'"
        ) from error

    if not panels:
        raise LayoutValidationError("Cannot render layout without panels.")

    min_x = min(panel.x for panel in panels)
    min_y = min(panel.y for panel in panels)
    max_x = max(panel.RightEdge() for panel in panels)
    max_y = max(panel.BottomEdge() for panel in panels)
    padding = 5

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(min_x - padding, max_x + padding)
    ax.set_ylim(min_y - padding, max_y + padding)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Solar Layout")

    for panel in panels:
        rect = Rectangle(
            (panel.x, panel.y),
            panel.width,
            panel.height,
            fill=True,
            facecolor="#8bbedd",
            edgecolor="#1f4e79",
            alpha=0.4,
        )
        ax.add_patch(rect)

    for x_value in rafters:
        ax.axvline(x=x_value, color="#cccccc", linestyle="--", linewidth=1)

    if layout.mounts:
        ax.scatter(
            [mount.x for mount in layout.mounts],
            [mount.y for mount in layout.mounts],
            color="black",
            s=15,
            label="Mounts",
        )

    if layout.joints:
        ax.scatter(
            [joint.x for joint in layout.joints],
            [joint.y for joint in layout.joints],
            marker="s",
            color="#555555",
            s=30,
            label="Joints",
        )

    if layout.mounts or layout.joints:
        ax.legend(loc="upper right")

    ax.invert_yaxis()
    ax.grid(False)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=200, bbox_inches="tight")

    if show_plot:
        plt.show()

    plt.close(fig)
