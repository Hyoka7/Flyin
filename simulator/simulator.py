from graph import GraphHandler
from models import ZoneTypes
from utils import get_sorted_key


class SimDrone:
    def __init__(self, drone_id: int, path: list[str]):
        self.drone_id = drone_id
        self.path = path
        self.goaled = False
        self.is_transit = False
        self.transit_dest = None
        self.path_index = 0

    @property
    def current_zone(self):
        return self.path[self.path_index]

    @property
    def next_zone(self):
        if len(self.path) <= self.path_index + 1:
            return None
        else:
            return self.path[self.path_index + 1]


class Simulator:
    def __init__(
        self,
        graph: GraphHandler,
    ):
        self.graph = graph
        self.turn = 0
        self.drones = [
            SimDrone(drone_id, self.graph.dijkstra_path())
            for drone_id in range(1, self.graph.drone_count + 1)
        ]
        self.remain_drone = self.graph.drone_count

    def run_drone(self):
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
            for drone in self.drones:
                if drone.goaled is True:
                    continue
                cur_zone = drone.current_zone
                next_zone = drone.next_zone
                con_key = get_sorted_key(cur_zone, next_zone)
                if drone.is_transit:
                    move.append(f"D{drone.drone_id}-{drone.transit_dest}")
                    zone_occupancy[drone.transit_dest] += 1
                    zone_reserved[drone.transit_dest] -= 1
                    drone.is_transit = False
                    drone.transit_dest = None
                    drone.path_index += 1
                elif self.graph.zones[next_zone].metadata.zone == ZoneTypes.Restricted:
                    if (
                        zone_reserved[next_zone] + zone_reserved[next_zone]
                        >= zone_capacity[next_zone]
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
                        and zone_occupancy[next_zone] + zone_reserved[next_zone]
                        >= zone_capacity[next_zone]
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
            if move:
                print(*move)
            else:
                print("Dead Lock Happened!")
                return None
        return self.turn
