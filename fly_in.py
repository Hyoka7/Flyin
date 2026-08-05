import os

from colors import print_color
from graph_handler import GraphHandler
from parser import Parser
from scheduler import Scheduler
from simulator import Simulator
from yen_path_finder import YenPathFinder


def main() -> int | None:
    """Parse arguments, build a schedule, and run the selected interface.

    Returns:
        Simulation turn count in terminal mode, otherwise None.
    """
    parser = Parser()
    try:
        args = parser.argument_parse()
    except SystemExit:
        return None
    file_path = args.map_file
    parse_res = parser.parse_file(file_path)
    if parse_res is None:
        return None
    handler = GraphHandler(parse_res)
    handler.construct()

    pathfinder = YenPathFinder(handler)
    scheduler = Scheduler(pathfinder)
    drone_paths = scheduler.scheduling(handler.drone_count)
    if not drone_paths:
        print_color("Aborting: No available path to goal")
        return None
    simulator = Simulator(handler, drone_paths)
    if args.vis:
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
        from pygame_visualizer import PygameVisualizer
        PygameVisualizer(handler, simulator).run()
        return None

    turns = simulator.run_drone()
    return turns


if __name__ == "__main__":
    main()
