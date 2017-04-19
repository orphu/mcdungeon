import code
import cPickle
import json
import math
import os
import random
import re
import sys
import time
import uuid
import yaml

import numpy

from materials import heightmap_solids
from pymclevel import mclevel, nbt

cache_version = '8'
dv_version = 922


def floor(n):
    return int(n)


def ceil(n):
    if int(n) == n:
        return int(n)
    return int(n) + 1


def clamp(n, a, b):
    rmin = min(a, b)
    rmax = max(a, b)
    if(n < rmin):
        return rmin
    if(n > rmax):
        return rmax
    return n


class Vec(object):

    def __init__(self, x, y, z):
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)

    @classmethod
    def from_string(cls, string):
        string = string.replace('(', '')
        string = string.replace(')', '')
        try:
            (x, y, z) = [int(x) for x in string.split(",")]
        except ValueError:
            x = 0
            y = 0
            z = 0
        return cls(x, y, z)

    def __add__(self, b):
        if isinstance(b, Vec):
            return Vec(self.x + b.x, self.y + b.y, self.z + b.z)
        else:
            return Vec(self.x + b, self.y + b, self.z + b)

    def __sub__(self, b):
        if isinstance(b, Vec):
            return Vec(self.x - b.x, self.y - b.y, self.z - b.z)
        else:
            return Vec(self.x - b, self.y - b, self.z - b)

    def __mul__(self, b):
        return Vec(self.x * b, self.y * b, self.z * b)

    def __str__(self):
        return "(%d,%d,%d)" % (self.x, self.y, self.z)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, b):
        if not isinstance(b, Vec):
            return False
        return self.x == b.x and self.y == b.y and self.z == b.z

    def __ne__(self, b):
        if not isinstance(b, Vec):
            return True
        return self.x != b.x or self.y != b.y or self.z != b.z

    def __hash__(self):
        return self.x + (self.y << 4) + (self.z << 8)

    def e(self, x):
        return Vec(self.x + x, self.y, self.z)

    def w(self, x):
        return Vec(self.x - x, self.y, self.z)

    def up(self, y):
        return Vec(self.x, self.y - y, self.z)

    def down(self, y):
        return Vec(self.x, self.y + y, self.z)

    def n(self, z):
        return Vec(self.x, self.y, self.z - z)

    def s(self, z):
        return Vec(self.x, self.y, self.z + z)

    def mag2d(self):
        return math.sqrt(self.x * self.x + self.z * self.z)

    def d(self, d):
        if (d == 0):
            return Vec(0, 0, -1)
        if (d == 1):
            return Vec(1, 0, 0)
        if (d == 2):
            return Vec(0, 0, 1)
        if (d == 3):
            return Vec(-1, 0, 0)

    def rotate(self, r):
        # rotate around xz plane
        while r < 0:
            r += 4
        if r == 0:
            return self
        elif r == 1:
            return Vec(-self.z, self.y, self.x)
        elif r == 2:
            return Vec(-self.x, self.y, -self.z)
        elif r == 3:
            return Vec(self.z, self.y, -self.x)

    def ccw(self):
        return self.rotate(-1)

    def cw(self):
        return self.rotate(1)

    def trans(self, x, y, z):
        return Vec(self.x + x, self.y + y, self.z + z)


# As of 1.9 pre 4:
#   North = -Z
#   South = +Z
#   East = +X
#   West = -X
NORTH = Vec(0, 0, -1)
SOUTH = Vec(0, 0, 1)
EAST = Vec(1, 0, 0)
WEST = Vec(-1, 0, 0)
UP = Vec(0, 1, 0)
DOWN = Vec(0, -1, 0)


class Vec2f(object):

    def __init__(self, x, z):
        self.x = float(x)
        self.z = float(z)

    @staticmethod
    def fromVec(vec):
        return Vec2f(vec.x, vec.z)

    def rotate(self, r):
        while r < 0:
            r += 4
        if r == 0:
            return self
        elif r == 1:
            return Vec2f(-self.z, self.x)
        elif r == 2:
            return Vec2f(-self.x, -self.z)
        elif r == 3:
            return Vec2f(self.z, -self.x)

    def det(self, b):
        return self.x * b.z - self.z * b.x

    def mag(self):
        return math.sqrt(self.x * self.x + self.z * self.z)

    def unit(self):
        mag = math.sqrt(self.x * self.x + self.z * self.z)
        return Vec2f(self.x / mag, self.z / mag)

    def __str__(self):
        return "(%f,%f)" % (self.x, self.z)

    def __add__(self, b):
        if isinstance(b, Vec2f):
            return Vec2f(self.x + b.x, self.z + b.z)
        else:
            return Vec2f(self.x + b, self.z + b)

    def __sub__(self, b):
        if isinstance(b, Vec2f):
            return Vec2f(self.x - b.x, self.z - b.z)
        else:
            return Vec2f(self.x - b, self.z - b)

    def __mul__(self, b):
        return Vec2f(self.x * b, self.z * b)


class Box(object):

    def __init__(self, loc, w, h, d):
        self.loc = loc
        self.w = w
        self.h = h
        self.d = d

    def x2(self):
        return self.loc.x + self.w

    def y2(self):
        return self.loc.y + self.h

    def z2(self):
        return self.loc.z + self.d

    def containsPoint(self, p):
        x = p.x - self.loc.x
        y = p.y - self.loc.y
        z = p.z - self.loc.z
        return (
            (x >= 0) and
            (x < self.w) and
            (y >= 0) and
            (y < self.h) and
            (z >= 0) and
            (z < self.d)
        )

    def intersects(self, b):
        if ((self.loc.x > b.x2()) or (self.x2() <= b.loc.x)):
            return False
        if ((self.loc.y > b.y2()) or (self.y2() <= b.loc.y)):
            return False
        if ((self.loc.z > b.z2()) or (self.z2() <= b.loc.z)):
            return False
        return True

    def __str__(self):
        return '(%d, %d, %d) w: %d, h: %d, d: %d' % (
            self.loc.x, self.loc.y, self.loc.z,
            self.w, self.h, self.d)

    def area(loc1, loc2):
        return abs((loc1.x - loc2.x) * (loc1.z - loc2.z))


def iterate_plane(loc1, loc2):
    for x in xrange(min(loc1.x, loc2.x), max(loc1.x, loc2.x) + 1):
        for y in xrange(min(loc1.y, loc2.y), max(loc1.y, loc2.y) + 1):
            for z in xrange(min(loc1.z, loc2.z), max(loc1.z, loc2.z) + 1):
                yield Vec(x, y, z)


def iterate_cube(*points):
    for x in xrange(min([p.x for p in points]),
                    max([p.x for p in points]) + 1):
        for y in xrange(min([p.y for p in points]),
                        max([p.y for p in points]) + 1):
            for z in xrange(min([p.z for p in points]),
                            max([p.z for p in points]) + 1):
                yield Vec(x, y, z)


def iterate_hollow_cube(near, far):
    for b in iterate_cube(near, Vec(near.x, far.y, far.z)):
        yield b
    for b in iterate_cube(near, Vec(far.x, near.y, far.z)):
        yield b
    for b in iterate_cube(near, Vec(far.x, far.y, near.z)):
        yield b
    for b in iterate_cube(Vec(near.x, near.y, far.z), far):
        yield b
    for b in iterate_cube(Vec(near.x, far.y, near.z), far):
        yield b
    for b in iterate_cube(Vec(far.x, near.y, near.z), far):
        yield b


def iterate_four_walls(corner1, corner3, height):
    corner2 = Vec(corner3.x, corner1.y, corner1.z)
    corner4 = Vec(corner1.x, corner1.y, corner3.z)
    for b in iterate_cube(corner1, corner2, corner1.up(height)):
        yield b
    for b in iterate_cube(corner2, corner3, corner2.up(height)):
        yield b
    for b in iterate_cube(corner3, corner4, corner3.up(height)):
        yield b
    for b in iterate_cube(corner4, corner1, corner4.up(height)):
        yield b


def iterate_flat_poly(*poly_points):
    min_x = floor(min([p.x for p in poly_points]))
    max_x = ceil(max([p.x for p in poly_points]))
    min_z = floor(min([p.z for p in poly_points]))
    max_z = ceil(max([p.z for p in poly_points]))
    min_y = floor(min([p.y for p in poly_points]))
    num_points = len(poly_points)

    def point_inside(p):
        if isinstance(p, Vec2f):
            p = Vec(p.x, 0, p.z)
        for i in xrange(num_points):
            a = poly_points[i]
            b = poly_points[(i + 1) % num_points]

            if isinstance(a, Vec2f):
                a = Vec(a.x, 0, a.z)
            if isinstance(b, Vec2f):
                b = Vec(b.x, 0, b.z)

            b_to_a = Vec2f.fromVec(b - a)
            p_to_a = Vec2f.fromVec(p - a)

            det = b_to_a.det(p_to_a)
            if det < 0:
                return False
        return True

    for x in xrange(min_x, max_x + 1):
        for z in xrange(min_z, max_z + 1):
            p = Vec(x, min_y, z)
            if (
                point_inside(p) and
                (
                    not point_inside(p.n(1)) or
                    not point_inside(p.s(1)) or
                    not point_inside(p.e(1)) or
                    not point_inside(p.w(1))
                )
            ):
                yield p


