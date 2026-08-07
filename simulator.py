from graph_handler import GraphHandler
from models import DroneSnapshot, DroneState, TurnSnapshot, ZoneTypes
from util import format_drone_id, format_path, get_sorted_key


class SimDrone:
    """Store mutable runtime state for one scheduled drone."""

    def __init__(self, drone_id: int, path: list[str]):
        """Initialize a drone at the first zone of its assigned path.

        Args:
            drone_id: One-based identifier used in simulation output.
            path: Ordered zones assigned to the drone.
        """
        self.drone_id = drone_id
        self.path = path
        self.goaled = False
        self.is_transit = False
        self.transit_dest: str | None = None
        self.path_index = 0

    @property
    def current_zone(self) -> str:
        """Return the zone occupied before the drone's next movement."""
        return self.path[self.path_index]

    @property
    def next_zone(self) -> str | None:
        """Return the next path zone, or None after the final zone."""
        if len(self.path) <= self.path_index + 1:
            return None
        return self.path[self.path_index + 1]


class Simulator:
    """Execute capacity-aware drone movements in discrete turns."""

    def __init__(self, graph: GraphHandler, drone_paths: list[list[str]]):
        """Initialize occupancy, capacity, and per-drone runtime state.

        Args:
            graph: Constructed map graph.
            drone_paths: One valid path for every graph drone.
        """
        self.graph = graph
        self.turn = 0
        self.drone_paths = drone_paths
        self.remain_drone = self.graph.drone_count
        self.drones = [
            SimDrone(drone_id + 1, self.drone_paths[drone_id])
            for drone_id in range(self.graph.drone_count)
        ]
        self.zone_occupancy = {name: 0 for name in self.graph.zones}
        self.zone_reserved = {name: 0 for name in self.graph.zones}
        self.zone_capacity = {
            name: self.graph.zones[name].metadata.max_drones
            for name in self.graph.zones
        }
        self.path_capacity = {
            name: self.graph.connection[name].metadata.max_link_capacity
            for name in self.graph.connection
        }
        self.zone_occupancy[self.graph.start] = self.remain_drone
        self.deadlocked = False

    def get_remaining_cost(self, drone: SimDrone) -> int:
        """Return the number of turns remaining on a drone's path.

        A restricted destination costs two turns. When the drone is already
        in transit, the first of those two turns has already been consumed.

        Args:
            drone: Runtime drone whose remaining path is measured.

        Returns:
            Weighted movement cost from the current state to the goal.
        """
        cost = sum(
            self.graph.get_move_cost(zone_name)
            for zone_name in drone.path[drone.path_index + 1:]
        )
        if drone.is_transit:
            cost -= 1
        return cost

    def get_snapshot(
        self,
        moves: tuple[str, ...] = (),
    ) -> TurnSnapshot:
        """Create an immutable view of the current simulation state.

        Args:
            moves: Movement strings produced during the current turn.

        Returns:
            A snapshot containing every drone and completion status.
        """
        snapshots: list[DroneSnapshot] = []
        for drone in self.drones:
            if drone.goaled:
                snapshot = DroneSnapshot(
                    drone.drone_id,
                    DroneState.DELIVERED,
                    self.graph.goal,
                    None,
                    None,
                )
            elif drone.is_transit:
                snapshot = DroneSnapshot(
                    drone.drone_id,
                    DroneState.IN_TRANSIT,
                    None,
                    drone.current_zone,
                    drone.transit_dest,
                )
            else:
                snapshot = DroneSnapshot(
                    drone.drone_id,
                    DroneState.AT_ZONE,
                    drone.current_zone,
                    None,
                    None,
                )
            snapshots.append(snapshot)
        return TurnSnapshot(
            self.turn,
            moves,
            tuple(snapshots),
            self.remain_drone == 0,
            self.deadlocked,
        )

    def step(self) -> TurnSnapshot:
        """Advance all eligible drones by exactly one simulation turn.

        Drones already in restricted transit arrive first. Drones farther
        along their paths are considered next; at the same path index, the
        drone with the lower remaining cost is considered first.

        Returns:
            The immutable state after the completed turn.
        """
        if self.remain_drone == 0 or self.deadlocked:
            return self.get_snapshot()

        moves: list[str] = []
        path_used = {name: 0 for name in self.graph.connection}
        active_drones = sorted(
            self.drones,
            key=lambda drone: (
                drone.is_transit,
                drone.path_index,
                -self.get_remaining_cost(drone),
                -drone.drone_id,
            ),
            reverse=True,
        )
        for drone in active_drones:
            if drone.goaled:
                continue
            cur_zone = drone.current_zone
            next_zone = drone.next_zone
            if next_zone is None:
                continue
            con_key = get_sorted_key(cur_zone, next_zone)
            if drone.is_transit:
                transit_dest = drone.transit_dest
                if transit_dest is None:
                    continue
                moves.append(
                    f"{format_drone_id(drone.drone_id)}-{transit_dest}"
                )
                self.zone_occupancy[transit_dest] += 1
                self.zone_reserved[transit_dest] -= 1
                drone.is_transit = False
                drone.transit_dest = None
                drone.path_index += 1
            elif (
                self.graph.zones[next_zone].metadata.zone
                == ZoneTypes.Restricted
            ):
                if (
                    self.zone_occupancy[next_zone]
                    + self.zone_reserved[next_zone]
                    >= self.zone_capacity[next_zone]
                    or path_used[con_key] >= self.path_capacity[con_key]
                ):
                    continue
                self.zone_occupancy[cur_zone] -= 1
                self.zone_reserved[next_zone] += 1
                path_used[con_key] += 1
                drone.is_transit = True
                drone.transit_dest = next_zone
                moves.append(
                    f"{format_drone_id(drone.drone_id)}-"
                    f"{format_path(cur_zone, next_zone)}"
                )
            else:
                zone_is_full = (
                    next_zone != self.graph.goal
                    and (
                        self.zone_occupancy[next_zone]
                        + self.zone_reserved[next_zone]
                        >= self.zone_capacity[next_zone]
                    )
                )
                path_is_full = (
                    path_used[con_key] >= self.path_capacity[con_key]
                )
                if zone_is_full or path_is_full:
                    continue
                self.zone_occupancy[next_zone] += 1
                self.zone_occupancy[cur_zone] -= 1
                path_used[con_key] += 1
                moves.append(
                    f"{format_drone_id(drone.drone_id)}-{next_zone}"
                )
                drone.path_index += 1
                if next_zone == self.graph.goal:
                    drone.goaled = True
                    self.remain_drone -= 1

        self.turn += 1
        if not moves and self.remain_drone > 0:
            self.deadlocked = True
        return self.get_snapshot(tuple(moves))

    def run_drone(self, logging: bool = True) -> int | None:
        """Run turns until delivery or deadlock.

        Args:
            logging: Whether to print required movement lines.

        Returns:
            Total completed turns, or None when a deadlock occurs.
        """
        while self.remain_drone > 0 and not self.deadlocked:
            snapshot = self.step()
            if snapshot.moves and logging:
                print(*snapshot.moves)
        if self.deadlocked:
            return None
        return self.turn
