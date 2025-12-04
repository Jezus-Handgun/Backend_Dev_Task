from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from .models import Joint, Panel


def _FindRowKey(row_map: Dict[float, List[Panel]], y_value: float, tolerance: float) -> float:
    for key in row_map:
        if abs(key - y_value) <= tolerance:
            return key
    return y_value


@dataclass
class JointCalculator:
    horizontal_gap_threshold: float = 1.0
    vertical_tolerance: float = 0.5

    def CalculateJoints(self, panels: Sequence[Panel]) -> List[Joint]:
        row_map: Dict[float, List[Panel]] = {}
        for panel in panels:
            row_key = _FindRowKey(row_map, panel.y, self.vertical_tolerance)
            row_map.setdefault(row_key, []).append(panel)
        joints: Dict[tuple[float, float], Joint] = {}
        for row_key, row_panels in row_map.items():
            row_panels.sort(key=lambda panel: panel.x)
            for left, right in zip(row_panels, row_panels[1:]):
                gap = right.x - left.RightEdge()
                if gap >= self.horizontal_gap_threshold:
                    continue
                seam_x = (left.RightEdge() + right.x) / 2.0
                top_joint = Joint(x=round(seam_x, 4), y=round(row_key, 4))
                bottom_joint = Joint(x=round(seam_x, 4),
                                     y=round(row_key + left.height, 4))
                joints[(top_joint.x, top_joint.y)] = top_joint
                joints[(bottom_joint.x, bottom_joint.y)] = bottom_joint
        return sorted(joints.values(), key=lambda item: (item.y, item.x))
