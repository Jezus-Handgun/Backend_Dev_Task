from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class PanelDimensions:
    width: float = 44.7
    height: float = 71.1


@dataclass(frozen=True)
class Panel:
    x: float
    y: float
    width: float
    height: float

    def RightEdge(self) -> float:
        return self.x + self.width

    def BottomEdge(self) -> float:
        return self.y + self.height


@dataclass(frozen=True)
class Mount:
    x: float
    y: float


@dataclass(frozen=True)
class Joint:
    x: float
    y: float


@dataclass(frozen=True)
class LayoutResult:
    mounts: Sequence[Mount]
    joints: Sequence[Joint]

    def MountCount(self) -> int:
        return len(self.mounts)

    def JointCount(self) -> int:
        return len(self.joints)


@dataclass(frozen=True)
class LayoutContext:
    result: LayoutResult
    panels: Sequence[Panel]
    rafters: Sequence[float]
