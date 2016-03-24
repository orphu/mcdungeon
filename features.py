import sys
import inspect

import materials
import loottable
import items
import shop
from utils import *
import perlin
from pymclevel import nbt


class Blank(object):
    _name = 'blank'
    _is_stairwell = False
    _is_secret = False

    def __init__(self, parent):
        self.parent = parent

    def placed(self):
        pass

    def render(self):
        pass


class Entrance(Blank):
    _name = 'entrance'

    def placed(self):
        # Default height of the doors into the entrance.
        self.height = self.parent.parent.room_height
        self.high_height = self.parent.parent.room_height
        self.low_height = self.parent.parent.room_height
        # Height of the tower above entry.
        self.u = self.parent.parent.room_height * 2
        self.inwater = False

    def render(self):
        start = self.parent.loc.trans(6, self.parent.parent.room_height - 3, 6)
        wstart = start.trans(-1, 0, -1)
        # Clear air space
        for p in iterate_cube(wstart,
                              wstart.trans(5, -self.height, 5)):
            self.parent.parent.setblock(p, materials.Air)
        # Walls
        for p in iterate_four_walls(wstart,
                                    wstart.trans(5, 0, 5),
                                    self.height):
            self.parent.parent.setblock(p, materials._wall)
        # Lower level openings
        # W side
        for p in iterate_cube(wstart.trans(1, 0, 0), wstart.trans(4, -3, 0)):
            self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(wstart.trans(1, 0, 5), wstart.trans(4, -3, 5)):
            self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(wstart.trans(0, 0, 1), wstart.trans(0, -3, 4)):
            self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(wstart.trans(5, 0, 1), wstart.trans(5, -3, 4)):
            self.parent.parent.setblock(p, materials.Air)
        # Draw the staircase
        mat = materials.StoneSlab
        for p in iterate_spiral(Vec(0, 0, 0),
                                Vec(4, 0, 4),
                                self.height * 2 + 2):
            self.parent.parent.setblock(start.trans(p.x,
                                                    floor(float(p.y) / 2.0),
                                                    p.z),
                                        mat, mat.data + (p.y % 2) * 8)


class Stairwell(Blank):
    _name = 'stairwell'
    _is_stairwell = True

    def render(self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
            start = self.parent.loc.trans(
                5,
                self.parent.parent.room_height -
                3,
                5)
            # Clear a stairwell
            for x in iterate_cube(start.trans(0, 0, 1), start.trans(5, -5, 4)):
                self.parent.parent.setblock(x, materials.Air)
            mat = random.choice([
                (materials.StoneStairs, materials.meta_mossycobble),
                (materials.OakWoodStairs, materials.Wood),
                (materials.StoneBrickStairs, materials.meta_stonedungeon)
            ])
            # Draw the steps
            for x in xrange(6):
                for p in iterate_cube(start.trans(x, -x, 1),
                                      start.trans(x, -x, 4)):
                    self.parent.parent.setblock(p,
                                                mat[0])
                    self.parent.parent.setblock(p.trans(0, 1, 0),
                                                mat[1])


class TripleStairs(Blank):
    _name = 'triplestairs'
    _is_stairwell = True

    def render(self):
        # create a shortcut to the set block fN
        sb = self.parent.parent.setblock

        center = self.parent.canvasCenter()

        start = self.parent.loc.trans(5, self.parent.parent.room_height - 2, 5)
        start = start.trans(0, -6, 0)

        # handrail
        for x in iterate_four_walls(start.trans(-1, -1, -1), start.trans(6, -1, 6), 0):
            sb(x, materials.IronBars, 0)
        sb(start.trans(2, -1, -1), materials.Air, 0)
        sb(start.trans(3, -1, -1), materials.Air, 0)

        # add a random deco object at the top
        decos = ((materials.Cauldron, 2),
                 (materials.Torch, 5),
                 (materials.FlowerPot, 10),
                 (materials.StoneDoubleSlab, 0),
                 (materials.Air, 0))

        deco = random.choice(decos)

        sb(start.trans(1, -1, 1), deco[0], deco[1])
        sb(start.trans(4, -1, 1), deco[0], deco[1])

        # using the following materials...
        mats = [
            (materials.Air, 0),  # 0
            (materials.StoneBrick, 0),  # 1
            (materials.StoneBrickStairs, 6),  # 2 upside down ascending south
            (materials.StoneBrickStairs, 0),  # 3 ascending east
            (materials.StoneBrickStairs, 1),  # 4 ascending west
            (materials.StoneBrickStairs, 3),  # 5 ascending north
            (materials.StoneBrickStairs, 7),  # 6 upside down ascending north
            (materials.Torch, 3)  # 7
        ]

        #...create the stairs
        template = [
            [[0, 3, 1, 1, 4, 0],
             [0, 1, 5, 5, 1, 0],
             [0, 7, 0, 0, 7, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [2, 2, 2, 2, 2, 2]],

            [[1, 1, 1, 1, 1, 1],
             [5, 6, 1, 1, 6, 5],
             [0, 0, 5, 5, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0]],

            [[1, 1, 1, 1, 1, 1],
             [1, 0, 1, 1, 0, 1],
             [5, 0, 1, 1, 0, 5],
             [0, 0, 5, 5, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0]],

            [[1, 1, 1, 1, 1, 1],
             [1, 0, 1, 1, 0, 1],
             [1, 0, 1, 1, 0, 1],
             [5, 0, 1, 1, 0, 5],
             [0, 0, 5, 5, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0]],

            [[1, 1, 1, 1, 1, 1],
             [1, 5, 1, 1, 5, 1],
             [1, 0, 1, 1, 0, 1],
             [1, 0, 1, 1, 0, 1],
             [5, 0, 1, 1, 0, 5],
             [0, 0, 5, 5, 0, 0],
             [0, 0, 0, 0, 0, 0]],

            [[1, 1, 1, 1, 1, 1],
             [1, 1, 1, 1, 1, 1],
             [1, 0, 1, 1, 0, 1],
             [1, 0, 1, 1, 0, 1],
             [1, 0, 1, 1, 0, 1],
             [5, 0, 1, 1, 0, 5],
             [0, 0, 5, 5, 0, 0]]
        ]
        # place the stuff
        for y in xrange(6):
            for x in xrange(6):
                for z in xrange(7):
                    sb(start.trans(x, y, z),
                        mats[template[y][z][x]][0],
                        mats[template[y][z][x]][1])


class TowerWithLadder(Blank):
    _name = 'towerwithladder'
    _is_stairwell = True

    def render(self):
        # create a shortcut to the set block fN
        sb = self.parent.parent.setblock

        center = self.parent.canvasCenter()

        start = self.parent.loc.trans(5, self.parent.parent.room_height - 2, 5)
        start = start.trans(0, -6, 0)

        mats = [
            (materials.Air, 0),  # 0
            (materials.StoneBrick, 0),  # 1
            (materials.Ladder, 3),  # 2 facing south
            (materials.Ladder, 2),  # 3 facing north
            (materials.StoneBrickStairs, 6),  # 4 upside down ascending south
            (materials.StoneBrickStairs, 7),  # 5 upside down ascending north
            (materials.IronBars, 0)  # 6
        ]

        template = [
            [0, 1, 1, 1, 1, 0],
            [1, 0, 2, 2, 0, 1],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 1],
            [0, 1, 6, 6, 1, 0]]

        top = [
            [0, 1, 1, 1, 1, 0],
            [1, 0, 2, 2, 0, 1],
            [5, 0, 0, 0, 0, 5],
            [4, 0, 0, 0, 0, 4],
            [1, 0, 0, 0, 0, 1],
            [0, 1, 1, 1, 1, 0]]

        # place the stuff
        for y in xrange(2):
            for x in xrange(6):
                for z in xrange(6):
                    sb(start.trans(x, y * 6 - 1, z),
                       mats[template[z][x]][0],
                       mats[template[z][x]][1])
                    sb(start.trans(x, y * 6 - 2, z),
                       mats[template[z][x]][0],
                       mats[template[z][x]][1])
                    sb(start.trans(x, y * 6 - 3, z),
                       mats[top[z][x]][0],
                       mats[top[z][x]][1])

        # finish ladder
        for x in iterate_cube(start.trans(2, 0, 1), start.trans(3, 2, 1)):
            sb(x, materials.Ladder, 3)


class Scaffolding(Blank):
    _name = 'scaffolding'
    _is_stairwell = True

    def render(self):
        # create a shortcut to the set block fN
        sb = self.parent.parent.setblock

        start = self.parent.loc.trans(5, self.parent.parent.room_height - 2, 5)
        start = start.trans(0, -7, 0)

        mats = [
            (materials.Air, 0),  # 0
            (materials.Fence, 0),  # 1
            (materials.OakWoodSlab, 0),  # 2
            (materials.OakWoodStairs, 0),  # 3 Acending East
            (materials.OakWoodStairs, 3)  # 4 Ascending North
        ]

        template = [
            [[0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 1],
             [1, 0, 0, 0, 0, 1],
             [1, 0, 0, 0, 0, 1],
             [1, 1, 1, 1, 1, 1]],

            [[0, 0, 0, 0, 2, 2],
                [0, 0, 0, 0, 2, 2],
                [0, 0, 0, 0, 0, 1],
                [1, 0, 0, 0, 0, 1],
                [1, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1]],

            [[0, 0, 0, 3, 1, 1],
                [0, 0, 0, 3, 1, 1],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 1]],

            [[2, 2, 3, 1, 1, 1],
                [2, 2, 3, 1, 1, 1],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 1]],

            [[1, 1, 1, 0, 0, 0],
                [1, 1, 1, 0, 0, 0],
                [4, 4, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 1]],

            [[1, 1, 1, 0, 0, 0],
                [1, 1, 1, 0, 0, 0],
                [1, 1, 0, 0, 0, 0],
                [4, 4, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 1]],

            [[1, 1, 1, 0, 0, 0],
                [1, 1, 1, 0, 0, 0],
                [1, 1, 0, 0, 0, 0],
                [1, 1, 0, 0, 0, 0],
                [4, 4, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 1]],
        ]

        # place the stuff
        for y in xrange(7):
            for x in xrange(6):
                for z in xrange(6):
                    sb(start.trans(x, y, z),
                       mats[template[y][z][x]][0],
                       mats[template[y][z][x]][1])


class Chasm(Blank):
    _name = 'chasm'
    material = materials.Air
    depth = 2

    def render(self):
        if (self.parent.canvasWidth() < 4 or
                self.parent.canvasLength() < 4):
            return
        # We'll render across the whole block, since that will look cool
        y = self.parent.canvasHeight()
        flip = random.randint(0, 1)
        for x in xrange(2, self.parent.parent.room_size * self.parent.size.x - 2):
            if (flip == 1):
                for p in iterate_cube(self.parent.loc +
                                      Vec(self.parent.parent.room_size * self.parent.size.x - x - 1,
                                          y,
                                          x + random.randint(-1, 0)),
                                      self.parent.loc +
                                      Vec(self.parent.parent.room_size * self.parent.size.x - x - 1,
                                          y + self.depth,
                                          x + random.randint(1, 2))
                                      ):
                    self.parent.parent.setblock(p, self.material)
            else:
                for p in iterate_cube(self.parent.loc +
                                      Vec(x,
                                          y,
                                          x + random.randint(-1, 0)),
                                      self.parent.loc +
                                      Vec(x,
                                          y + self.depth,
                                          x + random.randint(1, 2))
                                      ):
                    self.parent.parent.setblock(p, self.material)


class LavaChasm(Chasm):
    _name = 'lavachasm'
    material = materials.Lava
    depth = 0


class River(Chasm):
    _name = 'river'
    material = materials.Water
    depth = 0


class Columns(Blank):
    _name = 'columns'

    mats = (
        materials.Stone,
        materials.Wood,
        materials.Spruce,
        materials.Jungle,
        materials.Acacia,
        materials.DarkOak,
        materials.ChiseledSandstone,
        materials.SmoothSandstone,
        materials.ChiseledRedSandstone,
        materials.SmoothRedSandstone,
        materials.StoneDoubleSlab,
        materials.Obsidian,
        materials.StoneBrick,
        materials.meta_mossycobblewall,
        materials.meta_mossystonebrick,
        materials.meta_stonedungeon,
        materials.IronBars,
        materials.Fence,
        materials.NetherBrick,
        materials.NetherBrickFence,
        materials.Glowstone,
        materials.Prismarine,
        materials.PrismarineBricks,
        materials.DarkPrismarine
    )

    def render(self):
        limit = int(min(self.parent.canvasWidth(), self.parent.canvasLength()))
        if (limit < 6):
            return
        c = self.parent.canvasCenter()
        height = self.parent.canvasHeight() - 1
        start = random.randint(0, limit / 2 - 1)
        stop = limit / 2
        step = random.randint(2, 3)
        mat = random.choice(self.mats)
        for x in xrange(start, stop, step):
            for p in iterate_cube(Vec(c.x - x, 1, c.z - x),
                                  Vec(c.x - x, height, c.z - x)):
                self.parent.parent.setblock(self.parent.loc + p, mat)
            for p in iterate_cube(Vec(c.x + x + 1, 1, c.z - x),
                                  Vec(c.x + x + 1, height, c.z - x)):
                self.parent.parent.setblock(self.parent.loc + p, mat)
            for p in iterate_cube(Vec(c.x - x, 1, c.z + x + 1),
                                  Vec(c.x - x, height, c.z + x + 1)):
                self.parent.parent.setblock(self.parent.loc + p, mat)
            for p in iterate_cube(Vec(c.x + x + 1, 1, c.z + x + 1),
                                  Vec(c.x + x + 1, height, c.z + x + 1)):
                self.parent.parent.setblock(self.parent.loc + p, mat)


