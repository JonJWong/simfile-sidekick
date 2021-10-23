# -*- coding: utf-8 -*-

"""Contains helper methods used in image generation for Simfile Sidekick.

Various functions are defined here to assist with image generation and modifications for Simfile Sidekick. Some examples
include merging images, saving images, and generating the density graph or color breakdown.

This is free and unencumbered software released into the public domain. For more information, please refer to the
LICENSE file or visit <https://unlicense.org>.

Created with love by Artimst for the Dickson City Heroes and Stamina Nation.
"""

from common import BreakdownHelper as bh
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from typing import List
import logging
import math
import plotly.graph_objects as go

IMAGE_WIDTH = 1000  # Width of the density graph and breakdown image in pixels
GRAPH_HEIGHT = 400  # Height of the density graph in pixels

FONT_SIZE = 32
FONT = ImageFont.truetype("./resources/font/DejaVuSansMono.ttf", FONT_SIZE)
FONT_BOLD = ImageFont.truetype("./resources/font/DejaVuSansMono-Bold.ttf", FONT_SIZE)

# Since the font is monospaced, this gives us the width and height of a single character
CHAR_WIDTH, CHAR_HEIGHT = FONT.getsize("A")
FONT_LINE_SPACING = math.floor(CHAR_HEIGHT * 1.2)  # Add a small space between lines for readability
MAX_CHARS_PER_LINE = math.floor(IMAGE_WIDTH / CHAR_WIDTH)

# Colors defined in RGB
WHITE  = (255, 255, 255)
GRAY   = (150, 150, 150)  # Break segments
GREEN  = (  0, 128,   0)  # 16th notes
CYAN   = (  0, 206, 209)  # 20th notes
PURPLE = (153,  50, 204)  # 24th notes
YELLOW = (255, 255,   0)  # 32nd notes

BG     = ( 52,  54,  61)  # The dark gray background of Discord
BG_RGB = "rgb(52,54,61)"  # String representation of the above


def merge_images_vertically(image1: Image, image2: Image) -> Image:
    """ Merges two images vertically.

    Merges two images vertically. image1 will appear on top of image2.

    @param image1: The Image object of the first image.
    @param image2: The Image object of the second image.
    @return: The merged image.
    """
    if not image1 or not image2:
        logging.error("Can't merge '{}' with '{}', one of these images is null.".format(image1, image2));
        return None
    (width1, height1) = image1.size
    (width2, height2) = image2.size

    result_width = max(width1, width2)
    result_height = height1 + height2

    result = Image.new("RGB", (result_width, result_height))
    result.paste(im=image1, box=(0, 0))
    result.paste(im=image2, box=(0, height1))
    return result


def save_image(image: Image, path: str) -> bool:
    """ Save an image

    Saves an image to the specified path.

    @param image: The image to save.
    @param path: The path to save the image to.
    @return: True for successful saves.
    """
    try:
        image.save(path)
        return True
    except AttributeError as e:
        logging.error("The image '{}' doesn't appear to be a valid Image object.".format(image), exc_info=True)
        return False
    except OSError as e:
        logging.error("The file '{}' could not be saved.".format(path), exc_info=True)
        return False


def load_image(path: str) -> Image:
    """ Load an image

    Loads an image from the specified path into an Image object.

    @param path: The path to load the image from.
    @return: The image as an Image object.
    """
    try:
        return Image.open(path)
    except FileNotFoundError as e:
        logging.error("Unable to locate image file '{}'.".format(path), exc_info=True)
        return None
    except UnidentifiedImageError as e:
        logging.error("Unable to load image file '{}'. Is this an image file, or is the image corrupt?".format(path),
                      exc_info=True)
        return None


def create_breakdown_image(breakdown: str, header: str) -> Image:
    """ Creates the color coded breakdown image

    Instead of having a bunch of symbols in a chart's breakdown for non-16th note quantization, this will generate an
    image that has the breakdown numbers color coded instead of surrounded with symbols.

    @param breakdown: The breakdown array to color code.
    @param header: The header displayed above the breakdown.
    @return: The color coded breakdown image.
    """
    # Copy the array without density notation (no =, \, or ~) since we'll now be using color to identify density.
    raw_breakdown = bh.remove_density_breakdown_chars(breakdown)

    # The text we put on the image doesn't word wrap automatically. Each entry to the array will be a row of text that
    # fits within the image. We'll need to intelligently split the lines across whitespace.
    breakdown_arr = []
    while len(raw_breakdown) > 0:
        if len(raw_breakdown) <= MAX_CHARS_PER_LINE:
            breakdown_arr.append(raw_breakdown.strip())
            break
        else:
            for i in range(MAX_CHARS_PER_LINE, 0, -1):
                if raw_breakdown[i] == " ":
                    breakdown_arr.append(raw_breakdown[:i].strip())
                    raw_breakdown = raw_breakdown[i:]
                    break

    img = Image.new("RGB", (IMAGE_WIDTH, FONT_LINE_SPACING * (len(breakdown_arr) + 1)), BG)
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), header, WHITE, font=FONT_BOLD)
    draw.line((0, CHAR_HEIGHT + 1, CHAR_WIDTH * len(header), CHAR_HEIGHT + 1))  # Underlines the header text

    breakdown = breakdown.split(" ")
    x, y, index = 0, FONT_LINE_SPACING, 0

    for i, breakdown_line in enumerate(breakdown_arr):
        for j, breakdown_number in enumerate(breakdown_line.split(" ")):
            if any(c in ["(", ")"] for c in breakdown[index]):
                draw.text((x, y), breakdown_number, GRAY, font=FONT)
            elif "~" in breakdown[index]:
                draw.text((x, y), breakdown_number, CYAN, font=FONT)
            elif "\\" in breakdown[index]:
                draw.text((x, y), breakdown_number, PURPLE, font=FONT)
            elif "=" in breakdown[index]:
                draw.text((x, y), breakdown_number, YELLOW, font=FONT)
            elif breakdown[index] in ["/", "|", "-"] or "@" in breakdown[index]:
                draw.text((x, y), breakdown_number, WHITE, font=FONT)
            else:
                draw.text((x, y), breakdown_number, GREEN, font=FONT)
            index += 1
            x += CHAR_WIDTH * (len(breakdown_number) + 1)  # +1 for space
        # Move to the next line and reset x
        x = 0
        y += FONT_LINE_SPACING

    draw = ImageDraw.Draw(img)
    return img


def create_and_save_density_graph(x: List[int], y: List[float], path: str) -> bool:
    """ Creates and saves the density graph image.

    Creates the density graph using plotly, then saves it to the path specified.

    @param x: An array containing the measure numbers.
    @param y: An array containing the density of each measure.
    @param path: The path to save the graph image to.
    @return: True for successful saves.
    """

    # noinspection PyTypeChecker
    # line_color correctly takes a string type; not sure why PyCharm is expecting a dict
    fig = go.Figure(go.Scatter(
        x=x, y=y, fill="tozeroy", fillcolor="yellow", line_color="orange", line=dict(width=0.5)
    ))
    fig.update_layout(
        plot_bgcolor=BG_RGB, paper_bgcolor=BG_RGB, margin=dict(l=10, r=10, b=10, t=10, pad=10),
        autosize=False, width=IMAGE_WIDTH, height=GRAPH_HEIGHT
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)

    # noinspection PyBroadException
    # Plotly doesn't document possible exceptions, so we capture with a generic one.
    try:
        fig.write_image(path)
        return True
    except Exception as e:
        logging.error("The density graph could not be saved at '{}'.".format(path), exc_info=True)
        return False
