# Helpful functions that allow the text to appear prettier in the console when using the verbose option.


# Takes two numbers, e.g. a is 5 and b is 500
# This function will add two spaces before a
# output would be "  5" and "500"
def normalize_num(a, b):
    len_a = len(str(a))
    len_b = len(str(b))

    max_len = max(len_a, len_b)

    pad_a = max_len - len_a
    pad_b = max_len - len_b

    str_a = str(a)
    for i in range(pad_a):
        str_a = " " + str_a

    str_b = str(b)
    for i in range(pad_b):
        str_b = " " + str_b

    return str_a, str_b


def add_padding(string, num):
    while len(string) < num:
        string = " " + string
    return string


def get_percent(a, b):
    percent = round((a / b) * 100, 1)  # 1 decimal place
    return add_padding(str(percent) + "%", 6)  # 6 chars in "100.0%"


def normalize_string(string, length):
    if len(string) > length:
        string = string[0:length - 3]
        string = string + "..."

    while len(string) < length:
        string += " "  # need to add spaces since carriage return won't overlay last input

    return string
