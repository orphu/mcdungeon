import random
import math
import re
import sys
import os
import numpy
import cPickle
import time
from copy import *
from itertools import *
from pymclevel import mclevel, nbt

cache_version = '2'

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
    def __repr__(self):
        return self.__str__()
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


def spin(c = ''):
    spinner = ['O o o', 'O O o', 'o O O', 'o o O', 'o O O', 'O O o']
    if (c == ''):
        c = spinner[random.randint(0,len(spinner)-1)]
    sys.stdout.write("\r"+str(c)+"   \r")
    sys.stdout.flush()


def findChunkDepth(p, world):
    try:
        chunk = world.getChunk(p.x, p.z)
    except:
        return 0
    depth = world.Height
    # list of IDs that are solid. (for our purposes anyway)
    solids = ( 1, 2, 3, 4, 7, 12, 13, 24, 48, 49, 60, 82, 98)
    for x in xrange(16):
        for z in xrange(16):
            y = chunk.HeightMap[z, x]-1
            while (y > 0 and
                   chunk.Blocks[x, z, y] not in solids):
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
    # list of IDs that are solid. (for our purposes anyway)
    solids = ( 1, 2, 3, 4, 7, 12, 13, 24, 48, 49, 60, 82, 98)
    for x in xrange(16):
        for z in xrange(16):
            y = chunk.HeightMap[z, x]-1
            while (y > 0 and
                   chunk.Blocks[x, z, y] not in solids):
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
    view = chunk.Blocks[:,:,ymin:ymax]
    viewd = chunk.Data[:,:,ymin:ymax]
    for i,v in numpy.ndenumerate(view):
        if random.uniform(0.0, 100.0) <= chance:
            view[i] = material.val
            viewd[i] = 0

def loadDungeonCache(cache_path):
    '''Load the dungeon cache given a path'''
    global cache_version
    dungeonCache = {}
    mtime = 0
    # Try some basic versioning.
    if not os.path.exists(os.path.join(cache_path,
                                       'dungeon_scan_version_'+cache_version)):
        print 'Dungeon cache missing, or is an old verision. Resetting...'
        return dungeonCache, mtime

    # Try to load the cache
    if  os.path.exists(os.path.join(cache_path, 'dungeon_scan_cache')):
        try:
            FILE = open(os.path.join(cache_path, 'dungeon_scan_cache'), 'rb')
            dungeonCache = cPickle.load(FILE)
            FILE.close()
        except Exception as e:
            print e
            sys.exit('Failed to read the dungeon_scan_cache file. Check permissions and try again.')

    # Try to read the cache mtime
    if  os.path.exists(os.path.join(cache_path, 'dungeon_scan_mtime')):
        try:
            FILE = open(os.path.join(cache_path, 'dungeon_scan_mtime'), 'rb')
            mtime = cPickle.load(FILE)
            FILE.close()
        except Exception as e:
            print e
            sys.exit('Failed to read the dungeon_scan_mtime file. Check permissions and try again.')
    return dungeonCache, mtime


