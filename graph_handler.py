from collections import defaultdict
from heapq import heappop, heappush

from models import Connection, Drone, Zone, ZoneTypes
from util import get_sorted_key


class GraphHandler:
    """Build and query the graph represented by validated map models."""

    def __init__(self, data: list[Drone | Zone | Connection]):
        """Initialize empty graph indexes from parsed model data.

        Args:
            data: Validated drone, zone, and connection declarations.
        """
        self.data = data
        self.zones: dict[str, Zone] = {}
        self.connection: dict[tuple[str, str], Connection] = {}
        self.neighbors: defaultdict[str, list[Connection]] = defaultdict(list)
        self.start = ""
        self.goal = ""
        self.drone_count = 0

    def construct(self) -> None:
        """Populate zone, connection, and adjacency indexes from input data."""
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

    def get_move_cost(self, zone_name: str) -> int:
        """Return the turn cost of entering a zone.

        Args:
            zone_name: Destination zone name.

        Returns:
            Two for restricted zones, one for traversable one-turn zones, or
            negative one for blocked zones.
        """
        zone = self.zones[zone_name]

        if zone.metadata.zone == ZoneTypes.Restricted:
            return 2
        elif zone.metadata.zone in (ZoneTypes.Normal, ZoneTypes.Priority):
            return 1
        return -1

    def get_neighbor_name(
        self,
        current: str,
        connection: Connection,
    ) -> str | None:
        """Return the opposite endpoint of an incident connection.

        Args:
            current: Zone from which the connection is being inspected.
            connection: Bidirectional connection to inspect.

        Returns:
            The opposite zone name, or None if the connection is not incident
            to the current zone.
        """
        if connection.from_ == current:
            return connection.to
        elif connection.to == current:
            return connection.from_
        else:
            return None

    def dijkstra_cost(
        self,
        start: str | None = None,
        banned_connection: set[tuple[str, str]] | None = None,
        banned_node: set[str] | None = None,
    ) -> dict[str, float]:
        """Calculate weighted minimum costs from a source to every zone.

        Priority-zone count is used as a tie-breaker between equal-cost paths.

        Args:
            start: Source zone, defaulting to the graph start.
            banned_connection: Connections excluded from this search.
            banned_node: Zones excluded from this search.

        Returns:
            A mapping from zone name to minimum cost, with infinity for
            unreachable zones.
        """
        dists, _ = self._dijkstra(
            start,
            banned_connection,
            banned_node,
        )
        return dists

    def _dijkstra(
        self,
        start: str | None = None,
        banned_connection: set[tuple[str, str]] | None = None,
        banned_node: set[str] | None = None,
    ) -> tuple[dict[str, float], dict[str, str | None]]:
        """Calculate weighted distances and predecessor links.

        Args:
            start: Source zone, defaulting to the graph start.
            banned_connection: Connections excluded from this search.
            banned_node: Zones excluded from this search.

        Returns:
            A pair containing minimum costs and predecessor zone names.
        """
        if start is None:
            start = self.start
        if banned_connection is None:
            banned_connection = set()
        if banned_node is None:
            banned_node = set()
        dists = {name: float("inf") for name in self.zones}
        priority_scores = {name: float("inf") for name in self.zones}
        prev: dict[str, str | None] = {
            name: None for name in self.zones
        }
        dists[start] = 0
        priority_scores[start] = 0
        pq: list[tuple[float, float, str]] = []
        heappush(pq, (0, 0, start))
        while pq:
            cur_cost, priority_count, zone_name = heappop(pq)
            if (cur_cost, priority_count) != (
                dists[zone_name],
                priority_scores[zone_name],
            ):
                continue
            for connection in self.neighbors[zone_name]:
                neighbor = self.get_neighbor_name(
                    zone_name,
                    connection,
                )
                if neighbor is None:
                    continue
                con_key = get_sorted_key(zone_name, neighbor)
                if con_key in banned_connection or neighbor in banned_node:
                    continue
                new_priority_count = priority_count
                if self.zones[neighbor].metadata.zone == ZoneTypes.Priority:
                    new_priority_count -= 1
                move_cost = self.get_move_cost(neighbor)
                if move_cost == -1:
                    continue
                new_cost = cur_cost + move_cost
                if (new_cost, new_priority_count) < (
                    dists[neighbor],
                    priority_scores[neighbor],
                ):
                    dists[neighbor] = new_cost
                    priority_scores[neighbor] = new_priority_count
                    prev[neighbor] = zone_name
                    heappush(
                        pq,
                        (
                            new_cost,
                            new_priority_count,
                            neighbor,
                        ),
                    )
        return (dists, prev)

    def dijkstra_path(
        self,
        start: str | None = None,
        end: str | None = None,
        banned_connection: set[tuple[str, str]] | None = None,
        banned_node: set[str] | None = None,
    ) -> list[str]:
        """Return one minimum-cost path between two zones.

        Args:
            start: Source zone, defaulting to the graph start.
            end: Destination zone, defaulting to the graph goal.
            banned_connection: Connections excluded from this search.
            banned_node: Zones excluded from this search.

        Returns:
            Ordered zone names from source to destination, or an empty list
            when no valid path exists.
        """
        if start is None:
            start = self.start
        if end is None:
            end = self.goal
        if banned_connection is None:
            banned_connection = set()
        if banned_node is None:
            banned_node = set()
        dists, prev = self._dijkstra(
            start,
            banned_connection,
            banned_node,
        )
        if dists[end] == float("inf"):
            return []
        path = [end]
        current = end
        while current != start:
            next_current = prev[current]
            if next_current is None:
                return []
            current = next_current
            path.append(current)
        return path[::-1]
