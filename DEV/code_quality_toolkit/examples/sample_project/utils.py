"""Utility functions with intentionally long lines for demonstration."""


def format_message(name: str) -> str:
    greeting = "Olá, " + name
    return greeting + "!" * 3

# Testing stylecheck plugin making the plugin detect comment lines with extension greater than #<lines>

def complex_branching(value: int) -> int:
    if value < 0:
        return -1
    elif value == 0:
        return 0
    elif value < 10 and value % 2 == 0:
        return value // 2
    else:
        return value * 2

def number_to_name():
    number = input()
    if not number.isdigit():
        print("Enter a valid number")
        return

    number = int(number)
    if number >= 10:
        print("Number is too big")
        return

    if number == 1:
        print("one")
    elif number == 2:
        print("two")
    elif number == 3:
        print("three")
    elif number == 4:
        print("four")
    elif number == 5:
        print("five")
    elif number == 6:
        print("six")
    elif number == 7:
        print("seven")
    elif number == 8:
        print("eight")
    elif number == 9:
        print("nine")

def utils_args(arg1, arg2, arg3, arg4, arg5, arg6, arg7):
    return arg1 + arg2 + arg3 + arg4 + arg5 + arg6 + arg7
