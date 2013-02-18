import sys
import inspect

import materials
import loottable
import items
from utils import *
import perlin
from pymclevel import nbt


class Blank(object):
    _name = 'blank'
    _is_stairwell = False
    _is_secret = False

    def __init__ (self, parent):
        self.parent = parent

    def placed (self):
        pass

    def render (self):
        pass


class Entrance(Blank):
    _name = 'entrance'

    def placed (self):
        # Default height of the doors into the entrance.
        self.height = self.parent.parent.room_height
        self.high_height = self.parent.parent.room_height
        self.low_height = self.parent.parent.room_height
        # Height of the tower above entry.
        self.u = self.parent.parent.room_height*2
        self.inwater = False

    def render (self):
        start = self.parent.loc.trans(6,self.parent.parent.room_height-3,6)
        wstart = start.trans(-1,0,-1)
        # Clear air space
        for p in iterate_cube(wstart,
                              wstart.trans(5,-self.height,5)):
            self.parent.parent.setblock(p, materials.Air)
        # Walls
        for p in iterate_four_walls(wstart,
                                    wstart.trans(5,0,5),
                                    self.height):
            self.parent.parent.setblock(p, materials._wall)
        # Lower level openings
        # W side
        for p in iterate_cube(wstart.trans(1,0,0), wstart.trans(4,-3,0)):
            self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(wstart.trans(1,0,5), wstart.trans(4,-3,5)):
            self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(wstart.trans(0,0,1), wstart.trans(0,-3,4)):
            self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(wstart.trans(5,0,1), wstart.trans(5,-3,4)):
            self.parent.parent.setblock(p, materials.Air)
        # Draw the staircase
        mat = materials.StoneSlab
        for p in iterate_spiral(Vec(0,0,0),
                                Vec(4,0,4),
                                self.height*2+2):
            self.parent.parent.setblock(start.trans(p.x,
                                                    floor(float(p.y)/2.0),
                                                    p.z),
                                        mat, mat.data+(p.y%2)*8)
        # Signs
        locs = [
            (Vec(-1,-2, 0),4),
            (Vec(-1,-1, 0),4),
            (Vec(-1,-2, 5),4),
            (Vec(-1,-1, 5),4),
            (Vec( 0,-2,-1),2),
            (Vec( 0,-1,-1),2),
            (Vec( 0,-2, 6),3),
            (Vec( 0,-1, 6),3),
            (Vec( 5,-2,-1),2),
            (Vec( 5,-1,-1),2),
            (Vec( 5,-2, 6),3),
            (Vec( 5,-1, 6),3),
            (Vec( 6,-2, 0),5),
            (Vec( 6,-1, 0),5),
            (Vec( 6,-2, 5),5),
            (Vec( 6,-1, 5),5)
               ]
        random.shuffle(locs)
        signs = self.parent.parent.signs
        random.shuffle(signs)
        while (len(locs) >0 and len(signs) >0):
            loc = locs.pop()
            sign = signs.pop()
            self.parent.parent.setblock(wstart+loc[0],
                                        materials.WallSign, loc[1])
            self.parent.parent.addsign(wstart+loc[0],
                                       sign['s1'],
                                       sign['s2'],
                                       sign['s3'],
                                       sign['s4'])


class Stairwell(Blank):
    _name = 'stairwell'
    _is_stairwell = True

    def render (self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
            start = self.parent.loc.trans(5,self.parent.parent.room_height-3,5)
            # Clear a stairwell
            for x in iterate_cube(start.trans(0,0,1), start.trans(5,-5,4)):
                self.parent.parent.setblock(x, materials.Air)
            mat = random.choice([
                (materials.StoneStairs, materials.meta_mossycobble),
                (materials.WoodenStairs, materials.Wood),
                (materials.StoneBrickStairs, materials.meta_stonedungeon)
            ])
            # Draw the steps
            for x in xrange(6):
                for p in iterate_cube(start.trans(x,-x,1),
                                      start.trans(x,-x,4)):
                    self.parent.parent.setblock(p,
                                                mat[0])
                    self.parent.parent.setblock(p.trans(0,1,0),
                                                mat[1])


class TripleStairs(Blank):
    _name = 'triplestairs'
    _is_stairwell = True

    def render (self):
        #create a shortcut to the set block fN
        sb = self.parent.parent.setblock

        center = self.parent.canvasCenter()

        start = self.parent.loc.trans(5,self.parent.parent.room_height-2,5)
        start = start.trans(0,-6,0)

        #handrail
        for x in iterate_four_walls(start.trans(-1,-1,-1),start.trans(6,-1,6),0):
            sb(x, materials.IronBars, 0)
        sb( start.trans(2,-1,-1) , materials.Air, 0 )
        sb( start.trans(3,-1,-1) , materials.Air, 0 )

        #add a random deco object at the top
        decos = ( (materials.Cauldron, 2) ,
                  (materials.Torch, 0),
                  (materials.FlowerPot, 10),
                  (materials.DoubleSlab, 0),
                  (materials.Air, 0) )

        deco = random.choice(decos)

        sb( start.trans(1,-1,1) , deco[0], deco[1] )
        sb( start.trans(4,-1,1) , deco[0], deco[1] )

        #using the following materials...
        mats = [
            (materials.Air,0), #0
            (materials.StoneBrick,0), #1
            (materials.StoneBrickStairs, 6 ), #2 upside down ascending south
            (materials.StoneBrickStairs, 0 ), #3 ascending east
            (materials.StoneBrickStairs, 1 ), #4 ascending west
            (materials.StoneBrickStairs, 3 ), #5 ascending north
            (materials.StoneBrickStairs, 7 ), #6 upside down ascending north
            (materials.Torch, 3) #7
            ]

        #...create the stairs
        template = [
            [[ 0, 3, 1, 1, 4, 0],
             [ 0, 1, 5, 5, 1, 0],
             [ 0, 7, 0, 0, 7, 0],
             [ 0, 0, 0, 0, 0, 0],
             [ 0, 0, 0, 0, 0, 0],
             [ 0, 0, 0, 0, 0, 0],
             [ 2, 2, 2, 2, 2, 2]],

            [[ 1, 1, 1, 1, 1, 1],
             [ 5, 6, 1, 1, 6, 5],
             [ 0, 0, 5, 5, 0, 0],
             [ 0, 0, 0, 0, 0, 0],
             [ 0, 0, 0, 0, 0, 0],
             [ 0, 0, 0, 0, 0, 0],
             [ 0, 0, 0, 0, 0, 0]],

            [[ 1, 1, 1, 1, 1, 1],
             [ 1, 0, 1, 1, 0, 1],
             [ 5, 0, 1, 1, 0, 5],
             [ 0, 0, 5, 5, 0, 0],
             [ 0, 0, 0, 0, 0, 0],
             [ 0, 0, 0, 0, 0, 0],
             [ 0, 0, 0, 0, 0, 0]],

            [[ 1, 1, 1, 1, 1, 1],
             [ 1, 0, 1, 1, 0, 1],
             [ 1, 0, 1, 1, 0, 1],
             [ 5, 0, 1, 1, 0, 5],
             [ 0, 0, 5, 5, 0, 0],
             [ 0, 0, 0, 0, 0, 0],
             [ 0, 0, 0, 0, 0, 0]],

            [[ 1, 1, 1, 1, 1, 1],
             [ 1, 5, 1, 1, 5, 1],
             [ 1, 0, 1, 1, 0, 1],
             [ 1, 0, 1, 1, 0, 1],
             [ 5, 0, 1, 1, 0, 5],
             [ 0, 0, 5, 5, 0, 0],
             [ 0, 0, 0, 0, 0, 0]],

            [[ 1, 1, 1, 1, 1, 1],
             [ 1, 1, 1, 1, 1, 1],
             [ 1, 0, 1, 1, 0, 1],
             [ 1, 0, 1, 1, 0, 1],
             [ 1, 0, 1, 1, 0, 1],
             [ 5, 0, 1, 1, 0, 5],
             [ 0, 0, 5, 5, 0, 0]]
            ]
        #place the stuff
        for y in xrange(6):
            for x in xrange(6):
                for z in xrange(7):
                    sb(start.trans(x,y,z),
                        mats[ template[y][z][x] ][0],
                        mats[ template[y][z][x] ][1] )


class TowerWithLadder(Blank):
    _name = 'towerwithladder'
    _is_stairwell = True

    def render (self):
        #create a shortcut to the set block fN
        sb = self.parent.parent.setblock

        center = self.parent.canvasCenter()

        start = self.parent.loc.trans(5,self.parent.parent.room_height-2,5)
        start = start.trans(0,-6,0)

        mats = [
            (materials.Air,0), #0
            (materials.StoneBrick,0), #1
            (materials.Ladder, 3 ), #2 facing south
            (materials.Ladder, 2 ), #3 facing north
            (materials.StoneBrickStairs, 6 ), #4 upside down ascending south
            (materials.StoneBrickStairs, 7 ), #5 upside down ascending north
            (materials.IronBars, 0 ) #6
            ]

        template = [
            [ 0, 1, 1, 1, 1, 0],
            [ 1, 0, 2, 2, 0, 1],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0],
            [ 1, 0, 0, 0, 0, 1],
            [ 0, 1, 6, 6, 1, 0]]

        top = [
            [ 0, 1, 1, 1, 1, 0],
            [ 1, 0, 2, 2, 0, 1],
            [ 5, 0, 0, 0, 0, 5],
            [ 4, 0, 0, 0, 0, 4],
            [ 1, 0, 0, 0, 0, 1],
            [ 0, 1, 1, 1, 1, 0]]

        #place the stuff
        for y in xrange(2):
            for x in xrange(6):
                for z in xrange(6):
                    sb(start.trans(x,y*6-1,z),
                       mats[ template[z][x] ][0],
                       mats[ template[z][x] ][1] )
                    sb(start.trans(x,y*6-2,z),
                       mats[ template[z][x] ][0],
                       mats[ template[z][x] ][1] )
                    sb(start.trans(x,y*6-3,z),
                       mats[ top[z][x] ][0],
                       mats[ top[z][x] ][1] )

        #finish ladder
        for x in iterate_cube(start.trans(2,0,1), start.trans(3,2,1)):
            sb(x, materials.Ladder, 3 )