def iterate_points_inside_flat_poly(*poly_points):
    min_x = floor(min([p.x for p in poly_points]))
    max_x = ceil(max([p.x for p in poly_points]))
    min_z = floor(min([p.z for p in poly_points]))
    max_z = ceil(max([p.z for p in poly_points]))
    min_y = floor(min([p.y for p in poly_points]))
    num_points = len(poly_points)

    def point_inside(p):
        if isinstance(p, Vec2f):
            p = Vec(p.x, 0, p.z)
        for i in xrange(num_points):
            a = poly_points[i]
            b = poly_points[(i + 1) % num_points]

            if isinstance(a, Vec2f):
                a = Vec(a.x, 0, a.z)
            if isinstance(b, Vec2f):
                b = Vec(b.x, 0, b.z)

            b_to_a = Vec2f.fromVec(b - a)
            p_to_a = Vec2f.fromVec(p - a)

            det = b_to_a.det(p_to_a)
            if det < 0:
                return False
        return True

    for x in xrange(min_x, max_x + 1):
        for z in xrange(min_z, max_z + 1):
            p = Vec(x, min_y, z)
            if point_inside(p):
                yield p


def sum_points_inside_flat_poly(*poly_points):
    return sum(1 for p in iterate_points_inside_flat_poly(*poly_points))


def random_point_inside_flat_poly(*poly_points):
    points = {}
    for p in iterate_points_inside_flat_poly(*poly_points):
        points[p] = True
    return random.choice(points.keys())


def iterate_points_surrounding_box(box):
    near = box.loc.trans(-1, -1, -1)
    far = box.loc.trans(box.w + 1, box.h + 1, box.d + 1)
    return iterate_hollow_cube(near, far)


def iterate_spiral(p1, p2, height):
    p = p1
    box = Box(p1.trans(0, -height, 0), p2.x - p1.x, height, p2.z - p1.z)
    step = Vec(1, -1, 0)
    for y in xrange(int(height)):
        yield p
        if (box.containsPoint(p + step) is False):
            if (step == Vec(1, -1, 0)):
                step = Vec(0, -1, 1)
            elif (step == Vec(0, -1, 1)):
                step = Vec(-1, -1, 0)
            elif (step == Vec(-1, -1, 0)):
                step = Vec(0, -1, -1)
            else:
                step = Vec(1, -1, 0)
        p += step


def weighted_choice(items):
    """items is a list of tuples in the form (item, weight)"""
    weight_total = sum((int(item[1]) for item in items))
    n = random.uniform(0, weight_total)
    for item, weight in items:
        if n < int(weight):
            break
        n = n - int(weight)
    return item


def weighted_shuffle(master_list):
    """items is a list of tuples in the form (item, weight).
    We return a new list with higher probability choices
    listed toward the end. This let's us pop() item off the
    stack."""
    # Work on a copy so we don't destroy the original
    results = []
    items = []
    # remove any prob 0 items... we don't want to get stuck
    for item, weight in master_list:
        if int(weight) >= 1:
            items.append([item, int(weight)])
    # Return the items in a weighted random order
    while (len(items) > 0):
        weight_total = sum((item[1] for item in items))
        n = random.uniform(0, weight_total)
        for item, weight in items:
            if n < weight:
                break
            n = n - weight
        results.insert(0, item)
        items.remove([item, weight])
    return results


def random_line_from_file(filepath, default=''):
    """ Looks for text file at filepath and returns a random
    line from it."""
    if os.path.isfile(os.path.join(sys.path[0], filepath)):
        path = os.path.join(sys.path[0], filepath)
    elif os.path.isfile(filepath):
        path = filepath
    else:
        return default  # File not found

    # Retrieve a random line from a file, reading through the file once
    # Prevents us from having to load the whole file in to memory
    file_handle = open(path)
    lineNum = 0
    output = default
    while True:
        aLine = file_handle.readline()
        if not aLine:
            break
        if aLine[0] == '#' or aLine == '':
            continue
        lineNum = lineNum + 1
        # How likely is it that this is the last line of the file?
        if random.uniform(0, lineNum) < 1:
            output = aLine.rstrip()
    file_handle.close()
    return output


# Generate a number between min and max. Weighted towards higher numbers.
# (Beta distribution.)
def topheavy_random(min, max):
    d = max - min + 1
    return int(math.floor(math.sqrt(random.randrange(d * d))) + min)


def str2Vec(string):
    m = re.search('(-{0,1}\d+)[\s,]*(-{0,1}\d+)[\s,]*(-{0,1}\d+)', string)
    return Vec(m.group(1), m.group(2), m.group(3))


def iterate_tube(e0, e1, height):
    for y in xrange(height + 1):
        for p in iterate_ellipse(e0.up(y), e1.up(y)):
            yield p


def iterate_cylinder(*points):
    xmin = min([p.x for p in points])
    xmax = max([p.x for p in points])
    ymin = min([p.y for p in points])
    ymax = max([p.y for p in points])
    zmin = min([p.z for p in points])
    zmax = max([p.z for p in points])
    e0 = Vec(xmin, ymax, zmin)
    e1 = Vec(xmax, ymax, zmax)
    height = ymax - ymin
    for y in xrange(0, height + 1):
        for p in iterate_disc(e0.up(y), e1.up(y)):
            yield p


def iterate_disc(e0, e1):
    for (p0, p1) in zip(*[iter(iterate_ellipse(e0, e1))] * 2):
        # A little wasteful. We get a few points more than once,
        # but oh well.
        for x in xrange(p0.x, p1.x + 1):
            yield Vec(x, p0.y, p0.z)


def iterate_ellipse(p0, p1):
    '''Ellipse function based on Bresenham's. This is ported from C and
    probably horribly inefficient here in python, but we are dealing with
    tiny spaces, so it probably won't matter much.'''
    z = min(p0.y, p1.y)
    x0 = p0.x
    x1 = p1.x
    y0 = p0.z
    y1 = p1.z

    a = abs(x1 - x0)
    b = abs(y1 - y0)
    b1 = b & 1
    dx = 4 * (1 - a) * b * b
    # 3.8 instead of 4 here makes the small circles look a little nicer.
    dy = 3.8 * (b1 + 1) * a * a
    err = dx + dy + b1 * a * a
    e2 = 0

    if (x0 > x1):
        x0 = x1
        x1 += a
    if (y0 > y1):
        y0 = y1
    y0 += (b + 1) / 2
    y1 = y0 - b1
    a *= 8 * a
    b1 = 8 * b * b

    while True:
        yield Vec(x0, z, y0)
        yield Vec(x1, z, y0)
        yield Vec(x0, z, y1)
        yield Vec(x1, z, y1)
        e2 = 2 * err
        if (e2 >= dx):
            x0 += 1
            x1 -= 1
            dx += b1
            err += dx
        if (e2 <= dy):
            y0 += 1
            y1 -= 1
            dy += a
            err += dy
        if (x0 > x1):
            break
        # flat ellipses a=1
        # Bug here... not sure what is going on, but
        # this is only needed for ellipese with a
        # horizontal radius of 1
        # while (y0 - y1 < b):
        #    y0 += 1
        #    yield Vec(x0-1, z, y0)
        #    y1 -= 1
        #    yield Vec(x0-1, z, y1)


def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step


def dumpEnts(world, EntId="minecraft:item_frame"):
    for i, cPos in enumerate(world.allChunks):
        try:
            chunk = world.getChunk(*cPos)
        except mclevel.ChunkMalformed:
            continue
        for Entity in chunk.Entities:
            if (Entity["id"].value == EntId):
                print "==========================================="
                print "---", Entity["id"].value
                print Entity
        for Entity in chunk.TileEntities:
            if (Entity["id"].value == EntId):
                print "==========================================="
                print "---", Entity["id"].value
                print Entity
                pos = Vec(0, 0, 0)
                for name, tag in Entity.items():
                    if (name == 'x'):
                        pos.x = tag.value & 0xf
                    if (name == 'y'):
                        pos.y = tag.value
                    if (name == 'z'):
                        pos.z = tag.value & 0xf
                print pos
                print 'Block Value:', chunk.Blocks[pos.x, pos.z, pos.y]
                print 'Data Value:', chunk.Data[pos.x, pos.z, pos.y]

        if i % 100 == 0:
            print "Chunk {0}...".format(i)


