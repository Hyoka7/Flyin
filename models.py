from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Drone(BaseModel):
    """Store the validated number of drones declared by a map."""

    nb_drones: int = Field(..., gt=0)


class DroneState(str, Enum):
    """Describe a drone's location category in a simulation snapshot."""

    AT_ZONE = "at_zone"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


@dataclass(frozen=True)
class DroneSnapshot:
    """Represent one immutable drone state at the end of a turn."""

    drone_id: int
    state: DroneState
    zone: str | None
    transit_from: str | None
    transit_to: str | None


@dataclass(frozen=True)
class TurnSnapshot:
    """Represent all movements and drone states for one simulation turn."""

    turn: int
    moves: tuple[str, ...]
    drones: tuple[DroneSnapshot, ...]
    finished: bool
    deadlocked: bool


class ZoneTypes(str, Enum):
    """List the supported movement behaviours for zones."""

    Normal = "normal"
    Blocked = "blocked"
    Restricted = "restricted"
    Priority = "priority"


class ZoneMetadata(BaseModel):
    """Store validated optional properties attached to a zone."""

    model_config = ConfigDict(extra="forbid")
    zone: ZoneTypes = Field(ZoneTypes.Normal)
    color: str | None = Field(None)
    max_drones: int = Field(1, ge=1)


class Zone(BaseModel):
    """Represent a named graph zone and its display coordinates."""

    key: str
    name: str
    x: int
    y: int
    metadata: ZoneMetadata

    @model_validator(mode="after")
    def zone_name_validate(self) -> "Zone":
        """Validate the zone declaration prefix.

        Returns:
            The validated zone instance.

        Raises:
            ValueError: If the declaration prefix is not supported.
        """
        valid_name = ["start_hub", "end_hub", "hub"]
        if self.key not in valid_name:
            raise ValueError("key is unknown")
        return self


class ConnectionMetadata(BaseModel):
    """Store the validated capacity attached to a connection."""

    model_config = ConfigDict(extra="forbid")

    max_link_capacity: int = Field(1, ge=1)


class Connection(BaseModel):
    """Represent a bidirectional connection between two named zones."""

    model_config = ConfigDict(extra="forbid")
    key: str
    from_: str
    to: str
    metadata: ConnectionMetadata