class Scaffolding(Blank):
    _name = 'scaffolding'
    _is_stairwell = True

    def render (self):
        #create a shortcut to the set block fN
        sb = self.parent.parent.setblock

        start = self.parent.loc.trans(5,self.parent.parent.room_height-2,5)
        start = start.trans(0,-7,0)

        mats = [
            (materials.Air,0),           #0
            (materials.Fence,0),         #1
            (materials.WoodenSlab, 0 ),  #2 
            (materials.WoodenStairs, 0 ),#3 Acending East 
            (materials.WoodenStairs, 3 ) #4 Ascending North
            ]

        template = [
           [[ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 1],
            [ 1, 0, 0, 0, 0, 1],
            [ 1, 0, 0, 0, 0, 1],
            [ 1, 1, 1, 1, 1, 1]],

           [[ 0, 0, 0, 0, 2, 2],
            [ 0, 0, 0, 0, 2, 2],
            [ 0, 0, 0, 0, 0, 1],
            [ 1, 0, 0, 0, 0, 1],
            [ 1, 0, 0, 0, 0, 1],
            [ 1, 1, 1, 1, 1, 1]],

           [[ 0, 0, 0, 3, 1, 1],
            [ 0, 0, 0, 3, 1, 1],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 1, 0, 0, 1]],

           [[ 2, 2, 3, 1, 1, 1],
            [ 2, 2, 3, 1, 1, 1],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 1, 0, 0, 1]],

           [[ 1, 1, 1, 0, 0, 0],
            [ 1, 1, 1, 0, 0, 0],
            [ 4, 4, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 1, 0, 0, 1]],

           [[ 1, 1, 1, 0, 0, 0],
            [ 1, 1, 1, 0, 0, 0],
            [ 1, 1, 0, 0, 0, 0],
            [ 4, 4, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0],
            [ 0, 0, 1, 0, 0, 1]],

           [[ 1, 1, 1, 0, 0, 0],
            [ 1, 1, 1, 0, 0, 0],
            [ 1, 1, 0, 0, 0, 0],
            [ 1, 1, 0, 0, 0, 0],
            [ 4, 4, 0, 0, 0, 0],
            [ 0, 0, 1, 0, 0, 1]],
        ]

        #place the stuff
        for y in xrange(7):
            for x in xrange(6):
                for z in xrange(6):
                    sb(start.trans(x,y,z),
                       mats[ template[y][z][x] ][0],
                       mats[ template[y][z][x] ][1] )


class Chasm(Blank):
    _name = 'chasm'
    material = materials.Air
    depth = 2

    def render (self):
        if (self.parent.canvasWidth() < 4 or
            self.parent.canvasLength() < 4):
            return
        # We'll render across the whole block, since that will look cool
        y = self.parent.canvasHeight()
        flip = random.randint(0,1)
        for x in xrange(2, self.parent.parent.room_size*self.parent.size.x-2):
            if (flip == 1):
                for p in iterate_cube(self.parent.loc +
                                      Vec(self.parent.parent.room_size*self.parent.size.x-x-1,
                                          y,
                                          x+random.randint(-1,0)),
                                      self.parent.loc +
                                      Vec(self.parent.parent.room_size*self.parent.size.x-x-1,
                                          y + self.depth,
                                          x+random.randint(1,2))
                                     ):
                    self.parent.parent.setblock(p, self.material)
            else:
                for p in iterate_cube(self.parent.loc +
                                      Vec(x,
                                          y,
                                          x+random.randint(-1,0)),
                                      self.parent.loc +
                                      Vec(x,
                                          y + self.depth,
                                          x+random.randint(1,2))
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
        materials.Bedrock,
        materials.ChiseledSandstone,
        materials.DoubleSlab,
        materials.Obsidian,
        materials.StoneBrick,
        materials.meta_mossycobblewall,
        materials.meta_mossystonebrick,
        materials.meta_stonedungeon,
        materials.IronBars,
        materials.Fence,
        materials.NetherBrick,
        materials.NetherBrickFence,
        materials.Glowstone
    )

    def render (self):
        limit = int(min(self.parent.canvasWidth(), self.parent.canvasLength()))
        if (limit < 6):
            return
        c = self.parent.canvasCenter()
        height = self.parent.canvasHeight()-1
        start = random.randint(0, limit/2-1)
        stop = limit/2
        step = random.randint(2, 3)
        mat = random.choice(self.mats)
        for x in xrange(start, stop, step):
            for p in iterate_cube(Vec(c.x-x, 1, c.z-x),
                                  Vec(c.x-x, height, c.z-x)):
                self.parent.parent.setblock(self.parent.loc+p, mat)
            for p in iterate_cube(Vec(c.x+x+1, 1, c.z-x),
                                  Vec(c.x+x+1, height, c.z-x)):
                self.parent.parent.setblock(self.parent.loc+p, mat)
            for p in iterate_cube(Vec(c.x-x, 1, c.z+x+1),
                                  Vec(c.x-x, height, c.z+x+1)):
                self.parent.parent.setblock(self.parent.loc+p, mat)
            for p in iterate_cube(Vec(c.x+x+1, 1, c.z+x+1),
                                  Vec(c.x+x+1, height, c.z+x+1)):
                self.parent.parent.setblock(self.parent.loc+p, mat)


