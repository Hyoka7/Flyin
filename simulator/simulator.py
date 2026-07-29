from graph import GraphHandler
from models import DroneSnapshot, DroneState, TurnSnapshot, ZoneTypes
from utils import get_sorted_key


class SimDrone:
    def __init__(self, drone_id: int, path: list[str]):
        self.drone_id = drone_id
        self.path = path
        self.goaled = False
        self.is_transit = False
        self.transit_dest: str | None = None
        self.path_index = 0

    @property
    def current_zone(self) -> str:
        return self.path[self.path_index]

    @property
    def next_zone(self) -> str | None:
        if len(self.path) <= self.path_index + 1:
            return None
        return self.path[self.path_index + 1]


class Simulator:
    def __init__(self, graph: GraphHandler, drone_paths: list[list[str]]):
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

    def get_snapshot(
        self,
        moves: tuple[str, ...] = (),
    ) -> TurnSnapshot:
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
        if self.remain_drone == 0 or self.deadlocked:
            return self.get_snapshot()

        moves: list[str] = []
        path_used = {name: 0 for name in self.graph.connection}
        active_drones = sorted(
            self.drones,
            key=lambda drone: (
                drone.is_transit,
                drone.path_index,
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
                moves.append(f"D{drone.drone_id}-{transit_dest}")
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
                    self.zone_reserved[next_zone]
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
                    f"D{drone.drone_id}-{cur_zone}-{next_zone}"
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
                moves.append(f"D{drone.drone_id}-{next_zone}")
                drone.path_index += 1
                if next_zone == self.graph.goal:
                    drone.goaled = True
                    self.remain_drone -= 1

        self.turn += 1
        if not moves and self.remain_drone > 0:
            self.deadlocked = True
        return self.get_snapshot(tuple(moves))

    def run_drone(self, logging: bool = True) -> int | None:
        while self.remain_drone > 0 and not self.deadlocked:
            snapshot = self.step()
            if snapshot.moves and logging:
                print(*snapshot.moves)
        if self.deadlocked:
            if logging:
                print("Dead Lock Happened!")
            return None
        return self.turn
