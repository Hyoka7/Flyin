from parse import parse_file

# from utils import back_color_dic, print_color, text_color_dic

parse_res = parse_file("test.txt")
for k in parse_res:
    print(k)
# for back_color, _ in back_color_dic.items():
#     if back_color == "end":
#         continue
#     for text_color, _ in text_color_dic.items():
#         if text_color == "end":
#             continue
#         print_color(parse_res, back_color, text_color)
