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


def gen_autostereogram(depth_map, tile=None):
    """
    Given a depth map, return an autostereogram Image computed from that depth
    map.
    """
    depth_map_width, height = depth_map.size

    # If we have a tile, we want the strip width to be a multiple of the tile
    # width so it repeats cleanly.
    if tile:
        tile_width = tile.size[0]
        strip_width = tile_width
    else:
        strip_width = depth_map_width / 8

    num_strips = depth_map_width / strip_width
    image = Image.new("RGB", (depth_map_width, height))

    if tile:
        background_strip = gen_strip_from_tile(tile, strip_width, height)
    else:
        background_strip = gen_random_dot_strip(strip_width, height)

    strip_pixels = background_strip.load()

    depth_map = depth_map.convert('I')
    depth_pixels = depth_map.load()
    image_pixels = image.load()

    for x in xrange(depth_map_width):
        for y in xrange(height):
            # Need one full strip's worth to borrow from.
            if x < strip_width:
                image_pixels[x, y] = strip_pixels[x, y]
            else:
                depth_offset = depth_pixels[x, y] / num_strips
                image_pixels[x, y] = image_pixels[x - strip_width + depth_offset, y]

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