def spin(c=''):
    spinner = ['O o o', 'O O o', 'o O O', 'o o O', 'o O O', 'O O o']
    if (c == ''):
        c = spinner[random.randint(0, len(spinner) - 1)]
    sys.stdout.write("\r" + str(c) + "   \r")
    sys.stdout.flush()


def findChunkDepth(p, world):
    try:
        chunk = world.getChunk(p.x, p.z)
    except:
        return 0
    depth = world.Height
    for x in xrange(16):
        for z in xrange(16):
            y = chunk.HeightMap[z, x] - 1
            while (y > 0 and
                   chunk.Blocks[x, z, y] not in heightmap_solids):
                y = y - 1
            depth = min(y, depth)
    return depth


def findChunkDepths(p, world):
    try:
        chunk = world.getChunk(p.x, p.z)
    except:
        return 0
    min_depth = world.Height
    max_depth = 0
    for x in xrange(16):
        for z in xrange(16):
            y = chunk.HeightMap[z, x] - 1
            while (y > 0 and
                   chunk.Blocks[x, z, y] not in heightmap_solids):
                y = y - 1
            min_depth = min(y, min_depth)
            max_depth = max(y, max_depth)
    return (min_depth, max_depth)


def enum(*sequential, **named):
    '''Defines an object that can be used as an enum. Example:
        > Numbers = enum('ZERO', 'ONE', 'TWO')
        > Numbers.ZERO
        0
        > Numbers.ONE
        1'''
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)


def distribute(chunk, ymin, ymax, chance, material):
    '''Ditributes a material through the strata of a given array'''
    view = chunk.Blocks[:, :, ymin:ymax]
    viewd = chunk.Data[:, :, ymin:ymax]
    for i, v in numpy.ndenumerate(view):
        if random.uniform(0.0, 100.0) <= chance:
            view[i] = material.val
            viewd[i] = 0


def loadDungeonCache(cache_path):
    '''Load the dungeon cache given a path'''
    global cache_version
    dungeonCache = {}
    mtime = 0
    # Try some basic versioning.
    if not os.path.exists(
        os.path.join(cache_path, 'dungeon_scan_version_' + cache_version)
    ):
        print 'Dungeon cache missing, or is an old version. Resetting...'
        return dungeonCache, mtime

    # Try to load the cache
    if os.path.exists(os.path.join(cache_path, 'dungeon_scan_cache')):
        try:
            FILE = open(os.path.join(cache_path, 'dungeon_scan_cache'), 'rb')
            dungeonCache = cPickle.load(FILE)
            FILE.close()
        except Exception as e:
            print e
            sys.exit('Failed to read the dungeon_scan_cache file. '
                     ' Check permissions and try again.')

    # Try to read the cache mtime
    if os.path.exists(os.path.join(cache_path, 'dungeon_scan_mtime')):
        try:
            FILE = open(os.path.join(cache_path, 'dungeon_scan_mtime'), 'rb')
            mtime = cPickle.load(FILE)
            FILE.close()
        except Exception as e:
            print e
            sys.exit('Failed to read the dungeon_scan_mtime file. '
                     ' Check permissions and try again.')
    return dungeonCache, mtime


def loadTHuntCache(cache_path):
    '''Load the treasure hunt cache given a path'''
    global cache_version
    tHuntCache = {}
    mtime = 0
    # Try some basic versioning.
    if not os.path.exists(os.path.join(cache_path,
                                       'thunt_scan_version_' + cache_version)):
        print 'Treasure Hunt cache missing, or is an old version. Resetting...'
        return tHuntCache, mtime

    # Try to load the cache
    if os.path.exists(os.path.join(cache_path, 'thunt_scan_cache')):
        try:
            FILE = open(os.path.join(cache_path, 'thunt_scan_cache'), 'rb')
            tHuntCache = cPickle.load(FILE)
            FILE.close()
        except Exception as e:
            print e
            sys.exit('Failed to read the thunt_scan_cache file. '
                     ' Check permissions and try again.')

    # Try to read the cache mtime
    if os.path.exists(os.path.join(cache_path, 'thunt_scan_mtime')):
        try:
            FILE = open(os.path.join(cache_path, 'thunt_scan_mtime'), 'rb')
            mtime = cPickle.load(FILE)
            FILE.close()
        except Exception as e:
            print e
            sys.exit('Failed to read the thunt_scan_mtime file. '
                     ' Check permissions and try again.')
    return tHuntCache, mtime


def saveDungeonCache(cache_path, dungeonCache):
    ''' save the dungeon cache given a path and array'''
    global cache_version
    try:
        FILE = open(os.path.join(cache_path, 'dungeon_scan_cache'), 'wb')
        cPickle.dump(dungeonCache, FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write dungeon_scan_cache. '
                 ' Check permissions and try again.')
    mtime = int(time.time())
    try:
        FILE = open(os.path.join(cache_path, 'dungeon_scan_mtime'), 'wb')
        cPickle.dump(mtime, FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write dungeon_scan_mtime.'
                 'Check permissions and try again.')
    try:
        for f in os.listdir(cache_path):
            if re.search('dungeon_scan_version_.*', f):
                os.remove(os.path.join(cache_path, f))
        FILE = open(
            os.path.join(
                cache_path,
                'dungeon_scan_version_' +
                cache_version),
            'wb')
        cPickle.dump('SSsssss....BOOM', FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write dungeon_scan_version.'
                 'Check permissions and try again.')

    try:
        FILE = open(
            os.path.join(
                cache_path,
                'dungeon_scan_cache.yaml'
            ),
            'wb')
        decodedCache = [decodeDungeonInfo(d) for d in dungeonCache.values()]
        print >> FILE, yaml.dump(decodedCache, default_flow_style=False)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write dungeon_scan_cache.yaml. '
                 'Check permissions and try again.')


def saveTHuntCache(cache_path, tHuntCache):
    ''' save the treasure hunt cache given a path and array'''
    global cache_version
    try:
        FILE = open(os.path.join(cache_path, 'thunt_scan_cache'), 'wb')
        cPickle.dump(tHuntCache, FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write thunt_scan_cache. '
                 ' Check permissions and try again.')
    mtime = int(time.time())
    try:
        FILE = open(os.path.join(cache_path, 'thunt_scan_mtime'), 'wb')
        cPickle.dump(mtime, FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write thunt_scan_mtime.'
                 'Check permissions and try again.')
    try:
        for f in os.listdir(cache_path):
            if re.search('thunt_scan_version_.*', f):
                os.remove(os.path.join(cache_path, f))
        FILE = open(
            os.path.join(
                cache_path,
                'thunt_scan_version_' +
                cache_version),
            'wb')
        cPickle.dump('SSsssss....BOOM', FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write thunt_scan_version.'
                 'Check permissions and try again.')
    try:
        FILE = open(
            os.path.join(
                cache_path,
                'thunt_scan_cache.yaml'
            ),
            'wb')

        decodedCache = [decodeTHuntInfo(h) for h in tHuntCache.values()]

        # HACK for getting pyyaml to understand a list of Vecs
        for d in decodedCache:
            d['landmarks'] = str(d['landmarks'])

        print >> FILE, yaml.dump(decodedCache, default_flow_style=False)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write thunt_scan_cache.yaml. '
                 'Check permissions and try again.')


def loadChunkCache(cache_path):
    '''Load the chunk cache given a path'''
    global cache_version
    # Load the chunk cache
    chunkCache = {}
    chunkMTime = 0

    # Try some basic versioning.
    if not os.path.exists(os.path.join(cache_path,
                                       'chunk_scan_version_' + cache_version)):
        print 'Chunk cache missing, or is an old version. Resetting...'
        return chunkCache, chunkMTime

    if os.path.exists(os.path.join(cache_path, 'chunk_scan_cache')):
        try:
            FILE = open(os.path.join(cache_path, 'chunk_scan_cache'), 'rb')
            chunkCache = cPickle.load(FILE)
            FILE.close()
        except Exception as e:
            print e
            sys.exit('Failed to read the chunk_scan_cache file.'
                     'Check permissions and try again.')
    # Try to read the cache mtime
    if os.path.exists(os.path.join(cache_path, 'chunk_scan_mtime')):
        try:
            FILE = open(os.path.join(cache_path, 'chunk_scan_mtime'), 'rb')
            chunkMTime = cPickle.load(FILE)
            FILE.close()
        except Exception as e:
            print e
            sys.exit('Failed to read the dungeon_scan_mtime file.'
                     'Check permissions and try again.')
    return chunkCache, chunkMTime


