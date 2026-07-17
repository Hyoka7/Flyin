from pydantic import ValidationError
from models import Drone, Connection, Zone
from .patterns import connection_parse_pattern, zone_parse_pattern


class Parser():
    def parser(self,text: str, line_num: int, is_first:bool):
        if text.startswith("#") or text == "":
            pass
        if is_first:
            if not text.startswith("nb_drones:"):
                raise ValueError()
            try:
                key, value = text.split(":")
                if key != "nb_drones":
                    raise ValueError()
                else:
                    return {key: int(value)}
            except Exception:
                print(f"Parse error on line {line_num}: First line must be nb_drones: value")
                return False
        else:
            try:
                parse_res = zone_parse_pattern.parseString(text, parse_all=True).as_list()
                metadata = dict(parse_res[4:])
                if parse_res[0] in {"start_hub", "end_hub"}:
                    metadata.pop("max_drones", None)
                parse_dict = {
                    "key": parse_res[0],
                    "name": parse_res[1],
                    "x": parse_res[2],
                    "y": parse_res[3],
                    "metadata": metadata
                }
                return parse_dict
            except Exception:
                pass
            try:
                parse_res = connection_parse_pattern.parseString(text, parse_all=True).as_list()
                metadata = dict(parse_res[3:])
                parse_dict = {
                    "key": parse_res[0],
                    "from_": parse_res[1],
                    "to": parse_res[2],
                    "metadata": metadata
                }
                return parse_dict
            except Exception:
                print(f"parse error on line {line_num}: Bad Config")
                return False


    def validate_parse_result(self, line_num:int, data: dict):
            try:
                if "nb_drones" in data:
                     return Drone.model_validate(data)
                if "from_" in data and "to" in data:
                    return Connection.model_validate(data)
                return Zone.model_validate(data)
            except ValidationError as err:
                print(f"Validation error on line {line_num}, {err.errors()[0]['msg']}")
                return False
            
    def validate_all_result(
        self,
        parse_res: list[Drone | Zone | Connection],
    ) -> list[Drone | Zone | Connection] | None:
        zone_names: set[str] = set()
        connections: set[tuple[str, str]] = set()
        drone_count = 0
        start_hub_count = 0
        end_hub_count = 0

        for index, result in enumerate(parse_res):
            if isinstance(result, Drone):
                drone_count += 1
                if index != 0:
                    print("nb_drones must be the first definition")
                    return None
                continue

            if isinstance(result, Zone):
                if result.name in zone_names:
                    print(f"Duplicate zone name: {result.name}")
                    return None

                zone_names.add(result.name)
                if result.key == "start_hub":
                    start_hub_count += 1
                elif result.key == "end_hub":
                    end_hub_count += 1
                continue

            if result.from_ not in zone_names:
                print(
                    "Connection references an undefined zone: "
                    f"{result.from_}"
                )
                return None
            if result.to not in zone_names:
                print(
                    "Connection references an undefined zone: "
                    f"{result.to}"
                )
                return None
            
            if result.from_ == result.to:
                print(
                    f"Loop detected: {result.from_}-{result.to}"
                )
                return None

            connection = tuple(sorted((result.from_, result.to)))
            if connection in connections:
                print(
                    "Duplicate connection: "
                    f"{result.from_}-{result.to}"
                )
                return None
            connections.add(connection)

        if drone_count != 1:
            print("nb_drones must be defined exactly once")
            return None
        if start_hub_count != 1:
            print("start_hub must be defined exactly once")
            return None
        if end_hub_count != 1:
            print("end_hub must be defined exactly once")
            return None

        return parse_res


    def parse_file(self,path: str):
        results = []
        is_first = True
        with open(path, "r", encoding="utf-8") as f:
            for line_num,line in enumerate(f,start=1):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    continue
                result = self.parser(line,line_num, is_first)
                if result is False:
                    return None
                res_validate = self.validate_parse_result(line_num,result)
                if not res_validate:
                    return None
                results.append(res_validate)
                line_num += 1
                is_first = False
        if self.validate_all_result(results) is None:
            return None
        return results
