from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class Envelope(BaseModel):
    width_m: float
    depth_m: float
    axes_x: List[str] = Field(default_factory=list)
    axes_y: List[str] = Field(default_factory=list)
    grid_step_m: Optional[float] = None


class Counts(BaseModel):
    walls: int = 0
    columns: int = 0
    slabs: int = 0
    grids: int = 0


class FloorSpec(BaseModel):
    floor_id: str
    elevation_m: Optional[float] = None
    envelope: Envelope
    counts: Counts = Counts()
    notes: List[str] = Field(default_factory=list)


class BuildingSpec(BaseModel):
    project: str = "industrial MFC, anonymised"
    storeys: int
    floors: List[FloorSpec]
