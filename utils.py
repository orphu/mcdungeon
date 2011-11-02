import random
import math
import re
import sys
import numpy
from copy import *
from itertools import *
from pymclevel import mclevel, nbt

def floor(n):
    return int(n)


def ceil(n):
    if int(n) == n:
        return int(n)
    return int(n)+1


def clamp(n, a, b):
    rmin = min(a,b)
    rmax = max(a,b)
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
    def __add__(self, b):
        if type(b) == Vec: return Vec(self.x+b.x, self.y+b.y, self.z+b.z)
        else: return Vec(self.x+b, self.y+b, self.z+b)
    def __sub__(self, b):
        if type(b) == Vec: return Vec(self.x-b.x, self.y-b.y, self.z-b.z)
        else: return Vec(self.x-b, self.y-b, self.z-b)
    def __mul__(self, b):
        return Vec(self.x*b, self.y*b, self.z*b)
    def __str__(self):
        return "(%d,%d,%d)" % (self.x,self.y,self.z)
    def __eq__(self, b):
        if type(b) != Vec: return False
        return self.x==b.x and self.y==b.y and self.z==b.z
    def __ne__(self, b):
        if type(b) != Vec: return True
        return self.x!=b.x or self.y!=b.y or self.z!=b.z
    def __hash__(self):
        return self.x + (self.y<<4) + (self.z<<8)
    def e(self, x):
        return Vec(self.x+x, self.y, self.z)
    def w(self, x):
        return Vec(self.x-x, self.y, self.z)
    def up(self, y):
        return Vec(self.x,self.y-y,self.z)
    def down(self, y):
        return Vec(self.x,self.y+y,self.z)
    def n(self, z):
        return Vec(self.x,self.y,self.z-z)
    def s(self, z):
        return Vec(self.x,self.y,self.z+z)
    def mag2d(self):
        return math.sqrt(self.x*self.x + self.z*self.z)
    def d(self, d):
        if (d == 0):
            return Vec(0,0,-1)
        if (d == 1):
            return Vec(1,0,0)
        if (d == 2):
            return Vec(0,0,1)
        if (d == 3):
            return Vec(-1,0,0)
    def rotate(self, r):
        # rotate around xz plane
        while r < 0: r += 4
        if r == 0: return self
        elif r == 1: return Vec(-self.z, self.y, self.x)
        elif r == 2: return Vec(-self.x, self.y, -self.z)
        elif r == 3: return Vec(self.z, self.y, -self.x)
    def ccw(self):
        return self.rotate(-1)
    def cw(self):
        return self.rotate(1)
    def trans(self, x, y, z):
        return Vec(self.x+x, self.y+y, self.z+z)


# As of 1.9 pre 4:
#   North = -Z
#   South = +Z
#   East = +X
#   West = -X
NORTH = Vec(0,0,-1)
SOUTH = Vec(0,0,1)
EAST = Vec(1,0,0)
WEST = Vec(-1,0,0)
UP = Vec(0,1,0)
DOWN = Vec(0,-1,0)


class Vec2f(object):
    def __init__(self, x, z):
        self.x = float(x)
        self.z = float(z)

    @staticmethod
    def fromVec(vec):
        return Vec2f(vec.x,vec.z)

    def rotate(self, r):
        while r < 0: r += 4
        if r == 0: return self
        elif r == 1: return Vec2f(-self.z, self.x)
        elif r == 2: return Vec2f(-self.x, -self.z)
        elif r == 3: return Vec2f(self.z, -self.x)

    def det(self, b):
        return self.x*b.z - self.z*b.x

    def mag(self):
        return math.sqrt(self.x*self.x + self.z*self.z)

    def unit(self):
        mag = math.sqrt(self.x*self.x + self.z*self.z)
        return Vec2f(self.x/mag,self.z/mag)

    def __str__(self):
        return "(%f,%f)"%(self.x,self.z)

    def __add__(self, b):
        if type(b) == Vec2f: return Vec2f(self.x+b.x, self.z+b.z)
        else: return Vec2f(self.x+b, self.z+b)

    def __sub__(self, b):
        if type(b) == Vec2f: return Vec2f(self.x-b.x, self.z-b.z)
        else: return Vec2f(self.x-b, self.z-b)

    def __mul__(self, b):
        return Vec2f(self.x*b, self.z*b)