def saveChunkCache(cache_path, chunkCache):
    ''' save the chunk cache given a path and array'''
    global cache_version
    try:
        FILE = open(os.path.join(cache_path, 'chunk_scan_cache'), 'wb')
        cPickle.dump(chunkCache, FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write chunk_scan_cache.'
                 'Check permissions and try again.')
    chunkMTime = int(time.time())
    try:
        FILE = open(os.path.join(cache_path, 'chunk_scan_mtime'), 'wb')
        cPickle.dump(chunkMTime, FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write chunk_scan_mtime.'
                 'Check permissions and try again.')
    try:
        for f in os.listdir(cache_path):
            if re.search('chunk_scan_version_.*', f):
                os.remove(os.path.join(cache_path, f))
        FILE = open(os.path.join(cache_path,
                                 'chunk_scan_version_' + cache_version), 'wb')
        cPickle.dump('SSsssss....BOOM', FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write dungeon_scan_version.'
                 'Check permissions and try again.')


def encodeDungeonInfo(dungeon, version):
    '''Takes a dungeon object and Returns an NBT structure for a
    chest+book encoding a lot of things to remember about this
    dungeon.'''
    # Some old things need to be added.
    items = dungeon.dinfo
    items['position'] = dungeon.position
    items['entrance_pos'] = dungeon.entrance_pos
    items['entrance_height'] = int(dungeon.entrance.height)
    items['version'] = version
    items['xsize'] = dungeon.xsize
    items['zsize'] = dungeon.zsize
    items['levels'] = dungeon.levels
    items['timestamp'] = int(time.time())

    # Create the base tags
    root_tag = nbt.TAG_Compound()
    root_tag['id'] = nbt.TAG_String('minecraft:chest')
    root_tag['CustomName'] = nbt.TAG_String('MCDungeon Data Library')
    root_tag['Lock'] = nbt.TAG_String(str(uuid.uuid4()))
    root_tag['x'] = nbt.TAG_Int(0)
    root_tag['y'] = nbt.TAG_Int(0)
    root_tag['z'] = nbt.TAG_Int(0)
    inv_tag = nbt.TAG_List()
    root_tag['Items'] = inv_tag

    # Populate the pages
    slot = 0
    page = 0
    newslot = True
    for key in items:
        # Make a new book
        if newslot is True:
            if slot >= 27:
                sys.exit('Too many values to store, and not enough slots!')
            item_tag = nbt.TAG_Compound()
            inv_tag.append(item_tag)
            item_tag['Slot'] = nbt.TAG_Byte(slot)
            item_tag['Count'] = nbt.TAG_Byte(1)
            item_tag['id'] = nbt.TAG_String('minecraft:written_book')
            item_tag['Damage'] = nbt.TAG_Short(0)
            tag_tag = nbt.TAG_Compound()
            item_tag['tag'] = tag_tag
            tag_tag['title'] = nbt.TAG_String(
                'MCDungeon Data Volume %d' % (slot + 1)
            )
            tag_tag['author'] = nbt.TAG_String('Various')
            tag_tag['pages'] = nbt.TAG_List()
            newslot = False
            page = 0
        slot += 1
        tag_tag['pages'].append(
            nbt.TAG_String(encodeJSONtext(cPickle.dumps({key: items[key]})))
        )
        page += 1
        if page >= 50:
            newslot = True
    return root_tag


def encodeTHuntInfo(thunt, version):
    '''Takes a dungeon object and Returns an NBT structure for a
    chest+book encoding a lot of things to remember about this
    dungeon.'''
    # Some old things need to be added.
    items = thunt.dinfo
    items['position'] = thunt.position
    items['version'] = version
    items['steps'] = thunt.steps
    items['timestamp'] = int(time.time())
    items['landmarks'] = []
    items['min_distance'] = thunt.min_distance
    items['max_distance'] = thunt.max_distance

    for l in thunt.landmarks:
        items['landmarks'].append(l.pos)

    # Create the base tags
    root_tag = nbt.TAG_Compound()
    root_tag['id'] = nbt.TAG_String('minecraft:chest')
    root_tag['CustomName'] = nbt.TAG_String('MCDungeon THunt Data Library')
    root_tag['x'] = nbt.TAG_Int(0)
    root_tag['y'] = nbt.TAG_Int(0)
    root_tag['z'] = nbt.TAG_Int(0)
    inv_tag = nbt.TAG_List()
    root_tag['Items'] = inv_tag

    # Populate the pages
    slot = 0
    page = 0
    newslot = True
    for key in items:
        # Make a new book
        if newslot is True:
            if slot >= 27:
                sys.exit('Too many values to store, and not enough slots!')
            item_tag = nbt.TAG_Compound()
            inv_tag.append(item_tag)
            item_tag['Slot'] = nbt.TAG_Byte(slot)
            item_tag['Count'] = nbt.TAG_Byte(1)
            item_tag['id'] = nbt.TAG_String('minecraft:written_book')
            item_tag['Damage'] = nbt.TAG_Short(0)
            tag_tag = nbt.TAG_Compound()
            item_tag['tag'] = tag_tag
            tag_tag['title'] = nbt.TAG_String(
                'MCDungeon Data Volume %d' % (slot + 1)
            )
            tag_tag['author'] = nbt.TAG_String('Various')
            tag_tag['pages'] = nbt.TAG_List()
            newslot = False
            page = 0
        slot += 1
        tag_tag['pages'].append(
            nbt.TAG_String(encodeJSONtext(cPickle.dumps({key: items[key]})))
        )
        page += 1
        if page >= 50:
            newslot = True
    return root_tag


def encodeJSONtext(string):
    if isinstance(string, str):
        string = {
            "text": string
        }
    return json.dumps(string)


def decodeJSONtext(string):
    try:
        return json.loads(string)['text']
    except ValueError:
        return string


def decodeDungeonInfo(lib):
    '''Takes an NBT tag and tries to decode a Chest object containing
    MCDungeon info. Returns a dictionary full of key=>value pairs'''
    items = {}

    # Position is always the x,y,z of the entity
    items['position'] = Vec(
        int(lib['x'].value),
        int(lib['y'].value),
        int(lib['z'].value)
    )

    # Look for legacy sign-based entity.
    if lib['id'].value == "Sign":

        m = re.search('E:(\d+),(\d+)', lib["Text4"].value)
        items['entrance_pos'] = Vec(int(m.group(1)), 0, int(m.group(2)))
        m = re.search('T:(..)', lib["Text4"].value)
        items['entrance_height'] = int(m.group(1), 16)
        items['version'] = lib["Text1"].value[5:]
        (items['xsize'],
         items['zsize'],
         items['levels']) = [int(x) for x in lib["Text3"].value.split(',')]
        items['timestamp'] = int(lib.value["Text2"])
        m = re.search('H:(.)', lib.value["Text4"])
        items['fill_caves'] = int(m.group(1))
        return items

    # Check the chest name
    if (
        'CustomName' not in lib or
        lib['CustomName'].value != 'MCDungeon Data Library'
    ):
        sys.exit('Invalid data library NBT.')

    # iterate through the objects in the chest
    for book in lib['Items']:
        if (
            (book['id'].value != 387 and book['id'].value != 'minecraft:written_book') or
            book['tag']['title'].value.startswith('MCDungeon Data Volume') is False
        ):
            print 'Non-book or odd book found in chest!', items['position'], 'id:', book['id']
            if 'tag' in book and 'title' in book['tag'].value:
                print '\t', book['tag']['title'].value
            continue
        for page in book['tag']['pages']:
            items.update(cPickle.loads(str(decodeJSONtext(page.value))))
    return items


def decodeTHuntInfo(lib):
    '''Takes an NBT tag and tries to decode a Chest object containing
    MCDungeon info. Returns a dictionary full of key=>value pairs'''
    items = {}

    # Position is always the x,y,z of the entity
    items['position'] = Vec(
        int(lib['x'].value),
        int(lib['y'].value),
        int(lib['z'].value)
    )

    # Check the chest name
    if (
        'CustomName' not in lib or
        lib['CustomName'].value != 'MCDungeon THunt Data Library'
    ):
        sys.exit('Invalid data library NBT.')

    # iterate through the objects in the chest
    for book in lib['Items']:
        if (
            (book['id'].value != 387 and book['id'].value != 'minecraft:written_book')
        ):
            continue
        if (
            'title' not in book['tag']
        ):
            print 'Strange book with no title found in cache chest'
            continue
        if (
            book['tag']['title'].value.startswith('MCDungeon Data Volume') is False
        ):
            print 'Strange book found in cache chest: %s' % (book['tag']['title'].value)
            continue
        for page in book['tag']['pages']:
            items.update(cPickle.loads(str(decodeJSONtext(page.value))))
    return items


