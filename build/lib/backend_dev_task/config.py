from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping

import yaml

from .exceptions import LayoutValidationError


@dataclass(frozen=True)
class PanelSettings:
    width: float = 44.7
    height: float = 71.1


@dataclass(frozen=True)
class RafterSettings:
    spacing: float = 16.0
    edge_clearance: float = 2.0


@dataclass(frozen=True)
class MountSettings:
    span_limit: float = 48.0
    cantilever_limit: float = 16.0
    edge_clearance: float = 2.0


@dataclass(frozen=True)
class JointSettings:
    horizontal_gap_threshold: float = 1.0
    vertical_tolerance: float = 0.5


@dataclass(frozen=True)
class ValidationSettings:
    allow_negative_coordinates: bool = False
    allow_duplicates: bool = False
    allow_overlaps: bool = False
    coordinate_tolerance: float = 1e-4

    def __post_init__(self) -> None:
        if self.coordinate_tolerance <= 0:
            raise LayoutValidationError(
                "coordinate_tolerance must be a positive number."
            )


@dataclass(frozen=True)
class LayoutConfig:
    panel: PanelSettings = field(default_factory=PanelSettings)
    rafters: RafterSettings = field(default_factory=RafterSettings)
    mounts: MountSettings = field(default_factory=MountSettings)
    joints: JointSettings = field(default_factory=JointSettings)
    validation: ValidationSettings = field(default_factory=ValidationSettings)


def _BuildSection(data: Mapping[str, Any] | None, cls: type) -> Any:
    if not data:
        return cls()
    return cls(**{key: value for key, value in data.items()})


def _ReadYaml(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise LayoutValidationError(
            f"Configuration file '{path}' was not found.") from error
    payload = yaml.safe_load(text) or {}
    if not isinstance(payload, dict):
        raise LayoutValidationError(
            "Configuration file must define a mapping at the root level.")
    return payload


def LoadConfig(path: Path | None = None) -> LayoutConfig:
    payload: Dict[str, Any] = {}
    if path is not None:
        payload = _ReadYaml(path)
    return LayoutConfig(
        panel=_BuildSection(payload.get("panel"), PanelSettings),
        rafters=_BuildSection(payload.get("rafters"), RafterSettings),
        mounts=_BuildSection(payload.get("mounts"), MountSettings),
        joints=_BuildSection(payload.get("joints"), JointSettings),
        validation=_BuildSection(payload.get(
            "validation"), ValidationSettings),
    )
