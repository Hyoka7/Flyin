# import sys


from graph import GraphHandler
from models import Connection, Drone, Zone
from parse import Parser
from utils import get_sorted_key


def main(
    path: str,
) -> list[Drone | Zone | Connection] | None:
    parser = Parser()
    return parser.parse_file(path)


if __name__ == "__main__":
    result = main("test.txt")
    handler = GraphHandler(result)
    handler.construct()
    res1 = handler.dijkstra_path()
    res2 = handler.dijkstra_path(
        start="roof1",
        end=handler.goal,
    )
    res3 = handler.dijkstra_path(
        banned_connection={
            get_sorted_key("hub", "roof1"),
        },
    )
    res4 = handler.dijkstra_path(
        banned_connection={
            get_sorted_key("roof1", "roof2"),
        },
    )
    print(*res1)
    print(*res2)
    print(*res3)
    print(*res4)
    # if result is None:
    #     print("Aborting")
    #     sys.exit(1)

    # for item in result:
    #     print(item)