class Box(object):
    def __init__(self, loc, w, h, d):
        self.loc = loc
        self.w = w
        self.h = h
        self.d = d

    def x2(self): return self.loc.x+self.w

    def y2(self): return self.loc.y+self.h

    def z2(self): return self.loc.z+self.d

    def containsPoint(self, p):
        x = p.x - self.loc.x
        y = p.y - self.loc.y
        z = p.z - self.loc.z
        return ((x >= 0) and (x < self.w)
                and (y >= 0) and (y < self.h)
                and (z >= 0) and (z < self.d))

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
        return abs((loc1.x-loc2.x)*(loc1.z-loc2.z))


def iterate_plane(loc1, loc2):
    for x in xrange(min(loc1.x,loc2.x),max(loc1.x,loc2.x)+1):
      for y in xrange(min(loc1.y,loc2.y),max(loc1.y,loc2.y)+1):
        for z in xrange(min(loc1.z,loc2.z),max(loc1.z,loc2.z)+1):
          yield Vec(x,y,z)


def iterate_cube(*points):
    for x in xrange(min([p.x for p in points]),
                    max([p.x for p in points])+1):
      for y in xrange(min([p.y for p in points]),
                      max([p.y for p in points])+1):
        for z in xrange(min([p.z for p in points]),
                        max([p.z for p in points])+1):
          yield Vec(x,y,z)


def iterate_hollow_cube(near, far):
    for b in iterate_cube(near, Vec(near.x,far.y,far.z)):
        yield b
    for b in iterate_cube(near, Vec(far.x,near.y,far.z)):
        yield b
    for b in iterate_cube(near, Vec(far.x,far.y,near.z)):
        yield b
    for b in iterate_cube(Vec(near.x,near.y,far.z),far):
        yield b
    for b in iterate_cube(Vec(near.x,far.y,near.z),far):
        yield b
    for b in iterate_cube(Vec(far.x,near.y,near.z),far):
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


def iterate_points_inside_flat_poly(*poly_points):
    min_x = floor(min([p.x for p in poly_points]))
    max_x = ceil(max([p.x for p in poly_points]))
    min_z = floor(min([p.z for p in poly_points]))
    max_z = ceil(max([p.z for p in poly_points]))
    min_y = floor(min([p.y for p in poly_points]))
    num_points = len(poly_points)

    def point_inside(p):
        if type(p) == Vec2f:
            p = Vec(p.x,0,p.z)
        for i in xrange(num_points):
            a = poly_points[i]
            b = poly_points[(i+1) % num_points]

            if type(a) == Vec2f:
                a = Vec(a.x,0,a.z)
            if type(b) == Vec2f:
                b = Vec(b.x,0,b.z)

            b_to_a = Vec2f.fromVec(b-a)
            p_to_a = Vec2f.fromVec(p-a)

            det = b_to_a.det(p_to_a)
            if det < 0:
                return False
        return True

    for x in xrange(min_x,max_x+1):
      for z in xrange(min_z,max_z+1):
          p = Vec(x,min_y,z)
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
    near = box.loc.trans(-1,-1,-1)
    far = box.loc.trans(box.w+1,box.h+1,box.d+1)
    return iterate_hollow_cube(near, far)


def iterate_spiral(p1, p2, height):
    p = p1
    box = Box(p1.trans(0,-height,0), p2.x-p1.x, height, p2.z-p1.z)
    step = Vec(1,-1,0)
    for y in xrange(int(height)):
        yield p
        if (box.containsPoint(p+step) is False):
            if (step == Vec(1,-1,0)):
                step = Vec(0,-1,1)
            elif (step == Vec(0,-1,1)):
                step = Vec(-1,-1,0)
            elif (step == Vec(-1,-1,0)):
                step = Vec(0,-1,-1)
            else:
                step = Vec(1,-1,0)
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
        #item = weighted_choice(items)
        weight_total = sum((item[1] for item in items))
        n = random.uniform(0, weight_total)
        for item, weight in items:
            if n < weight:
                break
            n = n - weight
        results.insert(0, item)
        items.remove([item, weight])
    return results


