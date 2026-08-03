"""Provide ANSI color helpers for terminal output."""

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


def print_color(
    txt: object,
    color: str = "red",
) -> None:
    """Print an object using ANSI foreground and background colors.

    Args:
        txt: Object to print.
        color: Foreground color dictionary key.
    """
    print(
        text_color_dic[color],
        txt,
        text_color_dic["end"],
    )
