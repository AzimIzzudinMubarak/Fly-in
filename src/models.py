from typing import Optional, List
from pydantic import BaseModel, NonNegativeInt


class ZoneData(BaseModel):
    name: str
    x: int
    y: int
    zone_type: str = "normal"
    color: Optional[str] = None
    max_drones: int = 1
    is_start: bool = False
    is_end: bool = False


class ConnectionData(BaseModel):
    zone_a: str
    zone_b: str
    max_link_capacity: int = 1


class MapData(BaseModel):
    nb_drones: NonNegativeInt
    zones: List[ZoneData]
    connections: List[ConnectionData]
