from pathlib import Path

from graph import GraphHandler, YenPathFinder
from parse import Parser
from utils import get_sorted_key


THREE_PATH_MAP = """\
nb_drones: 3

start_hub: start 0 0
end_hub: goal 4 0
hub: a 1 0
hub: b 1 1
hub: c 2 1
hub: d 1 2
hub: e 2 2
hub: f 3 2

connection: start-a
connection: a-goal
connection: start-b
connection: b-c
connection: c-goal
connection: start-d
connection: d-e
connection: e-f
connection: f-goal
"""


def make_finder(
    tmp_path: Path,
    config: str,
) -> YenPathFinder:
    """Build a Yen path finder from a temporary map configuration."""
    config_path = tmp_path / "map.txt"
    config_path.write_text(config, encoding="utf-8")

    parsed = Parser().parse_file(str(config_path))
    assert parsed is not None

    graph = GraphHandler(parsed)
    graph.construct()
    return YenPathFinder(graph)


def test_returns_paths_in_cost_order(tmp_path: Path) -> None:
    finder = make_finder(tmp_path, THREE_PATH_MAP)

    assert finder.find_k_paths(3) == [
        ["start", "a", "goal"],
        ["start", "b", "c", "goal"],
        ["start", "d", "e", "f", "goal"],
    ]


def test_returns_all_available_paths_when_k_is_too_large(
    tmp_path: Path,
) -> None:
    finder = make_finder(tmp_path, THREE_PATH_MAP)

    paths = finder.find_k_paths(10)

    assert len(paths) == 3
    assert len({tuple(path) for path in paths}) == 3


def test_does_not_return_duplicate_paths_on_dense_graph(
    tmp_path: Path,
) -> None:
    finder = make_finder(
        tmp_path,
        """\
nb_drones: 1
start_hub: start 0 0
end_hub: goal 3 0
hub: a 1 0
hub: b 2 0
connection: start-goal
connection: start-a
connection: start-b
connection: a-b
connection: a-goal
connection: b-goal
""",
    )

    paths = finder.find_k_paths(10)

    assert len(paths) == 5
    assert len({tuple(path) for path in paths}) == 5


def test_non_positive_k_returns_no_paths(tmp_path: Path) -> None:
    finder = make_finder(tmp_path, THREE_PATH_MAP)

    assert finder.find_k_paths(0) == []
    assert finder.find_k_paths(-1) == []


def test_unreachable_goal_returns_no_paths(tmp_path: Path) -> None:
    finder = make_finder(
        tmp_path,
        """\
nb_drones: 1
start_hub: start 0 0
end_hub: goal 2 0
hub: isolated 1 0
connection: start-isolated
""",
    )

    assert finder.find_k_paths(3) == []


def test_builds_cumulative_costs_with_restricted_zone(
    tmp_path: Path,
) -> None:
    finder = make_finder(
        tmp_path,
        """\
nb_drones: 1
start_hub: start 0 0
end_hub: goal 3 0
hub: restricted_hub 1 0 [zone=restricted]
hub: normal_hub 2 0
connection: start-restricted_hub
connection: restricted_hub-normal_hub
connection: normal_hub-goal
""",
    )

    assert finder.build_cumsum(
        ["start", "restricted_hub", "normal_hub", "goal"]
    ) == [0, 2, 3, 4]


def test_bans_each_connection_after_matching_root(
    tmp_path: Path,
) -> None:
    finder = make_finder(tmp_path, THREE_PATH_MAP)

    banned = finder.build_banned_connect(
        [
            ["start", "a", "b", "goal"],
            ["start", "a", "c", "goal"],
            ["start", "d", "goal"],
        ],
        ["start", "a"],
    )

    assert banned == {
        get_sorted_key("a", "b"),
        get_sorted_key("a", "c"),
    }
