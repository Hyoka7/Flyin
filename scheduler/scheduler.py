from heapq import heappop, heappush

from graph import YenPathFinder


class Scheduler:
    def __init__(self, finder: YenPathFinder):
        self.finder: YenPathFinder = finder

    def scheduling(self, nb_drones: int):
        drone_path = []
        paths = self.finder.find_k_paths(nb_drones)
        path_costs = [self.finder.build_cumsum(path)[-1] for path in paths]
        path_pq = []
        for i in range(len(paths)):
            heappush(path_pq, ((path_costs[i], paths[i])))
        if not paths:
            return []
        for i in range(nb_drones):
            score, path = heappop(path_pq)
            drone_path.append(path)
            heappush(path_pq, (score + 1, path))
        return drone_path
