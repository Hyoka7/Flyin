from collections import defaultdict
from heapq import heappop, heappush

from models import Connection, Zone, ZoneTypes
from utils import get_sorted_key


class GraphHandler:
    def __init__(self, data: list):
        self.data: list = data
        self.zones: dict[Zone] = {}
        self.connection = {}
        self.neighbors = defaultdict(list)


    def construct(self):
        for d in self.data:
            if isinstance(d, Connection):
                self.neighbors[d.from_].append(d)
                self.neighbors[d.to].append(d)
                key = get_sorted_key(d.from_, d.to)
                self.connection[key] = d
            elif isinstance(d, Zone):
                self.zones[d.name] = d
                if d.key == "start_hub":
                    self.start = d.name
                elif d.key == "end_hub":
                    self.goal = d.name
            else:
                self.drone_count = d.nb_drones

    def get_move_cost(self, zone_name: str):
        zone = self.zones[zone_name]

        if zone.metadata.zone == ZoneTypes.Restricted:
            return 2
        elif zone.metadata.zone in (ZoneTypes.Normal, ZoneTypes.Priority):
            return 1
        return -1

    def get_neighbor_name(self, current, connection: Connection):
        if connection.from_ == current:
            return connection.to
        elif connection.to == current:
            return connection.from_
        else:
            return None

    def dijkstra_cost(self):
        dists = {name: float("inf") for name in self.zones}
        dists[self.start] = 0
        pq = []
        heappush(pq, (0, self.start))
        while pq:
            cur_cost, zone_name = heappop(pq)
            if cur_cost > dists[zone_name]:
                continue
            for connection in self.neighbors[zone_name]:
                neighbor = self.get_neighbor_name(
                    zone_name,
                    connection,
                )
                move_cost = self.get_move_cost(neighbor)
                if move_cost == -1:
                    continue
                new_cost = cur_cost + move_cost
                if new_cost < dists[neighbor]:
                    dists[neighbor] = new_cost
                    heappush(
                        pq,
                        (
                            new_cost,
                            neighbor,
                        ),
                    )
        return dists

    def dijkstra_path(self):
        dists = self.dijkstra_cost()
        if dists[self.goal] == float("inf"):
            return []
        path = [self.goal]
        current = self.goal
        while current != self.start:
            cur_cost = dists[current]
            move_cost = self.get_move_cost(current)
            for connection in self.neighbors[current]:
                neighbor = self.get_neighbor_name(current, connection)
                if cur_cost - move_cost == dists[neighbor]:
                    current = neighbor
                    path.append(neighbor)
                    break
        return path[::-1]
