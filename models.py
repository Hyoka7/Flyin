from pydantic import BaseModel, Field, model_validator, ConfigDict
from enum import Enum


class Drone(BaseModel):
    nb_drones: int = Field(..., gt=0)

class ZoneTypes(str, Enum):
    Normal = "normal"
    Blocked = "blocked"
    Restricted = "restricted"
    Priority = "priority"

class ZoneMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    zone: ZoneTypes = Field(ZoneTypes.Normal)
    color: str | None = Field(None)
    max_drones: int = Field(1, ge=1)

class Zone(BaseModel):
    key: str
    name: str
    x: int
    y: int
    metadata: ZoneMetadata
    
    @model_validator(mode="after")
    def zone_name_validate(self):
        valid_name = ["start_hub", "end_hub", "hub"]
        if self.key not in valid_name:
            raise ValueError("key is unknown")
        return self
    
class ConnectionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_link_capacity: int = Field(1, ge=1)

class Connection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str
    from_: str
    to: str
    metadata: ConnectionMetadata
