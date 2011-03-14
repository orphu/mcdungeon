import random
import math
import re
from copy import *

def floor(n):
    return int(n)


def ceil(n):
    if int(n) == n:
        return int(n)
    return int(n)+1


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
    def __hash__(self):
        return self.x + (self.y<<4) + (self.z<<8)
    def east(self, x):
        return Vec(self.x+x, self.y, self.z)
    def west(self, x):
        return Vec(self.x-x, self.y, self.z)
    def up(self, y):
        return Vec(self.x,self.y-y,self.z)
    def down(self, y):
        return Vec(self.x,self.y+y,self.z)
    def north(self, z):
        return Vec(self.x,self.y,self.z-z)
    def south(self, z):
        return Vec(self.x,self.y,self.z+z)
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
        x_intersect = (self.loc.x > b.x2()) and (self.x2() > b.loc.x)
        y_intersect = (self.loc.y > b.y2()) and (self.y2() > b.loc.y)
        z_intersect = (self.loc.z > b.z2()) and (self.z2() > b.loc.z)
        return x_intersect and y_intersect and z_intersect


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
    for b in iterate_cube(near, Vec(near.x,far.y,far.z)): yield b
    for b in iterate_cube(near, Vec(far.x,near.y,far.z)): yield b
    for b in iterate_cube(near, Vec(far.x,far.y,near.z)): yield b
    for b in iterate_cube(Vec(near.x,near.y,far.z),far): yield b
    for b in iterate_cube(Vec(near.x,far.y,near.z),far): yield b
    for b in iterate_cube(Vec(far.x,near.y,near.z),far): yield b


def iterate_four_walls(corner1, corner2, corner3, corner4, height):
    for b in iterate_cube(corner1, corner2, corner1.up(height)): yield b
    for b in iterate_cube(corner2, corner3, corner2.up(height)): yield b
    for b in iterate_cube(corner3, corner4, corner3.up(height)): yield b
    for b in iterate_cube(corner4, corner1, corner4.up(height)): yield b


def iterate_points_inside_flat_poly(*poly_points):
    min_x = floor(min([p.x for p in poly_points]))
    max_x = ceil(max([p.x for p in poly_points]))
    min_z = floor(min([p.z for p in poly_points]))
    max_z = ceil(max([p.z for p in poly_points]))
    min_y = floor(min([p.y for p in poly_points]))
    num_points = len(poly_points)

    def point_inside(p):
        if type(p) == Vec2f: p = Vec(p.x,0,p.z)
        for i in xrange(num_points):
            a = poly_points[i]
            b = poly_points[(i+1) % num_points]

            if type(a) == Vec2f: a = Vec(a.x,0,a.z)
            if type(b) == Vec2f: b = Vec(b.x,0,b.z)

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
    return sum(1 for p in iterate_points_inside_flat_poly(*poly_points))-1


def iterate_points_surrounding_box(box):
    near = box.loc.trans(-1,-1,-1)
    far = box.loc.trans(box.w+1,box.h+1,box.d+1)
    return iterate_hollow_cube(near, far)


def iterate_spiral(p1, p2, height):
    p = p1
    box = Box(p1.trans(0,-height,0), p2.x-p1.x, height, p2.z-p1.z)
    step = Vec(1,-1,0)
    for y in xrange(height):
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
        item = weighted_choice(items)
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

def iterate_disc(center, rx, rz):
    for x in drange(-rx, rx+1, 1.0):
        for z in drange(-rz, rz+1, 1.0):
            p = Vec2f(center.x+x, center.z+z)
            if ((x**2)/(rx**2) + (z**2)/(rz**2) <= 1):
                yield p

def drange(start, stop, step):
    r = start
    while r < stop:
        yield r
        r += step
