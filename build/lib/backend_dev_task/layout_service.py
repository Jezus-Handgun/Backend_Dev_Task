from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, Set, Tuple

from .config import LayoutConfig, LoadConfig, ValidationSettings
from .exceptions import LayoutValidationError
from .joints import JointCalculator
from .models import LayoutContext, LayoutResult, Panel, PanelDimensions
from .mounts import MountCalculator
from .rafters import RafterFactory


@dataclass
class PanelFactory:
    dimensions: PanelDimensions
    validation: ValidationSettings

    def BuildPanels(self, specs: Iterable[Mapping[str, float]]) -> List[Panel]:
        panels: List[Panel] = []
        seen_positions: Set[Tuple[int, int]] = set()
        tolerance = self.validation.coordinate_tolerance
        for item in specs:
            if not {"x", "y"}.issubset(item.keys()):
                raise LayoutValidationError(
                    "Each panel spec must contain 'x' and 'y'.")
            x_value = float(item["x"])
            y_value = float(item["y"])
            self._ValidateCoordinateBounds(x_value, y_value, tolerance)
            if not self.validation.allow_duplicates:
                key = self._QuantizeCoordinate(x_value, y_value, tolerance)
                if key in seen_positions:
                    raise LayoutValidationError(
                        f"Duplicate panel detected at ({x_value}, {y_value})."
                    )
                seen_positions.add(key)
            panels.append(Panel(
                x=x_value, y=y_value, width=self.dimensions.width, height=self.dimensions.height))
        if not self.validation.allow_overlaps:
            self._ValidateNoOverlap(panels, tolerance)
        panels.sort(key=lambda panel: (panel.y, panel.x))
        return panels

    def _ValidateCoordinateBounds(self, x_value: float, y_value: float, tolerance: float) -> None:
        if self.validation.allow_negative_coordinates:
            return
        if x_value < -tolerance or y_value < -tolerance:
            raise LayoutValidationError(
                f"Negative coordinates are not allowed (received x={x_value}, y={y_value})."
            )

    def _QuantizeCoordinate(self, x_value: float, y_value: float, tolerance: float) -> Tuple[int, int]:
        scale = max(tolerance, 1e-9)
        return (round(x_value / scale), round(y_value / scale))

    def _ValidateNoOverlap(self, panels: List[Panel], tolerance: float) -> None:
        for index, first in enumerate(panels):
            for second in panels[index + 1:]:
                if self._RectanglesOverlap(first, second, tolerance):
                    raise LayoutValidationError(
                        f"Panel at ({first.x}, {first.y}) overlaps panel at ({second.x}, {second.y})."
                    )

    def _RectanglesOverlap(self, first: Panel, second: Panel, tolerance: float) -> bool:
        separated_horizontally = (
            first.RightEdge() <= second.x + tolerance
            or second.RightEdge() <= first.x + tolerance
        )
        separated_vertically = (
            first.BottomEdge() <= second.y + tolerance
            or second.BottomEdge() <= first.y + tolerance
        )
        return not (separated_horizontally or separated_vertically)


class LayoutCalculator:
    def __init__(self, config: LayoutConfig | None = None) -> None:
        self.config = config or LoadConfig()
        self.dimensions = PanelDimensions(
            width=self.config.panel.width,
            height=self.config.panel.height,
        )
        self.panel_factory = PanelFactory(
            self.dimensions, self.config.validation)
        self.rafter_factory = RafterFactory(
            spacing=self.config.rafters.spacing,
            edge_clearance=self.config.rafters.edge_clearance,
        )
        self.mount_calculator = MountCalculator(
            span_limit=self.config.mounts.span_limit,
            cantilever_limit=self.config.mounts.cantilever_limit,
            edge_clearance=self.config.mounts.edge_clearance,
        )
        self.joint_calculator = JointCalculator(
            horizontal_gap_threshold=self.config.joints.horizontal_gap_threshold,
            vertical_tolerance=self.config.joints.vertical_tolerance,
        )

    def CalculateLayout(self, specs: Iterable[Mapping[str, float]]) -> LayoutResult:
        context = self.CalculateLayoutDetailed(specs)
        return context.result

    def CalculateLayoutDetailed(self, specs: Iterable[Mapping[str, float]]) -> LayoutContext:
        panels = self.panel_factory.BuildPanels(specs)
        if not panels:
            raise LayoutValidationError("At least one panel must be supplied.")
        min_x = min(panel.x for panel in panels)
        max_x = max(panel.RightEdge() for panel in panels)
        grid = self.rafter_factory.BuildGrid(min_x, max_x)
        mounts = self.mount_calculator.CalculateMounts(panels, grid)
        joints = self.joint_calculator.CalculateJoints(panels)
        result = LayoutResult(mounts=mounts, joints=joints)
        return LayoutContext(result=result, panels=panels, rafters=grid.positions)
