import sys
import inspect

import materials
import random
import perlin
from utils import Vec, Vec2f
import utils


class Blank(object):
    _name = 'blank'

    def __init__(self, parent):
        self.parent = parent

    def render(self):
        pass

    # Generic ruining used by multiple floors
    def ruinrender(self, ruinfactor = 2.0):
        c = self.parent.canvasCenter()
        y = self.parent.canvasHeight()
        r = random.randint(1, 1000)
        maxd = max(1, self.parent.canvasWidth(), self.parent.canvasLength())
        pn = perlin.SimplexNoise(256)
        for x in utils.iterate_points_inside_flat_poly(*self.parent.canvas):
            p = x + self.parent.loc
            d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
            n = (pn.noise3((p.x + r) / 4.0, y / 4.0, p.z / 4.0) + 1.0)
            n = n / ruinfactor
            if (n < d):
                self.parent.parent.setblock(p, materials._floor)
                self.parent.parent.blocks[p].data = 0


class Cobble(Blank):
    _name = 'cobble'
    ruin = False
    mat = materials.meta_mossycobble

    def render(self):
        if (utils.sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        for x in utils.iterate_points_inside_flat_poly(*self.parent.canvas):
            self.parent.parent.setblock(x + self.parent.loc, self.mat)
        # Ruined
        if (self.ruin):
            self.ruinrender()


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


class StoneTile(Blank):
    _name = 'stonetile'
    ruin = False
    stonetypes = (
        (materials.Granite, materials.PolishedGranite),
        (materials.Diorite, materials.PolishedDiorite),
        (materials.Andesite, materials.PolishedAndesite)
    )

    def render(self):
        mat = random.choice(self.stonetypes)
        if (utils.sum_points_inside_flat_poly(*self.parent.canvas) > 4):
            for x in utils.iterate_points_inside_flat_poly(
                *self.parent.canvas
            ):
                if ((x.x + x.z) & 1 == 1):
                    self.parent.parent.setblock(x + self.parent.loc, mat[0])
                else:
                    self.parent.parent.setblock(x + self.parent.loc, mat[1])
        # Ruined
        if (self.ruin):
            self.ruinrender()


class BrokenStoneTile(StoneTile):
    _name = 'brokenstonetile'
    ruin = True


class WoodTile(Blank):
    _name = 'woodtile'

    def render(self):
        if (utils.sum_points_inside_flat_poly(*self.parent.canvas) > 4):
            for x in utils.iterate_points_inside_flat_poly(
                *self.parent.canvas
            ):
                if ((x.x + x.z) & 1 == 1):
                    self.parent.parent.setblock(x + self.parent.loc,
                                                materials.Wood)
                else:
                    self.parent.parent.setblock(x + self.parent.loc,
                                                materials.OakWoodPlanks)


class MixedWoodTile(Blank):
    _name = 'mixedwoodtile'
    woodtypes = (
        materials.OakWoodPlanks,
        materials.SpruceWoodPlanks,
        materials.BirchWoodPlanks,
        materials.JungleWoodPlanks,
        materials.AcaciaWoodPlanks,
        materials.DarkOakWoodPlanks
    )

    def render(self):
        wood = random.sample(self.woodtypes, 2)
        if (utils.sum_points_inside_flat_poly(*self.parent.canvas) > 4):
            for x in utils.iterate_points_inside_flat_poly(
                *self.parent.canvas
            ):
                if ((x.x + x.z) & 1 == 1):
                    self.parent.parent.setblock(x + self.parent.loc, wood[0])
                else:
                    self.parent.parent.setblock(x + self.parent.loc, wood[1])


class RadialRug(Blank):
    _name = 'radialrug'
    ruin = False
    mat = materials.Wool
    colors = (
        (7, 8),       # dark grey / light grey
        (14, 0),      # red / white
        (11, 9),      # dark blue / cyan
        (1, 14),      # red / orange
        (7, 15),      # dark grey / black
        (11, 10),     # dark blue  / purple
        (12, 13),     # brown  / dark green
        (15, 13),     # black  / dark green
        (7, 8, 11),   # dark grey / light grey / dark blue
        (14, 0, 15),  # red / white / black
        (11, 14, 0),  # dark blue / orange / white
        (1, 4, 0),    # red / yellow / white
        (10, 4, 0),   # purple / yellow / white
    )
    _walk_weight = 5

    def render(self):
        if (utils.sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        color_profile = random.choice(self.colors)

        min_x = utils.floor(min([p.x for p in self.parent.canvas]))
        max_x = utils.ceil(max([p.x for p in self.parent.canvas]))
        min_z = utils.floor(min([p.z for p in self.parent.canvas]))
        max_z = utils.ceil(max([p.z for p in self.parent.canvas]))
        min_y = utils.floor(min([p.y for p in self.parent.canvas]))

        # Cut the canvas into quarters and fill one quarter with colors.
        # Then, copy that quarter into the other three quarters.
        width = utils.floor(((max_x - min_x + 1) + 1) / 2)
        depth = utils.floor(((max_z - min_z + 1) + 1) / 2)

        points = [[-1 for j in xrange(depth)] for i in xrange(width)]
        points_left = []
        for i in xrange(width):
            for j in xrange(depth):
                points_left.append((i, j))
        bounds = utils.Box(Vec(0, 0, 0), width, 1, depth)
        p = Vec(0, 0, 0)
        color_num = 0
        prev_dir = random.randint(0, 3)
        next_dir = random.randint(0, 3)
        while len(points_left) > 0:
            # pick random starting point and walk around the matrix
            point_index = random.randint(0, len(points_left) - 1)
            p = Vec(points_left[point_index][0],
                    0,
                    points_left[point_index][1])

            while (bounds.containsPoint(p) and
                   points[p.x][p.z] == -1 and
                   len(points_left) > 0):
                points[p.x][p.z] = color_num
                points_left.remove((p.x, p.z))

                # pick random direction to walk, try to keep walking same
                # direction
                if random.randint(0, self._walk_weight) != 0:
                    next_dir = prev_dir
                else:
                    while next_dir == prev_dir:
                        next_dir = random.randint(0, 3)
                if next_dir == 0:  # right
                    p += Vec(1, 0, 0)
                elif next_dir == 1:  # down
                    p += Vec(0, 0, 1)
                elif next_dir == 2:  # left
                    p += Vec(-1, 0, 0)
                else:  # up
                    p += Vec(0, 0, -1)
                prev_dir = next_dir
            color_num = (color_num + 1) % len(color_profile)

        for j in xrange(max_z - min_z + 1):
            for i in xrange(max_x - min_x + 1):
                p = self.parent.loc + Vec(min_x + i, min_y, min_z + j)
                self.parent.parent.setblock(p, self.mat)
                if i < width:
                    i_adj = i
                else:
                    i_adj = 2 * width - 1 - i
                if j < depth:
                    j_adj = j
                else:
                    j_adj = 2 * depth - 1 - j
                self.parent.parent.blocks[p].data = \
                    color_profile[points[i_adj][j_adj]]
        # Ruined
        if (self.ruin):
            self.ruinrender()


class BrokenRadialRug(RadialRug):
    _name = 'brokenradialrug'
    ruin = True


class RadialClay(RadialRug):
    _name = 'radialclay'
    mat = materials.WhiteStainedClay


class BrokenRadialClay(RadialRug):
    _name = 'brokenradialclay'
    mat = materials.WhiteStainedClay
    ruin = True


class CheckerRug(Blank):
    _name = 'checkerrug'
    ruin = False
    colors = (
        (7, 8),    # dark grey / light grey
        (9, 3),    # cyan / light blue
        # (14, 10), # red / purple
        (11, 9),   # dark blue / cyan
        (1, 14),   # red / orange
        (7, 15),   # dark grey / black
        # (3, 4),   # light blue  / yellow
        (11, 10),  # dark blue  / purple
        (12, 13),  # brown  / dark green
        (15, 13),  # black  / dark green
    )
    mat = materials.Wool

    def render(self):
        if (utils.sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        color = random.choice(self.colors)
        for x in utils.iterate_points_inside_flat_poly(*self.parent.canvas):
            self.parent.parent.setblock(x + self.parent.loc,
                                        self.mat)
            if ((x.x + x.z) & 1 == 1):
                self.parent.parent.blocks[x + self.parent.loc].data = color[0]
            else:
                self.parent.parent.blocks[x + self.parent.loc].data = color[1]
        # Runined
        if (self.ruin):
            self.ruinrender()


class BrokenCheckerRug(CheckerRug):
    _name = 'brokencheckerrug'
    ruin = True


class CheckerClay(CheckerRug):
    _name = 'checkerclay'
    mat = materials.WhiteStainedClay


class BrokenCheckerClay(CheckerRug):
    _name = 'brokencheckerclay'
    ruin = True
    mat = materials.WhiteStainedClay


class DoubleSlab(Blank):
    _name = 'doubleslab'
    ruin = False

    def render(self):
        if (utils.sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        for x in utils.iterate_points_inside_flat_poly(*self.parent.canvas):
            self.parent.parent.setblock(x + self.parent.loc,
                                        materials.StoneDoubleSlab)
        # Runined
        if (self.ruin):
            self.ruinrender()


class BrokenDoubleSlab(DoubleSlab):
    _name = 'brokendoubleslab'
    ruin = True


class Mosaic(Blank):
    _name = 'mosaic'
    ruin = False
    colours = (
        materials.LightBlueGlazedTerracotta,
        materials.YellowGlazedTerracotta,
        materials.GrayGlazedTerracotta,
        materials.LightGrayGlazedTerracotta,
        materials.CyanGlazedTerracotta,
        materials.PurpleGlazedTerracotta,
        materials.BlueGlazedTerracotta,
        materials.BrownGlazedTerracotta,
        materials.GreenGlazedTerracotta,
        materials.RedGlazedTerracotta,
        materials.BlackGlazedTerracotta
    )
    patterns = (
        [[0,2]],

        [[0,3],
         [1,2]],

        [[0,2],
         [1,3]],

        [[1,3],
         [2,0]],

        [[2,0,3,1],
         [0,0,3,3],
         [1,1,2,2],
         [3,1,2,0]],

        [[2,0,3,1],
         [0,2,1,3],
         [1,3,0,2],
         [3,1,2,0]]
    )

    def render(self):
        if (utils.sum_points_inside_flat_poly(*self.parent.canvas) > 4):
            block = random.choice(self.colours)
            pattern = random.choice(self.patterns)
            hmax = len(pattern)
            wmax = len(pattern[0])
            for x in utils.iterate_points_inside_flat_poly(
                *self.parent.canvas
            ):
                data = pattern[x.x%hmax][x.z%wmax]
                self.parent.parent.setblock(x + self.parent.loc, block, data)
            # Ruined
            if (self.ruin):
                self.ruinrender(3.0)


class BrokenMosaic(Mosaic):
    _name = 'brokenmosaic'
    ruin = True


class Mud(Blank):
    _name = 'mud'

    def render(self):
        pn = perlin.SimplexNoise(256)
        if (utils.sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        c = self.parent.canvasCenter()
        y = self.parent.canvasHeight()
        r = random.randint(1, 1000)
        maxd = max(1, self.parent.canvasWidth(), self.parent.canvasLength())
        for x in utils.iterate_points_inside_flat_poly(*self.parent.canvas):
            p = x + self.parent.loc
            d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
            n = (pn.noise3((p.x + r) / 4.0, y / 4.0, p.z / 4.0) + 1.0) / 2.0
            if (n >= d + .50):
                self.parent.parent.setblock(p, materials.Water)
            elif (n >= d + .30):
                self.parent.parent.setblock(p, materials.SoulSand)
            elif (n >= d + .20):
                self.parent.parent.setblock(p, materials.Farmland)
                self.parent.parent.blocks[p].data = random.randint(0, 1)
            elif (n >= d + .10):
                self.parent.parent.setblock(p, materials.Podzol)
                self.parent.parent.blocks[p].data = 2   # Podzol data val
            elif (n >= d):
                self.parent.parent.setblock(p, materials.Dirt)


class Sand(Blank):
    _name = 'sand'

    def render(self):
        pn = perlin.SimplexNoise(256)
        if (utils.sum_points_inside_flat_poly(*self.parent.canvas) <= 4):
            return
        c = self.parent.canvasCenter()
        y = self.parent.canvasHeight()
        r = random.randint(1, 1000)
        maxd = max(1, self.parent.canvasWidth(), self.parent.canvasLength())
        for x in utils.iterate_points_inside_flat_poly(*self.parent.canvas):
            p = x + self.parent.loc
            d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
            n = (pn.noise3((p.x + r) / 4.0, y / 4.0, p.z / 4.0) + 1.0) / 2.0
            if (n >= d + .20):
                self.parent.parent.setblock(p, materials.Sand)
            elif (n >= d + .10):
                self.parent.parent.setblock(p, materials.Sandstone)
            elif (n >= d):
                self.parent.parent.setblock(p, materials.Gravel)


class Bridges(Blank):
    _name = 'bridges'
    sandpit = False
    slabtypes = (
        materials.OakWoodSlab,
        materials.SpruceWoodSlab,
        materials.BirchWoodSlab,
        materials.JungleWoodSlab,
        materials.AcaciaWoodSlab,
        materials.DarkOakWoodSlab
    )

    def render(self):
        pn = perlin.SimplexNoise(256)
        # Find all the valid halls. These are halls with a size > 0.
        # We'll store a random position within the range of the hall.
        halls = [0, 0, 0, 0]
        hallcount = 0
        wires = set()
        #wirehooks = set()
        for h in xrange(4):
            if (self.parent.halls[h].size > 0):
                halls[h] = \
                    self.parent.halls[h].offset + 1 + \
                    random.randint(0, self.parent.halls[h].size - 3)
                hallcount += 1
        # We won't draw just half a bridge, unless this is a sandpit. (yet)
        if (hallcount < 2 and self.sandpit is False):
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
        h1 = Vec(self.parent.parent.room_size - self.parent.hallLength[1] - 1,
                 y,
                 z1)
        h2 = Vec(x2,
                 y,
                 self.parent.parent.room_size - self.parent.hallLength[2] - 1)
        h3 = Vec(self.parent.hallLength[3],
                 y,
                 z2)
        # Sandpit?
        mat = random.choice(self.slabtypes)
        if (self.sandpit is True):
            # Draw the false sand floor
            mat = materials.Sand
            c = self.parent.canvasCenter()
            y = self.parent.canvasHeight()
            r = random.randint(1, 1000)
            maxd = max(1,
                       self.parent.canvasWidth(),
                       self.parent.canvasLength())
            for x in utils.iterate_points_inside_flat_poly(
                *self.parent.canvas
            ):
                p = x + self.parent.loc
                d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
                n = (
                    pn.noise3(
                        (p.x + r) / 4.0,
                        y / 4.0,
                        p.z / 4.0) + 1.0) / 2.0
                if (n >= d + .10):
                    self.parent.parent.setblock(p, materials.Sand)
                elif (n >= d):
                    self.parent.parent.setblock(p, materials.Gravel)
                else:
                    self.parent.parent.setblock(p, materials._floor)
            # Find wire locations
            # h0
            # Cool fact: in 12w30c tripwires will trigger sand without hooks.
            if (halls[0] != 0):
                for x in xrange(1, self.parent.halls[0].size - 1):
                    p = Vec(self.parent.halls[0].offset + x,
                            y - 1,
                            self.parent.hallLength[0])
                    # if x == 0:
                    #    wirehooks.add((p, 4+3))
                    # elif x == self.parent.halls[0].size-1:
                    #    wirehooks.add((p, 4+1))
                    # else:
                    #    wires.add(p)
                    wires.add(p)
            # h1
            if (halls[1] != 0):
                for x in xrange(1, self.parent.halls[1].size - 1):
                    wires.add(
                        Vec(
                            (self.parent.parent.room_size -
                             self.parent.hallLength[1] - 1),
                            y - 1,
                            self.parent.halls[1].offset + x
                        )
                    )
            # h2
            if (halls[2] != 0):
                for x in xrange(1, self.parent.halls[2].size - 1):
                    wires.add(
                        Vec(
                            self.parent.halls[2].offset + x,
                            y - 1,
                            (self.parent.parent.room_size -
                             self.parent.hallLength[2] - 1)
                        )
                    )
            # h3
            if (halls[3] != 0):
                for x in xrange(1, self.parent.halls[3].size - 1):
                    wires.add(
                        Vec(
                            self.parent.hallLength[3],
                            y - 1,
                            self.parent.halls[3].offset + x
                        )
                    )
            for p in wires:
                self.parent.parent.setblock(
                    offset + p.down(1),
                    materials.Gravel,
                    lock=True
                )
                self.parent.parent.setblock(offset + p,
                                            materials.Tripwire, hide=True)
            # for p in wirehooks:
            #    self.parent.parent.setblock(offset+p[0].down(1), mat)
            #    self.parent.parent.setblock(offset+p[0],
            #                                materials.TripwireHook, p[1])
        # Draw the bridges, if a hallway exists.
        # h0 -> c1
        # h1 -> c2
        # h2 -> c3
        # h3 -> c4
        if (halls[0] != 0):
            for p in utils.iterate_cube(offset + h0, offset + c1):
                self.parent.parent.setblock(p, mat)
        if (halls[1] != 0):
            for p in utils.iterate_cube(offset + h1, offset + c2):
                self.parent.parent.setblock(p, mat)
        if (halls[2] != 0):
            for p in utils.iterate_cube(offset + h2, offset + c3):
                self.parent.parent.setblock(p, mat)
        if (halls[3] != 0):
            for p in utils.iterate_cube(offset + h3, offset + c4):
                self.parent.parent.setblock(p, mat)
        # Draw the connecting bridges.
        # c1 -> c2
        # c2 -> c3
        # c3 -> c4
        for p in utils.iterate_cube(offset + c1, offset + c2):
            self.parent.parent.setblock(p, mat)
        for p in utils.iterate_cube(offset + c2, offset + c3):
            self.parent.parent.setblock(p, mat)
        for p in utils.iterate_cube(offset + c3, offset + c4):
            self.parent.parent.setblock(p, mat)

# Catalog the floors we know about.
_floors = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses if of floors.Blank
    if issubclass(obj, Blank):
        _floors[obj._name] = obj


def new(name, parent):
    '''Return a new instance of the floor of a given name. Supply the parent
    dungeon object.'''
    if name in _floors.keys():
        return _floors[name](parent)
    return Blank(parent)
