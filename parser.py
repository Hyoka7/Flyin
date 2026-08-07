import argparse
from typing import Any, Literal

from pydantic import ValidationError
from pyparsing import ParseException

from colors import print_color
from models import Connection, Drone, Zone, ZoneTypes
from patterns import connection_parse_pattern, zone_parse_pattern


class Parser:
    """Parse CLI arguments and validate Fly-in map declarations."""

    def argument_parse(self) -> argparse.Namespace:
        """Parse the map path and optional visualization flag.

        Returns:
            An argparse namespace containing `map_file` and `vis`.
        """
        parser = argparse.ArgumentParser(description="Fly in")
        parser.add_argument(
            "map_file",
            help="Path to map file",
        )
        parser.add_argument(
            "-v",
            "--vis",
            action="store_true",
            help="Flag for visualization, default is False",
        )
        return parser.parse_args()

    def parse_line(
        self,
        text: str,
        line_num: int,
        is_first: bool,
    ) -> dict[str, Any] | Literal[False] | None:
        """Parse one meaningful map line into unvalidated field data.

        Args:
            text: Stripped input line.
            line_num: One-based source line number for error reporting.
            is_first: Whether this is the first meaningful declaration.

        Returns:
            Parsed fields, False after a reported error, or None for an
            ignored blank or comment line.
        """
        if text.startswith("#") or text == "":
            return None
        if is_first:
            try:
                key, value = text.split(":")
                if key != "nb_drones":
                    raise ValueError()
                else:
                    if int(value) < 0:
                        raise ValueError()
                    return {key: int(value)}
            except ValueError:
                print_color(
                    f"Parse error on line {line_num}: "
                    "First line must be nb_drones: positive value"
                )
                return False
        if text.startswith("connection:"):
            try:
                parse_res = connection_parse_pattern.parse_string(
                    text, parse_all=True
                ).as_list()
                metadata = dict(parse_res[3:])
                parse_dict = {
                    "key": parse_res[0],
                    "from_": parse_res[1],
                    "to": parse_res[2],
                    "metadata": metadata,
                }
                return parse_dict
            except ParseException as err:
                print_color(
                    f"parse error on line {line_num} "
                    f"col {err.col}: {err.msg}"
                )
                return False

        try:
            parse_res = zone_parse_pattern.parse_string(
                text, parse_all=True
            ).as_list()
            metadata = dict(parse_res[4:])
            if parse_res[0] in {"start_hub", "end_hub"}:
                metadata.pop("max_drones", None)
            parse_dict = {
                "key": parse_res[0],
                "name": parse_res[1],
                "x": parse_res[2],
                "y": parse_res[3],
                "metadata": metadata,
            }
            return parse_dict
        except ParseException as err:
            print_color(
                f"parse error on line {line_num} "
                f"col {err.col}: {err.msg}"
            )
            return False

    def validate_parse_result(
        self,
        line_num: int,
        data: dict[str, Any],
    ) -> Drone | Zone | Connection | Literal[False]:
        """Convert parsed fields into the appropriate validated model.

        Args:
            line_num: One-based source line number for error reporting.
            data: Raw fields produced by `parse_line`.

        Returns:
            A validated model, or False after a validation error.
        """
        try:
            if "nb_drones" in data:
                return Drone.model_validate(data)
            if "from_" in data and "to" in data:
                return Connection.model_validate(data)
            return Zone.model_validate(data)
        except ValidationError as err:
            message = err.errors()[0]["msg"]
            print_color(
                f"Error: Validation error on line {line_num}, {message}"
            )
            return False

    def validate_all_result(
        self,
        parse_res: list[Drone | Zone | Connection],
    ) -> list[Drone | Zone | Connection] | None:
        """Validate relationships and uniqueness across all declarations.

        Args:
            parse_res: Models in their original declaration order.

        Returns:
            The unchanged model list when valid, otherwise None.
        """
        zone_names: set[str] = set()
        connections: set[tuple[str, str]] = set()
        coordinates: set[tuple[int, int]] = set()
        drone_count = 0
        start_hub_count = 0
        end_hub_count = 0

        for index, result in enumerate(parse_res):
            if isinstance(result, Drone):
                drone_count += 1
                if index != 0:
                    print_color(
                        "Error: nb_drones must be the first definition"
                    )
                    return None
                continue

            if isinstance(result, Zone):
                if result.name in zone_names:
                    print_color(f"Error: Duplicate zone name: {result.name}")
                    return None
                if (result.x, result.y) in coordinates:
                    print_color(
                        "Error: Duplicate coordinate: "
                        f"({result.x},{result.y})"
                    )
                    return None
                zone_names.add(result.name)
                coordinates.add((result.x, result.y))
                if result.key == "start_hub":
                    start_hub_count += 1
                    if result.metadata.zone == ZoneTypes.Blocked:
                        print_color("Error: start hub is blocked")
                        return None
                elif result.key == "end_hub":
                    end_hub_count += 1
                    if result.metadata.zone == ZoneTypes.Blocked:
                        print_color("Error: end hub is blocked")
                        return None
                continue

            if result.from_ not in zone_names:
                print_color(
                    "Error: Connection references an undefined zone: "
                    f"{result.from_}"
                )
                return None
            if result.to not in zone_names:
                print_color(
                    "Error: Connection references an undefined zone: "
                    f"{result.to}"
                )
                return None

            if result.from_ == result.to:
                print_color(
                    f"Error: Loop detected: {result.from_}-{result.to}"
                )
                return None

            connection = (
                min(result.from_, result.to),
                max(result.from_, result.to),
            )
            if connection in connections:
                print_color(
                    f"Duplicate connection: {result.from_}-{result.to}"
                )
                return None
            connections.add(connection)

        if drone_count != 1:
            print_color("Error: nb_drones must be defined exactly once")
            return None
        if start_hub_count != 1:
            print_color("Error: start_hub must be defined exactly once")
            return None
        if end_hub_count != 1:
            print_color("Error: end_hub must be defined exactly once")
            return None

        return parse_res

    def parse_file(
        self,
        path: str,
    ) -> list[Drone | Zone | Connection] | None:
        """Read, parse, and validate a complete map file.

        Args:
            path: Path to the map configuration file.

        Returns:
            Validated declarations, or None after a reported error.
        """
        results: list[Drone | Zone | Connection] = []
        is_first = True
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("#"):
                        continue
                    result = self.parse_line(line, line_num, is_first)
                    if result is False or result is None:
                        return None
                    res_validate = self.validate_parse_result(line_num, result)
                    if res_validate is False:
                        return None
                    results.append(res_validate)
                    is_first = False
            if self.validate_all_result(results) is None:
                return None
            return results
        except OSError as err:
            print_color(f"Error while opening file: {err}")
            return None