class Arcane(Blank):
    _name = 'arcane'

    def render (self):
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
                dun.blocks[p.down(1)].material != materials.StillWater):
                dun.setblock(p, mat)
        mode = random.choice(['one','boxes', 'conc'])

        if mode == 'boxes':
            center = self.parent.canvasCenter()
            o = self.parent.loc + Vec(center.x,
                                      self.parent.canvasHeight()-1,
                                      center.z)
            o = o+Vec(-self.parent.canvasWidth()/2,
                      0,
                      -self.parent.canvasLength()/2)
            for x in xrange(self.parent.canvasWidth()/3+1):
                for z in xrange(self.parent.canvasLength()/3+1):
                    if random.random() < 0.5:
                        q = Vec(o.x+x*3, o.y, o.z+z*3)
                        sb(q, materials.RedStoneWire)
                        sb(q.trans(1,0,0), materials.RedStoneWire)
                        sb(q.trans(0,0,1), materials.RedStoneWire)
                        sb(q.trans(1,0,1), materials.RedStoneWire)
            return

        if mode == 'conc':
            center = self.parent.canvasCenter()
            c = self.parent.loc + Vec(center.x,
                                      self.parent.canvasHeight()-1,
                                      center.z)
            sb(c, materials.RedStoneWire)
            for p in iterate_ellipse(c.trans(-2,0,-2), c.trans(2,0,2)):
                sb(p, materials.RedStoneWire)
            for p in iterate_ellipse(c.trans(-4,0,-4), c.trans(4,0,4)):
                sb(p, materials.RedStoneWire)
            return

        center = self.parent.canvasCenter()
        c = self.parent.loc + Vec(center.x,
                                  self.parent.canvasHeight()-1,
                                  center.z)
        for p in iterate_cube(c.n(4), c.s(4)):
            sb(p, materials.RedStoneWire)
        for p in iterate_cube(c.e(4), c.w(4)):
            sb(p, materials.RedStoneWire)
        for p in iterate_four_walls(c.trans(-2,0,-2), c.trans(2,0,2),0):
            sb(p, materials.RedStoneWire)


class Mushrooms(Blank):
    _name = 'mushrooms'

    def render (self):
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
            r = random.randint(1,1000)
            for p in iterate_points_inside_flat_poly(*self.parent.canvas):
                if (pn.noise3(p.x/4.0, r/4.0, p.z/4.0) > .8):
                    q = p + self.parent.loc
                    sb(q.trans( 1,-1, 0))
                    sb(q.trans(-1,-1, 0))
                    sb(q.trans( 0,-1,-1))
                    sb(q.trans( 0,-1, 1))
            return

        if mode == 'fairyring':
            center = self.parent.canvasCenter()
            c = self.parent.loc + Vec(center.x,
                                      self.parent.canvasHeight()-1,
                                      center.z)
            radius = random.randint(2,5)
            for p in iterate_ellipse(c.trans(-radius,0,-radius),
                                     c.trans(radius,0,radius)):
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
                rp = self.parent.pos + Vec(x,0,z)
                if (self.parent.parent.rooms[rp].features[0]._is_stairwell is False and
                    self.parent.parent.rooms[rp].features[0]._name is not 'blank'):
                    p = self.parent.loc + Vec(
                        x * self.parent.parent.room_size,
                        self.parent.canvasHeight()-1,
                        z * self.parent.parent.room_size)
                    for q in iterate_cube(p+Vec(5,0,7), p+Vec(10,0,8)):
                        sb(q, materials.Fence)
                        sb(q.up(1), materials.WoodenPressurePlate)
                    # Seating
                    q = p+Vec(5,0,6)
                    o = random.randint(0,1)
                    while o <= 5:
                            sb(q.e(o), materials.WoodenStairs, 3)
                            o += random.randint(2,3)
                    q = p+Vec(5,0,9)
                    o = random.randint(0,1)
                    while o <= 5:
                            sb(q.e(o), materials.WoodenStairs, 2)
                            o += random.randint(2,3)

        # If the room is 1x1, stop here.
        if (self.parent.size.x < 2 and self.parent.size.z < 2):
            return
        # Draw a fire pit in the middle
        center = self.parent.canvasCenter()
        size = 2
        p0 = Vec(center.x - size/2 + 1,
                 self.parent.canvasHeight(),
                 center.z - size/2 + 1) + self.parent.loc
        p1 = p0.trans(size-1, 0, size-1)
        for p in iterate_disc(p0+Vec(-2,0,-2), p1+Vec(2,0,2)):
            sb(p, materials._floor)
            sb(p.up(1), materials.IronBars)
        for p in iterate_disc(p0, p1):
            sb(p, materials.Netherrack)
            sb(p.up(1), materials.Fire)