def saveDungeonCache(cache_path, dungeonCache):
    ''' save the dungeon cache given a path and array'''
    global cache_version
    try:
        FILE = open(os.path.join(cache_path, 'dungeon_scan_cache'), 'wb')
        cPickle.dump(dungeonCache, FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write dungeon_scan_cache. Check permissions and try again.')
    mtime = int(time.time())
    try:
        FILE = open(os.path.join(cache_path, 'dungeon_scan_mtime'), 'wb')
        cPickle.dump(mtime, FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write dungeon_scan_mtime. Check permissions and try again.')
    try:
        for f in os.listdir(cache_path):
            if re.search('dungeon_scan_version_.*', f):
                os.remove(os.path.join(cache_path, f))
        FILE = open(os.path.join(cache_path,
                                 'dungeon_scan_version_'+cache_version), 'wb')
        cPickle.dump('SSsssss....BOOM', FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write dungeon_scan_version. Check permissions and try again.')


def loadChunkCache(cache_path):
    '''Load the chunk cache given a path'''
    global cache_version
    # Load the chunk cache
    chunkCache = {}
    chunkMTime = 0

    # Try some basic versioning.
    if not os.path.exists(os.path.join(cache_path,
                                       'chunk_scan_version_'+cache_version)):
        print 'Chunk cache missing, or is an old verision. Resetting...'
        return chunkCache, chunkMTime

    if os.path.exists(os.path.join(cache_path, 'chunk_scan_cache')):
        try:
            FILE = open(os.path.join(cache_path, 'chunk_scan_cache'), 'rb')
            chunkCache = cPickle.load(FILE)
            FILE.close()
        except Exception as e:
            print e
            sys.exit('Failed to read the chunk_scan_cache file. Check permissions and try again.')
    # Try to read the cache mtime
    if  os.path.exists(os.path.join(cache_path, 'chunk_scan_mtime')):
        try:
            FILE = open(os.path.join(cache_path, 'chunk_scan_mtime'), 'rb')
            chunkMTime = cPickle.load(FILE)
            FILE.close()
        except Exception as e:
            print e
            sys.exit('Failed to read the dungeon_scan_mtime file. Check permissions and try again.')
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
        sys.exit('Failed to write chunk_scan_cache. Check permissions and try again.')
    chunkMTime = int(time.time())
    try:
        FILE = open(os.path.join(cache_path, 'chunk_scan_mtime'), 'wb')
        cPickle.dump(chunkMTime, FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write chunk_scan_mtime. Check permissions and try again.')
    try:
        for f in os.listdir(cache_path):
            if re.search('chunk_scan_version_.*', f):
                os.remove(os.path.join(cache_path, f))
        FILE = open(os.path.join(cache_path,
                                 'chunk_scan_version_'+cache_version), 'wb')
        cPickle.dump('SSsssss....BOOM', FILE, -1)
        FILE.close()
    except Exception as e:
        print e
        sys.exit('Failed to write dungeon_scan_version. Check permissions and try again.')

def encodeDungeonInfo(dungeon, version):
    '''Takes a dungeon object and Returns an NBT structure for a dispenser+book encoding a lot of things to
    remember about this dungeon.'''
    # Some old things need to be added.
    items = dungeon.dinfo
    items['entrance_pos'] = dungeon.entrance_pos
    items['entrance_height'] = int(dungeon.entrance.height)
    items['version'] = version
    items['xsize'] = dungeon.xsize
    items['zsize'] = dungeon.zsize
    items['levels'] = dungeon.levels
    items['timestamp'] = int(time.time())

    # Create the base tags
    root_tag = nbt.TAG_Compound()
    root_tag['id'] = nbt.TAG_String('Chest')
    root_tag['CustomName'] = nbt.TAG_String('MCDungeon Data Library')
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
        if newslot == True:
            if slot >= 27:
                say.exit('Too many values to store, and not enough slots!')
            item_tag = nbt.TAG_Compound()
            inv_tag.append(item_tag)
            item_tag['Slot'] = nbt.TAG_Byte(slot)
            item_tag['Count'] = nbt.TAG_Byte(1)
            item_tag['id'] = nbt.TAG_Short(387)
            item_tag['Damage'] = nbt.TAG_Short(0)
            tag_tag = nbt.TAG_Compound()
            item_tag['tag'] = tag_tag
            tag_tag['title'] = nbt.TAG_String('MCDungeon Data Volume %d'%(slot+1))
            tag_tag['author'] = nbt.TAG_String('Various')
            tag_tag['pages'] = nbt.TAG_List()
            newslot = False
            page = 0
        slot += 1
        tag_tag['pages'].append(nbt.TAG_String(cPickle.dumps({key: items[key]})))
        page += 1
        if page >= 50:
            newslot = True
    return root_tag

def decodeDungeonInfo(lib):
    '''Takes an NBT tag and tries to decode a Chest object containing
    MCDungeon info. Returns a dictionary full of key=>value pairs'''
    items = {}

    # Position is always the x,y,z of the entity
    items['position'] = Vec(int(lib['x']), int(lib['y']), int(lib['z']))

    # Look for legacy sign-based entity.
    if lib['id'] == "Sign":

        m = re.search('E:(\d+),(\d+)', lib["Text4"])
        items['entrance_pos'] = Vec(int(m.group(1)), 0, int(m.group(2)))
        m = re.search('T:(..)', lib["Text4"])
        items['entrance_height'] = int(m.group(1), 16)
        items['version'] = lib["Text1"][5:]
        (items['xsize'], items['zsize'], items['levels']) = [int(x) for x in lib["Text3"].split(',')]
        items['timestamp'] = int(lib["Text2"])
        m = re.search('H:(.)', lib["Text4"])
        items['fill_caves'] = int(m.group(1))
        return items

    # Check the chest name
    if ('CustomName' not in lib or
        lib['CustomName'] != 'MCDungeon Data Library'):
        sys.exit('Invalid data library NBT.')

    # iterate through the objects in the chest
    for book in lib['Items']:
        if (book['id'] != 387 or
            book['tag']['title'].startswith('MCDungeon Data Volume') is False):
            continue
        for page in book['tag']['pages']:
            items.update(cPickle.loads(str(page)))
    return items

# Some entity helpers
def get_entity_base_tags(eid='Chicken', Pos=Vec(0,0,0),
                         Motion=Vec(0,0,0), Rotation=Vec(0,0,0),
                         FallDistance=0.0, Fire=-1, Air=300, OnGround=0,
                         Dimension=0, Invulnerable=0, PortalCooldown=0,
                         CustomName=''):
    '''Returns an nbt.TAG_Compound containing tags common to all entities'''
    root_tag = nbt.TAG_Compound()
    root_tag['id'] = nbt.TAG_String(eid)
    root_tag['Pos'] = nbt.TAG_List()
    root_tag['Pos'].append(nbt.TAG_Double(Pos.x))
    root_tag['Pos'].append(nbt.TAG_Double(Pos.y))
    root_tag['Pos'].append(nbt.TAG_Double(Pos.z))
    root_tag['Motion'] = nbt.TAG_List()
    root_tag['Motion'].append(nbt.TAG_Double(Motion.x))
    root_tag['Motion'].append(nbt.TAG_Double(Motion.y))
    root_tag['Motion'].append(nbt.TAG_Double(Motion.z))
    root_tag['Rotation'] = nbt.TAG_List()
    root_tag['Rotation'].append(nbt.TAG_Float(Rotation.y))
    root_tag['Rotation'].append(nbt.TAG_Float(Rotation.x))
    root_tag['FallDistance']= nbt.TAG_Float(FallDistance)
    root_tag['Fire']= nbt.TAG_Short(Fire)
    root_tag['Air']= nbt.TAG_Short(Air)
    root_tag['OnGround']= nbt.TAG_Byte(OnGround)
    root_tag['Dimension']= nbt.TAG_Int(Dimension)
    root_tag['Invulnerable']= nbt.TAG_Byte(Invulnerable)
    root_tag['PortalCooldown']= nbt.TAG_Int(PortalCooldown)
    root_tag['CustomName'] = nbt.TAG_String(CustomName)
    return root_tag

def get_entity_mob_tags(eid='Chicken', Health=None, AttackTime=0,
                        HurtTime=0, DeathTime=0, CanPickUpLoot=0,
                        PersistenceRequired =0, CustomNameVisible=0,
                        InLove=0, Age=0, Owner='', Sitting=0, Size=4,
                        BatFlags=0, powered=0, ExplosionRadius=3,
                        Fuse=30, carried=0, carriedData=0, ExplosionPower=1,
                        CatType=0, Saddle=0, Sheared=0, Color=0,
                        SkeletonType=0, Invul=0, Angry=0, CollarColor=14,
                        Profession=5, Riches=0, PlayerCreated=0, IsVillager=0,
                        IsBaby=0, ConversionTime=-1, Anger=0,
                        **kwargs):
    '''Returns an nbt.TAG_Compound for a specific mob id'''

    if Health is None:
        if eid == 'Chicken':
            Health = 4
        elif eid in ('Bat',
                     'SnowMan'
                    ):
            Health = 6
        elif eid in ('Sheep',
                     'Silverfish'
                    ):
            Health = 8
        elif eid == 'Wolf':
            if Owner == '':
                Health = 8
            else:
                Health = 20
        elif eid in ('Cow',
                     'MushroomCow',
                     'Ozelot',
                     'Pig',
                     'Squid',
                     'Ghast'
                    ):
            Health = 10
        elif eid in ('CaveSpider'):
            Health = 12
        elif eid in ('Spider'):
            Health = 16
        elif eid in ('Villager',
                     'PigZombie',
                     'Blaze',
                     'Creeper',
                     'Skeleton'
                    ):
            Health = 20
        elif eid == 'Witch':
            Health = 26
        elif eid == 'Enderman':
            Health = 40
        elif eid in ('Slime',
                     'LavaSlime'
                    ):
            Health = Size*Size
        elif eid == 'VillagerGolem':
            Health = 100
        elif eid == 'EnderDragon':
            Health = 200
        elif eid == 'WitherBoss':
            Health = 300
        else:
            Health = 1

    root_tag = get_entity_base_tags(eid, **kwargs)
    root_tag['Health']= nbt.TAG_Short(Health)
    root_tag['AttackTime']= nbt.TAG_Short(AttackTime)
    root_tag['HurtTime']= nbt.TAG_Short(HurtTime)
    root_tag['DeathTime']= nbt.TAG_Short(DeathTime)

    root_tag['Equipment'] = nbt.TAG_List()
    root_tag['Equipment'].append(nbt.TAG_Compound())
    root_tag['Equipment'].append(nbt.TAG_Compound())
    root_tag['Equipment'].append(nbt.TAG_Compound())
    root_tag['Equipment'].append(nbt.TAG_Compound())
    root_tag['Equipment'].append(nbt.TAG_Compound())

    root_tag['DropChances'] = nbt.TAG_List()
    root_tag['DropChances'].append(nbt.TAG_Float(0.05))
    root_tag['DropChances'].append(nbt.TAG_Float(0.05))
    root_tag['DropChances'].append(nbt.TAG_Float(0.05))
    root_tag['DropChances'].append(nbt.TAG_Float(0.05))
    root_tag['DropChances'].append(nbt.TAG_Float(0.05))

    root_tag['CanPickUpLoot']= nbt.TAG_Byte(CanPickUpLoot)
    root_tag['PersistenceRequired']= nbt.TAG_Byte(PersistenceRequired)
    root_tag['CustomNameVisible']= nbt.TAG_Byte(CustomNameVisible)

    # Breeders
    if eid in ('Chicken', 'Cow', 'MushroomCow', 'Ozelot', 'Pig', 'Sheep',
               'Villager', 'Wolf'):
        root_tag['InLove']= nbt.TAG_Int(InLove)
        root_tag['Age']= nbt.TAG_Int(Age)

    # Can be tamed
    if eid in ('Ozelot', 'Wolf'):
        root_tag['Owner']= nbt.TAG_String(Owner)
        root_tag['Sitting']= nbt.TAG_Byte(Sitting)

    # Specific Mobs
    if eid == 'Bat':
        root_tag['BatFlags']= nbt.TAG_Byte(BatFlags)

    if eid == 'Creeper':
        root_tag['powered']= nbt.TAG_Byte(powered)
        root_tag['ExplosionRadius']= nbt.TAG_Byte(ExplosionRadius)
        root_tag['Fuse']= nbt.TAG_Short(Fuse)

    if eid == 'Enderman':
        root_tag['carried']= nbt.TAG_Short(carried)
        root_tag['carriedData']= nbt.TAG_Short(carriedData)

    if eid == 'Ghast':
        root_tag['ExplosionPower']= nbt.TAG_Int(ExplosionPower)

    if eid == 'Ozelot':
        root_tag['CatType']= nbt.TAG_Int(CatType)

    if eid == 'Pig':
        root_tag['Saddle']= nbt.TAG_Byte(Saddle)

    if eid == 'Sheep':
        root_tag['Sheared']= nbt.TAG_Byte(Sheared)
        root_tag['Color']= nbt.TAG_Byte(Color)

    if eid == 'Skeleton':
        root_tag['SkeletonType']= nbt.TAG_Byte(SkeletonType)

    if eid in ('Slime', 'LavaSlime'):
        root_tag['Size']= nbt.TAG_Int(Size)

    if eid == 'WitherBoss':
        root_tag['Invul']= nbt.TAG_Int(Invul)

    if eid == 'Wolf':
        root_tag['Angry']= nbt.TAG_Byte(Angry)
        root_tag['CollarColor']= nbt.TAG_Byte(CollarColor)

    if eid == 'Villager':
        root_tag['Profession']= nbt.TAG_Int(Profession)
        root_tag['Riches']= nbt.TAG_Int(Riches)

    if eid == 'VillagerGolem':
        root_tag['PlayerCreated']= nbt.TAG_Byte(PlayerCreated)

    if eid == 'Zombie':
        root_tag['IsVillager']= nbt.TAG_Byte(IsVillager)
        root_tag['IsBaby']= nbt.TAG_Byte(IsBaby)
        root_tag['ConversionTime']= nbt.TAG_Int(ConversionTime)

    if eid == 'PigZombie':
        root_tag['Anger']= nbt.TAG_Short(Anger)

    return root_tag

def get_entity_item_tags(eid='XPOrb', Value=1, Count=1, ItemInfo=None,
                         Damage=0,
                        **kwargs):
    '''Returns an nbt.TAG_Compound for a specific item. ItemInfo should contain
    an item object from items.'''

    root_tag = get_entity_base_tags(eid, **kwargs)

    # XPOrbs are easy. Otherwise try to create a generic item. This won't work
    # in every case... some ItemInfo are not viable items, and some require
    # an extra 'tag' compound tag to work right. 
    if eid == 'XPOrb':
        root_tag['Value']= nbt.TAG_Short(Value)
    elif (eid == "Item" and ItemInfo is not None):
        root_tag['Item'] = nbt.TAG_Compound()
        root_tag['Item']['id'] = nbt.TAG_Short(ItemInfo.value)
        root_tag['Item']['Damage'] = nbt.TAG_Short(Damage)
        root_tag['Item']['Count'] = nbt.TAG_Byte(Count)

    return root_tag

def get_entity_other_tags(eid='EnderCrystal', Direction='S', ItemInfo=None,
                          ItemDropChance=1.0, ItemRotation=0, Motive='Kebab',
                          Pos=Vec(0,0,0), Damage=0,
                        **kwargs):
    '''Returns an nbt.TAG_Compound for "other" type entities. These include
    EnderCrystal, EyeOfEnder, ItemFrame, and Painting. Chunk offsets will be
    calculated. ItemInfo should contain an item object from items.'''

    root_tag = get_entity_base_tags(eid=eid, Pos=Pos, **kwargs)

    # Positioning on these gets tricky. TileX/Y/Z is the block the
    # painting/ItemFrame is attached to, and Pos is the actual position in the
    # world. So we need to move Pos slightly according to size of the
    # Painting/ItemFrame and direction it is facing or Minecraft will complain
    # and try to move the entity itself. The entity must be centered on the tile
    # it is attached to on the appropriate face. 
    # Paintings and frames are 1-4 blocks tall and wide, and 0.0625 blocks thick. 
    if eid in ('ItemFrame', 'Painting'):
        # Copy the Pos location to Tile entries.
        root_tag['TileX']= nbt.TAG_Int(Pos.x)
        root_tag['TileY']= nbt.TAG_Int(Pos.y)
        root_tag['TileZ']= nbt.TAG_Int(Pos.z)
        # Set direction. For convenience we provide letters.
        dirs = {'N': 2,
                'S': 0,
                'E': 3,
                'W': 1}
        if Direction in dirs:
            Direction = dirs[Direction]
        root_tag['Direction']= nbt.TAG_Byte(Direction)

        # Now, shift Pos appropriately. First we need the size of the entity.
        # Default is 1x1, and ItemFrames are 1x1.
        sizes = {
            'Kebab':         (1,1),
            'Aztec':         (1,1),
            'Alban':         (1,1),
            'Aztec2':        (1,1),
            'Bomb':          (1,1),
            'Plant':         (1,1),
            'Wasteland':     (1,1),
            'Wanderer':      (1,2),
            'Graham':        (1,2),
            'Pool':          (2,1),
            'Courbet':       (2,1),
            'Sunset':        (2,1),
            'Sea':           (2,1),
            'Creebet':       (2,1),
            'Match':         (2,2),
            'Bust':          (2,2),
            'Stage':         (2,2),
            'Void':          (2,2),
            'SkullAndRoses': (2,2),
            'Wither':        (2,2),
            'Fighters':      (4,2),
            'Skeleton':      (4,3),
            'DonkeyKong':    (4,3),
            'Pointer':       (4,4),
            'PigScene':      (4,4),
            'Flaming Skull': (4,4),
        }
        if (eid == 'Painting' and Motive in sizes):
            width = sizes[Motive][0]
            height = sizes[Motive][1]
        else:
            width = 1
            height = 1

        # North face
        if Direction == 2:
            root_tag['Pos'][0].value += float(width)/2.0
            root_tag['Pos'][1].value -= float(height)/2.0
            root_tag['Pos'][2].value -= 0.0625
        # South face
        elif Direction == 0:
            root_tag['Pos'][0].value += float(width)/2.0
            root_tag['Pos'][1].value -= float(height)/2.0
            root_tag['Pos'][2].value += 1.0625
        # East face
        elif Direction == 3:
            root_tag['Pos'][0].value += 1.0625
            root_tag['Pos'][1].value -= float(height)/2.0
            root_tag['Pos'][2].value += 1 + float(width)/2.0
        # West face
        elif Direction == 1:
            root_tag['Pos'][0].value -= float(width)/2.0
            root_tag['Pos'][1].value -= float(height)/2.0
            root_tag['Pos'][2].value -= 0.0625

    # Attach an item to the frame (if any)
    if eid == 'ItemFrame':
        root_tag['ItemDropChance']= nbt.TAG_Float(ItemDropChance)
        root_tag['ItemRotation']= nbt.TAG_Byte(ItemRotation)
        if ItemInfo is not None:
            root_tag['Item'] = nbt.TAG_Compound()
            root_tag['Item']['id'] = nbt.TAG_Short(ItemInfo.value)
            root_tag['Item']['Damage'] = nbt.TAG_Short(Damage)
            root_tag['Item']['Count'] = nbt.TAG_Byte(1)

    # Set the painting.
    if eid == 'Painting':
        root_tag['Motive']= nbt.TAG_String(Motive)

    return root_tag
