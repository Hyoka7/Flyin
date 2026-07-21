# import sys


from graph import GraphHandler, YenPathFinder
from parse import Parser
from scheduler import Scheduler
from simulator import Simulator


def main(file_path: str):

    parser = Parser()
    parse_res = parser.parse_file(file_path)
    if parse_res is None:
        return
    handler = GraphHandler(parse_res)
    handler.construct()
    pathfinder = YenPathFinder(handler)
    scheduler = Scheduler(pathfinder)
    drone_paths = scheduler.scheduling(handler.drone_count)
    if not drone_paths:
        print("No available paths")
        return
    simulator = Simulator(handler, drone_paths)
    turns = simulator.run_drone()
    return turns

if __name__ == "__main__":
    main("test.txt")