# import sys

from graph import GraphHandler
from models import Connection, Drone, Zone
from parse import Parser


def main(
    path: str,
) -> list[Drone | Zone | Connection] | None:
    parser = Parser()
    return parser.parse_file(path)


if __name__ == "__main__":
    result = main("test.txt")
    handler = GraphHandler(result)
    handler.construct()
    res_cost = handler.dijkstra_cost()
    res_path = handler.dijkstra_path()
    print(res_cost)
    print(*res_path)
    # if result is None:
    #     print("Aborting")
    #     sys.exit(1)

    # for item in result:
    #     print(item)