# Some entity helpers

def get_tile_entity_tags(eid='chest', Pos=Vec(0, 0, 0),
                         CustomName=None, Lock=None, Base=0,
                         Patterns=(), Levels=0, Primary=0,
                         Secondary=0, BrewTime=0, Fuel=0, OutputSignal=0,
                         Command='', SuccessCount=0, LastOutput='',
                         Item='', Data=0, BurnTime=0, CookTime=0,
                         CookTimeTotal=0, TransferCooldown=0,
                         note=0, Record=0, RecordItem=None, Text1='',
                         Text2='', Text3='', Text4='', SkullType=0,
                         ExtraType=None,
                         Rot=0, ExactTeleport=0, ExitPos=Vec(0, 0, 0),
                         powered=0, PotionId=-1, CustomColor=0,
                         SplashPotion=0, isMovable=1, TrackOutput=1, auto=0,
                         conditionMet=1, Delay=0, SpawnCount=4, SpawnRange=4,
                         MinSpawnDelay=200, MaxSpawnDelay=800,
                         MaxNearbyEntities=6, RequiredPlayerRange=16,
                         SpawnData=None):
    '''Returns an nbt.TAG_Compound containing tags for tile
    entities'''

    # eids are always lower case.
    eid = eid.lower()

    # Convert Vec types into a tuple so we can use either.
    if isinstance(Pos, Vec):
        Pos = (Pos.x, Pos.y, Pos.z)

    root_tag = nbt.TAG_Compound()
    root_tag['id'] = nbt.TAG_String("minecraft:"+eid)
    root_tag['x'] = nbt.TAG_Int(Pos[0])
    root_tag['y'] = nbt.TAG_Int(Pos[1])
    root_tag['z'] = nbt.TAG_Int(Pos[2])

    if (
        CustomName is not None and
        eid in ('chest', 'furnace', 'dropper', 'hopper', 'dispenser',
                'brewing_stand', 'enchanting_table', 'command_block')
    ):
        root_tag['CustomName'] = nbt.TAG_String(CustomName)

    if (
        Lock is not None and
        eid in ('chest', 'furnace', 'dropper', 'hopper', 'dispenser',
                'brewing_stand', 'beacon')
    ):
        root_tag['Lock'] = nbt.TAG_String(Lock)

    if eid in ('command_block', 'noteblock'):
        root_tag['powered'] = nbt.TAG_Byte(powered)

    if eid == 'banner':
        root_tag['Base'] = nbt.TAG_Int(Base)
        root_tag['Patterns'] = nbt.TAG_List()
        # Supply a list of patterns as a list of tuples. Info is here
        # http://www.reddit.com/r/Minecraft/comments/2bhz8o/banner_nbt_a_quick_guide/
        # For example, red vertical stripes, followed by a yellow skull:
        # Pattern = ((1, 'ss'),(11, 'sku'))
        for p in Patterns:
            q = nbt.TAG_Compound()
            q['Color'] = nbt.TAG_Int(p[0])
            q['Pattern'] = nbt.TAG_String(p[1])
            root_tag['Patterns'].append(q)

    if eid == 'beacon':
        root_tag['Levels'] = nbt.TAG_Int(Levels)
        root_tag['Primary'] = nbt.TAG_Int(Primary)
        root_tag['Secondary'] = nbt.TAG_Int(Secondary)

    if eid in ('brewing_stand', 'chest', 'furnace', 'hopper', 'dispenser',
               'dropper'):
        root_tag['Items'] = nbt.TAG_List()

    if eid == 'brewing_stand':
        root_tag['BrewTime'] = nbt.TAG_Int(BrewTime)
        root_tag['Fuel'] = nbt.TAG_Byte(Fuel)

    if eid == 'cauldron':
        root_tag['PotionId'] = nbt.TAG_Short(PotionId)
        if PotionId == -1 and CustomColor != 0:
            root_tag['CustomColor'] = nbt.TAG_Int(CustomColor)
        root_tag['SplashPotion'] = nbt.TAG_Byte(SplashPotion)
        root_tag['isMovable'] = nbt.TAG_Byte(isMovable)

    if eid == 'comparator':
        root_tag['OutputSignal'] = nbt.TAG_Int(OutputSignal)

    if eid == 'command_block':
        root_tag['Command'] = nbt.TAG_String(Command)
        root_tag['SuccessCount'] = nbt.TAG_Int(SuccessCount)
        root_tag['LastOutput'] = nbt.TAG_String(LastOutput)
        root_tag['TrackOutput'] = nbt.TAG_Byte(TrackOutput)
        root_tag['auto'] = nbt.TAG_Byte(auto)
        root_tag['conditionMet'] = nbt.TAG_Byte(conditionMet)

    if eid == 'end_gateway':
        root_tag['Age'] = nbt.TAG_Long(201)
        root_tag['ExactTeleport'] = nbt.TAG_Byte(ExactTeleport)
        exit_tag = nbt.TAG_Compound()
        exit_tag['X'] = nbt.TAG_Int(ExitPos.x)
        exit_tag['Y'] = nbt.TAG_Int(ExitPos.y)
        exit_tag['Z'] = nbt.TAG_Int(ExitPos.z)
        root_tag['ExitPortal'] = exit_tag

    if eid == 'flower_pot':
        root_tag['Item'] = nbt.TAG_String(Item)
        root_tag['Data'] = nbt.TAG_Int(Data)

    if eid == 'furnace':
        root_tag['BurnTime'] = nbt.TAG_Short(BurnTime)
        root_tag['CookTime'] = nbt.TAG_Short(CookTime)
        root_tag['CookTimeTotal'] = nbt.TAG_Short(CookTimeTotal)

    if eid == 'hopper':
        root_tag['TransferCooldown'] = nbt.TAG_Int(TransferCooldown)

    if eid == 'jukebox':
        root_tag['Record'] = nbt.TAG_Int(Record)
        # Should be a full nbt.TAG_Compound item
        if RecordItem is not None:
            root_tag['RecordItem'] = RecordItem

    if eid == 'mob_spawner':
        if SpawnData is not None:
            root_tag['SpawnData'] = SpawnData
        else:
            root_tag['SpawnData'] = nbt.TAG_Compound()
            root_tag['SpawnData']['id'] = nbt.TAG_String("minecraft:bat")
        root_tag['SpawnCount'] = nbt.TAG_Short(SpawnCount)
        root_tag['SpawnRange'] = nbt.TAG_Short(SpawnRange)
        root_tag['Delay'] = nbt.TAG_Short(Delay)
        root_tag['MinSpawnDelay'] = nbt.TAG_Short(MinSpawnDelay)
        root_tag['MaxSpawnDelay'] = nbt.TAG_Short(MaxSpawnDelay)
        root_tag['MaxNearbyEntities'] = nbt.TAG_Short(MaxNearbyEntities)
        root_tag['RequiredPlayerRange'] = nbt.TAG_Short(RequiredPlayerRange)

    if eid == 'noteblock':
        root_tag['note'] = nbt.TAG_Byte(note)

    if eid == 'sign':
        root_tag['Text1'] = nbt.TAG_String(Text1)
        root_tag['Text2'] = nbt.TAG_String(Text2)
        root_tag['Text3'] = nbt.TAG_String(Text3)
        root_tag['Text4'] = nbt.TAG_String(Text4)

    if eid == 'skull':
        root_tag['SkullType'] = nbt.TAG_Byte(SkullType)
        root_tag['Rot'] = nbt.TAG_Byte(Rot)
        if ExtraType is not None:
            root_tag['ExtraType'] = nbt.TAG_String(ExtraType)

    return root_tag


