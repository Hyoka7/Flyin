from heapq import heappop, heappush

from yen_path_finder import YenPathFinder


class Scheduler:
    """Select useful routes and assign one route to every drone."""

    def __init__(self, finder: YenPathFinder):
        """Initialize a scheduler with a candidate path finder.

        Args:
            finder: Yen path finder bound to the target graph.
        """
        self.finder: YenPathFinder = finder

    def _assign_paths(
        self,
        nb_drones: int,
        paths: list[list[str]],
    ) -> list[list[str]]:
        """Distribute drones among a fixed set of candidate paths.

        Args:
            nb_drones: Number of routes that must be assigned.
            paths: Candidate paths available for assignment.

        Returns:
            One ordered zone path for each drone.
        """
        drone_path = []
        path_costs = [self.finder.build_cumsum(path)[-1] for path in paths]
        path_pq: list[tuple[int, list[str]]] = []
        for i in range(len(paths)):
            heappush(path_pq, (path_costs[i], paths[i]))
        for _ in range(nb_drones):
            score, path = heappop(path_pq)
            drone_path.append(path)
            heappush(path_pq, (score + 1, path))
        return drone_path

    def scheduling(self, nb_drones: int) -> list[list[str]]:
        """Choose a route set that minimizes measured simulation turns.

        Args:
            nb_drones: Number of drones to schedule.

        Returns:
            The best simulated path assignment, or an empty list when the
            goal is unreachable.
        """
        from simulator import Simulator

        candidates = self.finder.find_k_paths(nb_drones)
        if not candidates:
            return []

        selected = [candidates[0]]
        remaining = candidates[1:]
        best_assignment = self._assign_paths(nb_drones, selected)
        best_turns = Simulator(
            self.finder.graph,
            best_assignment,
        ).run_drone(logging=False)

        while remaining:
            next_path = None
            next_assignment = None
            next_turns = best_turns

            for candidate in remaining:
                test_assignment = self._assign_paths(
                    nb_drones,
                    selected + [candidate],
                )
                turns = Simulator(
                    self.finder.graph,
                    test_assignment,
                ).run_drone(logging=False)
                if turns is not None and (
                    next_turns is None or turns < next_turns
                ):
                    next_path = candidate
                    next_assignment = test_assignment
                    next_turns = turns

            if next_path is None or next_assignment is None:
                break

            selected.append(next_path)
            remaining.remove(next_path)
            best_assignment = next_assignment
            best_turns = next_turns

        return best_assignment
