from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .exceptions import LayoutValidationError
from .models import Mount, Panel
from .rafters import RafterGrid


@dataclass
class MountCalculator:
    span_limit: float = 48.0
    cantilever_limit: float = 16.0
    edge_clearance: float = 2.0

    def CalculateMounts(self, panels: Sequence[Panel], grid: RafterGrid) -> List[Mount]:
        mounts: List[Mount] = []
        for panel in panels:
            mounts.extend(self._CalculatePanelMounts(panel, grid))
        return mounts

    def _CalculatePanelMounts(self, panel: Panel, grid: RafterGrid) -> List[Mount]:
        allowed_start = panel.x + self.edge_clearance
        allowed_end = panel.RightEdge() - self.edge_clearance
        rafters = grid.PositionsInRange(allowed_start, allowed_end)
        if not rafters:
            raise LayoutValidationError(
                f"No rafters available inside panel spanning from {allowed_start} to {allowed_end}."
            )
        if rafters[0] - panel.x - self.edge_clearance > self.cantilever_limit:
            raise LayoutValidationError(
                f"Left cantilever limit exceeded for panel at x={panel.x}."
            )
        if panel.RightEdge() - self.edge_clearance - rafters[-1] > self.cantilever_limit:
            raise LayoutValidationError(
                f"Right cantilever limit exceeded for panel at x={panel.x}."
            )
        for first, second in zip(rafters, rafters[1:]):
            if second - first > self.span_limit + 1e-6:
                raise LayoutValidationError(
                    f"Span limit exceeded inside panel at x={panel.x}."
                )
        top_y = panel.y
        bottom_y = panel.BottomEdge()
        panel_mounts = [Mount(x=value, y=top_y) for value in rafters]
        panel_mounts.extend(Mount(x=value, y=bottom_y) for value in rafters)
        return panel_mounts