def get_entity_base_tags(eid='chicken', Pos=Vec(0, 0, 0),
                         Motion=Vec(0, 0, 0), Rotation=Vec(0, 0, 0),
                         FallDistance=0.0, Fire=0, Air=300, OnGround=0,
                         NoGravity=0, Dimension=0, Invulnerable=0,
                         PortalCooldown=0, UUIDMost=None, UUIDLeast=None,
                         CustomName='', CustomNameVisible=0, Silent=0,
                         Passengers=[], Glowing=0, Tags=[]):
    '''
    Returns an nbt.TAG_Compound containing tags common to all entities.
    In general, you don't want to call this. You want to call
    get_entity_mob_tags(), get_entity_item() get_entity_other_tags() instead.
    '''

    # eids are always lower case.
    eid = eid.lower()

    # Convert Vec types into a tuple so we can use either
    if isinstance(Pos, Vec):
        Pos = (Pos.x, Pos.y, Pos.z)

    root_tag = nbt.TAG_Compound()
    root_tag['id'] = nbt.TAG_String("minecraft:"+eid)
    root_tag['Pos'] = nbt.TAG_List()
    root_tag['Pos'].append(nbt.TAG_Double(Pos[0]))
    root_tag['Pos'].append(nbt.TAG_Double(Pos[1]))
    root_tag['Pos'].append(nbt.TAG_Double(Pos[2]))
    root_tag['Motion'] = nbt.TAG_List()
    root_tag['Motion'].append(nbt.TAG_Double(Motion.x))
    root_tag['Motion'].append(nbt.TAG_Double(Motion.y))
    root_tag['Motion'].append(nbt.TAG_Double(Motion.z))
    root_tag['Rotation'] = nbt.TAG_List()
    root_tag['Rotation'].append(nbt.TAG_Float(Rotation.y))
    root_tag['Rotation'].append(nbt.TAG_Float(Rotation.x))
    root_tag['FallDistance'] = nbt.TAG_Float(FallDistance)
    root_tag['Fire'] = nbt.TAG_Short(Fire)
    root_tag['Air'] = nbt.TAG_Short(Air)
    root_tag['OnGround'] = nbt.TAG_Byte(OnGround)
    root_tag['NoGravity'] = nbt.TAG_Byte(NoGravity)
    root_tag['Dimension'] = nbt.TAG_Int(Dimension)
    root_tag['Invulnerable'] = nbt.TAG_Byte(Invulnerable)
    root_tag['PortalCooldown'] = nbt.TAG_Int(PortalCooldown)
    # Generate a UUID if one was not supplied. Most and Least are the high and
    # low 64 bit of the UUID 128 bit number. They are stored as signed 64 bit
    # integers.
    if (UUIDMost is None or UUIDLeast is None):
        u = uuid.uuid4().int
        UUIDMost = u >> 64
        if (UUIDMost & 0x8000000000000000):
            UUIDMost = -0x10000000000000000 + UUIDMost
        UUIDLeast = u & (1 << 64) - 1
        if (UUIDLeast & 0x8000000000000000):
            UUIDLeast = -0x10000000000000000 + UUIDLeast
    root_tag['UUIDMost'] = nbt.TAG_Long(UUIDMost)
    root_tag['UUIDLeast'] = nbt.TAG_Long(UUIDLeast)
    if CustomName is not None:
        root_tag['CustomName'] = nbt.TAG_String(CustomName)
        root_tag['CustomNameVisible'] = nbt.TAG_Byte(CustomNameVisible)
    if Silent:
        root_tag['Silent'] = nbt.TAG_Byte(Silent)
    # Passengers is a list of TAG_Compounds of other entities.
    if len(Passengers) > 0:
        root_tag['Passengers'] = nbt.TAG_List()
        for passenger in Passengers:
            root_tag['Passengers'].append(passenger)
    if Glowing:
        root_tag['Glowing'] = nbt.TAG_Byte(Glowing)
    # Tags is a list of strings.
    if len(Tags) > 0:
        root_tag['Tags'] = nbt.TAG_List()
        for tag in Tags:
            root_tag['Tags'].append(nbt.TAG_String(tag))
    return root_tag


