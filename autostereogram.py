import argparse
import os
from PIL import Image
from random import randint
import sys


def gen_random_dot_strip(width, height):
    """
    Given a target width and height in pixels, return an RGB Image of those
    dimensions consisting of random dots.

    This strip will be repeated as the background for the autostereogram.
    """
    strip = Image.new("RGB", (width, height))
    pix = strip.load()
    for x in range(width):
        for y in range(height):
            r = randint(0, 256)
            g = randint(0, 256)
            b = randint(0, 256)
            pix[x,y] = (r, g, b)

    return strip


def gen_strip_from_tile(tile, width, height):
    """
    Given an open tile Image, return an Image of the specified width and height,
    repeating tile as necessary to fill the image.

    This strip will be repeated as the background for the autostereogram.
    """
    tile_pixels = tile.load()
    tile_width, tile_height = tile.size

    strip = Image.new("RGB", (width, height))
    pix = strip.load()
    for x in range(width):
        for y in range(height):
            x_offset = x % tile_width
            y_offset = y % tile_height
            pix[x,y] = tile_pixels[x_offset,y_offset]

    return strip


def gen_autostereogram(depth_map, levels=48, tile=None):
    """
    Given a depth map, return an autostereogram Image computed from that depth
    map.
    """

    depth_map_width, height = depth_map.size
    # The minimum strip width must be greater than the maximum depth map offset,
    # which is `levels`, or offsets may overlap.
    num_strips = int(depth_map_width * .75 / levels)
    strip_width = depth_map_width // num_strips

    # The depth map images is padded to the left and right by 1 strip width.
    image = Image.new("RGB", (depth_map_width + strip_width * 2, height))

    if tile:
        background_strip = gen_strip_from_tile(tile, strip_width, height)
    else:
        background_strip = gen_random_dot_strip(strip_width, height)

    strip_pixels = background_strip.load()

    depth_map = depth_map.convert('I')
    depth_pixels = depth_map.load()
    image_pixels = image.load()

    for y in range(height):
        # Copy in one strip worth of background image, as left-padding for the
        # depth map.
        for x in range(strip_width):
            image_pixels[x, y] = strip_pixels[x, y]

        # Copy in the pixels for the depth map, offset horizontally by their depth.
        for x in range(depth_map_width):
            depth_offset = round(depth_pixels[x, y] * levels / 255.0)
            offset = x + strip_width
            image_pixels[offset, y] = image_pixels[x + depth_offset, y]

        # Fill in one strip to the right of the depth map as right-padding.
        for x in range(strip_width):
            offset = depth_map_width + strip_width + x
            image_pixels[offset, y] = image_pixels[offset - strip_width, y]

    return image


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create an autostereogram from a provided depth map.")
    parser.add_argument('depth_map', metavar='DEPTHMAP', type=str,
                        help='The depth map from which to compute the autostereogram')
    parser.add_argument('outfile', metavar='OUTFILE', type=str, nargs='?',
                        help='The depth map from which to compute the autostereogram')
    parser.add_argument('--tile', metavar='TILE', dest='tile', action='store',
                        default=None,
                        help='An image to tile as the background for the autostereogram')

    args = parser.parse_args()

    if args.tile:
        autostereogram = gen_autostereogram(Image.open(args.depth_map),
                                            tile=Image.open(args.tile))
    else:
        autostereogram = gen_autostereogram(Image.open(args.depth_map))

    if args.outfile:
        autostereogram.save(args.outfile)
    else:
        # If no outfile is given, save the autostereogram as
        # <DEPTHMAP>_stereo.<DEPTHMAP EXTENSION> in the current directory.
        filename, extension = os.path.split(args.depth_map)[1].rsplit(".", 1)
        autostereogram.save(filename + "_stereo." + extension)