class Arcane(Blank):
    _name = 'arcane'

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        # Custom block placer. Don't place stuff where things already exist,
        # also check for things we aren't alowed to place stuff on.
        dun = self.parent.parent

        def sb(p, mat):
            if (p in dun.blocks and
                    dun.blocks[p].material == materials.Air and
                    dun.blocks[p.down(1)].material != materials.Farmland and
                    dun.blocks[p.down(1)].material != materials.SoulSand and
                    dun.blocks[p.down(1)].material != materials.Water and
                    dun.blocks[p.down(1)].material != materials.Lava and
                    dun.blocks[p.down(1)].material != materials.CobblestoneSlab and
                    dun.blocks[p.down(1)].material != materials.StillWater):
                dun.setblock(p, mat)
        mode = random.choice(['one', 'boxes', 'conc'])

        if mode == 'boxes':
            center = self.parent.canvasCenter()
            o = self.parent.loc + Vec(center.x,
                                      self.parent.canvasHeight() - 1,
                                      center.z)
            o = o + Vec(-self.parent.canvasWidth() / 2,
                        0,
                        -self.parent.canvasLength() / 2)
            for x in xrange(self.parent.canvasWidth() / 3 + 1):
                for z in xrange(self.parent.canvasLength() / 3 + 1):
                    if random.random() < 0.5:
                        q = Vec(o.x + x * 3, o.y, o.z + z * 3)
                        sb(q, materials.RedstoneWire)
                        sb(q.trans(1, 0, 0), materials.RedstoneWire)
                        sb(q.trans(0, 0, 1), materials.RedstoneWire)
                        sb(q.trans(1, 0, 1), materials.RedstoneWire)
            return

        if mode == 'conc':
            center = self.parent.canvasCenter()
            c = self.parent.loc + Vec(center.x,
                                      self.parent.canvasHeight() - 1,
                                      center.z)
            sb(c, materials.RedstoneWire)
            for p in iterate_ellipse(c.trans(-2, 0, -2), c.trans(2, 0, 2)):
                sb(p, materials.RedstoneWire)
            for p in iterate_ellipse(c.trans(-4, 0, -4), c.trans(4, 0, 4)):
                sb(p, materials.RedstoneWire)
            return

        center = self.parent.canvasCenter()
        c = self.parent.loc + Vec(center.x,
                                  self.parent.canvasHeight() - 1,
                                  center.z)
        for p in iterate_cube(c.n(4), c.s(4)):
            sb(p, materials.RedstoneWire)
        for p in iterate_cube(c.e(4), c.w(4)):
            sb(p, materials.RedstoneWire)
        for p in iterate_four_walls(c.trans(-2, 0, -2), c.trans(2, 0, 2), 0):
            sb(p, materials.RedstoneWire)


class Mushrooms(Blank):
    _name = 'mushrooms'

    def render(self):
        if (self.parent.canvasWidth() < 2 or self.parent.canvasLength() < 2):
            return

        # Custom block placer. Don't place stuff where things already exist,
        # also check for things we aren't alowed to place stuff on.
        # Picks red or brown mushrooms randomly if no material is supplied.
        dun = self.parent.parent

        def sb(p, mat=''):
            if (p in dun.blocks and
                    dun.blocks[p].material == materials.Air and
                    dun.blocks[p.down(1)].material != materials.Farmland and
                    dun.blocks[p.down(1)].material != materials.SoulSand and
                    dun.blocks[p.down(1)].material != materials.Water and
                    dun.blocks[p.down(1)].material != materials.StillWater):
                if mat == '':
                    mat = random.choice([materials.RedMushroom,
                                         materials.BrownMushroom,
                                         materials.Air])
                dun.setblock(p, mat)

        mode = random.choice(['perlin', 'fairyring'])
        if mode == 'perlin':
            pn = perlin.SimplexNoise(256)
            r = random.randint(1, 1000)
            for p in iterate_points_inside_flat_poly(*self.parent.canvas):
                if (pn.noise3(p.x / 4.0, r / 4.0, p.z / 4.0) > .8):
                    q = p + self.parent.loc
                    sb(q.trans(1, -1, 0))
                    sb(q.trans(-1, -1, 0))
                    sb(q.trans(0, -1, -1))
                    sb(q.trans(0, -1, 1))
            return

        if mode == 'fairyring':
            center = self.parent.canvasCenter()
            c = self.parent.loc + Vec(center.x,
                                      self.parent.canvasHeight() - 1,
                                      center.z)
            radius = random.randint(2, 5)
            for p in iterate_ellipse(c.trans(-radius, 0, -radius),
                                     c.trans(radius, 0, radius)):
                sb(p)
            return


class MessHall(Blank):
    _name = 'messhall'

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return
        sb = self.parent.parent.setblock
        # Draw tables. cram several in the room if it is large enough.
        for x in xrange(self.parent.size.x):
            for z in xrange(self.parent.size.z):
                rp = self.parent.pos + Vec(x, 0, z)
                if (self.parent.parent.rooms[rp].features[0]._is_stairwell is False and
                        self.parent.parent.rooms[rp].features[0]._name is not 'blank'):
                    p = self.parent.loc + Vec(
                        x * self.parent.parent.room_size,
                        self.parent.canvasHeight() - 1,
                        z * self.parent.parent.room_size)
                    for q in iterate_cube(p + Vec(5, 0, 7), p + Vec(10, 0, 8)):
                        sb(q, materials.Fence)
                        sb(q.up(1), materials.WoodenPressurePlate)
                    # Seating
                    q = p + Vec(5, 0, 6)
                    o = random.randint(0, 1)
                    while o <= 5:
                        sb(q.e(o), materials.OakWoodStairs, 3)
                        o += random.randint(2, 3)
                    q = p + Vec(5, 0, 9)
                    o = random.randint(0, 1)
                    while o <= 5:
                        sb(q.e(o), materials.OakWoodStairs, 2)
                        o += random.randint(2, 3)

        # If the room is 1x1, stop here.
        if (self.parent.size.x < 2 and self.parent.size.z < 2):
            return
        # Draw a fire pit in the middle
        center = self.parent.canvasCenter()
        size = 2
        p0 = Vec(center.x - size / 2 + 1,
                 self.parent.canvasHeight(),
                 center.z - size / 2 + 1) + self.parent.loc
        p1 = p0.trans(size - 1, 0, size - 1)
        for p in iterate_disc(p0 + Vec(-2, 0, -2), p1 + Vec(2, 0, 2)):
            sb(p, materials._floor)
            sb(p.up(1), materials.IronBars)
        for p in iterate_disc(p0, p1):
            sb(p, materials.Netherrack)
            sb(p.up(1), materials.Fire)


class Dais(Blank):
    _name = 'dais'

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return
        center = self.parent.canvasCenter()
        size = random.randint(4,
                              min(self.parent.canvasWidth(),
                                  self.parent.canvasLength()) - 4)
        torches = (random.random() < .5)
        platform = random.choice([materials.meta_mossycobble,
                                  materials.meta_mossystonebrick,
                                  materials.meta_stonedungeon,
                                  materials.Stone,
                                  materials.StoneBrick])
        steps = random.choice([materials.CobblestoneSlab,
                               materials.StoneSlab,
                               materials.StoneBrickSlab])
        pfunc = iterate_cube
        sfunc = iterate_four_walls
        if (random.random() < .5):
            pfunc = iterate_disc
            sfunc = iterate_tube

        p0 = Vec(center.x - size / 2 + 1,
                 self.parent.canvasHeight(),
                 center.z - size / 2 + 1) + self.parent.loc
        p1 = p0.trans(size - 1, 0, size - 1)

        if torches:
            for p in (Vec(p0.x + 1, p0.y - 1, p0.z + 1), Vec(p1.x - 1, p0.y - 1, p1.z - 1),
                      Vec(p0.x + 1, p0.y - 1, p1.z - 1), Vec(p1.x - 1, p0.y - 1, p0.z + 1)):
                self.parent.parent.setblock(p, materials.Fence)
                self.parent.parent.setblock(p.up(1), materials.Fence)
                self.parent.parent.setblock(p.up(2), materials.Torch, 5)
        for p in pfunc(p0, p1):
            self.parent.parent.setblock(p.up(1), platform)
        for p in sfunc(p0, p1, 0):
            if self.parent.parent.blocks[p.up(2)].material != materials.Fence:
                self.parent.parent.setblock(p.up(1), steps)


