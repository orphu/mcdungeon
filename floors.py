import sys
import inspect

import materials
import random
import perlin
from utils import *

class Blank(object):
    _name = 'blank'
    def __init__ (self, parent):
        self.parent = parent
    def render (self):
        pass

class Cobble(Blank):
    _name = 'cobble'
    ruin = False
    mat = materials.meta_mossycobble
    def render (self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        for x in iterate_points_inside_flat_poly(*self.parent.canvas):
            self.parent.parent.setblock(x+self.parent.loc, self.mat)
        # Ruined
        if (self.ruin is False):
            return
        c = self.parent.canvasCenter()
        y = self.parent.canvasHeight()
        r = random.randint(1,1000)
        maxd = max(1, self.parent.canvasWidth(), self.parent.canvasLength())
        pn = perlin.SimplexNoise(256)
        for x in iterate_points_inside_flat_poly(*self.parent.canvas):
            p = x+self.parent.loc
            d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
            n = (pn.noise3((p.x+r) / 4.0, y / 4.0, p.z / 4.0) + 1.0) / 2.0
            if (n < d):
                self.parent.parent.setblock(p, materials._floor)
                self.parent.parent.blocks[p].data = 0


class BrokenCobble(Cobble):
    _name = 'brokencobble'
    ruin = True
    mat = materials.meta_mossycobble


class StoneBrick(Cobble):
    _name = 'stonebrick'
    ruin = False
    mat = materials.meta_mossystonebrick


class BrokenStoneBrick(Cobble):
    _name = 'brokenstonebrick'
    ruin = True
    mat = materials.meta_mossystonebrick


class WoodTile(Blank):
    _name = 'woodtile'
    def render (self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) > 4):
            for x in iterate_points_inside_flat_poly(*self.parent.canvas):
                if ((x.x+x.z)&1 == 1):
                    self.parent.parent.setblock(x+self.parent.loc,
                                                materials.Wood)
                else:
                    self.parent.parent.setblock(x+self.parent.loc,
                                                materials.WoodPlanks)