class Dais(Blank):
    _name = 'dais'

    def render (self):
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

        p0 = Vec(center.x - size/2 + 1,
                 self.parent.canvasHeight(),
                 center.z - size/2 + 1) + self.parent.loc
        p1 = p0.trans(size-1, 0, size-1)

        if torches:
            for p in (Vec(p0.x+1,p0.y-1,p0.z+1), Vec(p1.x-1,p0.y-1,p1.z-1),
                      Vec(p0.x+1,p0.y-1,p1.z-1), Vec(p1.x-1,p0.y-1,p0.z+1)):
                self.parent.parent.setblock(p, materials.Fence)
                self.parent.parent.setblock(p.up(1), materials.Fence)
                self.parent.parent.setblock(p.up(2), materials.Torch)
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
        pass

    def render(self):
        sb = self.parent.parent.setblock

        # Reform the basic room shape.
        for p in iterate_cube(self.parent.loc,
                              self.parent.loc+Vec(self.parent.parent.room_size-1,
                                                  self.parent.parent.room_height-2,
                                                  self.parent.parent.room_size-1)):
            sb(p, None)
        self.c1 = self.parent.loc + Vec(3,
                                  self.parent.parent.room_height-2,
                                  3)
        self.c3 = self.parent.loc + Vec(self.parent.parent.room_size-4,
                                  self.parent.parent.room_height-2,
                                  self.parent.parent.room_size-4)
        for q in iterate_cube(self.c1.up(1), self.c3.up(3)):
            sb(q, materials.Air)
        for q in iterate_cube(self.c1.up(4), self.c3.up(4)):
            sb(q, materials._ceiling)
        for q in iterate_cube(self.c1, self.c3):
            sb(q, materials._floor)
        for q in iterate_four_walls(self.c1, self.c3, self.parent.parent.room_height-2):
            sb(q, materials._wall)

        # Fix the hallway and create the secret door mechansm.
        # Find the direction, room, and connecting room.
        # room = this room
        # d = direction out of this room
        # offset = offset of the hallways
        # oroom = connecting room
        # od = direction out of the connecting room
        # length = legth of the opposite hall

        o = self.parent.loc.trans(2,0,2)
        # hall positions to grid direction
        dirs = {3: Vec(-1,0,0),
                1: Vec(1,0,0),
                2: Vec(0,0,1),
                0: Vec(0,0,-1)}

        room = self.parent
        d = 0
        for x in xrange(4):
            if room.halls[x]._name != 'blank':
                d = x
        offset = room.halls[d].offset
        oroom = self.parent.parent.rooms[room.pos+dirs[d]]
        od = (d+2)%4
        length = oroom.hallLength[od]-2

        # Figure our our deltas. There are 8 possibilities based on direction
        # and offset. Offset will basically mirror across width. 
        # dw = delta width
        # dl = delta length
        # spos = start pos for the mechanism

        # d = 0 (West)
        if d == 0:
            dw = Vec(1,0,0)
            dl = Vec(0,0,-1)
            spos = o.trans(offset,0,0)
        # d = 1 (South)
        elif d == 1:
            dw = Vec(0,0,1)
            dl = Vec(1,0,0)
            spos = o.trans(11,0,offset)
        # d = 2 (East)
        elif d == 2:
            dw = Vec(1,0,0)
            dl = Vec(0,0,1)
            spos = o.trans(offset,0,11)
        # d = 3 (North)
        else:
            dw = Vec(0,0,1)
            dl = Vec(-1,0,0)
            spos = o.trans(0,0,offset)
        if offset >= 7:
            dw = dw*-1
            if (d == 0 or d == 2):
                spos = spos.trans(-2,0,0)
            elif (d == 1 or d == 3):
                spos = spos.trans(0,0,-2)

        # Position the start block for the mechanism
        spos = spos + dl*length - dw*2

        if self.parent.parent.args.debug:
            print
            print 'room:', room.pos
            print 'dir:', d
            print 'offset:', offset
            print 'dl:', dl
            print 'dw:', dw
            print

        mats = [
            [materials.Air,0],          # 0 (ignore these)
            [materials.Air,0],          # 1
            [materials._wall,0],        # 2
            [materials.Stone,0],        # 3
            [materials._wall,0],        # 4
            [materials.RedStoneWire,0], # 5
            [materials.StickyPiston,3], # 6 - toggle piston
            [materials.RedStoneTorchOn,2],# 7
            [materials._ceiling, 0],    # 8
            [materials.StickyPiston, 4],# 9 - pusher piston
            [materials.RedStoneRepeaterOff, 3],# 10 - piston repeater
            [materials.RedStoneRepeaterOff, 7],# 11 - toggle repeater
            [materials.Torch, 0],       # 12
            [materials._secret_door, 0],# 13
            [materials._floor, 0],      # 14
            [materials._subfloor, 0]    # 15
        ]

        template = [
           [[ 8, 8, 8, 8, 8],
            [ 8, 8, 8, 8, 8],
            [ 8, 8, 8, 8, 8],
            [ 8, 8, 8, 8, 8],
            [ 8, 8, 8, 8, 8],
            [ 8, 8, 8, 8, 8]],
           [[ 2, 4, 4, 4, 4],
            [ 1, 1, 1,12, 4],
            [ 2, 4, 4, 4, 4],
            [ 2, 1, 1, 1, 4],
            [ 2, 1, 1, 1, 4],
            [ 2, 1, 1, 1, 4]],
           [[ 2, 4, 4, 4, 4],
            [ 1, 7, 1 ,1,13],
            [ 2, 4, 6, 1, 4],
            [ 2,11, 9, 9, 4],
            [ 2, 5,10,10, 4],
            [ 2, 5, 5, 5, 4]],
           [[ 2, 4, 4, 4, 4],
            [ 1, 1, 1, 1,13],
            [ 2, 4, 6, 1, 4],
            [ 2, 3, 9, 9, 4],
            [ 2, 3, 3, 3, 4],
            [ 2, 3, 3, 3, 4]],
           [[14,14,14,14,14],
            [14,14,14,14,14],
            [14,14,14,14,14],
            [14,14,14,14,14],
            [14,14,14,14,14],
            [14,14,14,14,14]],
           [[15,15,15,15,15],
            [15,15,15,15,15],
            [15,15,15,15,15],
            [15,15,15,15,15],
            [15,15,15,15,15],
            [15,15,15,15,15]],
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
                    p = spos+dl*l+dw*w+Vec(0,1,0)*y
                    sb(p, mats[template[y][w][l]][0],
                          mats[template[y][w][l]][1])

        # The button.
        p = spos+dl*3+dw*5+Vec(0,1,0)*2
        blocks = self.parent.parent.blocks
        while blocks[p+dl].material != materials.Air:
            sb(p.up(1), materials.Air)
            sb(p, materials.RedStoneWire)
            sb(p.down(1), materials.Stone)
            p = p + dl
        sb(p+dl, materials.StoneButton, bdata)

        # Extend the hallway into the room.
        o = spos+dw
        p = o-dl*(length+1)+Vec(0,4,0)
        for q in iterate_cube(o, p):
            sb(q-dw, materials._wall, lock=True)
            if q.y == o.y:
                sb(q, materials._ceiling)
            elif q.y == p.y:
                sb(q, materials._floor)
            else:
                sb(q, materials.Air, lock=True)
                sb(q-dl, materials.Air, lock=True)
            sb(q+dw, materials._wall, lock=True)

        # Clear out any doors or extra torches in this room/hall
        for q in iterate_cube(o+dw*2+dl*5, p-dw-dl):
            if q in self.parent.parent.doors:
                del(self.parent.parent.doors[q])
            if q in self.parent.parent.torches:
                del(self.parent.parent.torches[q])

        # Kill the canvas to prevent spawners and chests from appearing
        self.parent.canvas = (
            Vec(0,0,0),
            Vec(0,0,0),
            Vec(0,0,0))

        # Call the room post-renderer.
        self.renderSecretPost()


class SecretStudy(SecretRoom):
    _name = 'secretstudy'

    def renderSecretPost(self):
        sb = self.parent.parent.setblock
        blocks = self.parent.parent.blocks

        # Bookshelves
        for p in iterate_four_walls(Vec(1,-1,1), Vec(8,-1,8),2):
            if (p.x not in (3, 6) and
                p.z not in (3, 6)):
                sb(self.c1+p, materials.Bookshelf)
            else:
                sb(self.c1+p, materials.Air)

        # A Clock!
        sb(self.c1+Vec(2,-3,1), materials._wall)
        self.parent.parent.addentity(
            get_entity_other_tags("ItemFrame",
                                  Pos=self.c1+Vec(2,-3,1),
                                  Direction="S",
                                  ItemInfo=items.byName("clock")
                                 )
        )

        # Lighting
        for p in (Vec(2,-1,2), Vec(2,-1,7),
                  Vec(7,-1,2), Vec(7,-1,7)):
            sb(self.c1+p, materials.Fence)
            sb(self.c1+p.up(1), materials.Torch, 5)

        # Desk
        mats = [
           (materials.Air,0),          # 0
           (materials.WoodenStairs,7), # 1
           (materials.Chest,0),        # 2
           (materials.CraftingTable,0),# 3
           (materials.WallSign,0),     # 4
           (materials.WoodenStairs,0), # 5
           (materials.WoodenStairs,6), # 6
        ]
        template = [
           [3,1,6,2],
           [0,4,5,4]
        ]
        oo = self.c1.trans(4,-1,3)
        for x in xrange(2):
            for z in xrange(4):
                p = oo.trans(x,0,z)
                sb(p,
                   mats[template[x][z]][0],
                   mats[template[x][z]][1])
        self.parent.parent.blocks[self.c1+Vec(5,-1,4)].data = 2
        self.parent.parent.blocks[self.c1+Vec(5,-1,5)].data = 0
        self.parent.parent.blocks[self.c1+Vec(5,-1,6)].data = 3
        sb(self.c1.trans(4,-2,4), materials.Torch)

        # A chest in a study should have writing supplies :)
        #item, probability, max stack amount
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
                amount = random.randint(1,min(s[2],s[0].maxstack))
                deskloot.append(loottable.Loot(len(deskloot),amount,s[0].value,s[0].data,'',flag=s[0].flag))
        self.parent.parent.addchest(self.c1.trans(4,-1,6), loot=deskloot)

        self.parent.parent.cobwebs(self.c1.up(4), self.c3)


class SecretAlchemyLab(SecretRoom):
    _name = 'secretalchemylab'

    def renderSecretPost(self):
        sb = self.parent.parent.setblock
        blocks = self.parent.parent.blocks

        # Bookshelves
        for p in iterate_four_walls(Vec(1,-1,1), Vec(8,-1,8),2):
            if (p.x not in (3, 6) and
                p.z not in (3, 6)):
                sb(self.c1+p, materials.Bookshelf)
            else:
                sb(self.c1+p, materials.Air)

        # Lighting
        for p in (Vec(2,-1,2), Vec(2,-1,7),
                  Vec(7,-1,2), Vec(7,-1,7)):
            sb(self.c1+p, materials.Fence)
            sb(self.c1+p.up(1), materials.Torch, 5)

        # Desk
        mats = [
           (materials.Air,0),          # 0
           (materials.WoodenStairs,7), # 1
           (materials.Chest,0),        # 2
           (materials.CraftingTable,0),# 3
           (materials.WallSign,0),     # 4
           (materials.WoodenStairs,0), # 5
           (materials.WoodenStairs,6), # 6
           (materials.WoodenSlab,8)    # 7
        ]
        template = [
           [1,7,6,2],
           [4,5,4,0]
        ]
        oo = self.c1.trans(4,-1,3)
        for x in xrange(2):
            for z in xrange(4):
                p = oo.trans(x,0,z)
                sb(p,
                   mats[template[x][z]][0],
                   mats[template[x][z]][1])
        self.parent.parent.blocks[self.c1+Vec(5,-1,3)].data = 2
        self.parent.parent.blocks[self.c1+Vec(5,-1,4)].data = 0
        self.parent.parent.blocks[self.c1+Vec(5,-1,5)].data = 3
        sb(self.c1.trans(4,-2,5), materials.Torch)

        # Wither skulls are rare
        SkullType = weighted_choice(((0,30),(1,1)))
        sb(self.c1.trans(4,-2,3), materials.Head, 1)
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Skull')
        root_tag['x'] = nbt.TAG_Int(self.c1.trans(4,-2,3).x)
        root_tag['y'] = nbt.TAG_Int(self.c1.trans(4,-2,3).y)
        root_tag['z'] = nbt.TAG_Int(self.c1.trans(4,-2,3).z)
        root_tag['SkullType'] = nbt.TAG_Byte(SkullType)
        root_tag['Rot'] = nbt.TAG_Byte(random.randint(0,15))
        self.parent.parent.tile_ents[self.c1.trans(4,-2,3)] = root_tag
        #
        sb(self.c1.trans(4,-2,4), materials.BrewingStand)
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Cauldron')
        root_tag['x'] = nbt.TAG_Int(self.c1.trans(4,-2,4).x)
        root_tag['y'] = nbt.TAG_Int(self.c1.trans(4,-2,4).y)
        root_tag['z'] = nbt.TAG_Int(self.c1.trans(4,-2,4).z)
        self.parent.parent.tile_ents[self.c1.trans(4,-2,4)] = root_tag

        # A chest in an alchemy lab should have brewing supplies :)
        #item, probability, max stack amount
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
                amount = random.randint(1,min(s[2],s[0].maxstack))
                deskloot.append(loottable.Loot(len(deskloot),amount,s[0].value,s[0].data,'',flag=s[0].flag))
        self.parent.parent.addchest(self.c1.trans(4,-1,6), loot=deskloot)

        self.parent.parent.cobwebs(self.c1.up(4), self.c3)


class SecretSepulchure(SecretRoom):
    _name = 'secretsepulchure'

    def renderSecretPost(self):
        sb = self.parent.parent.setblock
        blocks = self.parent.parent.blocks

        # Different walls
        for q in iterate_four_walls(self.c1, self.c3, self.parent.parent.room_height-2):
            sb(q, materials.meta_mossystonebrick)

        # Lighting
        for p in (Vec(1,-1,1), Vec(1,-1,8),
                  Vec(8,-1,1), Vec(8,-1,8)):
            sb(self.c1+p, materials.Fence)
            sb(self.c1+p.up(1), materials.Torch, 5)

        # Sarcophagus
        for p in iterate_cube(self.c1.trans(2,-1,4), self.c1.trans(7,-1,6)):
            sb(p, materials.Sandstone)
        sb(self.c1+Vec(2,-1,4), materials.SandstoneSlab)
        sb(self.c1+Vec(2,-1,6), materials.SandstoneSlab)
        sb(self.c1+Vec(7,-1,4), materials.SandstoneSlab)
        sb(self.c1+Vec(7,-1,6), materials.SandstoneSlab)
        sb(self.c1+Vec(3,-2,5), materials.StoneBrick)
        sb(self.c1+Vec(4,-2,5), materials.StoneBrickSlab)
        sb(self.c1+Vec(5,-2,5), materials.StoneBrickSlab)
        sb(self.c1+Vec(6,-2,5), materials.StoneBrickStairs, 0)

        # Loot for the sarcophagus.
        loota = []
        lootb = []
        bone = items.byName('bone')
        for slot in xrange(11,15,1):
            loota.append(loottable.Loot(slot,1,bone.value,bone.data,''))
            lootb.append(loottable.Loot(slot,1,bone.value,bone.data,''))
        for slot in xrange(18,27,1):
            loota.append(loottable.Loot(slot,1,bone.value,bone.data,''))
        for slot in xrange(0,9,1):
            lootb.append(loottable.Loot(slot,1,bone.value,bone.data,''))

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
        sb(self.c1+Vec(4,-1,5), materials.Chest)
        self.parent.parent.addchest(self.c1+Vec(4,-1,5), loot=loota)

        i = weighted_choice(lootc)
        lootb[7].id = i.value
        lootb[7].damage = i.data
        sb(self.c1+Vec(5,-1,5), materials.Chest)
        self.parent.parent.addchest(self.c1+Vec(5,-1,5), loot=lootb)

        #Vines
        for p in iterate_cube(self.c1.up(4), self.c3):
            if random.randint(1,100) <= 20:
                self.parent.parent.vines(p, grow=True)

        # Cobwebs
        self.parent.parent.cobwebs(self.c1.up(4), self.c3)

class Forge(Blank):
    _name = 'forge'

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        sb = self.parent.parent.setblock

        # Note: Anvil block damage values are different from when they are
        # in the player's inventory
        mats = [
            (materials.Air, 0),             # 0
            (materials.Furnace, 0),         # 1
            (materials.DoubleSlab, 0),      # 2
            (materials.Water, 0),           # 3
            (materials.BrickBlock, 0),      # 4
            (materials.StoneSlab, 0),       # 5
            (materials.Lava, 0),            # 6
            (materials.Chest, 0),           # 7
            (materials.CraftingTable, 0),   # 8
            (materials.Anvil, 0),           # 9
            (materials.AnvilSlightlyDmg, 4),# 10
            (materials.AnvilVeryDmg, 8),    # 11
            (materials.Cauldron, 0),        # 12
            (materials.Cauldron, 1),        # 13
            (materials.Cauldron, 2),        # 14
            (materials.Cauldron, 3),        # 15
        ]

        template = [
            [0,2,5,2,2,7],
            [2,3,4,6,6,2],
            [2,3,4,6,6,2],
            [1,2,5,2,2,8]
        ]

        #random anvil (or other...)
        anvil_options = ((9,1),     #New anvil
                         (10,15),   #Slightly Damged
                         (11,30),   #Very Damaged
                         (12,30),    #Empty cauldron
                         (13,30),    #1/3 cauldron
                         (14,30),    #2/3 cauldron
                         (15,30),    #Full cauldron
                         (1,50))    #Furnace!
        template[0][0] = weighted_choice(anvil_options)

        center = self.parent.canvasCenter()
        o = self.parent.loc.trans(center.x-1,
                                  self.parent.canvasHeight()-1,
                                  center.z-2)

        for x in xrange(4):
            for z in xrange(6):
                p = o.trans(x,0,z)
                sb(p,
                   mats[template[x][z]][0],
                   mats[template[x][z]][1])

        sb (o.trans(0,0,3), materials.StoneStairs, 0)
        sb (o.trans(0,0,4), materials.StoneStairs, 0)
        sb (o.trans(3,0,3), materials.StoneStairs, 1)
        sb (o.trans(3,0,4), materials.StoneStairs, 1)
        sb (o.trans(1,0,5), materials.StoneStairs, 3)
        sb (o.trans(2,0,5), materials.StoneStairs, 3)

        # Tall rooms won't have a flume
        if self.parent.canvasHeight() > 4:
            return

        sb (o.trans(0,-2,3), materials.StoneStairs, 0)
        sb (o.trans(0,-2,4), materials.StoneStairs, 0)
        sb (o.trans(3,-2,3), materials.StoneStairs, 1)
        sb (o.trans(3,-2,4), materials.StoneStairs, 1)
        sb (o.trans(1,-2,5), materials.StoneStairs, 3)
        sb (o.trans(2,-2,5), materials.StoneStairs, 3)
        sb (o.trans(1,-2,2), materials.StoneStairs, 2)
        sb (o.trans(2,-2,2), materials.StoneStairs, 2)


class Pool(Blank):
    _name = 'pool'

    def render (self):
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
        p0 = Vec(center.x - size/2 + 1,
                 self.parent.canvasHeight(),
                 center.z - size/2 + 1) + self.parent.loc
        p1 = p0.trans(size-1, 0, size-1)
        for p in iterate_disc(p0, p1):
            self.parent.parent.setblock(p, materials.Water)
        for p in iterate_ellipse(p0, p1):
            self.parent.parent.setblock(p, materials._floor)
            self.parent.parent.setblock(p.up(1), mat)

class CircleOfSkulls(Blank):
    _name = 'circleofskulls'

    def render (self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        center = self.parent.canvasCenter()
        size = random.randint(6,
                                min(self.parent.canvasWidth(),
                                    self.parent.canvasLength()) - 1)
        p0 = Vec(center.x - size/2 + 1,
                 self.parent.canvasHeight(),
                 center.z - size/2 + 1) + self.parent.loc
        p1 = p0.trans(size-1, 0, size-1)

        skulls = (
            (0, 50), # Plain Skull
            (1, 1),  # Wither Skull
        )
        counter = 0
        for p in iterate_ellipse(p0, p1):
            if( (p.x + p.z) % 2 == 0 ):
                self.parent.parent.setblock(p, materials._floor)
                self.parent.parent.setblock(p.up(1), materials.Fence)
                # Abort if there is no skull here
                if (random.randint(0,100) < 33):
                    continue
                SkullType = weighted_choice(skulls)
                self.parent.parent.setblock(p.up(2), materials.Head, 1)
                root_tag = nbt.TAG_Compound()
                root_tag['id'] = nbt.TAG_String('Skull')
                root_tag['x'] = nbt.TAG_Int(p.x)
                root_tag['y'] = nbt.TAG_Int(p.y-2)
                root_tag['z'] = nbt.TAG_Int(p.z)
                root_tag['SkullType'] = nbt.TAG_Byte(SkullType)
                root_tag['Rot'] = nbt.TAG_Byte(random.randint(0,15))
                self.parent.parent.tile_ents[p.up(2)] = root_tag

            elif( random.randint(0,100) < 33 ):
                self.parent.parent.setblock(p, materials._floor)
                self.parent.parent.setblock(p.up(1), materials.Torch)

class Cell(Blank):
    _name = 'cell'


    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        sb = self.parent.parent.setblock

        mats = [
            (materials.Air, 0), # 0
            (materials._wall, 0), # 1
            (materials.IronBars, 0) # 2
        ]

        center = self.parent.canvasCenter()

        o = self.parent.loc.trans(center.x-2,
                                  self.parent.canvasHeight()-1,
                                  center.z-2)

        locs = [ o ]

        # If it's a bigroom, add more cells.
        # 2x2 rooms have no conflicts. 
        if (self.parent.size.x == 2 and self.parent.size.z == 2):
            locs.extend( [ o.trans(5,0,0), o.trans(-5,0,0) ] )
            locs.extend( [ o.trans(0,0,5), o.trans(0,0,-5) ] )

        # 2x1 rooms need to check for stairwells.
        elif (self.parent.size.x == 2):
            if(self.parent.pos + Vec(0,self.parent.size.y,0) not in
               self.parent.parent.stairwells):
                locs.extend( [ o.trans(-5,0,0) ] )
            if(self.parent.pos + Vec(1,self.parent.size.y,0) not in
               self.parent.parent.stairwells):
                locs.extend( [ o.trans(5,0,0) ] )

        # 1x2 rooms need to check for stairwells.
        elif (self.parent.size.z == 2):
            if(self.parent.pos + Vec(0,self.parent.size.y,0) not in
               self.parent.parent.stairwells):
                locs.extend( [ o.trans(0,0,-5) ] )
            if(self.parent.pos + Vec(0,self.parent.size.y,1) not in
               self.parent.parent.stairwells):
                locs.extend( [ o.trans(0,0,5) ] )

        for loc in locs:
            #each side has a random chance of being a space, wall, or bars
            n = random.choice( (0,0,2,2,2,2,1) )
            e = random.choice( (0,0,2,2,2,2,1) )
            s = random.choice( (0,0,2,2,2,2,1) )
            w = random.choice( (0,0,2,2,2,2,1) )

            template = [
                [1,1,n,n,1,1],
                [1,0,0,0,0,1],
                [w,0,0,0,0,e],
                [w,0,0,0,0,e],
                [1,0,0,0,0,1],
                [1,1,s,s,1,1]
            ]


            for x in xrange(6):
                for z in xrange(6):
                    p = loc.trans(x,0,z)
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

        sb = self.parent.parent.setblock

        center = self.parent.canvasCenter()

        o = self.parent.loc.trans(center.x-2,
                                  self.parent.canvasHeight()-1,
                                  center.z-2)

        locs = [ o ]

        # If it's a bigroom, add more cells.
        stairs = self.parent.parent.stairwells
        p = self.parent.pos
        y = self.parent.size.y-1
        # 2x2 rooms N,S,E,W are fine, need to check diagonals.
        if (self.parent.size.x == 2 and self.parent.size.z == 2):
            locs.extend( [ o.trans(0,0,-5), o.trans(0,0,5),
                           o.trans(5,0,0), o.trans(-5,0,0)] )
            # NW
            if(p+Vec(0,y,0) not in stairs and
               p+Vec(0,y+1,0) not in stairs):
                locs.extend( [ o.trans(-5,0,-5) ] )
            # NE
            if(p+Vec(1,y,0) not in stairs and
               p+Vec(1,y+1,0) not in stairs):
                locs.extend( [ o.trans(5,0,-5) ] )
            # SW
            if(p+Vec(0,y,1) not in stairs and
               p+Vec(0,y+1,1) not in stairs):
                locs.extend( [ o.trans(-5,0,5) ] )
            # SE
            if(p+Vec(1,y,1) not in stairs and
               p+Vec(1,y+1,1) not in stairs):
                locs.extend( [ o.trans(5,0,5) ] )

        # 2x1 rooms need to check for stairwells.
        elif (self.parent.size.x == 2):
            if(p+Vec(0,y,0) not in stairs and
               p+Vec(0,y+1,0) not in stairs):
                locs.extend( [ o.trans(-5,0,0) ] )
            if(p+Vec(1,y,0) not in stairs and
               p+Vec(1,y+1,0) not in stairs):
                locs.extend( [ o.trans(5,0,0) ] )

        # 1x2 rooms need to check for stairwells.
        elif (self.parent.size.z == 2):
            if(p+Vec(0,y,0) not in stairs and
               p+Vec(0,y+1,0) not in stairs):
                locs.extend( [ o.trans(0,0,-5) ] )
            if(p+Vec(0,y,1) not in stairs and
               p+Vec(0,y+1,1) not in stairs):
                locs.extend( [ o.trans(0,0,5) ] )

        for loc in locs:
            #choose a random crop. there's a 33% change it'll be a dead bush
            #i mean good lord, it's in an UNDERGROUND ABANDONED dungeon (:
            crops = [
                (materials.Fern, 2),
                (materials.TallGrass, 1),
                (materials.DeadBush, 0),
                (materials.RedMushroom, 0),
                (materials.BrownMushroom, 0),
                (materials.NetherWart, 0)
            ]
            if( random.randint(0, 100) < 34 ):
                crop = (materials.DeadBush, 0)
            else:
                crop = random.choice(crops)

            #choose an appropriate soil
            soil = ( materials.Dirt, 0 )
            if( crop[0] == materials.NetherWart ):
                soil = (materials.SoulSand,0)

            #torches if it needs it to survive
            needsLight = 0
            if( crop[0] == materials.Fern or crop[0] == materials.DeadBush
                or crop[0] == materials.TallGrass ):
                needsLight = 1


            for x in xrange(6):
                for z in xrange(6):
                    p = loc.trans(x,0,z)
                    if( random.randint(0, 100) < 40 ):
                        sb(p, crop[0], crop[1])

                    sb(p.down(1), soil[0], soil[1])

                    if( x == 0 or x == 5 or z == 0 or z == 5 ):
                        sb(p, materials.Fence, 0 )

            if( needsLight == 1 ):
                sb( loc.trans(0,-1,5), materials.Torch, 5)
                sb( loc.trans(5,-1,5), materials.Torch, 5)
                sb( loc.trans(5,-1,0), materials.Torch, 5)
                sb( loc.trans(0,-1,0), materials.Torch, 5)

            # Add some gates
            sb(loc.trans(2,0,0), materials.FenceGate, 0)
            sb(loc.trans(2,0,5), materials.FenceGate, 0)


class Chapel(Blank):
    _name = 'chapel'

    decos = ( (materials.Cauldron, 2) ,
               (materials.Head, 1),
               (materials.Torch, 0),
               (materials.Chest, 5),
               (materials.CraftingTable, 0) )

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        #choose a carpet color
        carpetColor = random.randint(0,15)

        sb = self.parent.parent.setblock

        center = self.parent.canvasCenter()
        o = self.parent.loc.trans(center.x,
                                  self.parent.canvasHeight()-1,
                                  center.z+1)

        # Adjust size for stairs and entrances.
        # If it's a bigroom, add more cells.
        stairs = self.parent.parent.stairwells
        p = self.parent.pos
        y = self.parent.size.y-1
        N_margin = 1
        S_margin = 1
        E_margin = 3
        W_margin = 1
        carpet_pos = -1
        # 2x1 rooms we may shrink on X
        if (self.parent.size.x == 2 and self.parent.size.z == 1):
            if(p+Vec(0,y,0) in stairs or
               p+Vec(0,y+1,0) in stairs):
                W_margin += 8
            if(p+Vec(1,y,0) in stairs or
               p+Vec(1,y+1,0) in stairs):
                E_margin += 8
        # 1x2 rooms may shrink on Z
        elif (self.parent.size.x == 1 and self.parent.size.z == 2):
            if(p+Vec(0,y,0) in stairs or
               p+Vec(0,y+1,0) in stairs):
                N_margin += 8
                carpet_pos += 4
            if(p+Vec(0,y,1) in stairs or
               p+Vec(0,y+1,1) in stairs):
                S_margin += 8
                carpet_pos -= 4
        # 2x2 rooms may shrink on Z
        elif (self.parent.size.z == 2):
            if(p+Vec(0,y,0) in stairs or
               p+Vec(0,y+1,0) in stairs or
               p+Vec(1,y,0) in stairs or
               p+Vec(1,y+1,0) in stairs):
                N_margin += 8
                carpet_pos += 4
            if(p+Vec(0,y,1) in stairs or
               p+Vec(0,y+1,1) in stairs or
               p+Vec(1,y,1) in stairs or
               p+Vec(1,y+1,1) in stairs):
                S_margin += 8
                carpet_pos -= 4

        #pews
        for x in xrange( -1 * self.parent.canvasWidth()/2 + W_margin ,
                         self.parent.canvasWidth()/2 - E_margin, 1):
            for z in xrange( -1 * self.parent.canvasLength()/2 + N_margin ,
                             self.parent.canvasLength()/2 - S_margin , 1):
                p = o.trans(x,0,z)
                if( z == carpet_pos or z == carpet_pos+1 ):
                    sb(p.down(1),
                       materials.Wool, carpetColor)
                elif( x % 2 == 0):
                    sb(p,
                      materials.WoodenStairs, 1)

        #carpet continues in front of pews
        for x in xrange( self.parent.canvasWidth()/2 - E_margin,
                         self.parent.canvasWidth()/2 - E_margin + 3, 1):
            for z in xrange( carpet_pos, carpet_pos+2 , 1):
                p = o.trans(x,0,z)
                sb(p.down(1),
                   materials.Wool, carpetColor)


        #altar and deco
        deco = random.choice(self.decos)

        mats = [
            (materials.Air, 0), # 0
            deco, # 1
            (materials.StoneBrickStairs, 6), # 2
            (materials.StoneBrickStairs, 7) # 3
        ]

        template = [1,0,2,3,0,1]

        for z in xrange(6):
                p = o.trans(self.parent.canvasWidth()/2 -1,0, z+carpet_pos-2)
                sb(p,
                   mats[template[z]][0],
                   mats[template[z]][1])

class ConstructionArea(Blank):
    _name = 'constructionarea'

    def render(self):
        if (self.parent.canvasWidth() < 6 or self.parent.canvasLength() < 6):
            return

        sb = self.parent.parent.setblock
        gb = self.parent.parent.getblock
        pn = perlin.SimplexNoise(256)
        loc = self.parent.loc+Vec(0,-1,0)

        # Replace some wall sections with wooden "rebar"
        for x in xrange(self.parent.parent.room_size*self.parent.size.x):
            for z in xrange(self.parent.parent.room_size*self.parent.size.z):
                for y in xrange(self.parent.parent.room_height*self.parent.size.y-3):
                    p = self.parent.loc.trans(x,y,z) + Vec(0,1,0)
                    if (gb(p) == materials._wall and
                           pn.noise3(p.x/4.0, (p.y+1337)/4.0, p.z/4.0) < 0):
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
        y = self.parent.size.y-1
        # NW
        if(p+Vec(0,y,0) in stairs or
           p+Vec(0,y+1,0) in stairs):
            canvas = canvas - set(iterate_cube(Vec(0,y_level,0),
                                               Vec(15,y_level,15)))
        if(self.parent.size.x == 2):
            if(p+Vec(1,y,0) in stairs or
               p+Vec(1,y+1,0) in stairs):
                canvas = canvas - set(iterate_cube(Vec(16,y_level,0),
                                                   Vec(32,y_level,15)))
        if(self.parent.size.z == 2):
            if(p+Vec(0,y,1) in stairs or
               p+Vec(0,y+1,1) in stairs):
                canvas = canvas - set(iterate_cube(Vec(0,y_level,16),
                                                   Vec(15,y_level,32)))
        if(self.parent.size.x == 2 and self.parent.size.z == 2):
            if(p+Vec(1,y,1) in stairs or
               p+Vec(1,y+1,1) in stairs):
                canvas = canvas - set(iterate_cube(Vec(16,y_level,32),
                                                   Vec(16,y_level,32)))

        # A few crafting tables
        num = int(area / 128)+1
        if num > 0:
            for x in xrange(num):
                p = random.choice(list(canvas))
                canvas.remove(p)
                sb(p + loc, materials.CraftingTable)
                sb(p.down(1) + loc, materials._floor)

        # Some piles of wall blocks
        num = int(area / 128)+2
        if num > 0:
            for x in xrange(num):
                p = random.choice(list(canvas))
                canvas.remove(p)
                sb(p + loc, materials._wall)
                sb(p.down(1) + loc, materials._floor)

        # Some supply chests
        num = int(area / 256)+1
        if num > 0:
            for x in xrange(num):
                p = random.choice(list(canvas))
                canvas.remove(p)
                sb(p + loc, materials.Chest)
                sb(p.down(1) + loc, materials._floor)

                #item, probability, max stack amount
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
                                (items.byName('wooden plank'), .5, 10),
                                (items.byName('wooden slab'), .5, 10),
                                (items.byName('fence'), .5, 10),
                                (items.byName('clock'), .1, 1),
                                (items.byName('compass'), .1, 1),
                                (items.byName('stone brick'), 1, 10)]
                # Generate loot and place chest
                supplyloot = []
                for s in supply_items:
                    if (random.random() < s[1]):
                        amount = random.randint(1,min(s[2],s[0].maxstack))
                        supplyloot.append(loottable.Loot(len(supplyloot),amount,s[0].value,s[0].data,'',flag=s[0].flag))
                self.parent.parent.addchest(p + loc, loot=supplyloot)

        # Rarely, a damaged anvil
        if random.random() < .1:
            p = random.choice(list(canvas))
            canvas.remove(p)
            sb(p + loc, materials.AnvilVeryDmg, 8)
            sb(p.down(1) + loc, materials._floor)

        # Some random lumber
        num = int(area / 128)+2
        trys = 0
        while (num > 0 and trys < 100):
            trys += 1
            p = random.choice(list(canvas))
            d = random.choice([Vec(1,0,0), Vec(0,0,1)])
            # Make sure we have room for this log
            if (p+d not in canvas or
                p+d*2 not in canvas):
                continue

            data = 4
            if d == Vec(0,0,1):
                data = 8
            num -= 1
            canvas.remove(p)
            canvas.remove(p+d)
            canvas.remove(p+d*2)
            sb(p + loc, materials.Wood, data)
            sb(p.down(1) + loc, materials._floor)
            sb(p + d + loc, materials.Wood, data)
            sb(p.down(1) + d + loc, materials._floor)
            sb(p + d*2 + loc, materials.Wood, data)
            sb(p.down(1) + d*2 + loc, materials._floor)
            # maybe stack them
            if (random.random() < .5):
                p += Vec(0,-1,0)
                sb(p + loc, materials.Wood, data)
                sb(p + d + loc, materials.Wood, data)
                sb(p + d*2 + loc, materials.Wood, data)

        # Scaffolding
        num = int(area / 128)+1
        trys = 0
        while (num > 0 and trys < 100):
            trys += 1
            p = random.choice(list(canvas))
            d = [Vec(1,0,0), Vec(0,0,1), Vec(1,0,1),
                 Vec(0,0,-1), Vec(1,0,-1),
                 Vec(0,0,2), Vec(1,0,2),
                 Vec(2,0,0), Vec(2,0,1),
                 Vec(-1,0,0), Vec(-1,0,1),
                 Vec(0,0,0)]
            # Make sure we have room for this scaffold
            # Check that all offsets are a subset of the remaining canvas.
            # The extra offsets are to allow for a one block space near the
            # scaffold so the fence blocks don't try to connect to anything.
            # Plus it just looks better to have some spacing. 
            if (set([p+x for x in d]) <= canvas) is False:
                continue

            num -= 1
            canvas.remove(p)
            canvas.remove(p+d[0])
            canvas.remove(p+d[1])
            canvas.remove(p+d[2])
            p += Vec(0,1,0)
            sb(p + loc, materials._floor)
            sb(p + d[0] + loc, materials._floor)
            sb(p + d[1] + loc, materials._floor)
            sb(p + d[2] + loc, materials._floor)
            p += Vec(0,-1,0)
            sb(p + loc, materials.Fence)
            sb(p + d[0] + loc, materials.Fence)
            sb(p + d[1] + loc, materials.Fence)
            sb(p + d[2] + loc, materials.Fence)
            p += Vec(0,-1,0)
            sb(p + loc, materials.Fence)
            sb(p + d[0] + loc, materials.Fence)
            sb(p + d[1] + loc, materials.Fence)
            sb(p + d[2] + loc, materials.Fence)
            p += Vec(0,-1,0)
            sb(p + loc, materials.WoodenSlab)
            sb(p + d[0] + loc, materials.WoodenSlab)
            sb(p + d[1] + loc, materials.WoodenSlab)
            sb(p + d[2] + loc, materials.WoodenSlab)


# Catalog the features we know about. 
_features = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses if of features.Blank
    if issubclass(obj, Blank):
        _features[obj._name] = obj

def new (name, parent):
    '''Return a new instance of the feature of a given name. Supply the parent
    dungeon object.'''
    if name in _features.keys():
        return _features[name](parent)
    return Blank(parent)
