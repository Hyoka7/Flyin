text_color_dic = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "end": "\033[0m",
}

back_color_dic = {
    "black": "\033[40m",
    "red": "\033[41m",
    "green": "\033[42m",
    "yellow": "\033[43m",
    "blue": "\033[44m",
    "magenta": "\033[45m",
    "cyan": "\033[46m",
    "white": "\033[47m",
    "end": "\033[0m",
}


def print_color(txt, color1="yellow", color2="black"):
    print(back_color_dic[color2], text_color_dic[color1], txt, text_color_dic["end"])