class SecretRoom(Blank):
    _name = 'secretroom'
    _is_secret = True

    def placed(self):
        self.parent._pistontrap = False

    def renderSecretPost(self):
        # Hide the room from maps.
        self.hideRoom()

    def hideRoom(self):
        '''Hide all the blocks in this chunk so that they don't show up on
        maps'''
        d = self.parent.parent
        for p in iterate_cube(self.parent.loc,
                              self.parent.loc + Vec(d.room_size - 1,
                                                    d.room_height - 1,
                                                    d.room_size - 1)):
            if p in d.blocks:
                d.blocks[p].blank=True

    def render(self):
        sb = self.parent.parent.setblock

        # Reform the basic room shape.
        for p in iterate_cube(self.parent.loc,
                              self.parent.loc + Vec(self.parent.parent.room_size - 1,
                                                    self.parent.parent.room_height - 2,
                                                    self.parent.parent.room_size - 1)):
            # Remove all blocks.
            sb(p, None)
            # Clear out any doors or extra torches.
            if p in self.parent.parent.doors:
                del(self.parent.parent.doors[p])
            if p in self.parent.parent.torches:
                del(self.parent.parent.torches[p])

        self.c1 = self.parent.loc + Vec(3,
                                        self.parent.parent.room_height - 2,
                                        3)
        self.c3 = self.parent.loc + Vec(self.parent.parent.room_size - 4,
                                        self.parent.parent.room_height - 2,
                                        self.parent.parent.room_size - 4)

        for q in iterate_cube(self.c1.up(1), self.c3.up(3)):
            sb(q, materials.Air)
        for q in iterate_cube(self.c1.up(4), self.c3.up(4)):
            sb(q, materials._ceiling)
        for q in iterate_cube(self.c1, self.c3):
            sb(q, materials._floor)
        for q in iterate_four_walls(self.c1, self.c3, self.parent.parent.room_height - 2):
            sb(q, materials._wall)

        # Fix the hallway and create the secret door mechansm.
        # Find the direction, room, and connecting room.
        # room = this room
        # d = direction out of this room
        # offset = offset of the hallways
        # oroom = connecting room
        # od = direction out of the connecting room
        # length = legth of the opposite hall

        o = self.parent.loc.trans(2, 0, 2)
        # hall positions to grid direction
        dirs = {3: Vec(-1, 0, 0),
                1: Vec(1, 0, 0),
                2: Vec(0, 0, 1),
                0: Vec(0, 0, -1)}

        room = self.parent
        d = 0
        for x in xrange(4):
            if room.halls[x]._name != 'blank':
                d = x
        offset = room.halls[d].offset
        oroom = self.parent.parent.rooms[room.pos + dirs[d]]
        od = (d + 2) % 4
        length = oroom.hallLength[od] - 2

        # Save d for any inherited secret rooms.
        self.direction = d

        # Figure our our deltas. There are 8 possibilities based on direction
        # and offset. Offset will basically mirror across width.
        # dw = delta width
        # dl = delta length
        # spos = start pos for the mechanism

        # d = 0 (West)
        if d == 0:
            dw = Vec(1, 0, 0)
            dl = Vec(0, 0, -1)
            spos = o.trans(offset, 0, 0)
        # d = 1 (South)
        elif d == 1:
            dw = Vec(0, 0, 1)
            dl = Vec(1, 0, 0)
            spos = o.trans(11, 0, offset)
        # d = 2 (East)
        elif d == 2:
            dw = Vec(1, 0, 0)
            dl = Vec(0, 0, 1)
            spos = o.trans(offset, 0, 11)
        # d = 3 (North)
        else:
            dw = Vec(0, 0, 1)
            dl = Vec(-1, 0, 0)
            spos = o.trans(0, 0, offset)
        if offset >= 7:
            dw = dw * -1
            if (d == 0 or d == 2):
                spos = spos.trans(-2, 0, 0)
            elif (d == 1 or d == 3):
                spos = spos.trans(0, 0, -2)

        # Position the start block for the mechanism
        spos = spos + dl * length - dw * 2

        if self.parent.parent.args.debug:
            print
            print 'room:', room.pos
            print 'dir:', d
            print 'offset:', offset
            print 'dl:', dl
            print 'dw:', dw
            print

        mats = [
            [materials.Air, 0],                  # 0 (ignore these)
            [materials.Air, 0],                  # 1
            [materials._wall, 0],                # 2
            [materials.Stone, 0],                # 3
            [materials._wall, 0],                # 4
            [materials.RedstoneWire, 0],         # 5
            [materials.StickyPiston, 3],         # 6 - toggle piston
            [materials.RedstoneTorchOn, 2],      # 7
            [materials._ceiling, 0],             # 8
            [materials.StickyPiston, 4],         # 9 - pusher piston
            [materials.RedstoneRepeaterOff, 3],  # 10 - piston repeater
            [materials.RedstoneRepeaterOff, 7],  # 11 - toggle repeater
            [materials.Glowstone, 0],            # 12
            [materials._secret_door, 0],         # 13
            [materials._floor, 0],               # 14
            [materials._subfloor, 0]             # 15
        ]

        template = [
            [[8, 8, 8, 8, 8],
             [8, 8, 8, 12, 8],
             [8, 8, 8, 8, 8],
             [8, 8, 8, 8, 8],
             [8, 8, 8, 8, 8],
             [8, 8, 8, 8, 8]],
            [[2, 4, 4, 4, 4],
             [1, 1, 1, 1, 4],
             [2, 4, 4, 4, 4],
             [2, 1, 1, 1, 4],
             [2, 1, 1, 1, 4],
             [2, 1, 1, 1, 4]],
            [[2, 4, 4, 4, 4],
             [1, 7, 1, 1, 13],
             [2, 4, 6, 1, 4],
             [2, 11, 9, 9, 4],
             [2, 5, 10, 10, 4],
             [2, 5, 5, 5, 4]],
            [[2, 4, 4, 4, 4],
             [1, 1, 1, 1, 13],
             [2, 4, 6, 1, 4],
             [2, 3, 9, 9, 4],
             [2, 3, 3, 3, 4],
             [2, 3, 3, 3, 4]],
            [[14, 14, 14, 14, 14],
             [14, 14, 14, 14, 14],
             [14, 14, 14, 14, 14],
             [14, 14, 14, 14, 14],
             [14, 14, 14, 14, 14],
             [14, 14, 14, 14, 14]],
            [[15, 15, 15, 15, 15],
             [15, 15, 15, 15, 15],
             [15, 15, 15, 15, 15],
             [15, 15, 15, 15, 15],
             [15, 15, 15, 15, 15],
             [15, 15, 15, 15, 15]],
        ]
        bdata = 3

        # Data adjustments for directions. There are 8, but the defaults are
        # for East, low offset.

        # West
        if d == 0:
            bdata = 4
            if offset >= 7:
                mats[6][1] = 2
                mats[7][1] = 1
                mats[9][1] = 5
                mats[10][1] = 1
                mats[11][1] = 5
            else:
                mats[6][1] = 2

        # South
        if d == 1:
            bdata = 1
            if offset >= 7:
                mats[6][1] = 5
                mats[7][1] = 3
                mats[9][1] = 3
                mats[10][1] = 2
                mats[11][1] = 6
            else:
                mats[6][1] = 5
                mats[7][1] = 4
                mats[9][1] = 2
                mats[10][1] = 0
                mats[11][1] = 4

        # East, flipped
        if (d == 2 and offset >= 7):
            # flip the pusher piston
            mats[7][1] = 1
            mats[9][1] = 5
            mats[10][1] = 1
            mats[11][1] = 5

        # North
        if d == 3:
            bdata = 2
            if offset >= 7:
                mats[6][1] = 4
                mats[7][1] = 3
                mats[9][1] = 3
                mats[10][1] = 2
                mats[11][1] = 6
            else:
                mats[6][1] = 4
                mats[7][1] = 4
                mats[9][1] = 2
                mats[10][1] = 0
                mats[11][1] = 4

        # Draw the mechanism
        for y in xrange(6):
            for w in xrange(6):
                for l in xrange(5):
                    p = spos + dl * l + dw * w + Vec(0, 1, 0) * y
                    sb(p,
                       mats[template[y][w][l]][0],
                       mats[template[y][w][l]][1],
                       blank=(l != 4)
                      )

        # The button.
        p = spos + dl * 3 + dw * 5 + Vec(0, 1, 0) * 2
        blocks = self.parent.parent.blocks
        while (p + dl) not in blocks or blocks[p + dl].material != materials.Air:
            sb(p.up(1), materials.Air, hide=True)
            sb(p, materials.RedstoneWire, hide=True)
            sb(p.down(1), materials.Stone, blank=True)
            p = p + dl
        sb(p, materials._wall, lock=True)
        sb(p + dl, materials.StoneButton, bdata)

        # Extend the hallway into the room.
        o = spos + dw
        p = o - dl * (length + 1) + Vec(0, 4, 0)
        for q in iterate_cube(o, p):
            sb(q - dw, materials._wall, lock=True)
            if q.y == o.y:
                sb(q, materials._ceiling)
            elif q.y == p.y:
                sb(q, materials._floor)
            else:
                sb(q, materials.Air, lock=True)
                sb(q - dl, materials.Air, lock=True)
            sb(q + dw, materials._wall, lock=True)

        # Clear out any additional doors or extra torches in the hall.
        for q in iterate_cube(o + dw * 2 + dl * 5, p - dw - dl):
            if q in self.parent.parent.doors:
                del(self.parent.parent.doors[q])
            if q in self.parent.parent.torches:
                del(self.parent.parent.torches[q])

        # Kill the canvas to prevent spawners and chests from appearing
        self.parent.canvas = (
            Vec(0, 0, 0),
            Vec(0, 0, 0),
            Vec(0, 0, 0))

        # Call the room post-renderer.
        self.renderSecretPost()


class SecretStudy(SecretRoom):
    _name = 'secretstudy'

    def renderSecretPost(self):
        sb = self.parent.parent.setblock
        blocks = self.parent.parent.blocks

        # Bookshelves
        for p in iterate_four_walls(Vec(1, -1, 1), Vec(8, -1, 8), 2):
            if (p.x not in (3, 6) and
                    p.z not in (3, 6)):
                sb(self.c1 + p, materials.Bookshelf)
            else:
                sb(self.c1 + p, materials.Air)

        # Framed study stuff
        loot = weighted_choice((("clock", 4),
                                ("written book", 1),
                                ("custom painting", 1)))
        sb(self.c1 + Vec(2, -3, 1), materials._wall)
        self.parent.parent.addentity(
            get_entity_other_tags("ItemFrame",
                                  Pos=self.c1 + Vec(2, -3, 1),
                                  Facing="S",
                                  ItemTags=self.parent.parent.inventory.buildFrameItemTag(loot)
                                  )
        )

        # Lighting
        for p in (Vec(2, -1, 2), Vec(2, -1, 7),
                  Vec(7, -1, 2), Vec(7, -1, 7)):
            sb(self.c1 + p, materials.Fence)
            sb(self.c1 + p.up(1), materials.Torch, 5)

        # Desk
        mats = [
            (materials.Air, 0),          # 0
            (materials.OakWoodStairs, 7),  # 1
            (materials.Chest, 0),        # 2
            (materials.CraftingTable, 0),  # 3
            (materials.WallSign, 0),     # 4
            (materials.OakWoodStairs, 0),  # 5
            (materials.OakWoodStairs, 6),  # 6
        ]
        template = [
            [3, 1, 6, 2],
            [0, 4, 5, 4]
        ]
        oo = self.c1.trans(4, -1, 3)
        for x in xrange(2):
            for z in xrange(4):
                p = oo.trans(x, 0, z)
                sb(p,
                   mats[template[x][z]][0],
                   mats[template[x][z]][1])
        self.parent.parent.blocks[self.c1 + Vec(5, -1, 4)].data = 2
        self.parent.parent.blocks[self.c1 + Vec(5, -1, 5)].data = 0
        self.parent.parent.blocks[self.c1 + Vec(5, -1, 6)].data = 3

        if (random.random() < 0.1):
            sb(self.c1.trans(4, -2, 4), materials.Cake, random.randrange(0, 6))
        elif (random.random() < 0.4):
            sb(self.c1.trans(4, -2, 4),
               materials.FlowerPot, random.randrange(1, 12))
        else:
            sb(self.c1.trans(4, -2, 4), materials.Torch, 5)

        # A chest in a study should have writing supplies :)
        # item, probability, max stack amount
        writing_items = [(items.byName('written book'), 1, 1),
                         (items.byName('written book'), 0.3, 1),
                         (items.byName('written book'), 0.2, 1),
                         (items.byName('book'), 0.7, 5),
                         (items.byName('paper'), 0.8, 10),
                         (items.byName('ink sac'), 0.9, 5),
                         (items.byName('feather'), 0.9, 10),
                         (items.byName('leather'), 0.4, 5),
                         (items.byName('apple'), 0.2, 1)]
        # Generate desk loot and place chest
        deskloot = []
        for s in writing_items:
            if (random.random() < s[1]):
                amount = random.randint(1, min(s[2], s[0].maxstack))
                deskloot.append(
                    loottable.Loot(
                        len(deskloot),
                        amount,
                        s[0].value,
                        s[0].data,
                        '',
                        flag=s[0].flag))
        self.parent.parent.addchest(self.c1.trans(4, -1, 6), loot=deskloot)

        self.parent.parent.cobwebs(self.c1.up(4), self.c3)

        # Hide the room from maps.
        self.hideRoom()

class SecretAlchemyLab(SecretRoom):
    _name = 'secretalchemylab'

    def renderSecretPost(self):
        sb = self.parent.parent.setblock
        blocks = self.parent.parent.blocks

        # Bookshelves
        for p in iterate_four_walls(Vec(1, -1, 1), Vec(8, -1, 8), 2):
            if (p.x not in (3, 6) and
                    p.z not in (3, 6)):
                sb(self.c1 + p, materials.Bookshelf)
            else:
                sb(self.c1 + p, materials.Air)

        # Lighting
        for p in (Vec(2, -1, 2), Vec(2, -1, 7),
                  Vec(7, -1, 2), Vec(7, -1, 7)):
            sb(self.c1 + p, materials.Fence)
            sb(self.c1 + p.up(1), materials.Torch, 5)

        # Desk
        mats = [
            (materials.Air, 0),          # 0
            (materials.OakWoodStairs, 7),  # 1
            (materials.Chest, 0),        # 2
            (materials.CraftingTable, 0),  # 3
            (materials.WallSign, 0),     # 4
            (materials.OakWoodStairs, 0),  # 5
            (materials.OakWoodStairs, 6),  # 6
            (materials.OakWoodSlab, 8)    # 7
        ]
        template = [
            [1, 7, 6, 2],
            [4, 5, 4, 0]
        ]
        oo = self.c1.trans(4, -1, 3)
        for x in xrange(2):
            for z in xrange(4):
                p = oo.trans(x, 0, z)
                sb(p,
                   mats[template[x][z]][0],
                   mats[template[x][z]][1])
        self.parent.parent.blocks[self.c1 + Vec(5, -1, 3)].data = 2
        self.parent.parent.blocks[self.c1 + Vec(5, -1, 4)].data = 0
        self.parent.parent.blocks[self.c1 + Vec(5, -1, 5)].data = 3
        sb(self.c1.trans(4, -2, 5), materials.Torch, 5)

        # Wither skulls are rare
        SkullType = weighted_choice(((0, 30), (1, 1)))
        sb(self.c1.trans(4, -2, 3), materials.MobHead, 1)
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Skull')
        root_tag['x'] = nbt.TAG_Int(self.c1.trans(4, -2, 3).x)
        root_tag['y'] = nbt.TAG_Int(self.c1.trans(4, -2, 3).y)
        root_tag['z'] = nbt.TAG_Int(self.c1.trans(4, -2, 3).z)
        root_tag['SkullType'] = nbt.TAG_Byte(SkullType)
        root_tag['Rot'] = nbt.TAG_Byte(random.randint(0, 15))
        self.parent.parent.tile_ents[self.c1.trans(4, -2, 3)] = root_tag
        #
        sb(self.c1.trans(4, -2, 4), materials.BrewingStand)
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Cauldron')
        root_tag['x'] = nbt.TAG_Int(self.c1.trans(4, -2, 4).x)
        root_tag['y'] = nbt.TAG_Int(self.c1.trans(4, -2, 4).y)
        root_tag['z'] = nbt.TAG_Int(self.c1.trans(4, -2, 4).z)
        self.parent.parent.tile_ents[self.c1.trans(4, -2, 4)] = root_tag

        # A chest in an alchemy lab should have brewing supplies :)
        # item, probability, max stack amount
        writing_items = [(items.byName('glass bottle'), 1, 5),
                         (items.byName('book'), 0.7, 5),
                         (items.byName('paper'), 0.8, 10),
                         (items.byName('nether wart'), 0.3, 5),
                         (items.byName('glowstone dust'), 0.3, 5),
                         (items.byName('redstone dust'), 0.3, 5),
                         (items.byName('fermented spider eye'), 0.3, 5),
                         (items.byName('magma cream'), 0.1, 2),
                         (items.byName('sugar'), 0.2, 5),
                         (items.byName('glistering melon'), 0.2, 2),
                         (items.byName('spider eye'), 0.2, 5),
                         (items.byName('ghast tear'), 0.2, 2),
                         (items.byName('blaze powder'), 0.2, 1),
                         (items.byName('gunpowder'), 0.4, 3),
                         (items.byName('golden carrot'), 0.2, 1)]
        # Generate desk loot and place chest
        deskloot = []
        for s in writing_items:
            if (random.random() < s[1]):
                amount = random.randint(1, min(s[2], s[0].maxstack))
                deskloot.append(
                    loottable.Loot(
                        len(deskloot),
                        amount,
                        s[0].value,
                        s[0].data,
                        '',
                        flag=s[0].flag))
        self.parent.parent.addchest(self.c1.trans(4, -1, 6), loot=deskloot)

        self.parent.parent.cobwebs(self.c1.up(4), self.c3)

        # Hide the room from maps.
        self.hideRoom()

