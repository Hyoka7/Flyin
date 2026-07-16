from pydantic import BaseModel, Field
from pyparsing import Group, OneOrMore, Optional, Regex, Suppress, Word, alphas, nums

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
    Word("connection:") + zone_name + Suppress("-") + zone_name + options
)


class Drone(BaseModel):
    nb_drones: int = Field(..., gt=0)


class Zone(BaseModel):
    key: str
    name: str
    x: int
    y: int
    metadata: dict[str, str]


class Connection(BaseModel):
    key: str
    _from: str
    to: str
    metadata: dict[str, str]


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
        return parse_dict
    except Exception:
        pass
    try:
        parse_res = connection_parse_pattern.parseString(text, parse_all=True).as_list()
        parse_dict = {
            "key": parse_res[0],
            "from": parse_res[1],
            "to": parse_res[2],
            "matadata": dict(parse_res[3:]),
        }
        if "max_drones" not in parse_dict["metadata"]:
            parse_dict["metadata"]["max_drones"] = 1
        return parse_dict
    except Exception:
        print("parse error")
        return False


def validate_parse_result(data: dict):
    if "nb_drones" in data:
        if Drone.model_validate(data):
            return Drone(data)
        else:
            return False

    if "from" in data and "to" in data:
        if Connection.model_validate(data):
            return Connection(data)
        else:
            return False

    if Zone.model_validate(data):
        return Zone(data)
    else:
        return False

def parse_file(path: str):
    results = []
    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            result = parser(line)
            if result is False:
                return None
            res_validate = validate_parse_result(result)
            if not res_validate:
                print("Bad")
                return None
            results.append(res_validate)
    return results