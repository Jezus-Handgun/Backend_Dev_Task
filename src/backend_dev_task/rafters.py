from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class RafterGrid:
    positions: List[float]

    def PositionsInRange(self, start_x: float, end_x: float) -> List[float]:
        return [value for value in self.positions if start_x - 1e-6 <= value <= end_x + 1e-6]


class RafterFactory:
    def __init__(self, spacing: float = 16.0, edge_clearance: float = 2.0) -> None:
        self.spacing = spacing
        self.edge_clearance = edge_clearance

    def BuildGrid(self, min_x: float, max_x: float) -> RafterGrid:
        if min_x > max_x:
            raise ValueError("min_x cannot exceed max_x")
        first_rafter = min_x + self.edge_clearance
        while first_rafter - self.spacing > min_x - self.spacing * 2:
            first_rafter -= self.spacing
        positions: List[float] = []
        current = first_rafter
        limit = max_x + self.spacing * 2
        while current <= limit:
            positions.append(round(current, 4))
            current += self.spacing
        return RafterGrid(positions)
