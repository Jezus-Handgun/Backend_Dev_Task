from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

from .config import LayoutConfig, LoadConfig
from .layout_service import LayoutCalculator
from .models import LayoutContext


def LoadSamplePanels() -> Iterable[Mapping[str, float]]:
    return [
        {"x": 0, "y": 0},
        {"x": 45.05, "y": 0},
        {"x": 90.1, "y": 0},
        {"x": 0, "y": 71.6},
        {"x": 135.15, "y": 0},
        {"x": 135.15, "y": 71.6},
        {"x": 0, "y": 143.2},
        {"x": 45.05, "y": 143.2},
        {"x": 135.15, "y": 143.2},
        {"x": 90.1, "y": 143.2},
    ]


def WriteLayoutToFile(
    result_dir: Path | None = None, config: LayoutConfig | None = None
) -> tuple[Path, LayoutContext, str]:
    if result_dir is None:
        result_dir = Path("output")
    result_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = result_dir / f"layout_{timestamp}.json"
    calculator = LayoutCalculator(config=config)
    context = calculator.CalculateLayoutDetailed(LoadSamplePanels())
    layout = context.result
    payload = {
        "mounts": [{"x": mount.x, "y": mount.y} for mount in layout.mounts],
        "joints": [{"x": joint.x, "y": joint.y} for joint in layout.joints],
    }
    result_path.write_text(json.dumps(payload, indent=2))
    print(f"Layout written to {result_path}")
    return result_path, context, timestamp


def ResolvePlotPath(
    json_path: Path, override_path: Path | None, timestamp: str
) -> Path:
    if override_path is None:
        return json_path.with_suffix(".png")
    override_path = Path(override_path)
    if override_path.is_dir() or not override_path.suffix:
        override_path.mkdir(parents=True, exist_ok=True)
        return override_path / f"layout_{timestamp}.png"
    suffix = override_path.suffix or ".png"
    stem = override_path.stem or "layout"
    return override_path.with_name(f"{stem}_{timestamp}{suffix}")


def ParseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate sample layout output.")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to a YAML configuration file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where layout JSON files will be stored.",
    )
    parser.add_argument(
        "--plot-path",
        type=Path,
        default=None,
        help="Optional PNG file path for the rendered layout.",
    )
    parser.add_argument(
        "--show-plot",
        action="store_true",
        help="Display the rendered layout in a matplotlib window.",
    )
    return parser.parse_args()


def main() -> None:
    args = ParseArgs()
    config = LoadConfig(args.config)
    result_path, context, timestamp = WriteLayoutToFile(
        result_dir=args.output_dir, config=config)
    if args.plot_path is not None or args.show_plot:
        from .visualization import RenderLayout

        plot_path = ResolvePlotPath(result_path, args.plot_path, timestamp)
        RenderLayout(
            layout=context.result,
            panels=context.panels,
            rafters=context.rafters,
            output_path=plot_path,
            show_plot=args.show_plot,
        )


if __name__ == "__main__":
    main()
