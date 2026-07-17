from pyparsing import Group, OneOrMore, Optional, Regex, Suppress, Word, alphas, nums, Keyword


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