class SecretSepulchure(SecretRoom):
    _name = 'secretsepulchure'

    def renderSecretPost(self):
        sb = self.parent.parent.setblock
        blocks = self.parent.parent.blocks
        dungeon = self.parent.parent

        # We also a frame of reference for the back left corner
        # (bl) and vectors for crossing the room (rt) and (fw) so we can draw
        # everything relative to the hallway orientation.
        # Hall on North side
        if self.direction == 0:
            bl = self.c3
            rt = Vec(-1, 0, 0)
            fw = Vec(0, 0, -1)
            st_d = (1, 0, 3, 2)
            chest = 2
            gems = ('W', 'E')
        # Hall on East side
        if self.direction == 1:
            bl = Vec(self.c1.x, self.c1.y, self.c3.z)
            rt = Vec(0, 0, -1)
            fw = Vec(1, 0, 0)
            st_d = (3, 2, 0, 1)
            chest = 5
            gems = ('N', 'S')
        # Hall on South side
        if self.direction == 2:
            bl = self.c1
            rt = Vec(1, 0, 0)
            fw = Vec(0, 0, 1)
            st_d = (0, 1, 2, 3)
            chest = 3
            gems = ('E', 'W')
        # Hall on West Side
        if self.direction == 3:
            bl = Vec(self.c3.x, self.c1.y, self.c1.z)
            rt = Vec(0, 0, 1)
            fw = Vec(-1, 0, 0)
            st_d = (2, 3, 1, 0)
            chest = 4
            gems = ('S', 'N')

        # Different walls
        for q in iterate_four_walls(self.c1, self.c3, self.parent.parent.room_height - 2):
            sb(q, materials.meta_mossystonebrick)

        # Loot for the sarcophagus.
        loota = []
        lootb = []
        bone = items.byName('bone')
        for slot in xrange(11, 15, 1):
            loota.append(loottable.Loot(slot, 1, bone.value, bone.data, ''))
            lootb.append(loottable.Loot(slot, 1, bone.value, bone.data, ''))
        for slot in xrange(18, 27, 1):
            loota.append(loottable.Loot(slot, 1, bone.value, bone.data, ''))
        for slot in xrange(0, 9, 1):
            lootb.append(loottable.Loot(slot, 1, bone.value, bone.data, ''))

        # Random stuff to be buried with. Like Crypt, but not as good.
        lootc = [(items.byName('iron ingot'), 5),
                 (items.byName('written book'), 10),
                 (items.byName('bow'), 10),
                 (items.byName('diamond'), 5),
                 (items.byName('gold ingot'), 5),
                 (items.byName('bowl'), 10),
                 (items.byName('feather'), 10),
                 (items.byName('golden apple'), 5),
                 (items.byName('arrow'), 10),
                 (items.byName('clock'), 10),
                 (items.byName('compass'), 10),
                 (items.byName('gold nugget'), 10),
                 (items.byName('ghast tear'), 1),
                 (items.byName('bottle o\' enchanting'), 10),
                 (items.byName('glass bottle'), 10)]

        # Chance of random head
        loothead = [(items.byName('bone'), 100),
                    (items.byName('skeleton skull'), 10),
                    (items.byName('wither skeleton skull'), 1),
                    (items.byName('zombie head'), 1),
                    (items.byName('head'), 1),
                    (items.byName('creeper head'), 1)]

        i = weighted_choice(lootc)
        loota[7].id = i.value
        loota[7].damage = i.data
        loota[7].flag = i.flag
        i = weighted_choice(loothead)
        loota[4].id = i.value
        loota[4].damage = i.data

        i = weighted_choice(lootc)
        lootb[7].id = i.value
        lootb[7].damage = i.data
        # Swap the contents if East or South
        if self.direction in (0, 1):
            loota, lootb = lootb, loota

        # Sarcophagus
        mats = (
            (materials.Air, 0),
            (materials.Sandstone, 0),
            (materials.SandstoneSlab, 0),
            (materials.StoneBrickStairs, st_d[1]),
            (materials.Chest, chest),
            (materials.StoneBrick, 0),
            (materials.StoneBrickSlab, 0),
        )
        template = ((
            (2, 1, 1, 2),
            (1, 4, 4, 1),
            (2, 1, 1, 2)
        ), (
            (0, 0, 0, 0),
            (3, 6, 6, 5),
            (0, 0, 0, 0)
        )
        )
        tomb_name = 'Here lies ' + self.parent.parent.namegen.genname()
        for y in xrange(2):
            for x in xrange(4):
                for z in xrange(3):
                    p = bl + rt * (x + 3) + fw * (z + 2) + \
                        Vec(0, -1, 0) * (y + 1)
                    sb(p,
                       mats[template[y][z][x]][0],
                       mats[template[y][z][x]][1])
                    if template[y][z][x] == 4:
                        if x == 1:
                            dungeon.addchest(p, loot=loota, name=tomb_name)
                        else:
                            dungeon.addchest(p, loot=lootb)

        # Snaaaaaake! It's a snaaaaaaaake!
        mats = (
            (materials.Air, 0),
            (materials.Torch, 5),
            (materials.Sandstone, 2),
            (materials.SandstoneStairs, st_d[2]),
            (materials.SandstoneStairs, st_d[3]),
            (materials.SandstoneStairs, st_d[2] + 4),
            (materials.SandstoneStairs, st_d[3] + 4),
            (materials.SandstoneSlab, 0),
        )
        template = (
            (1, 0, 6, 5, 2),
            (6, 0, 5, 0, 0),
            (4, 7, 3, 0, 0),
        )
        for y in xrange(3):
            for z in xrange(5):
                p = bl + rt + fw * (z + 1) + Vec(0, 1, 0) * (-3 + y)
                sb(p,
                   mats[template[y][z]][0],
                   mats[template[y][z]][1])
                sb(p + rt * 7,
                   mats[template[y][z]][0],
                   mats[template[y][z]][1])

        # Lootable gems for eyes
        loot = weighted_choice((("emerald", 10),
                                ("diamond", 1)))
        for p in (Vec(1, -3, 5), Vec(8, -3, 5)):
            q = bl + rt * p.x + fw * p.z + Vec(0, 1, 0) * p.y
            if p.x <= 5:
                d = gems[0]
            else:
                d = gems[1]
            tags = get_entity_other_tags("ItemFrame",
                                         ItemTags=self.parent.parent.inventory.buildFrameItemTag(loot),
                                         Pos=q,
                                         Facing=d)
            dungeon.addentity(tags)

        # Vines
        for p in iterate_cube(self.c1.up(4), self.c3):
            if random.randint(1, 100) <= 20:
                self.parent.parent.vines(p, grow=True)

        # Cobwebs
        self.parent.parent.cobwebs(self.c1.up(4), self.c3)

        # Hide the room from maps.
        self.hideRoom()