def get_entity_mob_tags(eid='chicken', Health=None, AbsorptionAmount=0,
                        FallFlying=0, HurtTime=0, DeathTime=0,
                        CanPickUpLoot=0, NoAI=0, PersistenceRequired=0,
                        InLove=0, Age=0, Owner='', Sitting=0, Size=3,
                        wasOnGround=1, BatFlags=0, powered=0,
                        ExplosionRadius=3, Fuse=30, ignited=0, carried=0,
                        carriedData=0, Lifetime=0, PlayerSpawned=0, Bred=0,
                        SpellTicks=0, ChestedHorse=0, EatingHaystack=0,
                        Tame=0, Temper=0, Variant=None, OwnerUUID=None,
                        ExplosionPower=1, CatType=0, RabbitType=None,
                        MoreCarrotTicks=0, Sheared=0, Color=0,
                        Invul=0, Angry=0, CollarColor=14, Riches=0,
                        Career=None, CareerLevel=1, Willing=0, PlayerCreated=0,
                        IsBaby=0, ConversionTime=-1, CanBreakDoors=0, Anger=0,
                        Leashed=0, Leash=None, LeftHanded=0, Profession=None,
                        SkeletonTrap=0, EggLayTime=0, Strength=3,
                        SkeletonTrapTime=0, Peek=0, AttachFace=0, APX=0,
                        APY=0, APZ=0, Pumpkin=0, LifeTicks=0, BoundX=0,
                        BoundY=0, BoundZ=0, Johnny=0, Saddle=0,
                        **kwargs):
    '''Returns an nbt.TAG_Compound for a specific mob id'''

    eid = eid.lower()

    # Be nice, and figure out the health of common entities for us.
    if Health is None:
        if eid in (
            'chicken',
            'snowman',
        ):
            Health = 4
        elif eid in (
            'bat',
        ):
            Health = 6
        elif eid in (
            'endermite',
            'parrot',
            'sheep',
            'silverfish'
        ):
            Health = 8
        elif eid == 'wolf':
            if Owner == '':
                Health = 8
            else:
                Health = 20
        elif eid in (
            'cow',
            'mooshroom',
            'ocelot',
            'pig',
            'rabbit',
            'squid',
            'ghast'
        ):
            Health = 10
        elif eid in ('cave_spider'):
            Health = 12
        elif eid in ('vex'):
            Health = 14
        elif eid in (
            'donkey',
            'horse',
            'llama',
            'mule',
            'skeleton_horse',
            'zombie_horse',
        ):
            Health = 15
        elif eid in ('spider'):
            Health = 16
        elif eid in (
            'blaze',
            'creeper',
            'husk',
            'skeleton'
            'stray'
            'villager',
            'wither_skeleton'
            'zombie'
            'zombie_pigman',
            'zombie_villager'
        ):
            Health = 20
        elif eid in ('evocation_illager', 'vindication_illager'):
            Health = 24
        elif eid == 'witch':
            Health = 26
        elif eid in ('guardian', 'polar_bear', 'shulker'):
            Health = 30
        elif eid == 'enderman':
            Health = 40
        elif eid in (
            'slime',
            'magma_cube'
        ):
            Health = Size * Size
        elif eid in ('elder_guardian'):
            Health = 80
        elif eid in (
            'giant',
            'villager_golem'
        ):
            Health = 100
        elif eid == 'ender_dragon':
            Health = 200
        elif eid == 'wither':
            Health = 300
        else:
            Health = 1

    root_tag = get_entity_base_tags(eid, **kwargs)
    root_tag['Health'] = nbt.TAG_Float(Health)
    root_tag['AbsorptionAmount'] = nbt.TAG_Float(AbsorptionAmount)
    root_tag['HurtTime'] = nbt.TAG_Short(HurtTime)
    root_tag['DeathTime'] = nbt.TAG_Short(DeathTime)
    root_tag['FallFlying'] = nbt.TAG_Byte(FallFlying)

    root_tag['HandItems'] = nbt.TAG_List()
    root_tag['HandItems'].append(nbt.TAG_Compound())
    root_tag['HandItems'].append(nbt.TAG_Compound())

    root_tag['ArmorItems'] = nbt.TAG_List()
    root_tag['ArmorItems'].append(nbt.TAG_Compound())
    root_tag['ArmorItems'].append(nbt.TAG_Compound())
    root_tag['ArmorItems'].append(nbt.TAG_Compound())
    root_tag['ArmorItems'].append(nbt.TAG_Compound())

    root_tag['HandDropChances'] = nbt.TAG_List()
    root_tag['HandDropChances'].append(nbt.TAG_Float(0.085))
    root_tag['HandDropChances'].append(nbt.TAG_Float(0.085))

    root_tag['ArmorDropChances'] = nbt.TAG_List()
    root_tag['ArmorDropChances'].append(nbt.TAG_Float(0.085))
    root_tag['ArmorDropChances'].append(nbt.TAG_Float(0.085))
    root_tag['ArmorDropChances'].append(nbt.TAG_Float(0.085))
    root_tag['ArmorDropChances'].append(nbt.TAG_Float(0.085))

    root_tag['CanPickUpLoot'] = nbt.TAG_Byte(CanPickUpLoot)
    root_tag['NoAI'] = nbt.TAG_Byte(NoAI)
    root_tag['PersistenceRequired'] = nbt.TAG_Byte(PersistenceRequired)
    root_tag['LeftHanded'] = nbt.TAG_Byte(LeftHanded)
    root_tag['Leashed'] = nbt.TAG_Byte(Leashed)

    # If Leashed, figure out what we are leashed to. Leash can be provided as a
    # world coordinate of a block (Vec ot tuple), or another entity.
    if (Leashed == 1 and Leash is not None):
        root_tag['Leash'] = nbt.TAG_Compound()
        # Convert to tuple if Vec.
        if isinstance(Leash, Vec):
            Leash = (Leash.x, Leash.y, Leash.z)
        if isinstance(Leash, nbt.TAG_Compound):
            root_tag['Leash']['UUIDMost'] = Leash['UUIDMost']
            root_tag['Leash']['UUIDLeast'] = Leash['UUIDLeast']
        else:
            root_tag['Leash']['X'] = Leash[0]
            root_tag['Leash']['Y'] = Leash[1]
            root_tag['Leash']['Z'] = Leash[2]

    # Breeders
    if eid in ('chicken', 'cow', 'donkey', 'horse', 'llama', 'mooshroom',
               'ocelot', 'pig', 'rabbit', 'sheep', 'villager', 'wolf',
               'zombie_horse'):
        root_tag['InLove'] = nbt.TAG_Int(InLove)
        root_tag['Age'] = nbt.TAG_Int(Age)

    # Can be tamed
    if eid in ('ocelot', 'wolf', 'horse', 'parrot'):
        root_tag['Owner'] = nbt.TAG_String(Owner)
        root_tag['Sitting'] = nbt.TAG_Byte(Sitting)

    # Specific Mobs
    if eid == 'bat':
        root_tag['BatFlags'] = nbt.TAG_Byte(BatFlags)

    if eid == 'chicken':
        if EggLayTime == 0:
            root_tag['EggLayTime'] = nbt.TAG_Int(random.randint(6000, 12000))
        else:
            root_tag['EggLayTime'] = nbt.TAG_Int(EggLayTime)

    if eid == 'creeper':
        root_tag['powered'] = nbt.TAG_Byte(powered)
        root_tag['ExplosionRadius'] = nbt.TAG_Byte(ExplosionRadius)
        root_tag['Fuse'] = nbt.TAG_Short(Fuse)
        root_tag['ignited'] = nbt.TAG_Byte(ignited)

    if eid == 'enderman':
        root_tag['carried'] = nbt.TAG_Short(carried)
        root_tag['carriedData'] = nbt.TAG_Short(carriedData)

    if eid == 'endermite':
        root_tag['Lifetime'] = nbt.TAG_Int(Lifetime)
        root_tag['PlayerSpawned'] = nbt.TAG_Byte(PlayerSpawned)

    if eid == 'evocation_illager':
        root_tag['SpellTicks'] = nbt.TAG_Int(SpellTicks)

    if eid in ('donkey', 'llama', 'horse', 'mule', 'skeleton_horse',
               'zombie_horse'):
        root_tag['Bred'] = nbt.TAG_Byte(Bred)
        root_tag['EatingHaystack'] = nbt.TAG_Byte(EatingHaystack)
        root_tag['Tame'] = nbt.TAG_Byte(Tame)
        root_tag['Temper'] = nbt.TAG_Int(Temper)
        root_tag['OwnerUUID'] = nbt.TAG_String(OwnerUUID)

    if eid in ('donkey', 'llama', 'mule'):
        root_tag['ChestedHorse'] = nbt.TAG_Byte(ChestedHorse)
        root_tag['Items'] = nbt.TAG_List()

    if eid in ('donkey', 'horse', 'mule', 'skeleton_horse', 'zombie_horse'):
        root_tag['ArmorItem'] = nbt.TAG_Compound()
        root_tag['SaddleItem'] = nbt.TAG_Compound()

    if eid in ('horse'):
        # If Variant is not supplied, pick a random one.
        if Variant is None:
            Variant = random.randint(0, 6) | (random.randint(0, 4)*256) << 8
        root_tag['Variant'] = nbt.TAG_Int(Variant)

    if eid in ('llama'):
        if Variant is None:
            Variant = random.randint(0, 3)
        root_tag['Variant'] = nbt.TAG_Int(Variant)
        root_tag['Strength'] = nbt.TAG_Int(Strength)
        root_tag['DecorItem'] = nbt.TAG_Compound()

    if eid in ('skeleton_horse'):
        root_tag['SkeletonTrap'] = nbt.TAG_Byte(SkeletonTrap)
        root_tag['SkeletonTrapTime'] = nbt.TAG_Int(SkeletonTrapTime)

    if eid == 'ghast':
        root_tag['ExplosionPower'] = nbt.TAG_Int(ExplosionPower)

    if eid == 'ocelot':
        root_tag['CatType'] = nbt.TAG_Int(CatType)

    if eid == 'parrot':
        if Variant is None:
            Variant = random.randint(0, 4)
        root_tag['Variant'] = nbt.TAG_Byte(Variant)

    if eid == 'pig':
        root_tag['Saddle'] = nbt.TAG_Byte(Saddle)

    if eid == 'rabbit':
        if RabbitType is None:
            RabbitType = random.randint(0, 5)
        root_tag['RabbitType'] = nbt.TAG_Int(RabbitType)
        root_tag['MoreCarrotTicks'] = nbt.TAG_Int(MoreCarrotTicks)

    if eid == 'sheep':
        root_tag['Sheared'] = nbt.TAG_Byte(Sheared)
        root_tag['Color'] = nbt.TAG_Byte(Color)

    if eid == 'shulker':
        root_tag['AttachFace'] = nbt.TAG_Byte(AttachFace)
        root_tag['Color'] = nbt.TAG_Byte(Color)
        root_tag['Peek'] = nbt.TAG_Byte(Peek)
        root_tag['APX'] = nbt.TAG_Int(APX)
        root_tag['APY'] = nbt.TAG_Int(APY)
        root_tag['APZ'] = nbt.TAG_Int(APZ)

    if eid in ('slime', 'magma_cube'):
        root_tag['Size'] = nbt.TAG_Int(Size)
        root_tag['wasOnGround'] = nbt.TAG_Byte(wasOnGround)

    if eid == 'snowman':
        root_tag['Pumpkin'] = nbt.TAG_Byte(Pumpkin)

    if eid == 'vex':
        if LifeTicks == 0:
            LifeTicks = random.randint(33, 108) * 20
        root_tag['LifeTicks'] = nbt.TAG_Int(LifeTicks)
        root_tag['BoundX'] = nbt.TAG_Int(BoundX)
        root_tag['BoundY'] = nbt.TAG_Int(BoundY)
        root_tag['BoundZ'] = nbt.TAG_Int(BoundZ)

    if eid == 'villager':
        root_tag['Riches'] = nbt.TAG_Int(Riches)
        if Profession is None:
            Profession = random.randint(0, 5)
        root_tag['Profession'] = nbt.TAG_Int(Profession)
        if Career is None:
            if Profession == 0:
                Career = random.randint(1, 4)
            elif Profession == 1:
                Career = random.randint(1, 2)
            elif Profession == 3:
                Career = random.randint(1, 3)
            elif Profession == 4:
                Career = random.randint(1, 2)
            else:
                Career = 1
        root_tag['Career'] = nbt.TAG_Int(Career)
        root_tag['CareerLevel'] = nbt.TAG_Int(CareerLevel)
        root_tag['Willing'] = nbt.TAG_Byte(Willing)

    if eid == 'villager_golem':
        root_tag['PlayerCreated'] = nbt.TAG_Byte(PlayerCreated)

    if eid == 'vindication_illager':
        root_tag['Johnny'] = nbt.TAG_Byte(Johnny)

    if eid == 'wither':
        root_tag['Invul'] = nbt.TAG_Int(Invul)

    if eid == 'wolf':
        root_tag['Angry'] = nbt.TAG_Byte(Angry)
        root_tag['CollarColor'] = nbt.TAG_Byte(CollarColor)

    if eid in ('husk', 'zombie', 'zombie_pigman', 'zombie_villager'):
        root_tag['IsBaby'] = nbt.TAG_Byte(IsBaby)
        root_tag['CanBreakDoors'] = nbt.TAG_Byte(CanBreakDoors)

    if eid in ('zombie_villager'):
        if Profession is None:
            Profession = random.randint(0, 4)
        root_tag['Profession'] = nbt.TAG_Int(Profession)
        root_tag['ConversionTime'] = nbt.TAG_Int(ConversionTime)

    if eid == 'zombie_pigman':
        root_tag['Anger'] = nbt.TAG_Short(Anger)

    return root_tag


