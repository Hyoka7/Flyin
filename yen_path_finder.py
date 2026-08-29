from heapq import heappop, heappush

from graph_handler import GraphHandler
from models import ZoneTypes
from util import get_sorted_key


class YenPathFinder:
    """Generate alternative loopless routes with Yen's algorithm."""

    def __init__(self, graph: GraphHandler):
        """Store the graph used for all path searches.

        Args:
            graph: Constructed graph handler.
        """
        self.graph = graph

    def build_banned_connect(
        self,
        fixed_path: list[list[str]],
        curr_path: list[str],
    ) -> set[tuple[str, str]]:
        """Find next edges that would recreate already accepted root paths.

        Args:
            fixed_path: Paths already accepted by Yen's algorithm.
            curr_path: Root path currently being expanded.

        Returns:
            Undirected connection keys to exclude from the spur search.
        """
        banned: set[tuple[str, str]] = set()
        curr_len = len(curr_path)
        for fixed in fixed_path:
            if len(fixed) <= curr_len:
                continue
            if curr_path == fixed[:curr_len]:
                banned.add(
                    get_sorted_key(
                        fixed[curr_len - 1],
                        fixed[curr_len],
                    )
                )
        return banned

    def build_cumsum(self, path: list[str]) -> list[int]:
        """Build cumulative movement costs for every path prefix.

        Args:
            path: Ordered zone names.

        Returns:
            Cumulative cost at each index, beginning with zero.
        """
        cumsum = [0] * len(path)
        for i in range(1, len(path)):
            cost = self.graph.get_move_cost(path[i])
            cumsum[i] = cumsum[i - 1] + cost
        return cumsum

    def build_priority_count(self, path: list[str]) -> int:
        """Count priority destinations contained in a path.

        Args:
            path: Ordered zone names.

        Returns:
            Number of priority zones after the starting zone.
        """
        return sum(
            1
            for zone_name in path[1:]
            if self.graph.zones[zone_name].metadata.zone == ZoneTypes.Priority
        )

    def find_k_paths(self, k: int) -> list[list[str]]:
        """Return up to K minimum-cost loopless paths.

        Args:
            k: Maximum number of paths to generate.

        Returns:
            Accepted paths ordered by weighted cost and priority tie-breakers.
        """
        if k <= 0:
            return []
        original_path = self.graph.dijkstra_path()
        if original_path == []:
            return []
        fixed_paths = [original_path]
        cand_pq: list[tuple[float, int, list[str]]] = []
        cand_keys: set[tuple[str, ...]] = set()
        cand_keys.add(tuple(original_path))
        while len(fixed_paths) < k:
            previous_path = fixed_paths[-1]
            previous_cumsum = self.build_cumsum(previous_path)
            for i in range(len(previous_path) - 1):
                branch_node = previous_path[i]
                root_path = previous_path[: i + 1]
                root_cost = previous_cumsum[i]
                banned_nodes = set(root_path[:-1])
                banned_connection = self.build_banned_connect(
                    fixed_paths,
                    root_path,
                )
                new_path = self.graph.dijkstra_path(
                    branch_node,
                    self.graph.goal,
                    banned_connection,
                    banned_nodes,
                )
                if not new_path:
                    continue
                branch_to_goal_path = root_path[:-1] + new_path
                new_path_key = tuple(branch_to_goal_path)
                if new_path_key in cand_keys:
                    continue
                cand_keys.add(new_path_key)
                priority_count = self.build_priority_count(branch_to_goal_path)
                new_dists = self.graph.dijkstra_cost(
                    branch_node,
                    banned_connection,
                    banned_nodes,
                )
                branch_to_goal_cost = new_dists[self.graph.goal]
                heappush(
                    cand_pq,
                    (
                        root_cost + branch_to_goal_cost,
                        -priority_count,
                        branch_to_goal_path,
                    ),
                )
            if cand_pq:
                _, _, path = heappop(cand_pq)
                fixed_paths.append(path)
            else:
                break
        return fixed_paths
