from __future__ import annotations

from pathlib import Path

import pytest

from backend_dev_task.cli import ResolvePlotPath
from backend_dev_task.config import (
    JointSettings,
    LayoutConfig,
    LoadConfig,
    ValidationSettings,
)
from backend_dev_task.exceptions import LayoutValidationError
from backend_dev_task.layout_service import LayoutCalculator
from backend_dev_task.visualization import RenderLayout


@pytest.fixture()
def SamplePanels() -> list[dict[str, float]]:
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


def test_layout_returns_mounts_and_joints(SamplePanels: list[dict[str, float]]) -> None:
    calculator = LayoutCalculator()
    result = calculator.CalculateLayout(SamplePanels)
    assert result.MountCount() == 54
    assert result.JointCount() == 12
    first_mount = result.mounts[0]
    assert pytest.approx(first_mount.x) == 2.0
    assert pytest.approx(first_mount.y) == 0.0


def test_missing_coordinate_raises() -> None:
    calculator = LayoutCalculator()
    with pytest.raises(LayoutValidationError):
        calculator.CalculateLayout([{"x": 0}])


def test_no_panels_raises() -> None:
    calculator = LayoutCalculator()
    with pytest.raises(LayoutValidationError):
        calculator.CalculateLayout([])


def test_span_limit_violation_triggers_error() -> None:
    calculator = LayoutCalculator()
    calculator.mount_calculator.span_limit = 10.0
    with pytest.raises(LayoutValidationError):
        calculator.CalculateLayout([{"x": 0.0, "y": 0.0}])


def test_panel_without_available_rafter_raises() -> None:
    calculator = LayoutCalculator()
    calculator.rafter_factory.spacing = 200.0
    with pytest.raises(LayoutValidationError):
        calculator.CalculateLayout([{"x": 3.0, "y": 0.0}])


def test_shared_joint_created_once() -> None:
    calculator = LayoutCalculator()
    layout = calculator.CalculateLayout(
        [
            {"x": 0.0, "y": 0.0},
            {"x": 44.7, "y": 0.0},
            {"x": 0.0, "y": 71.1},
            {"x": 44.7, "y": 71.1},
        ]
    )
    assert layout.JointCount() == 3
    assert any(
        pytest.approx(joint.x) == 44.7 and pytest.approx(joint.y) == 71.1
        for joint in layout.joints
    )


def test_large_horizontal_gap_skips_joint() -> None:
    calculator = LayoutCalculator()
    layout = calculator.CalculateLayout(
        [
            {"x": 0.0, "y": 0.0},
            {"x": 46.0, "y": 0.0},
        ]
    )
    assert layout.JointCount() == 0


def test_custom_joint_threshold_via_config(SamplePanels: list[dict[str, float]]) -> None:
    config = LayoutConfig(
        joints=JointSettings(horizontal_gap_threshold=0.0,
                             vertical_tolerance=0.5)
    )
    calculator = LayoutCalculator(config=config)
    result = calculator.CalculateLayout(SamplePanels)
    assert result.JointCount() == 0


def test_load_config_file_overrides(tmp_path: "Path") -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("mounts:\n  span_limit: 30\n")
    config = LoadConfig(config_file)
    assert config.mounts.span_limit == 30


def test_negative_coordinates_rejected_by_default() -> None:
    calculator = LayoutCalculator()
    with pytest.raises(LayoutValidationError):
        calculator.CalculateLayout([{"x": -1.0, "y": 0.0}])


def test_negative_coordinates_allowed_via_config() -> None:
    config = LayoutConfig(
        validation=ValidationSettings(allow_negative_coordinates=True)
    )
    calculator = LayoutCalculator(config=config)
    result = calculator.CalculateLayout([{"x": -1.0, "y": 0.0}])
    assert result.MountCount() > 0


def test_duplicate_panels_rejected() -> None:
    calculator = LayoutCalculator()
    with pytest.raises(LayoutValidationError):
        calculator.CalculateLayout([
            {"x": 0.0, "y": 0.0},
            {"x": 0.0, "y": 0.0},
        ])


def test_duplicates_allowed_in_config() -> None:
    config = LayoutConfig(
        validation=ValidationSettings(
            allow_duplicates=True, allow_overlaps=True)
    )
    calculator = LayoutCalculator(config=config)
    result = calculator.CalculateLayout([
        {"x": 0.0, "y": 0.0},
        {"x": 0.0, "y": 0.0},
    ])
    assert result.MountCount() > 0


def test_overlapping_panels_rejected() -> None:
    calculator = LayoutCalculator()
    with pytest.raises(LayoutValidationError):
        calculator.CalculateLayout([
            {"x": 0.0, "y": 0.0},
            {"x": 10.0, "y": 0.0},
        ])


def test_overlaps_allowed_via_config() -> None:
    config = LayoutConfig(validation=ValidationSettings(allow_overlaps=True))
    calculator = LayoutCalculator(config=config)
    result = calculator.CalculateLayout([
        {"x": 0.0, "y": 0.0},
        {"x": 10.0, "y": 0.0},
    ])
    assert result.MountCount() > 0


def test_calculate_layout_detailed_returns_context(SamplePanels: list[dict[str, float]]) -> None:
    calculator = LayoutCalculator()
    context = calculator.CalculateLayoutDetailed(SamplePanels)
    assert context.result.MountCount() == 54
    assert len(context.panels) == len(SamplePanels)
    assert len(context.rafters) > 0


def test_render_layout_writes_png(tmp_path: "Path", SamplePanels: list[dict[str, float]]) -> None:
    pytest.importorskip("matplotlib")
    calculator = LayoutCalculator()
    context = calculator.CalculateLayoutDetailed(SamplePanels)
    output_path = tmp_path / "layout.png"
    RenderLayout(
        layout=context.result,
        panels=context.panels,
        rafters=context.rafters,
        output_path=output_path,
        show_plot=False,
    )
    assert output_path.exists()


def test_resolve_plot_path_default_uses_json_timestamp(tmp_path: "Path") -> None:
    json_path = tmp_path / "layout_20250101_120000.json"
    resolved = ResolvePlotPath(json_path, None, "20250101_120000")
    assert resolved.name == "layout_20250101_120000.png"


def test_resolve_plot_path_directory_argument(tmp_path: "Path") -> None:
    json_path = tmp_path / "layout_20250101_120000.json"
    plot_dir = tmp_path / "plots"
    resolved = ResolvePlotPath(json_path, plot_dir, "20250101_120000")
    assert resolved.parent == plot_dir
    assert resolved.name == "layout_20250101_120000.png"


def test_resolve_plot_path_file_argument_gets_timestamp(tmp_path: "Path") -> None:
    json_path = tmp_path / "layout_20250101_120000.json"
    plot_file = tmp_path / "custom.png"
    resolved = ResolvePlotPath(json_path, plot_file, "20250101_120000")
    assert resolved.name == "custom_20250101_120000.png"
