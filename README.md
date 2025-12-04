# Backend Dev Task

Solar-layout helper that turns a list of panel coordinates into two precise maps:
where to bolt mounts onto rafters and where to join adjacent modules.
Plus a visualization so you can verify the result quickly.

## How It Works (TL;DR)

- We read panel top-left coordinates (defaults mirror the PDF sample data).
- `LayoutCalculator` builds the context: generates a rafter grid, normalizes panel
  dimensions, and then runs two specialized calculators.
- `MountCalculator` finds usable rafters inside each panel, enforces limits, and emits
  mounting points on the top and bottom edges.
- `JointCalculator` looks for horizontally/vertically adjacent panels and adds unique
  connectors that can serve up to four panels at once.
- The result (`LayoutResult`) contains two coordinate arrays (`mounts`, `joints`). The
  CLI writes them to JSON, and `RenderLayout` can draw a PNG with panels/rafters/joints.

## Requirements

- Python 3.10+
- (Optional) virtual environment

## Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[test]
```

## Running The Service

The CLI runs the algorithm against the inputs defined in the config (defaults come from
`config.yaml`). Treat it as a reference snapshot or point it to your own YAML file to
recompute different geometries.

```powershell
python -m backend_dev_task.cli
```

Pass a custom configuration or output directory:

```powershell
python -m backend_dev_task.cli --config config.yaml --output-dir output
```

The command stores its output in `output/layout_<timestamp>.json`, e.g.
`output/layout_20251203_101500.json`. Inside you get both mount and joint arrays for
whatever pipeline or report you want to plug them into.

Optional plotting (requires `pip install -e .[viz]` to pull in `matplotlib` and `pillow`):

```powershell
python -m backend_dev_task.cli --config config.yaml --show-plot
```

Every plot run also writes `layout_<timestamp>.png` alongside the JSON file. Provide a
custom directory via `--plot-path path/to/dir` or a filename (the timestamp is appended
automatically to avoid overwriting previous renders).

## Configuration

Settings live in `config.yaml`. All keys are optional—omit a section to fall back to
defaults. Editing this file is the quickest way to experiment with rafter spacing,
validation thresholds, and layout tolerances.

```yaml
panel:
  width: 44.7
  height: 71.1
rafters:
  spacing: 16.0
  edge_clearance: 2.0
mounts:
  span_limit: 48.0
  cantilever_limit: 16.0
  edge_clearance: 2.0
joints:
  horizontal_gap_threshold: 1.0
  vertical_tolerance: 0.5
validation:
  allow_negative_coordinates: false
  allow_duplicates: false
  allow_overlaps: false
  coordinate_tolerance: 0.0001
```

Use the `validation` block to relax or tighten input checks (negative coordinates,
duplicate panels, overlap detection, tolerance for float comparisons). The PDF profile keeps every guard enabled.

The same YAML structure can be used anywhere the code accepts a `LayoutConfig` (e.g.,
`LayoutCalculator(config=LoadConfig(Path("my_config.yaml")))`).

## Running Tests (pytest)

Execute all tests with:

```powershell
python -m pytest
```

You can also run a single file:

```powershell
python -m pytest tests/test_layout.py
```

## Library Usage

```python
from backend_dev_task.layout_service import LayoutCalculator

calculator = LayoutCalculator()
layout = calculator.CalculateLayout([
  {"x": 0, "y": 0},
  {"x": 45.05, "y": 0},
])
print(len(layout.mounts), len(layout.joints))
```

`layout` exposes two collections (`mounts`, `joints`) represented as lists of `(x, y)`
coordinates. Feed them to downstream calculations (costing, CAD export, reporting,
etc.).

## Visualization Module

The helper `backend_dev_task.visualization.RenderLayout` renders panels, rafters,
mounts, and joints using `matplotlib`. Import it manually or rely on the CLI flags to
generate PNG files / show the chart once `matplotlib` is installed via the `viz`
extra.
