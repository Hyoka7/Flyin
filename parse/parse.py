from pydantic import BaseModel, Field, model_validator, ValidationError
from pyparsing import Group, OneOrMore, Optional, Regex, Suppress, Word, alphas, nums, Keyword
from enum import Enum


key = Word(alphas + "_" + alphas)
string = Word(alphas)
zone_name = Regex(r"[^\s-]+")
number = Word(nums)
separator = Suppress(":")
key_value = key + Suppress("=") + (string | number)
dct = Group(key_value)
options = Optional(Suppress("[") + OneOrMore(dct) + Suppress("]"))
zone_parse_pattern = key + separator + zone_name + number + number + options
connection_parse_pattern = (
    Keyword("connection:") + zone_name + Suppress("-") + zone_name + options
)

class ZoneTypes(Enum):
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"

class Drone(BaseModel):
    nb_drones: int = Field(..., gt=0)


class Zone(BaseModel):
    key: str
    name: str
    x: int
    y: int
    metadata: dict[str, str | int]

    @model_validator(mode="after")
    def zone_type_validate(self):
        valid_zone = ["normal","blocked","restricted","priority"]
        if "zone" in self.metadata:
            if self.metadata["zone"] not in valid_zone:
                raise ValueError("zone type is unknown")
        return self
    
    @model_validator(mode="after")
    def zone_name_validate(self):
        valid_name = ["start_hub", "end_hub", "hub"]
        if self.key not in valid_name:
            raise ValueError("key is unknown")
        return self
    
    @model_validator(mode="after")
    def metadata_validate(self):
        valid_datas = ["zone","color","max_drones"]
        for key, _ in self.metadata.items():
            if key not in valid_datas:
                raise ValueError("metadata is unknown")
        return self
            


class Connection(BaseModel):
    key: str
    from_: str
    to: str
    metadata: dict[str, str | int]

    @model_validator(mode="after")
    def metadata_validate(self):
        valid_datas = ["max_link_capacity"]
        for key, _ in self.metadata.items():
            if key not in valid_datas:
                raise ValueError("metadata is unknown")
        return self





def parser(text: str):
    if text.startswith("#") or text == "":
        pass
    if text.startswith("nb_drones:"):
        try:
            key, value = text.split(":")
            if key != "nb_drones":
                raise Exception
            else:
                return {key: int(value)}
        except Exception:
            print("First line must be nb_drones: value")
    try:
        parse_res = zone_parse_pattern.parseString(text, parse_all=True).as_list()
        parse_dict = {
            "key": parse_res[0],
            "name": parse_res[1],
            "x": parse_res[2],
            "y": parse_res[3],
            "metadata": dict(parse_res[4:]),
        }
        if "max_drones" not in parse_dict["metadata"]:
            parse_dict["metadata"]["max_drones"] = 1
        else:
            parse_dict["metadata"]["max_drones"] = int(parse_dict["metadata"]["max_drones"])
        if "color" not in parse_dict["metadata"]:
            parse_dict["metadata"]["color"] = None
        return parse_dict
    except Exception:
        pass
    try:
        parse_res = connection_parse_pattern.parseString(text, parse_all=True).as_list()
        parse_dict = {
            "key": parse_res[0],
            "from_": parse_res[1],
            "to": parse_res[2],
            "metadata": dict(parse_res[3:]),
        }
        return parse_dict
    except Exception as err:
        print(f"parse err {err}")
        return False


def validate_parse_result(line_num:int,data: dict):
        try:
            if "nb_drones" in data:
                 return Drone.model_validate(data)
            if "from_" in data and "to" in data:
                return Connection.model_validate(data)
            return Zone.model_validate(data)
        except ValidationError as err:
            print(f"Validation error on line {line_num}, {err.errors()[0]['msg']}")
            return False


def parse_file(path: str):
    results = []
    with open(path, "r", encoding="utf-8") as file:
        for line_num, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            result = parser(line)
            if result is False:
                return None
            res_validate = validate_parse_result(line_num,result)
            if not res_validate:
                return None
            results.append(res_validate)
    return results