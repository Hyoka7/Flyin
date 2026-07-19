# import sys

import sys

from graph import GraphHandler
from models import Connection, Drone, Zone
from parse import Parser
from simulator import Simulator


def main(
    path: str,
) -> list[Drone | Zone | Connection] | None:
    parser = Parser()
    return parser.parse_file(path)


if __name__ == "__main__":
    result = main("test.txt")
    handler = GraphHandler(result)
    handler.construct()
    if handler.dijkstra_path() == []:
        print("Can't reach goal.")
        print("Aborting")
        sys.exit(1)
    sim = Simulator(handler)
    print(sim.run_drone())

    # if result is None:
    #     print("Aborting")
    #     sys.exit(1)

    # for item in result:
    #     print(item)
