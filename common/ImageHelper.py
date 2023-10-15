# -*- coding: utf-8 -*-

# MOST OF THIS FILE IS NOW DEPRECATED AS IT IS EXTRANOUS TO MY USE CASES - JWong

"""Contains helper methods used in image generation for Simfile Sidekick.

Various functions are defined here to assist with image generation and modifications for Simfile Sidekick. Some examples
include merging images, saving images, and generating the density graph.

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
CHAR_LEFT, CHAR_TOP, CHAR_RIGHT, CHAR_BOTTOM = FONT.getbbox("A")
CHAR_WIDTH = CHAR_RIGHT - CHAR_LEFT
CHAR_HEIGHT = CHAR_BOTTOM - CHAR_TOP
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