class SecretShop(SecretRoom):
    _name = 'secretshop'

    def renderSecretPost(self):
        dungeon = self.parent.parent
        sb = dungeon.setblock
        blocks = dungeon.blocks
        s = shop.rollShop()
        shopkeeper_name = dungeon.namegen.genname()
        name_post = "'" if shopkeeper_name.endswith("s") else "'s"

        # We also a frame of reference for the back left corner
        # (bl) and vectors for crossing the room (rt) and (fw) so we can draw
        # everything relative to the hallway orientation.
        # Hall on North side
        if self.direction == 0:
            bl = self.c3
            rt = Vec(-1, 0, 0)
            fw = Vec(0, 0, -1)
            orient = {'L':3,'R':2,'U':4,'D':5}
            frame_or = 'N'
        # Hall on East side
        if self.direction == 1:
            bl = Vec(self.c1.x, self.c1.y, self.c3.z)
            rt = Vec(0, 0, -1)
            fw = Vec(1, 0, 0)
            orient = {'L':4,'R':5,'U':2,'D':3}
            frame_or = 'E'
        # Hall on South side
        if self.direction == 2:
            bl = self.c1
            rt = Vec(1, 0, 0)
            fw = Vec(0, 0, 1)
            orient = {'L':2,'R':3,'U':5,'D':4}
            frame_or = 'S'
        # Hall on West Side
        if self.direction == 3:
            bl = Vec(self.c3.x, self.c1.y, self.c1.z)
            rt = Vec(0, 0, 1)
            fw = Vec(-1, 0, 0)
            orient = {'L':5,'R':4,'U':3,'D':2}
            frame_or = 'W'

        # materials by profession id
        if (s.profession == 0): # Farmer
            upperslab = materials.UpperOakWoodSlab
            pillers = materials.Wood
            floor = materials.BirchWoodPlanks
            banner_cols = [15,1]
        elif (s.profession == 1): # Librarian
            upperslab = materials.UpperDarkOakWoodSlab
            pillers = materials.DarkOak
            floor = materials.JungleWoodPlanks
            banner_cols = [15,4]
        elif (s.profession == 2): # Priest
            upperslab = materials.UpperAcaciaWoodSlab
            pillers = materials.AcaciaWoodPlanks
            floor = materials.NetherBrick
            banner_cols = [0,14]
        elif (s.profession == 3): # Blacksmith
            upperslab = materials.UpperStoneSlab
            pillers = materials.ChiseledStoneBrick
            floor = materials.PolishedGranite
            banner_cols = [15,2]
        else: # Butcher (4 and future)
            upperslab = materials.UpperQuartzSlab
            pillers = materials.PillarQuartzBlock
            floor = materials.PolishedDiorite
            banner_cols = [15,0]

        # Floor
        for q in iterate_cube(self.c1, self.c3):
            sb(q, floor)

        # Ceiling
        for q in iterate_cube(self.c1.up(4), self.c3.up(4)):
            sb(q, floor)

        # Pillers
        pillers_loc = [bl+(rt*5)+(fw*5),bl+rt+(fw*5),bl+(rt*5)+fw]
        for p in pillers_loc:
            for i in range(1,4):
                sb(p.up(i), pillers)

        # Shop's Banners
        banner_pos = [[bl.up(3)+(rt*6)+(fw*5),orient['U']],
                      [bl.up(3)+(rt*6)+(fw*1),orient['U']],
                      [bl.up(3)+(rt*5)+(fw*6),orient['R']],
                      [bl.up(3)+(rt*1)+(fw*6),orient['R']]]
        for b in banner_pos:
            sb(b[0], materials.WallBanner,b[1])
            dungeon.addtileentity(get_tile_entity_tags(
                                    eid='Banner',
                                    Pos=b[0],
                                    Base=banner_cols[0],
                                    Patterns=[[banner_cols[1],'ss']]))
        # Dungeon's Banners
        banner_pos = [[bl.up(3)+(rt*8)+(fw*1),orient['D']],
                      [bl.up(3)+(rt*1)+(fw*8),orient['L']]]
        for b in banner_pos:
            sb(b[0], materials.WallBanner,b[1])
            dungeon.adddungeonbanner(b[0])

        # Desks
        for q in iterate_cube(bl.up(1)+rt+(fw*6), bl.up(1)+rt+(fw*8)):
            sb(q, upperslab)
        for q in iterate_cube(bl.up(1)+(rt*6)+fw, bl.up(1)+(rt*8)+fw):
            sb(q, upperslab)
        # Ender chest
        p = bl.up(2)+rt+(fw*7)
        sb(p, materials.EnderChest, orient['U'])
        dungeon.addtileentity(get_tile_entity_tags(
                                    eid='EnderChest',
                                    Pos=p))

        # Free sample!
        p = bl.up(3)+(rt*7)
        dungeon.addentity(
            get_entity_other_tags("ItemFrame",
                                  Pos=p,
                                  Facing=frame_or,
                                  ItemTags=dungeon.inventory.buildFrameItemTag(s.free_sample.lower())
                                  )
        )

        # Workshop blocks
        sb(bl.up(1)+(rt*1)+(fw*1), materials.Furnace, orient['U'])
        sb(bl.up(1)+(rt*1)+(fw*2), materials.CraftingTable)

        # Top of booth
        for q in iterate_cube(bl.up(3)+(rt*5)+(fw*4), bl.up(3)+(rt*5)+(fw*2)):
            sb(q, upperslab)
        for q in iterate_cube(bl.up(3)+(rt*4)+(fw*5), bl.up(3)+(rt*2)+(fw*5)):
            sb(q, upperslab)
        # Bottom of booth
        for q in iterate_cube(bl.up(1)+(rt*5)+(fw*4), bl.up(1)+(rt*5)+(fw*2)):
            sb(q, upperslab)
        for q in iterate_cube(bl.up(1)+(rt*4)+(fw*5), bl.up(1)+(rt*2)+(fw*5)):
            sb(q, upperslab)

        # Desk plant
        sb(bl.up(2)+(rt*2)+(fw*5), materials.FlowerPot, random.randrange(1, 12))

        # lights
        redstonepos = ([1,0],[7,0],[0,7],[9,8],[5,5])
        lamppos =     ([1,1],[7,1],[1,7],[8,8],[6,5],[5,6])
        for p in redstonepos:
            sb(bl.up(4)+(rt*p[0])+(fw*p[1]), materials.RedstoneTorchOn, 5)
        for p in lamppos:
            sb(bl.up(4)+(rt*p[0])+(fw*p[1]), materials.RedstoneLampOn)

        shopname = s.name.replace("{{name's}}", shopkeeper_name+name_post)
        shopname = shopname.replace("{{name}}", shopkeeper_name)
        signtext = shopname.split(' ')
        if (len(signtext) == 0):
            signtext = ['','','Shop','']
        elif (len(signtext) == 1):
            signtext = ['','',signtext[0],'']
        elif (len(signtext) == 2):
            signtext = ['',signtext[0],signtext[1],'']
        elif (len(signtext) == 3):
            signtext = ['',signtext[0],signtext[1],signtext[2]]

        spos = bl.up(3)+(rt*6)+(fw*3)
        sb(spos, materials.WallSign, orient['U'])
        dungeon.addsign(spos,signtext[0],signtext[1],signtext[2],signtext[3])
        spos = bl.up(3)+(rt*3)+(fw*6)
        sb(spos, materials.WallSign, orient['R'])
        dungeon.addsign(spos,signtext[0],signtext[1],signtext[2],signtext[3])

        # Create the shopkeeper
        pos = bl.up(1) +(rt*3)+(fw*3)
        tags = get_entity_mob_tags('Villager',
                                   Pos=pos,
                                   Profession=s.profession,
                                   CustomName=shopkeeper_name)
        # Setting the CareerLevel to a value higher than Career will
        # prevent new trades from being added, according to the wiki
        tags['Career'] = nbt.TAG_Int(1)
        tags['CareerLevel'] = nbt.TAG_Int(100)
        tags['Offers'] = nbt.TAG_Compound()
        tags['Offers']['Recipes'] = nbt.TAG_List()
        for trade in s.trades:
            rec = nbt.TAG_Compound()
            rec['rewardExp'] = nbt.TAG_Byte(0)
            # If the trade is limited, we utilise the upper Int limit
            # to prevent the maxUses from increasing
            if (trade.limited):
                rec['maxUses'] = nbt.TAG_Int(2147483647)
                rec['uses'] = nbt.TAG_Int(2147483647-trade.max_uses)
            else:
                rec['maxUses'] = nbt.TAG_Int(trade.max_uses)
            rec['buy'] = dungeon.inventory.buildItemTag(trade.inputLoot)
            rec['sell'] = dungeon.inventory.buildItemTag(trade.outputLoot)
            if trade.input2 != None:
                rec['buyB'] = dungeon.inventory.buildItemTag(trade.input2Loot)
            tags['Offers']['Recipes'].append(rec)
        dungeon.addentity(tags)

        # Flyer
        max_lev = (self.c1.y // dungeon.room_height) + 1
        headline = random.choice([
            "Grand Opening",
            "Sale! Sale! Sale!",
            "Our prices are crazy!",
            "Don't miss out...",
            "Fantastic deals today!",
            "The world famous...",
            "Always Open!",
            "Goods bought and sold.",
        ])
        page =  '{text:"'+headline+'",bold:true,extra:[{text:"\n\n'+shopname
        page += '\n\nFind me on the '+converttoordinal(max_lev)
        page += ' level!\n\n'+s.promotext+'",bold:false}]}'
        note = nbt.TAG_Compound()
        note['id'] = nbt.TAG_String(items.byName("written book").id)
        note['Damage'] = nbt.TAG_Short(0)
        note['Count'] = nbt.TAG_Byte(1)
        note['tag'] = nbt.TAG_Compound()
        note['tag']['title'] = nbt.TAG_String("Shop Flyer")
        note['tag']['author'] = nbt.TAG_String(shopkeeper_name)
        note['tag']['pages'] = nbt.TAG_List()
        note['tag']['pages'].append(nbt.TAG_String(page))
        # 1-3 flyers
        for _ in range(0,random.randint(1,3)):
            dungeon.addplaceditem(note, max_lev=max_lev)

        # Hide the room from maps.
        self.hideRoom()


class SecretArmory(SecretRoom):
    _name = 'secretarmory'

    def renderSecretPost(self):
        dungeon = self.parent.parent
        sb = dungeon.setblock
        blocks = dungeon.blocks

        # Different ceiling
        for q in iterate_cube(self.c1.up(4), self.c3.up(4)):
            sb(q, materials.StoneBrickSlab, 13, hide=True)
        # Differnt floor
        for q in iterate_cube(self.c1, self.c3):
            sb(q, materials.meta_mossystonebrick)
        # Different walls
        for q in iterate_four_walls(self.c1, self.c3, self.parent.parent.room_height - 2):
            sb(q, materials.meta_mossystonebrick)

        # Fancy wall coverings
        for p in iterate_four_walls(Vec(1, -1, 1), Vec(8, -1, 8), 3):
            sb(self.c1 + p, materials.meta_mossycobblewall)
        for p in iterate_four_walls(Vec(1, -4, 1), Vec(8, -4, 8), 0):
            sb(self.c1 + p, materials.meta_mossystonebrick)

        # Lighting
        for p in (Vec(1, -2, 1), Vec(1, -2, 8),
                  Vec(8, -2, 1), Vec(8, -2, 8)):
            sb(self.c1 + p, materials.Torch, 5)

        # Thing in the middle
        for p in iterate_cube(Vec(4, -1, 4), Vec(5, -1, 5)):
            sb(self.c1 + p, materials.meta_mossycobblewall)
            sb(self.c1 + p.up(3), materials.BlockOfQuartz, 1, hide=True)

        # Armory alcoves. We want to leave out the ones on the wall with the
        # hallway. Each entry here stores:
        # (sign location), sign direction, (frame location), 'frame direction'
        alcoves = []
        # North Side
        if self.direction != 0:
            alcoves.append([Vec(3, -1, 1), 3, Vec(3, -2, 0), 'S'])
            alcoves.append([Vec(6, -1, 1), 3, Vec(6, -2, 0), 'S'])
        # East Side
        if self.direction != 1:
            alcoves.append([Vec(8, -1, 3), 4, Vec(9, -2, 3), 'W'])
            alcoves.append([Vec(8, -1, 6), 4, Vec(9, -2, 6), 'W'])
        # South Side
        if self.direction != 2:
            alcoves.append([Vec(3, -1, 8), 2, Vec(3, -2, 9), 'N'])
            alcoves.append([Vec(6, -1, 8), 2, Vec(6, -2, 9), 'N'])
        # West Side
        if self.direction != 3:
            alcoves.append([Vec(1, -1, 3), 5, Vec(0, -2, 3), 'E'])
            alcoves.append([Vec(1, -1, 6), 5, Vec(0, -2, 6), 'E'])

        # Now, add a random item to each frame.
        gear = (
            ("random leather helmet", 16),
            ("random leather chestplate", 16),
            ("random leather leggings", 16),
            ("random leather boots", 16),
            ("chainmail helmet", 8),
            ("chainmail chestplate", 8),
            ("chainmail leggings", 8),
            ("chainmail boots", 8),
            ("iron helmet", 4),
            ("iron chestplate", 4),
            ("iron leggings", 4),
            ("iron boots", 4),
            ("iron horse armor", 4),
            ("gold helmet", 2),
            ("gold chestplate", 2),
            ("gold leggings", 2),
            ("gold boots", 2),
            ("gold horse armor", 2),
            ("diamond helmet", 1),
            ("diamond chestplate", 1),
            ("diamond leggings", 1),
            ("diamond boots", 1),
            ("diamond horse armor", 1),
            ("bow", 16),
            ("dungeon shield", 16),
            ("iron sword", 8),
            ("iron axe", 8),
            ("gold sword", 4),
            ("gold axe", 4),
            ("diamond sword", 2),
            ("diamond axe", 2),
            ("fishing rod", 8),
            ("carrot on a stick", 8),
            ("shears", 8),
            ("name tag", 8)
        )

        for p in alcoves:
            item = weighted_choice(gear)

            if 'sword' in item:
                ItemRotation = random.randint(0, 3)
            elif 'axe' in item:
                ItemRotation = random.choice((0, 3))
            else:
                ItemRotation = 0

            # Spice things up with some synonyms
            if 'sword' in item:
                item_name = random.choice(('sword', 'blade', 'claymore',
                                           'cutlass', 'sabre', 'scimitar'))
            elif 'pickaxe' in item:
                item_name = random.choice(('pickaxe', 'pickax', 'pick'))
            elif 'axe' in item:
                item_name = random.choice(('ax', 'axe', 'hatchet'))
            elif 'shears' in item:
                item_name = random.choice(('shears', 'clippers', 'scissors'))
            elif 'fishing rod' in item:
                item_name = random.choice(
                    ('fishing rod', 'fishing pole', 'rod'))
            elif 'chestplate' in item:
                item_name = random.choice(('chestplate', 'tunic', 'vest',
                                           'mail', 'plate'))
            elif 'helmet' in item:
                item_name = random.choice(
                    ('helmet', 'hat', 'helm', 'headgear'))
            elif 'boots' in item:
                item_name = random.choice(('boots', 'shoes'))
            elif "name tag" in item:
                item_name = random.choice(('name tag', 'tag', 'dog tags'))
            elif "horse armor" in item:
                item_name = random.choice(('horse armor', 'barding'))
            elif "shield" in item:
                item_name = random.choice(('shield', 'buckler'))
            else:
                item_name = item.split()[-1]

            # Owner's name
            name = dungeon.namegen.genname()
            # The plaque
            sb(self.c1 + p[0], materials.WallSign, p[1])
            sb(self.c1 + p[0].up(1), materials.Air)
            if name.endswith("s"):
                dungeon.addsign(self.c1 + p[0],
                                '',
                                item_name.capitalize(),
                                'of ' + name,
                                ''
                                )
            else:
                dungeon.addsign(self.c1 + p[0],
                                '',
                                name + "'s",
                                item_name,
                                ''
                                )
            # Name the item
            # Special case, tags should just have the name
            if (item == 'name tag'):
                displayname = name
            elif name.endswith("s"):
                displayname = item_name.capitalize() + ' of ' + name
            else:
                displayname = name + "'s " + item_name
            # Build the frame tags
            tags = get_entity_other_tags("ItemFrame",
                                         Pos=self.c1 + p[2],
                                         Facing=p[3],
                                         ItemRotation=ItemRotation,
                                         ItemTags=self.parent.parent.inventory.buildFrameItemTag(item,customname=displayname))
            # Place the item frame.
            dungeon.addentity(tags)

        name = dungeon.namegen.genname()

        # DEATH KNIGHT! RRRRRAGH!
        if random.random() < .80:
            pos = Vec(3, -2, 3)
            # Always get a weapon
            while True:
                item = weighted_choice(gear)
                if ('bow' in item or
                        'sword' in item or
                        'axe' in item):
                    break
            # Place some lore
            words = random.choice([
                "...some say the corpse of {name} still wanders these halls "
                "clutching his enchanted {item} in his moldering hands...",
                "...Beware! For {name} cheats death to this day...",
                "...I can feel the presence of the {item}... So close. It "
                "calls my name! {name}! {name}!",
                "...They shall never hold the {item}. I will carry it with "
                "me, even in death! -{name}",
                "...My guide, {name}, seems strangely calm in this horrible "
                "place. As if he has been here before..."
            ])
            words = words.format(name=name, item=item.split()[-1])
            note = nbt.TAG_Compound()
            note['id'] = nbt.TAG_String(items.byName("written book").id)
            note['Damage'] = nbt.TAG_Short(0)
            note['Count'] = nbt.TAG_Byte(1)
            note['tag'] = nbt.TAG_Compound()
            note['tag']['title'] = nbt.TAG_String("A torn page")
            note['tag']['author'] = nbt.TAG_String("Unknown")
            note['tag']['pages'] = nbt.TAG_List()
            note['tag']['pages'].append(nbt.TAG_String('"%s"'%(words)))
            max_lev = (self.c1.y // dungeon.room_height) + 1
            dungeon.addplaceditem(note, max_lev=max_lev)

            # helmet
            while True:
                helmet = weighted_choice(gear)
                if 'helmet' in helmet:
                    break
            helmet_tags = nbt.TAG_Compound()
            helmet_tags['id'] = nbt.TAG_String(items.byName(helmet).id)
            # chest
            while True:
                chest = weighted_choice(gear)
                if 'chestplate' in chest:
                    break
            chest_tags = nbt.TAG_Compound()
            chest_tags['id'] = nbt.TAG_String(items.byName(chest).id)
            # leggings
            while True:
                leggings = weighted_choice(gear)
                if 'leggings' in leggings:
                    break
            leggings_tags = nbt.TAG_Compound()
            leggings_tags['id'] = nbt.TAG_String(items.byName(leggings).id)
            # boots
            while True:
                boots = weighted_choice(gear)
                if 'boots' in boots:
                    break
            boots_tags = nbt.TAG_Compound()
            boots_tags['id'] = nbt.TAG_String(items.byName(boots).id)

            tags = get_entity_mob_tags("Skeleton",
                                       Pos=self.c1 + pos,
                                       CanPickUpLoot=1,
                                       SkeletonType=random.randint(0, 1),
                                       PersistenceRequired=1,
                                       CustomName=name
                                       )
            tags['ArmorItems'][0] = boots_tags
            tags['ArmorItems'][1] = leggings_tags
            tags['ArmorItems'][2] = chest_tags
            tags['ArmorItems'][3] = helmet_tags

            tags['HandDropChances'][0].value = 1.0
            tags['HandDropChances'][1].value = 1.0

            tags['ArmorDropChances'][0].value = 0.0
            tags['ArmorDropChances'][1].value = 0.0
            tags['ArmorDropChances'][2].value = 0.0
            tags['ArmorDropChances'][3].value = 0.0
            dungeon.addentity(tags)
        else:
            pos = Vec(5, -2, 5)
            item = weighted_choice(gear)

        # Centerpiece
        if name.endswith("s"):
            displayname = item.split()[-1].capitalize() + ' of ' + name
        else:
            displayname = name + "'s " + item.split()[-1]

        xplevel = (int(self.c1.y / dungeon.room_height) + 1) * 5
        tags = get_entity_item_tags("Item",
                                    Pos=self.c1 + pos.up(1),
                                    Age=-32768,
                                    ItemInfo=items.byName(item))
        tags['Item']['tag'] = nbt.TAG_Compound()
        tags['Item']['tag']['display'] = nbt.TAG_Compound()
        tags['Item']['tag']['display']['Name'] = nbt.TAG_String(displayname)
        if 'leather' in item and 'horse' not in item:
            tags['Item']['tag']['display']['color'] = nbt.TAG_Int(
                random.randrange(16777215))
        tags['Item']['tag']['ench'] = loottable.enchant_tags(item,
                                                             xplevel)
        dungeon.addentity(tags)

        # Hide the room from maps.
        self.hideRoom()


class SecretEnchantingLibrary(SecretRoom):
    _name = 'secretenchantinglibrary'

    def renderSecretPost(self):
        dungeon = self.parent.parent
        sb = dungeon.setblock
        blocks = dungeon.blocks

        # We need to expand the room one block so we can center the enchanting
        # table. We'll do this one block "back" and one block "right" of the
        # entrance. We also need a frame of reference for the back left corner
        # (bl) and vectors for crossing the room (rt) and (fw) so we can draw
        # everything relative to the hallway orientation.
        # Hall on North side
        if self.direction == 0:
            self.c1 = self.c1.w(1)
            self.c3 = self.c3.s(1)
            bl = self.c3
            rt = Vec(-1, 0, 0)
            fw = Vec(0, 0, -1)
            chests = (4, 2, 5)
        # Hall on East side
        if self.direction == 1:
            self.c1 = self.c1.n(1)
            self.c1 = self.c1.w(1)
            bl = Vec(self.c1.x, self.c1.y, self.c3.z)
            rt = Vec(0, 0, -1)
            fw = Vec(1, 0, 0)
            chests = (4, 1, 3)
        # Hall on South side
        if self.direction == 2:
            self.c1 = self.c1.n(1)
            self.c3 = self.c3.e(1)
            bl = self.c1
            rt = Vec(1, 0, 0)
            fw = Vec(0, 0, 1)
            chests = (5, 3, 4)
        # Hall on West Side
        if self.direction == 3:
            self.c3 = self.c3.e(1)
            self.c3 = self.c3.s(1)
            bl = Vec(self.c3.x, self.c1.y, self.c1.z)
            rt = Vec(0, 0, 1)
            fw = Vec(-1, 0, 0)
            chests = (3, 4, 2)

        # Reform the room (again)
        for q in iterate_cube(self.c1.up(1), self.c3.up(3)):
            sb(q, materials.Air)
        for q in iterate_cube(self.c1.up(4), self.c3.up(4)):
            sb(q, materials.StoneBrickSlab, 13, hide=True)
        for q in iterate_cube(self.c1, self.c3):
            sb(q, materials.ChiseledStoneBrick)
        for q in iterate_four_walls(self.c1, self.c3, self.parent.parent.room_height - 2):
            sb(q, materials.meta_mossystonebrick)

        # Fancy carpet
        mats = [
            materials.BlackWool.data,
            materials.GrayWool.data,
            materials.LightGrayWool.data,
            materials.OrangeWool.data,
        ]
        # Random stripe color (skip white, grays, and black)
        mats[3] = random.randint(1, 6) + random.randint(0, 1) * 8

        template = (
            (1, 3, 3, 1, 3, 1, 3, 3, 1),
            (3, 3, 2, 0, 2, 0, 2, 3, 3),
            (3, 2, 0, 2, 0, 2, 0, 2, 3),
            (1, 0, 2, 0, 2, 0, 2, 0, 1),
            (3, 2, 0, 2, 0, 2, 0, 2, 3),
            (1, 0, 2, 0, 2, 0, 2, 0, 1),
            (3, 2, 0, 2, 0, 2, 0, 2, 3),
            (3, 3, 2, 0, 2, 0, 2, 3, 3),
            (1, 3, 3, 3, 3, 3, 3, 3, 1)
        )
        for x in xrange(9):
            for z in xrange(9):
                if template[z][x] != 1:
                    p = bl + rt * (x + 1) + fw * (z + 1)
                    sb(p,
                       materials.PinkWool,
                       mats[template[z][x]])
                # Columns
                else:
                    p = bl + rt * (x + 1) + fw * (z + 1)
                    sb(p.up(1), materials.CobblestoneWall)
                    sb(p.up(2), materials.CobblestoneWall)
                    sb(p.up(3), materials.CobblestoneWall)
                    sb(p.up(4), materials.meta_mossystonebrick)

        # Lighting
        for p in (Vec(1, -4, 1), Vec(1, -4, 9),
                  Vec(9, -4, 1), Vec(9, -4, 9),
                  Vec(5, -4, 5)):
            sb(self.c1 + p, materials.RedstoneLampOn, hide=True)
            sb(self.c1 + p.up(1), materials.BlockOfRedstone, hide=True)

        # The book cases
        levs = int(self.c1.y / dungeon.room_height) + 1
        spots = [
            Vec(5, 2, 3), Vec(5, 1, 3),
            Vec(3, 2, 6), Vec(3, 1, 6),
            Vec(4, 2, 3), Vec(4, 1, 3),
            Vec(3, 2, 4), Vec(3, 1, 4),
            Vec(3, 2, 5), Vec(3, 1, 5)
        ]
        mat = materials.Bookshelf
        while len(spots) > 0:
            if levs < 1:
                mat = materials.OakWoodPlanks
            levs -= 1
            s = spots.pop()
            p = (bl + rt * s.x + fw * s.z).up(s.y)
            sb(p, mat)
            p = (bl + rt * 10 - rt * s.x + fw * s.z).up(s.y)
            sb(p, mat)

        # Enchanting table
        p = self.c1 + Vec(5, -1, 5)
        sb(p, materials.EnchantmentTable)
        tags = nbt.TAG_Compound()
        tags['id'] = nbt.TAG_String('EnchantTable')
        tags['x'] = nbt.TAG_Int(p.x)
        tags['y'] = nbt.TAG_Int(p.y)
        tags['z'] = nbt.TAG_Int(p.z)
        dungeon.tile_ents[p] = tags

        # Loot chests
        p = (bl + rt * 1 + fw * 5).up(1)
        sb(p, materials.Chest, chests[0])
        tags = nbt.TAG_Compound()
        dungeon.addchest(p)
        p = (bl + rt * 9 + fw * 5).up(1)
        sb(p, materials.Chest, chests[2])
        tags = nbt.TAG_Compound()
        dungeon.addchest(p)

        # Ender chest
        p = (bl + rt * 5 + fw * 1).up(1)
        sb(p, materials.EnderChest, chests[1])
        tags = nbt.TAG_Compound()
        tags['id'] = nbt.TAG_String('EnderChest')
        tags['x'] = nbt.TAG_Int(p.x)
        tags['y'] = nbt.TAG_Int(p.y)
        tags['z'] = nbt.TAG_Int(p.z)
        dungeon.tile_ents[p] = tags

        # She's a witch!
        tags = get_entity_mob_tags("Witch",
                                   Pos=self.c1 + Vec(5, -2, 5) + fw * 2,
                                   PersistenceRequired=1,
                                   CustomName=self.parent.parent.namegen.genname(),
                                   CanPickUpLoot=1
                                   )
        dungeon.addentity(tags)

        # Hide the room from maps.
        self.hideRoom()


class Forge(Blank):
    _name = 'forge'

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        dungeon = self.parent.parent
        sb = dungeon.setblock

        # Note: Anvil block damage values are different from when they are
        # in the player's inventory
        mats = [
            (materials.Air, 0),             # 0
            (materials.Furnace, 0),         # 1
            (materials.StoneDoubleSlab, 0),      # 2
            (materials.Water, 0),           # 3
            (materials.BrickBlock, 0),      # 4
            (materials.StoneSlab, 0),       # 5
            (materials.Lava, 0),            # 6
            (materials.Chest, 0),           # 7
            (materials.CraftingTable, 0),   # 8
            (materials.Anvil, 0),           # 9
            (materials.AnvilSlightlyDmg, 4),  # 10
            (materials.AnvilVeryDmg, 8),    # 11
            (materials.Cauldron, 0),        # 12
            (materials.Cauldron, 1),        # 13
            (materials.Cauldron, 2),        # 14
            (materials.Cauldron, 3),        # 15
        ]

        template = [
            [0, 2, 5, 2, 2, 7],
            [2, 3, 4, 6, 6, 2],
            [2, 3, 4, 6, 6, 2],
            [1, 2, 5, 2, 2, 8]
        ]

        # random anvil (or other...)
        anvil_options = ((9, 1),  # New anvil
                         (10, 15),  # Slightly Damged
                         (11, 30),  # Very Damaged
                         (12, 30),  # Empty cauldron
                         (13, 30),  # 1/3 cauldron
                         (14, 30),  # 2/3 cauldron
                         (15, 30),  # Full cauldron
                         (1, 50))  # Furnace!
        template[0][0] = weighted_choice(anvil_options)

        center = self.parent.canvasCenter()
        o = self.parent.loc.trans(center.x - 1,
                                  self.parent.canvasHeight() - 1,
                                  center.z - 2)

        # item, probability, max stack amount
        supply_items = [(items.byName('charcoal'), .8, 10),
                        (items.byName('coal'), .8, 10),
                        (items.byName('iron ore'), .3, 5),
                        (items.byName('gold ore'), .1, 1),
                        (items.byName('iron sword'), .3, 1)]
        # Generate loot and place chest
        supplyloot = []
        for s in supply_items:
            if (random.random() < s[1]):
                amount = random.randint(1, min(s[2], s[0].maxstack))
                supplyloot.append(
                    loottable.Loot(
                        len(supplyloot),
                        amount,
                        s[0].value,
                        s[0].data,
                        '',
                        flag=s[0].flag))

        for x in xrange(4):
            for z in xrange(6):
                p = o.trans(x, 0, z)
                sb(p,
                   mats[template[x][z]][0],
                   mats[template[x][z]][1])
                if mats[template[x][z]][0] == materials.Chest:
                    dungeon.addchest(p, loot=supplyloot)

        sb(o.trans(0, 0, 3), materials.StoneStairs, 0)
        sb(o.trans(0, 0, 4), materials.StoneStairs, 0)
        sb(o.trans(3, 0, 3), materials.StoneStairs, 1)
        sb(o.trans(3, 0, 4), materials.StoneStairs, 1)
        sb(o.trans(1, 0, 5), materials.StoneStairs, 3)
        sb(o.trans(2, 0, 5), materials.StoneStairs, 3)

        # Tall rooms won't have a flume
        if self.parent.canvasHeight() > 4:
            return

        sb(o.trans(0, -2, 3), materials.StoneStairs, 0)
        sb(o.trans(0, -2, 4), materials.StoneStairs, 0)
        sb(o.trans(3, -2, 3), materials.StoneStairs, 1)
        sb(o.trans(3, -2, 4), materials.StoneStairs, 1)
        sb(o.trans(1, -2, 5), materials.StoneStairs, 3)
        sb(o.trans(2, -2, 5), materials.StoneStairs, 3)
        sb(o.trans(1, -2, 2), materials.StoneStairs, 2)
        sb(o.trans(2, -2, 2), materials.StoneStairs, 2)


class Pool(Blank):
    _name = 'pool'

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return
        mat = random.choice((
            materials.StoneSlab,
            materials.CobblestoneSlab,
            materials.SandstoneSlab,
            materials.StoneBrickSlab
        ))
        center = self.parent.canvasCenter()
        size = random.randint(4,
                              min(self.parent.canvasWidth(),
                                  self.parent.canvasLength()) - 2)
        p0 = Vec(center.x - size / 2 + 1,
                 self.parent.canvasHeight(),
                 center.z - size / 2 + 1) + self.parent.loc
        p1 = p0.trans(size - 1, 0, size - 1)
        for p in iterate_disc(p0, p1):
            self.parent.parent.setblock(p, materials.Water)
        for p in iterate_ellipse(p0, p1):
            self.parent.parent.setblock(p, materials._floor)
            self.parent.parent.setblock(p.up(1), mat)


class CircleOfSkulls(Blank):
    _name = 'circleofskulls'

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        center = self.parent.canvasCenter()
        size = random.randint(6,
                              min(self.parent.canvasWidth(),
                                  self.parent.canvasLength()) - 1)
        p0 = Vec(center.x - size / 2 + 1,
                 self.parent.canvasHeight(),
                 center.z - size / 2 + 1) + self.parent.loc
        p1 = p0.trans(size - 1, 0, size - 1)

        skulls = (
            (0, 50),  # Plain Skull
            (1, 1),  # Wither Skull
        )
        counter = 0
        for p in iterate_ellipse(p0, p1):
            if((p.x + p.z) % 2 == 0):
                self.parent.parent.setblock(p, materials._floor)
                self.parent.parent.setblock(p.up(1), materials.Fence)
                # Abort if there is no skull here
                if (random.randint(0, 100) < 33):
                    continue
                SkullType = weighted_choice(skulls)
                self.parent.parent.setblock(p.up(2), materials.MobHead, 1)
                root_tag = nbt.TAG_Compound()
                root_tag['id'] = nbt.TAG_String('Skull')
                root_tag['x'] = nbt.TAG_Int(p.x)
                root_tag['y'] = nbt.TAG_Int(p.y - 2)
                root_tag['z'] = nbt.TAG_Int(p.z)
                root_tag['SkullType'] = nbt.TAG_Byte(SkullType)
                root_tag['Rot'] = nbt.TAG_Byte(random.randint(0, 15))
                self.parent.parent.tile_ents[p.up(2)] = root_tag

            elif(random.randint(0, 100) < 33):
                self.parent.parent.setblock(p, materials._floor)
                self.parent.parent.setblock(p.up(1), materials.Torch, 5)


class Cell(Blank):
    _name = 'cell'

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        sb = self.parent.parent.setblock

        mats = [
            (materials.Air, 0),  # 0
            (materials._wall, 0),  # 1
            (materials.IronBars, 0)  # 2
        ]

        center = self.parent.canvasCenter()

        o = self.parent.loc.trans(center.x - 2,
                                  self.parent.canvasHeight() - 1,
                                  center.z - 2)

        locs = [o]

        # If it's a bigroom, add more cells.
        # 2x2 rooms have no conflicts.
        if (self.parent.size.x == 2 and self.parent.size.z == 2):
            locs.extend([o.trans(5, 0, 0), o.trans(-5, 0, 0)])
            locs.extend([o.trans(0, 0, 5), o.trans(0, 0, -5)])

        # 2x1 rooms need to check for stairwells.
        elif (self.parent.size.x == 2):
            if(self.parent.pos + Vec(0, self.parent.size.y, 0) not in
               self.parent.parent.stairwells):
                locs.extend([o.trans(-5, 0, 0)])
            if(self.parent.pos + Vec(1, self.parent.size.y, 0) not in
               self.parent.parent.stairwells):
                locs.extend([o.trans(5, 0, 0)])

        # 1x2 rooms need to check for stairwells.
        elif (self.parent.size.z == 2):
            if(self.parent.pos + Vec(0, self.parent.size.y, 0) not in
               self.parent.parent.stairwells):
                locs.extend([o.trans(0, 0, -5)])
            if(self.parent.pos + Vec(0, self.parent.size.y, 1) not in
               self.parent.parent.stairwells):
                locs.extend([o.trans(0, 0, 5)])

        for loc in locs:
            # each side has a random chance of being a space, wall, or bars
            n = random.choice((0, 0, 2, 2, 2, 2, 1))
            e = random.choice((0, 0, 2, 2, 2, 2, 1))
            s = random.choice((0, 0, 2, 2, 2, 2, 1))
            w = random.choice((0, 0, 2, 2, 2, 2, 1))

            template = [
                [1, 1, n, n, 1, 1],
                [1, 0, 0, 0, 0, 1],
                [w, 0, 0, 0, 0, e],
                [w, 0, 0, 0, 0, e],
                [1, 0, 0, 0, 0, 1],
                [1, 1, s, s, 1, 1]
            ]

            for x in xrange(6):
                for z in xrange(6):
                    p = loc.trans(x, 0, z)
                    sb(p,
                       mats[template[x][z]][0],
                       mats[template[x][z]][1])
                    sb(p.up(1),
                       mats[template[x][z]][0],
                       mats[template[x][z]][1])
                    sb(p.up(2),
                       materials._wall,
                       0)


class Farm(Blank):
    _name = 'farm'

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        center = self.parent.canvasCenter()

        o = self.parent.loc.trans(center.x - 2,
                                  self.parent.canvasHeight() - 1,
                                  center.z - 2)

        locs = [o]

        # If it's a bigroom, add more cells.
        stairs = self.parent.parent.stairwells
        p = self.parent.pos
        y = self.parent.size.y - 1
        # 2x2 rooms N,S,E,W are fine, need to check diagonals.
        if (self.parent.size.x == 2 and self.parent.size.z == 2):
            locs.extend([o.trans(0, 0, -5), o.trans(0, 0, 5),
                         o.trans(5, 0, 0), o.trans(-5, 0, 0)])
            # NW
            if(p + Vec(0, y, 0) not in stairs and
               p + Vec(0, y + 1, 0) not in stairs):
                locs.extend([o.trans(-5, 0, -5)])
            # NE
            if(p + Vec(1, y, 0) not in stairs and
               p + Vec(1, y + 1, 0) not in stairs):
                locs.extend([o.trans(5, 0, -5)])
            # SW
            if(p + Vec(0, y, 1) not in stairs and
               p + Vec(0, y + 1, 1) not in stairs):
                locs.extend([o.trans(-5, 0, 5)])
            # SE
            if(p + Vec(1, y, 1) not in stairs and
               p + Vec(1, y + 1, 1) not in stairs):
                locs.extend([o.trans(5, 0, 5)])

        # 2x1 rooms need to check for stairwells.
        elif (self.parent.size.x == 2):
            if(p + Vec(0, y, 0) not in stairs and
               p + Vec(0, y + 1, 0) not in stairs):
                locs.extend([o.trans(-5, 0, 0)])
            if(p + Vec(1, y, 0) not in stairs and
               p + Vec(1, y + 1, 0) not in stairs):
                locs.extend([o.trans(5, 0, 0)])

        # 1x2 rooms need to check for stairwells.
        elif (self.parent.size.z == 2):
            if(p + Vec(0, y, 0) not in stairs and
               p + Vec(0, y + 1, 0) not in stairs):
                locs.extend([o.trans(0, 0, -5)])
            if(p + Vec(0, y, 1) not in stairs and
               p + Vec(0, y + 1, 1) not in stairs):
                locs.extend([o.trans(0, 0, 5)])

        self.plant(locs)

    def plant(self, locs):
        sb = self.parent.parent.setblock

        crops = [
            (materials.Fern, 2),
            (materials.TallGrass, 1),
            (materials.DeadBush, 0),
            (materials.RedMushroom, 0),
            (materials.BrownMushroom, 0),
            (materials.NetherWart, 0)
        ]

        for loc in locs:
            # choose a random crop. there's a 33% change it'll be a dead bush
            # i mean good lord, it's in an UNDERGROUND ABANDONED dungeon (:
            if(random.randint(0, 100) < 34):
                crop = (materials.DeadBush, 0)
            else:
                crop = random.choice(crops)

            # choose an appropriate soil
            soil = (materials.Dirt, 0)
            if(crop[0] == materials.NetherWart):
                soil = (materials.SoulSand, 0)

            # torches if it needs it to survive
            needsLight = 0
            if(crop[0] == materials.Fern or crop[0] == materials.DeadBush
                    or crop[0] == materials.TallGrass):
                needsLight = 1

            for x in xrange(6):
                for z in xrange(6):
                    p = loc.trans(x, 0, z)
                    if(random.randint(0, 100) < 40):
                        sb(p, crop[0], crop[1])

                    sb(p.down(1), soil[0], soil[1])

                    if(x == 0 or x == 5 or z == 0 or z == 5):
                        sb(p, materials.Fence, 0)

            if(needsLight == 1):
                sb(loc.trans(0, -1, 5), materials.Torch, 5)
                sb(loc.trans(5, -1, 5), materials.Torch, 5)
                sb(loc.trans(5, -1, 0), materials.Torch, 5)
                sb(loc.trans(0, -1, 0), materials.Torch, 5)

            # Add some gates
            sb(loc.trans(2, 0, 0), materials.FenceGate, 0)
            sb(loc.trans(2, 0, 5), materials.FenceGate, 0)


class WildGrowth(Farm):
    _name = 'wildgrowth'

    grassPercentage = 15
    # format: mat, block val, top block val (tall flowers only)
    flowers = [
        ((materials.Air, 0), 80),
        ((materials.Poppy, 0), 4),
        ((materials.BlueOrchid, 1), 4),
        ((materials.Allium, 2), 4),
        ((materials.AzureBluet, 3), 4),
        ((materials.RedTulip, 4), 1),
        ((materials.OrangeTulip, 5), 1),
        ((materials.WhiteTulip, 6), 1),
        ((materials.PinkTulip, 7), 1),
        ((materials.OxeyeDaisy, 8), 4),
        ((materials.Dandelion, 0), 4),
        ((materials.Lilac, 1, 8), 4),
        ((materials.RoseBush, 4, 8), 4),
        ((materials.Peony, 5, 8), 4),
        ((materials.Fern, 2), 40),
        ((materials.DeadBush, 0), 40),
        ((materials.TallGrass, 1), 40),
        ((materials.DoubleTallGrass, 3, 8), 40),
        ((materials.DoubleFern, 2, 8), 40)
        # (materials.Sunflower, 0, 8), #Doesn't look right underground
    ]

    def plant(self, locs):
        sb = self.parent.parent.setblock

        for loc in locs:
            for x in xrange(6):
                for z in xrange(6):
                    p = loc.trans(x, 0, z)
                    if(random.randint(0, 100) < 45):
                        flower = weighted_choice(self.flowers)
                        sb(p, flower[0], flower[1])
                        if (len(flower) > 2):   # tall flower
                            sb(p.up(1), flower[0], flower[2])
                        # Place dirt/grass only under flowers
                        if(random.randint(0, 100) < self.grassPercentage):
                            sb(p.down(1), materials.Grass, 0)
                        else:
                            sb(p.down(1), materials.Dirt, 1)    # No grass dirt
        # Grow some vines
        sx = self.parent.size.x * self.parent.parent.room_size
        sz = self.parent.size.z * self.parent.parent.room_size
        sy = self.parent.size.y * self.parent.parent.room_height

        c1 = self.parent.loc + Vec(0, 0, 0)
        c3 = c1 + Vec(sx - 1, sy - 2, sz - 1)

        for p in iterate_cube(c1,
                              c3):
            if random.randint(1, 100) <= 20:
                self.parent.parent.vines(p, grow=True)

        # Add a rabbit. Possibly killer.
        if random.randint(1,100) < 75:
            dungeon = self.parent.parent
            pos = self.parent.loc + Vec(8,3,8)
            # 50% chance of a killer rabbit.
            rtype = weighted_choice((
                (0,10),
                (1,10),
                (2,10),
                (3,10),
                (4,10),
                (5,10),
                (99,60),
            ))
            # Add the rabbit entity to the room.
            dungeon.addentity(get_entity_mob_tags('Rabbit',
                                         Pos=pos,
                                         RabbitType=rtype,
                                         PersistenceRequired=1))
            # If it's a killer rabbit, add a holy hand grenade to the surface
            # chest.
            if rtype == 99:
                tag = dungeon.inventory.buildFrameItemTag('magic_holy hand grenade of antioch')
                dungeon.addplaceditem(tag, max_lev=0)


class WildGarden(WildGrowth):
    _name = 'wildgarden'

    grassPercentage = 45
    # format: mat, block val, top block val (tall flowers only)
    flowers = [
        ((materials.Air, 0), 20),
        ((materials.Poppy, 0), 4),
        ((materials.BlueOrchid, 1), 4),
        ((materials.Allium, 2), 4),
        ((materials.AzureBluet, 3), 4),
        ((materials.RedTulip, 4), 1),
        ((materials.OrangeTulip, 5), 1),
        ((materials.WhiteTulip, 6), 1),
        ((materials.PinkTulip, 7), 1),
        ((materials.OxeyeDaisy, 8), 4),
        ((materials.Dandelion, 0), 4),
        ((materials.Lilac, 1, 8), 4),
        ((materials.RoseBush, 4, 8), 4),
        ((materials.Peony, 5, 8), 4),
        ((materials.Fern, 2), 2),
        ((materials.TallGrass, 1), 2),
        ((materials.DoubleTallGrass, 3, 8), 2),
        ((materials.DoubleFern, 2, 8), 2)
        # (materials.Sunflower, 0, 8), #Doesn't look right underground
    ]


class Chapel(Blank):
    _name = 'chapel'

    decos = ((materials.Cauldron, 2),
             (materials.BlockOfRedstone, 0),
             (materials.Banner, 4),
             (materials.Chest, 5))

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        # Choose a carpet color
        # (Exclude some of the gaudier colours, e.g. pinks)
        carpetColor = random.choice([0, 1, 3, 7, 8, 9, 10, 11, 12, 13, 14, 15])

        sb = self.parent.parent.setblock

        center = self.parent.canvasCenter()
        o = self.parent.loc.trans(center.x,
                                  self.parent.canvasHeight() - 1,
                                  center.z + 1)

        # Adjust size for stairs and entrances.
        # If it's a bigroom, add more cells.
        stairs = self.parent.parent.stairwells
        p = self.parent.pos
        y = self.parent.size.y - 1
        N_margin = 1
        S_margin = 1
        E_margin = 3
        W_margin = 1
        carpet_pos = -1
        # 2x1 rooms we may shrink on X
        if (self.parent.size.x == 2 and self.parent.size.z == 1):
            if(p + Vec(0, y, 0) in stairs or
               p + Vec(0, y + 1, 0) in stairs):
                W_margin += 8
            if(p + Vec(1, y, 0) in stairs or
               p + Vec(1, y + 1, 0) in stairs):
                E_margin += 8
        # 1x2 rooms may shrink on Z
        elif (self.parent.size.x == 1 and self.parent.size.z == 2):
            if(p + Vec(0, y, 0) in stairs or
               p + Vec(0, y + 1, 0) in stairs):
                N_margin += 8
                carpet_pos += 4
            if(p + Vec(0, y, 1) in stairs or
               p + Vec(0, y + 1, 1) in stairs):
                S_margin += 8
                carpet_pos -= 4
        # 2x2 rooms may shrink on Z
        elif (self.parent.size.z == 2):
            if(p + Vec(0, y, 0) in stairs or
               p + Vec(0, y + 1, 0) in stairs or
               p + Vec(1, y, 0) in stairs or
               p + Vec(1, y + 1, 0) in stairs):
                N_margin += 8
                carpet_pos += 4
            if(p + Vec(0, y, 1) in stairs or
               p + Vec(0, y + 1, 1) in stairs or
               p + Vec(1, y, 1) in stairs or
               p + Vec(1, y + 1, 1) in stairs):
                S_margin += 8
                carpet_pos -= 4

        # pews
        for x in xrange(-1 * self.parent.canvasWidth() / 2 + W_margin,
                        self.parent.canvasWidth() / 2 - E_margin, 1):
            for z in xrange(-1 * self.parent.canvasLength() / 2 + N_margin,
                            self.parent.canvasLength() / 2 - S_margin, 1):
                p = o.trans(x, 0, z)
                if(z == carpet_pos or z == carpet_pos + 1):
                    sb(p.down(1),
                       materials.Wool, carpetColor)
                    sb(p, materials.WhiteCarpet, carpetColor)
                elif(x % 2 == 0):
                    sb(p,
                       materials.OakWoodStairs, 1)

        # carpet continues in front of pews
        for x in xrange(self.parent.canvasWidth() / 2 - E_margin,
                        self.parent.canvasWidth() / 2 - E_margin + 3, 1):
            for z in xrange(carpet_pos, carpet_pos + 2, 1):
                p = o.trans(x, 0, z)
                sb(p.down(1),
                   materials.Wool, carpetColor)
                sb(p, materials.WhiteCarpet, carpetColor)

        #altar and deco
        deco = random.choice(self.decos)

        mats = [
            (materials.Air, 0),  # 0
            deco,  # 1
            (materials.StoneBrickStairs, 6),  # 2
            (materials.StoneBrickStairs, 7)  # 3
        ]

        template = [1, 0, 2, 3, 0, 1]

        for z in xrange(6):
            p = o.trans(
                self.parent.canvasWidth() /
                2 -
                1,
                0,
                z +
                carpet_pos -
                2)
            sb(p,
               mats[template[z]][0],
               mats[template[z]][1])
            # Special case for banners
            if (mats[template[z]][0] == materials.Banner):
                self.parent.parent.adddungeonbanner(p)
            # Special case for chests
            elif (mats[template[z]][0] == materials.Chest):
                self.parent.parent.addchest(p, loot=None)


class ConstructionArea(Blank):
    _name = 'constructionarea'

    def render(self):
        if (self.parent.canvasWidth() < 6 or self.parent.canvasLength() < 6):
            return

        sb = self.parent.parent.setblock
        gb = self.parent.parent.getblock
        pn = perlin.SimplexNoise(256)
        loc = self.parent.loc + Vec(0, -1, 0)

        # Replace some wall sections with wooden "rebar"
        for x in xrange(self.parent.parent.room_size * self.parent.size.x):
            for z in xrange(self.parent.parent.room_size * self.parent.size.z):
                for y in xrange(self.parent.parent.room_height * self.parent.size.y - 3):
                    p = self.parent.loc.trans(x, y, z) + Vec(0, 1, 0)
                    if (gb(p) == materials._wall and
                            pn.noise3(p.x / 4.0, (p.y + 1337) / 4.0, p.z / 4.0) < 0):
                        sb(p, materials.Fence)
                    elif (gb(p) == materials.Torch):
                        sb(p, materials.Air)

        # Place some random tools and equipment around the room.
        canvas = set(iterate_points_inside_flat_poly(*self.parent.canvas))
        area = len(canvas)
        y_level = random.choice(list(canvas)).y

        # If it's a big room we may need to mask off areas.
        stairs = self.parent.parent.stairwells
        p = self.parent.pos
        y = self.parent.size.y - 1
        # NW
        if(p + Vec(0, y, 0) in stairs or
           p + Vec(0, y + 1, 0) in stairs):
            canvas = canvas - set(iterate_cube(Vec(0, y_level, 0),
                                               Vec(15, y_level, 15)))
        if(self.parent.size.x == 2):
            if(p + Vec(1, y, 0) in stairs or
               p + Vec(1, y + 1, 0) in stairs):
                canvas = canvas - set(iterate_cube(Vec(16, y_level, 0),
                                                   Vec(32, y_level, 15)))
        if(self.parent.size.z == 2):
            if(p + Vec(0, y, 1) in stairs or
               p + Vec(0, y + 1, 1) in stairs):
                canvas = canvas - set(iterate_cube(Vec(0, y_level, 16),
                                                   Vec(15, y_level, 32)))
        if(self.parent.size.x == 2 and self.parent.size.z == 2):
            if(p + Vec(1, y, 1) in stairs or
               p + Vec(1, y + 1, 1) in stairs):
                canvas = canvas - set(iterate_cube(Vec(16, y_level, 32),
                                                   Vec(16, y_level, 32)))

        # A few crafting tables
        num = int(area / 128) + 1
        if num > 0:
            for x in xrange(num):
                p = random.choice(list(canvas))
                canvas.remove(p)
                sb(p + loc, materials.CraftingTable)
                sb(p.down(1) + loc, materials._floor)

        # Some piles of wall blocks
        num = int(area / 128) + 2
        if num > 0:
            for x in xrange(num):
                p = random.choice(list(canvas))
                canvas.remove(p)
                sb(p + loc, materials._wall)
                sb(p.down(1) + loc, materials._floor)

        # Some supply chests
        num = int(area / 256) + 1
        if num > 0:
            for x in xrange(num):
                p = random.choice(list(canvas))
                canvas.remove(p)
                sb(p + loc, materials.Chest)
                sb(p.down(1) + loc, materials._floor)

                # item, probability, max stack amount
                supply_items = [(items.byName('wooden pickaxe'), 1, 1),
                                (items.byName('stone pickaxe'), .5, 1),
                                (items.byName('iron pickaxe'), .1, 1),
                                (items.byName('diamond pickaxe'), .02, 1),
                                (items.byName('wooden axe'), .8, 1),
                                (items.byName('stone axe'), .3, 1),
                                (items.byName('iron axe'), .1, 1),
                                (items.byName('diamond axe'), .02, 1),
                                (items.byName('wooden shovel'), .8, 1),
                                (items.byName('stone shovel'), .3, 1),
                                (items.byName('iron shovel'), .1, 1),
                                (items.byName('diamond shovel'), .02, 1),
                                (items.byName('oak wood planks'), .5, 10),
                                (items.byName('oak wood slab'), .5, 10),
                                (items.byName('fence'), .5, 10),
                                (items.byName('clock'), .1, 1),
                                (items.byName('compass'), .1, 1),
                                (items.byName('stone brick'), 1, 10)]
                # Generate loot and place chest
                supplyloot = []
                for s in supply_items:
                    if (random.random() < s[1]):
                        amount = random.randint(1, min(s[2], s[0].maxstack))
                        supplyloot.append(
                            loottable.Loot(
                                len(supplyloot),
                                amount,
                                s[0].value,
                                s[0].data,
                                '',
                                flag=s[0].flag))
                self.parent.parent.addchest(p + loc, loot=supplyloot)

        # Rarely, a damaged anvil
        if random.random() < .1:
            p = random.choice(list(canvas))
            canvas.remove(p)
            sb(p + loc, materials.AnvilVeryDmg, 8)
            sb(p.down(1) + loc, materials._floor)

        # Some random lumber
        num = int(area / 128) + 2
        trys = 0
        while (num > 0 and trys < 100):
            trys += 1
            p = random.choice(list(canvas))
            d = random.choice([Vec(1, 0, 0), Vec(0, 0, 1)])
            # Make sure we have room for this log
            if (p + d not in canvas or
                    p + d * 2 not in canvas):
                continue

            data = 4
            if d == Vec(0, 0, 1):
                data = 8
            num -= 1
            canvas.remove(p)
            canvas.remove(p + d)
            canvas.remove(p + d * 2)
            sb(p + loc, materials.Wood, data)
            sb(p.down(1) + loc, materials._floor)
            sb(p + d + loc, materials.Wood, data)
            sb(p.down(1) + d + loc, materials._floor)
            sb(p + d * 2 + loc, materials.Wood, data)
            sb(p.down(1) + d * 2 + loc, materials._floor)
            # maybe stack them
            if (random.random() < .5):
                p += Vec(0, -1, 0)
                sb(p + loc, materials.Wood, data)
                sb(p + d + loc, materials.Wood, data)
                sb(p + d * 2 + loc, materials.Wood, data)

        # Scaffolding
        num = int(area / 128) + 1
        trys = 0
        while (num > 0 and trys < 100):
            trys += 1
            p = random.choice(list(canvas))
            d = [Vec(1, 0, 0), Vec(0, 0, 1), Vec(1, 0, 1),
                 Vec(0, 0, -1), Vec(1, 0, -1),
                 Vec(0, 0, 2), Vec(1, 0, 2),
                 Vec(2, 0, 0), Vec(2, 0, 1),
                 Vec(-1, 0, 0), Vec(-1, 0, 1),
                 Vec(0, 0, 0)]
            # Make sure we have room for this scaffold
            # Check that all offsets are a subset of the remaining canvas.
            # The extra offsets are to allow for a one block space near the
            # scaffold so the fence blocks don't try to connect to anything.
            # Plus it just looks better to have some spacing.
            if (set([p + x for x in d]) <= canvas) is False:
                continue

            num -= 1
            canvas.remove(p)
            canvas.remove(p + d[0])
            canvas.remove(p + d[1])
            canvas.remove(p + d[2])
            p += Vec(0, 1, 0)
            sb(p + loc, materials._floor)
            sb(p + d[0] + loc, materials._floor)
            sb(p + d[1] + loc, materials._floor)
            sb(p + d[2] + loc, materials._floor)
            p += Vec(0, -1, 0)
            sb(p + loc, materials.Fence)
            sb(p + d[0] + loc, materials.Fence)
            sb(p + d[1] + loc, materials.Fence)
            sb(p + d[2] + loc, materials.Fence)
            p += Vec(0, -1, 0)
            sb(p + loc, materials.Fence)
            sb(p + d[0] + loc, materials.Fence)
            sb(p + d[1] + loc, materials.Fence)
            sb(p + d[2] + loc, materials.Fence)
            p += Vec(0, -1, 0)
            sb(p + loc, materials.OakWoodSlab)
            sb(p + d[0] + loc, materials.OakWoodSlab)
            sb(p + d[1] + loc, materials.OakWoodSlab)
            sb(p + d[2] + loc, materials.OakWoodSlab)


# Catalog the features we know about.
_features = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses if of features.Blank
    if issubclass(obj, Blank):
        _features[obj._name] = obj


def new(name, parent):
    '''Return a new instance of the feature of a given name. Supply the parent
    dungeon object.'''
    if name in _features.keys():
        return _features[name](parent)
    return Blank(parent)