def str2Vec(string):
    m = re.search('(-{0,1}\d+)[\s,]*(-{0,1}\d+)[\s,]*(-{0,1}\d+)', string)
    return Vec(m.group(1), m.group(2), m.group(3))


def iterate_tube(e0, e1, height):
    for y in xrange(height+1):
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
    for y in xrange(0, height+1):
        for p in iterate_disc(e0.up(y), e1.up(y)):
            yield p


def iterate_disc(e0, e1):
    for (p0, p1) in zip(*[iter(iterate_ellipse(e0, e1))]*2):
        # A little wasteful. We get a few points more than once, 
        # but oh well. 
        for x in xrange(p0.x, p1.x+1):
            yield Vec(x, p0.y, p0.z)


def iterate_ellipse(p0, p1):
    # Ellipse function based on Bresenham's. This is ported from C and probably
    # horribly inefficient here in python, but we are dealing with tiny spaces, so
    # it probably won't matter much.'''
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
    y0 += (b +  1) / 2
    y1 = y0 - b1
    a *= 8 * a
    b1 = 8 * b * b

    while  True:
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
        #while (y0 - y1 < b):
        #    y0 += 1
        #    yield Vec(x0-1, z, y0)
        #    y1 -= 1
        #    yield Vec(x0-1, z, y1)


def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step


def dumpEnts(world):
    for i, cPos in enumerate(world.allChunks):
        try:
            chunk = world.getChunk(*cPos);
        except mclevel.ChunkMalformed:
            continue
        for tileEntity in chunk.TileEntities:
            pos = Vec(0,0,0)
            if (tileEntity["id"].value == "Trap"):
                for name, tag in tileEntity.items():
                    print '   ',name, tag.value
                    if (name == 'x'):
                        pos.x = tag.value & 0xf
                    if (name == 'y'):
                        pos.y = tag.value
                    if (name == 'z'):
                        pos.z = tag.value & 0xf
                print pos
                print 'Block Value:',chunk.Blocks[pos.x, pos.z, pos.y]
                print 'Data Value:',chunk.Data[pos.x, pos.z, pos.y]

        if i % 100 == 0:
            print "Chunk {0}...".format(i)
        chunk.unload()


def spin(c = ''):
    spinner = ['|', '/', '-', '\\']
    if (c == ''):
        c = spinner[random.randint(0,len(spinner)-1)]
    sys.stdout.write("\r"+str(c)+"   \r")
    sys.stdout.flush()


def findChunkDepth(p, world):
    try:
        chunk = world.getChunk(p.x, p.z)
    except:
        return 0
    depth = 128
    # list of IDs that are solid. (for our purposes anyway)
    solids = ( 1, 2, 3, 4, 7, 12, 13, 24, 48, 49, 60, 82)
    for x in xrange(16):
        for z in xrange(16):
            y = chunk.HeightMap[z, x]-1
            while (y > 0 and
                   chunk.Blocks[x, z, y] not in solids):
                y = y - 1
            depth = min(y, depth)
    chunk.unload()
    return depth

def findChunkDepths(p, world):
    try:
        chunk = world.getChunk(p.x, p.z)
    except:
        return 0
    min_depth = 128
    max_depth = 0
    # list of IDs that are solid. (for our purposes anyway)
    solids = ( 1, 2, 3, 4, 7, 12, 13, 24, 48, 49, 60, 82)
    for x in xrange(16):
        for z in xrange(16):
            y = chunk.HeightMap[z, x]-1
            while (y > 0 and
                   chunk.Blocks[x, z, y] not in solids):
                y = y - 1
            min_depth = min(y, min_depth)
            max_depth = max(y, max_depth)
    chunk.unload()
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
    view = chunk.Blocks[:,:,ymin:ymax]
    viewd = chunk.Data[:,:,ymin:ymax]
    for i,v in numpy.ndenumerate(view):
        if random.uniform(0.0, 100.0) <= chance:
            view[i] = material.val
            viewd[i] = 0
