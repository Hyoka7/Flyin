from parse import Parser

# from utils import back_color_dic, print_color, text_color_dic

parser = Parser()
parse_res = parser.parse_file("test.txt")
if parse_res is None:
    print("Aborting")
    exit(1)
for k in parse_res:
    print(k)
# for back_color, _ in back_color_dic.items():
#     if back_color == "end":
#         continue
#     for text_color, _ in text_color_dic.items():
#         if text_color == "end":
#             continue
#         print_color(parse_res, back_color, text_color)
