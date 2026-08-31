from typing import Optional, List
from pydantic import BaseModel, Field


class ZoneData(BaseModel):
    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: Optional[str] = None
    max_drones: int = Field(default=1, ge=1)
    is_start: bool = False
    is_end: bool = False


class ConnectionData(BaseModel):
    zone_a: str
    zone_b: str
    max_link_capacity: int = Field(default=1, ge=1)


class MapData(BaseModel):
    nb_drones: int = Field(ge=0, le=1000)
    zones: List[ZoneData]
    connections: List[ConnectionData]
