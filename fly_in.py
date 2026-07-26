import argparse

from graph import GraphHandler, YenPathFinder
from parse import Parser
from scheduler import Scheduler
from simulator import Simulator


def main(file_path: str, show_gui: bool = False) -> int | None:
    parser = Parser()
    parse_res = parser.parse_file(file_path)
    if parse_res is None:
        return None
    handler = GraphHandler(parse_res)
    handler.construct()

    if show_gui:
        from visualizer import Visualizer, VisualizerUnavailableError

        try:
            Visualizer(handler).run()
        except VisualizerUnavailableError as err:
            print(f"GUI unavailable: {err}")
        return None

    pathfinder = YenPathFinder(handler)
    scheduler = Scheduler(pathfinder)
    drone_paths = scheduler.scheduling(handler.drone_count)
    if not drone_paths:
        print("No available paths")
        return None
    simulator = Simulator(handler, drone_paths)
    turns = simulator.run_drone()
    print(turns)
    return turns


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(
        description="Route drones through a network of zones."
    )
    argument_parser.add_argument(
        "map_file",
        nargs="?",
        default="test.txt",
        help="path to the map configuration file",
    )
    argument_parser.add_argument(
        "--gui",
        action="store_true",
        help="display the initial map with tkinter",
    )
    arguments = argument_parser.parse_args()
    main(arguments.map_file, show_gui=arguments.gui)
