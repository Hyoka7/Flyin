from graph import GraphHandler
from models import ZoneTypes
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
        else:
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

    def run_drone(self, logging: bool = True) -> int | None:
        zone_occupancy = {name: 0 for name in self.graph.zones}
        zone_reserved = {name: 0 for name in self.graph.zones}
        zone_capacity = {
            name: self.graph.zones[name].metadata.max_drones
            for name in self.graph.zones
        }
        path_capacity = {
            name: self.graph.connection[name].metadata.max_link_capacity
            for name in self.graph.connection
        }
        zone_occupancy[self.graph.start] = self.remain_drone
        while self.remain_drone > 0:
            move = []
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
                if drone.goaled is True:
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
                    move.append(f"D{drone.drone_id}-{transit_dest}")
                    zone_occupancy[transit_dest] += 1
                    zone_reserved[transit_dest] -= 1
                    drone.is_transit = False
                    drone.transit_dest = None
                    drone.path_index += 1
                elif (
                    self.graph.zones[next_zone].metadata.zone
                    == ZoneTypes.Restricted
                ):
                    if (
                        zone_reserved[next_zone] >= zone_capacity[next_zone]
                        or path_used[con_key] >= path_capacity[con_key]
                    ):
                        continue
                    zone_occupancy[cur_zone] -= 1
                    zone_reserved[next_zone] += 1
                    path_used[con_key] += 1
                    drone.is_transit = True
                    drone.transit_dest = next_zone
                    move.append(f"D{drone.drone_id}-{cur_zone}-{next_zone}")
                    continue
                else:
                    if (
                        next_zone != self.graph.goal
                        and (
                            zone_occupancy[next_zone]
                            + zone_reserved[next_zone]
                            >= zone_capacity[next_zone]
                        )
                    ) or path_used[con_key] >= path_capacity[con_key]:
                        continue
                    zone_occupancy[next_zone] += 1
                    zone_occupancy[cur_zone] -= 1
                    path_used[con_key] += 1
                    move.append(f"D{drone.drone_id}-{next_zone}")
                    drone.path_index += 1
                    if next_zone == self.graph.goal:
                        drone.goaled = True
                        self.remain_drone -= 1
            self.turn += 1
            if move and logging:
                print(*move)
            else:
                if not move:
                    if logging:
                        print("Dead Lock Happened!")
                    return None
        return self.turn
