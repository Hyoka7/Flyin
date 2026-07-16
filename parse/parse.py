from pyparsing import Group, OneOrMore, Optional, Regex, Suppress, Word, alphas, nums

key = Word(alphas + "_" + alphas)
string = Word(alphas)
zone_name = Regex("[^\s-]+")
number = Word(nums)
separator = Suppress(":")
key_value = key + Suppress("=") + (string | number)
dct = Group(key_value)
options = Optional(Suppress("[") + OneOrMore(dct) + Suppress("]"))
parse_pattern = key + separator + zone_name + number + number + options


res = parse_pattern.parseString("hub: corridorA 4 3 [zone=3]", parseAll=True)
print(res)
