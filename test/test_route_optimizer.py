from graph import GraphHandler, YenPathFinder
from parse import Parser
from scheduler import Scheduler
from simulator import Simulator


def build_graph(path: str) -> GraphHandler:
    parse_result = Parser().parse_file(path)
    assert parse_result is not None
    graph = GraphHandler(parse_result)
    graph.construct()
    return graph


def test_adds_path_when_shared_start_connection_leads_to_fork() -> None:
    graph = build_graph("test_configs/test_route_optimizer.txt")
    finder = YenPathFinder(graph)
    candidates = finder.find_k_paths(graph.drone_count)

    shortest_only = [candidates[0]] * graph.drone_count
    shortest_turns = Simulator(
        graph,
        shortest_only,
    ).run_drone(logging=False)

    optimized_paths = Scheduler(finder).scheduling(graph.drone_count)
    optimized_turns = Simulator(
        graph,
        optimized_paths,
    ).run_drone(logging=False)

    assert len({tuple(path) for path in optimized_paths}) == 2
    assert optimized_turns is not None
    assert shortest_turns is not None
    assert optimized_turns < shortest_turns
