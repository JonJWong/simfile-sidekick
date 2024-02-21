import re


def findall_with_regex_dotall(data, regex):
    """Returns array of results from the given regex. Search will span over newline characters."""
    try:
        return re.findall(regex, data, re.DOTALL)
    except AttributeError:
        return -1


def findall_with_regex(data, regex):
    """Returns array of results from the given regex."""
    try:
        return re.findall(regex, data)
    except AttributeError:
        return -1


def find_with_regex_dotall(data, regex):
    """Returns the first match from a given regex. Search will span over newline characters."""
    try:
        return re.search(regex, data, re.DOTALL).group(1)
    except AttributeError:
        return -1


def find_with_regex(data, regex):
    """Returns the first match from a given regex."""
    try:
        return re.search(regex, data).group(1)
    except AttributeError:
        return "N/A"