def get_entity_item_tags(eid='xp_orb', Value=1, Count=1, ItemInfo=None,
                         Damage=0, Health=5, Age=0, PickupDelay=0,
                         Owner=None, Thrower=None, **kwargs):
    '''Returns an nbt.TAG_Compound for a specific item. ItemInfo
    should contain an item object from items.'''

    eid = eid.lower()

    root_tag = get_entity_base_tags(eid, **kwargs)

    root_tag['Health'] = nbt.TAG_Short(Health)
    root_tag['Age'] = nbt.TAG_Short(Age)

    # xp_orbs are easy. Otherwise try to create a generic item. This won't work
    # in every case... some ItemInfo are not viable items, and some require
    # an extra 'tag' compound tag to work right.
    if eid == 'xp_orb':
        root_tag['Value'] = nbt.TAG_Short(Value)

    if eid == "item":
        root_tag['PickupDelay'] = nbt.TAG_Short(PickupDelay)
        if ItemInfo is not None:
            root_tag['Item'] = nbt.TAG_Compound()
            root_tag['Item']['id'] = nbt.TAG_String(ItemInfo.id)
            root_tag['Item']['Damage'] = nbt.TAG_Short(Damage)
            root_tag['Item']['Count'] = nbt.TAG_Byte(Count)
        if Owner is not None:
            root_tag['Owner'] = nbt.TAG_String(Owner)
        if Thrower is not None:
            root_tag['Thrower'] = nbt.TAG_String(Thrower)

    return root_tag


def get_entity_other_tags(eid='ender_crystal', Facing='S',
                          ItemTags=None, ItemDropChance=1.0,
                          ItemRotation=0, Motive='Kebab', Pos=Vec(0, 0, 0),
                          Damage=0, DisabledSlots=0, Invisible=0,
                          NoBasePlate=0, NoGravity=0, ShowArms=0,
                          Small=0, Health=None, Pose=None, Marker=0,
                          **kwargs):
    '''Returns an nbt.TAG_Compound for "other" type entities. These
    include ender_crystal, eye_of_ender_signal, item_frame,
    Painting, leash_knot, and armor_stand. Chunk offsets will be
    calculated. ItemTags should contain an item as NBT tags.'''

    eid = eid.lower()

    # Convert Vec types so we can use either
    if isinstance(Pos, Vec):
        Pos = (Pos.x, Pos.y, Pos.z)

    root_tag = get_entity_base_tags(eid=eid, Pos=Pos, **kwargs)

    if eid == 'armor_stand':
        root_tag['DisabledSlots'] = nbt.TAG_Int(DisabledSlots)
        root_tag['HandItems'] = nbt.TAG_List()
        root_tag['HandItems'].append(nbt.TAG_Compound())
        root_tag['HandItems'].append(nbt.TAG_Compound())
        root_tag['ArmorItems'] = nbt.TAG_List()
        root_tag['ArmorItems'].append(nbt.TAG_Compound())
        root_tag['ArmorItems'].append(nbt.TAG_Compound())
        root_tag['ArmorItems'].append(nbt.TAG_Compound())
        root_tag['ArmorItems'].append(nbt.TAG_Compound())
        root_tag['Invisible'] = nbt.TAG_Byte(Invisible)
        root_tag['Marker'] = nbt.TAG_Byte(Marker)
        root_tag['NoBasePlate'] = nbt.TAG_Byte(NoBasePlate)
        root_tag['NoGravity'] = nbt.TAG_Byte(NoGravity)
        root_tag['ShowArms'] = nbt.TAG_Byte(ShowArms)
        root_tag['Small'] = nbt.TAG_Byte(Small)
        if Health is not None:
            root_tag['Health'] = nbt.TAG_Float(Health)
        else:
            root_tag['Health'] = nbt.TAG_Float(20)
        if Pose is not None:
            root_tag['Pose'] = Pose

    # Positioning on these gets tricky. TileX/Y/Z is the block the
    # painting/item_frame is contained within, and Pos is the actual position in the
    # world. So we need to move Pos slightly according to size of the
    # Painting/item_frame and direction it is facing or Minecraft will complain
    # and try to move the entity itself. The entity must be centered on the
    # tile it is attached to on the appropriate face. Paintings and frames
    # are 1-4 blocks tall and wide, and 0.03125 blocks thick.
    if eid in ('item_frame', 'painting'):
        # Set direction. For convenience we provide letters.
        dirs = {'N': 2,
                'S': 0,
                'E': 3,
                'W': 1}
        if Facing in dirs:
            Facing = dirs[Facing]
        root_tag['Facing'] = nbt.TAG_Byte(Facing)

        # Now, shift Pos appropriately. First we need the size of the entity.
        # Default is 1x1, and Item Frames are 1x1.
        sizes = {
            'Kebab': (1, 1),
            'Aztec': (1, 1),
            'Alban': (1, 1),
            'Aztec2': (1, 1),
            'Bomb': (1, 1),
            'Plant': (1, 1),
            'Wasteland': (1, 1),
            'Wanderer': (1, 2),
            'Graham': (1, 2),
            'Pool': (2, 1),
            'Courbet': (2, 1),
            'Sunset': (2, 1),
            'Sea': (2, 1),
            'Creebet': (2, 1),
            'Match': (2, 2),
            'Bust': (2, 2),
            'Stage': (2, 2),
            'Void': (2, 2),
            'SkullAndRoses': (2, 2),
            'Wither': (2, 2),
            'Fighters': (4, 2),
            'Skeleton': (4, 3),
            'DonkeyKong': (4, 3),
            'Pointer': (4, 4),
            'PigScene': (4, 4),
            'Flaming Skull': (4, 4),
        }
        if (eid == 'painting' and Motive in sizes):
            width = sizes[Motive][0]
            height = sizes[Motive][1]
        else:
            width = 1
            height = 1

        # North facing
        if Facing == 2:
            root_tag['Pos'][0].value += float(width) / 2.0
            root_tag['Pos'][1].value -= float(height) / 2.0
            root_tag['Pos'][2].value -= 0.03125
        # South facing
        elif Facing == 0:
            root_tag['Pos'][0].value += float(width) / 2.0
            root_tag['Pos'][1].value -= float(height) / 2.0
            root_tag['Pos'][2].value += 1.03125
        # East facing
        elif Facing == 3:
            root_tag['Pos'][0].value += 1.03125
            root_tag['Pos'][1].value -= float(height) / 2.0
            root_tag['Pos'][2].value += float(width) / 2.0
        # West facing
        elif Facing == 1:
            root_tag['Pos'][0].value -= 0.03125
            root_tag['Pos'][1].value -= float(height) / 2.0
            root_tag['Pos'][2].value += float(width) / 2.0

        # Copy the Pos location to Tile entries.
        root_tag['TileX'] = nbt.TAG_Int(int(root_tag['Pos'][0].value))
        root_tag['TileY'] = nbt.TAG_Int(int(root_tag['Pos'][1].value + 0.5))
        root_tag['TileZ'] = nbt.TAG_Int(int(root_tag['Pos'][2].value))

    # Attach an item to the frame (if any)
    if eid == 'item_frame':
        root_tag['ItemDropChance'] = nbt.TAG_Float(ItemDropChance)
        root_tag['ItemRotation'] = nbt.TAG_Byte(ItemRotation)
        if ItemTags is not None:
            root_tag['Item'] = ItemTags

    # Set the painting.
    if eid == 'painting':
        root_tag['Motive'] = nbt.TAG_String(Motive)

    return root_tag


# Convert number to ordinal (1st, 2nd etc.)
# source: http://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
def converttoordinal(numb):
    if numb < 20:  # determining suffix for < 20
        if numb == 1:
            suffix = 'st'
        elif numb == 2:
            suffix = 'nd'
        elif numb == 3:
            suffix = 'rd'
        else:
            suffix = 'th'
    else:  # determining suffix for > 20
        tens = str(numb)
        tens = tens[-2]
        unit = str(numb)
        unit = unit[-1]
        if tens == "1":
            suffix = "th"
        else:
            if unit == "1":
                suffix = 'st'
            elif unit == "2":
                suffix = 'nd'
            elif unit == "3":
                suffix = 'rd'
            else:
                suffix = 'th'
    return str(numb) + suffix


def DebugBreakpoint(banner="Debugger started (CTRL-D to quit)"):
    '''Drop to the python console for some debugging'''

    # use exception trick to pick up the current frame
    try:
        raise None
    except:
        frame = sys.exc_info()[2].tb_frame.f_back

    # evaluate commands in current namespace
    namespace = frame.f_globals.copy()
    namespace.update(frame.f_locals)

    print "START DEBUG"
    code.interact(banner=banner, local=namespace)
    print "END DEBUG"
