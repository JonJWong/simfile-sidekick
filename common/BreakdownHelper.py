# -*- coding: utf-8 -*-

"""Contains helper methods used in the generation of breakdown notation for Simfile Sidekick.

Various functions are defined here to assist with the generation and modification of the density breakdown notation.

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst for the Dickson City Heroes and Stamina Nation.
"""


def remove_density_breakdown_chars(breakdown: str) -> str:
    """ Removes the breakdown density notation icons.

    Removes only the density notation icons (e.g. the equal sign, backslash, and tilde)

    @param breakdown: The breakdown array to remove symbols from.
    @return: The breakdown array without symbols.
    """
    breakdown = breakdown.replace("=", "").replace("\\", "").replace("~", "")
    return breakdown


def remove_all_breakdown_chars(breakdown: str) -> str:
    """ Removes the breakdown separators and density notation icons.

    Removes all break and density notation icons in the breakdown.

    @param breakdown: The breakdown array to remove symbols from.
    @return: The breakdown array without symbols.
    """
    breakdown = remove_density_breakdown_chars(breakdown)
    breakdown = breakdown.replace("(", "").replace(")", "").replace("*", "")
    return breakdown


def get_separator(length: int) -> str:
    """ Returns the separator used in the simplified breakdowns.

    Returns the symbol that represents a given length for the simplified breakdowns.

    @param length: The length of the break.
    @return: The corresponding symbol for the provided length break.
    """
    if length <= 1:
        return " "
    elif 1 < length <= 4:
        return "-"
    elif 4 < length <= 32:
        return "/"
    else:
        return "|"