class CheckerRug(Blank):
    _name = 'checkerrug'
    ruin = False
    colors = (
        (7,8),   # dark grey / light grey
        (9,3),   # cyan / light blue
        #(14,10), # red / purple
        (11,9),  # dark blue / cyan
        (1,14),  # red / orange
        (7,15),  # dark grey / black
        #(3,4),   # light blue  / yellow
        (11,10), # dark blue  / purple
        (12,13), # brown  / dark green
        (15,13), # black  / dark green
        )
    def render (self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        color = random.choice(self.colors)
        for x in iterate_points_inside_flat_poly(*self.parent.canvas):
            self.parent.parent.setblock(x+self.parent.loc,
                                        materials.Wool)
            if ((x.x+x.z)&1 == 1):
                self.parent.parent.blocks[x+self.parent.loc].data = color[0]
            else:
                self.parent.parent.blocks[x+self.parent.loc].data = color[1]
        # Runined
        pn = perlin.SimplexNoise(256)
        if (self.ruin is False):
            return
        c = self.parent.canvasCenter()
        y = self.parent.canvasHeight()
        r = random.randint(1,1000)
        maxd = max(1, self.parent.canvasWidth(), self.parent.canvasLength())
        for x in iterate_points_inside_flat_poly(*self.parent.canvas):
            p = x+self.parent.loc
            d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
            n = (pn.noise3((p.x+r) / 4.0, y / 4.0, p.z / 4.0) + 1.0) / 2.0
            if (n < d):
                self.parent.parent.setblock(p, materials._floor)
                self.parent.parent.blocks[p].data = 0


class BrokenCheckerRug(CheckerRug):
    _name = 'brokencheckerrug'
    ruin = True


class DoubleSlab(Blank):
    _name = 'doubleslab'
    ruin = False
    def render (self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        for x in iterate_points_inside_flat_poly(*self.parent.canvas):
            self.parent.parent.setblock(x+self.parent.loc,
                                        materials.DoubleSlab)
        # Runined
        pn = perlin.SimplexNoise(256)
        if (self.ruin is False):
            return
        c = self.parent.canvasCenter()
        y = self.parent.canvasHeight()
        r = random.randint(1,1000)
        maxd = max(1, self.parent.canvasWidth(), self.parent.canvasLength())
        for x in iterate_points_inside_flat_poly(*self.parent.canvas):
            p = x+self.parent.loc
            d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
            n = (pn.noise3((p.x+r) / 4.0, y / 4.0, p.z / 4.0) + 1.0) / 2.0
            if (n < d):
                self.parent.parent.setblock(p, materials._floor)
                self.parent.parent.blocks[p].data = 0


class BrokenDoubleSlab(DoubleSlab):
    _name = 'brokendoubleslab'
    ruin = True


class Mud(Blank):
    _name = 'mud'
    def render (self):
        pn = perlin.SimplexNoise(256)
        if (sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        c = self.parent.canvasCenter()
        y = self.parent.canvasHeight()
        r = random.randint(1,1000)
        maxd = max(1, self.parent.canvasWidth(), self.parent.canvasLength())
        for x in iterate_points_inside_flat_poly(*self.parent.canvas):
            p = x+self.parent.loc
            d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
            n = (pn.noise3((p.x+r) / 4.0, y / 4.0, p.z / 4.0) + 1.0) / 2.0
            if (n >= d+.50):
                self.parent.parent.setblock(p, materials.Water)
            elif (n >= d+.30):
                self.parent.parent.setblock(p, materials.SoulSand)
            elif (n >= d+.15):
                self.parent.parent.setblock(p, materials.Farmland)
                self.parent.parent.blocks[p].data = random.randint(0,1)
            elif (n >= d):
                self.parent.parent.setblock(p, materials.Dirt)


class Sand(Blank):
    _name = 'sand'
    def render (self):
        pn = perlin.SimplexNoise(256)
        if (sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        c = self.parent.canvasCenter()
        y = self.parent.canvasHeight()
        r = random.randint(1,1000)
        maxd = max(1, self.parent.canvasWidth(), self.parent.canvasLength())
        for x in iterate_points_inside_flat_poly(*self.parent.canvas):
            p = x+self.parent.loc
            d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
            n = (pn.noise3((p.x+r) / 4.0, y / 4.0, p.z / 4.0) + 1.0) / 2.0
            if (n >= d+.20):
                self.parent.parent.setblock(p, materials.Sand)
            elif (n >= d+.10):
                self.parent.parent.setblock(p, materials.Sandstone)
            elif (n >= d):
                self.parent.parent.setblock(p, materials.Gravel)


class Bridges(Blank):
    _name = 'bridges'
    sandpit = False
    def render(self):
        pn = perlin.SimplexNoise(256)
        # Find all the valid halls. These are halls with a size > 0.
        # We'll store a random position within the range of the hall.
        halls = [0,0,0,0]
        hallcount = 0
        buttons = set()
        for h in xrange(4):
            if (self.parent.halls[h].size > 0):
                halls[h] = \
                    self.parent.halls[h].offset + 1 + \
                    random.randint(0, self.parent.halls[h].size - 3)
                hallcount += 1
        # We won't draw just half a bridge, unless this is a sandpit. (yet)
        if (hallcount < 2 and self.sandpit == False):
            return
        midpoint = self.parent.parent.room_size / 2
        y = self.parent.canvasHeight()
        offset = self.parent.loc
        # Look for the X bounds between halls.
        if (halls[0] != 0 and halls[2] != 0):
            x1 = halls[0]
            x2 = halls[2]
        elif (halls[0] != 0):
            x1 = halls[0]
            x2 = x1
        elif (halls[2] != 0):
            x2 = halls[2]
            x1 = x2
        else:
            x1 = midpoint
            x2 = midpoint
        # Look for the Z bounds between halls.
        if (halls[1] != 0 and halls[3] != 0):
            z1 = halls[1]
            z2 = halls[3]
        elif (halls[1] != 0):
            z1 = halls[1]
            z2 = z1
        elif (halls[3] != 0):
            z2 = halls[3]
            z1 = z2
        else:
            z1 = midpoint
            z2 = midpoint
        # Now construct our points. 
        # c1-4 are the corners of the connecting
        # box. h0-3 are the start points of the halls.
        c1 = Vec(x1, y, z1)
        c2 = Vec(x2, y, z1)
        c3 = Vec(x2, y, z2)
        c4 = Vec(x1, y, z2)
        h0 = Vec(x1,
                 y,
                 self.parent.hallLength[0])
        h1 = Vec(self.parent.parent.room_size-self.parent.hallLength[1]-1,
                 y,
                 z1)
        h2 = Vec(x2,
                 y,
                 self.parent.parent.room_size-self.parent.hallLength[2]-1)
        h3 = Vec(self.parent.hallLength[3],
                 y,
                 z2)
        # Sandpit?
        mat = materials.WoodenSlab
        if (self.sandpit == True):
            # Draw the false sand floor
            mat = materials.Sand
            c = self.parent.canvasCenter()
            y = self.parent.canvasHeight()
            r = random.randint(1,1000)
            maxd = max(1, self.parent.canvasWidth(), self.parent.canvasLength())
            for x in iterate_points_inside_flat_poly(*self.parent.canvas):
                p = x+self.parent.loc
                d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
                n = (pn.noise3((p.x+r) / 4.0, y / 4.0, p.z / 4.0) + 1.0) / 2.0
                if (n >= d+.10):
                    self.parent.parent.setblock(p, materials.Sand)
                elif (n >= d):
                    self.parent.parent.setblock(p, materials.Gravel)
                else:
                    self.parent.parent.setblock(p, materials._floor)
            # Find button locations
            # h0
            if (halls[0] !=  0):
                for x in xrange(0, self.parent.halls[0].size - 2):
                    buttons.add(Vec(self.parent.halls[0].offset+1+x,
                                    y-1,
                                    self.parent.hallLength[0]))
            # h1
            if (halls[1] !=  0):
                for x in xrange(0, self.parent.halls[1].size - 2):
                    buttons.add(Vec(self.parent.parent.room_size-self.parent.hallLength[1]-1,
                                    y-1,
                                    self.parent.halls[1].offset+1+x))
            # h2
            if (halls[2] !=  0):
                for x in xrange(0, self.parent.halls[2].size - 2):
                    buttons.add(Vec(self.parent.halls[2].offset+1+x,
                                    y-1,
                                    self.parent.parent.room_size-self.parent.hallLength[2]-1))
            # h3
            if (halls[3] !=  0):
                for x in xrange(0, self.parent.halls[3].size - 2):
                    buttons.add(Vec(self.parent.hallLength[3],
                                    y-1,
                                    self.parent.halls[3].offset+1+x))
            for p in buttons:
                self.parent.parent.setblock(offset+p.down(1), mat)
                self.parent.parent.setblock(offset+p,
                                            materials.StonePressurePlate)
        # Draw the bridges, if a hallway exists.
        # h0 -> c1
        # h1 -> c2
        # h2 -> c3
        # h3 -> c4
        if (halls[0] !=  0):
            for p in iterate_cube(offset+h0,offset+c1):
                self.parent.parent.setblock(p, mat)
        if (halls[1] != 0):
            for p in iterate_cube(offset+h1,offset+c2):
                self.parent.parent.setblock(p, mat)
        if (halls[2] != 0):
            for p in iterate_cube(offset+h2,offset+c3):
                self.parent.parent.setblock(p, mat)
        if (halls[3] != 0):
            for p in iterate_cube(offset+h3,offset+c4):
                self.parent.parent.setblock(p, mat)
        # Draw the connecting bridges.
        # c1 -> c2
        # c2 -> c3
        # c3 -> c4
        for p in iterate_cube(offset+c1,offset+c2):
            self.parent.parent.setblock(p, mat)
        for p in iterate_cube(offset+c2,offset+c3):
            self.parent.parent.setblock(p, mat)
        for p in iterate_cube(offset+c3,offset+c4):
            self.parent.parent.setblock(p, mat)

# Catalog the floors we know about. 
_floors = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses if of floors.Blank
    if issubclass(obj, Blank):
        _floors[obj._name] = obj

def new (name, parent):
    '''Return a new instance of the floor of a given name. Supply the parent
    dungeon object.'''
    if name in _floors.keys():
        return _floors[name](parent)
    return Blank(parent)
