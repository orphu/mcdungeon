import sys
import inspect

import materials
import rooms
import ruins
import loottable
import cfg
from utils import *


class Blank(object):
    _name = 'blank'

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
        for p in iterate_spiral(Vec(0,0,0),
                                Vec(4,0,4),
                                self.height*2+2):
            mat = materials.StoneSlab
            if ((p.y%2) == 1):
                mat = materials.DoubleSlab
            self.parent.parent.setblock(start.trans(p.x,
                                                    floor(float(p.y)/2.0),
                                                    p.z),
                                        mat)
        # Signs
        locs = [
            (Vec(-1,-2, 0),4),
            (Vec(-1,-1, 0),4),
            (Vec(-1,-2, 5),4),
            (Vec(-1,-1, 5),4),
            (Vec( 0,-2,-1),3),
            (Vec( 0,-1,-1),3),
            (Vec( 0,-2, 6),2),
            (Vec( 0,-1, 6),2),
            (Vec( 5,-2,-1),3),
            (Vec( 5,-1,-1),3),
            (Vec( 5,-2, 6),2),
            (Vec( 5,-1, 6),2),
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


class Entrance_old(Blank):
    _name = 'entrance_old'

    def placed (self):
        # Default height of the doors into the entrance.
        self.height = self.parent.parent.room_height
        # Height of the tower above entry.
        self.u = self.parent.parent.room_height*2
        self.inwater = False

    def render (self):
        start = self.parent.loc.trans(6,self.parent.parent.room_height-3,6)
        wstart = start.trans(-1,0,-1)
        b1 = wstart.trans(-1,-self.height-self.u,-1)
        b2 = b1.trans(7,0,0)
        b3 = b1.trans(7,0,7)
        b4 = b1.trans(0,0,7)
        c1 = wstart.trans(-2,-self.height-self.parent.parent.room_height,-2)
        c2 = c1.trans(9,0,0)
        c3 = c1.trans(9,0,9)
        c4 = c1.trans(0,0,9)
        # Battlements (chest level)
        #    This is the solid outer wall right under the battlements
        for p in iterate_cube(c1,c3):
            self.parent.parent.setblock(p, materials._wall)
        #    The "floor" This extends to the ground to make the base thicker. 
        for p in iterate_cube(c1.trans(1,1,1),c3.trans(-1,
                                                       self.height+2,
                                                       -1)):
            self.parent.parent.setblock(p, materials._wall)
        #    Place the battlement blocks on the wall
        for p in iterate_cube(Vec(0,-1,0), Vec(4,-1,4)):
            if (((p.x+p.z)&1) == 0):
                self.parent.parent.setblock(c1+p, materials._wall)
                self.parent.parent.setblock(c2.trans(-p.x,p.y,p.z),
                                            materials._wall)
                self.parent.parent.setblock(c3.trans(-p.x,p.y,-p.z),
                                            materials._wall)
                self.parent.parent.setblock(c4.trans(p.x,p.y,-p.z),
                                            materials._wall)
        #     Carve out a walkway
        for p in iterate_cube(c1.trans(1,0,1),
                              c3.trans(-1,-10,-1)):
            self.parent.parent.setblock(p, materials.Air)
        # Battlements (top of the tower)
        #    This is the solid outer wall right under the battlements
        for p in iterate_cube(b1,b3):
            self.parent.parent.setblock(p, materials._wall)
        #    Place the battlement blocks on the wall
        for p in iterate_cube(Vec(0,-1,0), Vec(2,-1,2)):
            if (((p.x+p.z)&1) == 0):
                self.parent.parent.setblock(b1+p, materials._wall)
                self.parent.parent.setblock(b2.trans(-p.x,p.y,p.z),
                                            materials._wall)
                self.parent.parent.setblock(b3.trans(-p.x,p.y,-p.z),
                                            materials._wall)
                self.parent.parent.setblock(b4.trans(p.x,p.y,-p.z),
                                            materials._wall)
        # Clear air space inside the tower
        for p in iterate_cube(wstart,
                              wstart.trans(5,-self.height-self.u-2,5)):
            self.parent.parent.setblock(p, materials.Air)
        # Walls
        for p in iterate_four_walls(wstart,
                                    wstart.trans(5,0,5),
                                    self.u+self.height-1):
            self.parent.parent.setblock(p, materials._wall)
        # Chest level openings
        # W side
        for p in iterate_cube(c1.trans(3,0,2), c1.trans(6,-3,2)):
            self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(c1.trans(3,0,7), c1.trans(6,-3,7)):
            self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(c1.trans(2,0,3), c1.trans(2,-3,6)):
            self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(c1.trans(7,0,3), c1.trans(7,-3,6)):
            self.parent.parent.setblock(p, materials.Air)
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
        # Ground level openings
        # W side
        for p in iterate_cube(wstart.trans(2,0,0),
                              wstart.trans(3,-3,-1)):
                self.parent.parent.setblock(p.trans(0,-self.height,0),
                                            materials.Air)
        # E side
        for p in iterate_cube(wstart.trans(2,0,5), wstart.trans(3,-3,6)):
                self.parent.parent.setblock(p.trans(0,-self.height,0),
                                            materials.Air)
        # N side
        for p in iterate_cube(wstart.trans(0,0,2), wstart.trans(-1,-3,3)):
                self.parent.parent.setblock(p.trans(0,-self.height,0),
                                            materials.Air)
        # S side
        for p in iterate_cube(wstart.trans(5,0,2), wstart.trans(6,-3,3)):
                self.parent.parent.setblock(p.trans(0,-self.height,0),
                                            materials.Air)
        # Draw the staircase
        for p in iterate_spiral(Vec(0,0,0),
                                Vec(4,0,4),
                                (self.u+self.height)*2):
            mat = materials.StoneSlab
            dat = 0
            if ((p.y%2) == 1):
                mat = materials.DoubleSlab
                dat = 0
            self.parent.parent.setblock(start.trans(p.x,
                                                    floor(float(p.y)/2.0),
                                                    p.z),
                                        mat)
            self.parent.parent.blocks[start.trans(p.x,
                                                  floor(float(p.y)/2.0),
                                                  p.z)].data = dat
        # Supply chest
        pos = c1.trans(1, 0, 1)
        self.parent.parent.setblock(pos, materials.Chest)
        self.parent.parent.addchest(pos, 0)
        # Ruin
        if (random.randint(1,100) <= cfg.tower_ruin):
            r = self.parent.parent.room_height*2
            ruins.ruinBlocks(b1.trans(0,r-1,0),
                             b3.trans(0,r-1,0),
                             r,
                             self.parent.parent)
        # Signs
        locs = [
            (Vec(-1,-2, 0),4),
            (Vec(-1,-1, 0),4),
            (Vec(-1,-2, 5),4),
            (Vec(-1,-1, 5),4),
            (Vec( 0,-2,-1),3),
            (Vec( 0,-1,-1),3),
            (Vec( 0,-2, 6),2),
            (Vec( 0,-1, 6),2),
            (Vec( 5,-2,-1),3),
            (Vec( 5,-1,-1),3),
            (Vec( 5,-2, 6),2),
            (Vec( 5,-1, 6),2),
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
            #print 'Sign:', wstart+loc[0], loc[1]
            #print sign['s1']
            #print sign['s2']
            #print sign['s3']
            #print sign['s4']

        # Sandbar island
        if (self.inwater is False):
            return
        d = 2
        s1 = wstart.trans(-3,-self.height,-3)
        s3 = wstart.trans(8,-self.height,8)
        for y in xrange(self.parent.parent.room_height +
                        self.height):
            for p in iterate_disc(s1.trans(-d,y+1,-d),
                                  s3.trans(d,y+1,d)):
                if (p not in self.parent.parent.blocks):
                    self.parent.parent.setblock(p, materials._sandbar)
            d += 1

class Stairwell(Blank):
    _name = 'stairwell'

    def render (self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
            start = self.parent.loc.trans(5,self.parent.parent.room_height-3,5)
            # Clear a stairwell
            for x in iterate_cube(start.trans(0,0,1), start.trans(5,-5,4)):
                self.parent.parent.setblock(x, materials.Air)
            # Draw the steps
            for x in xrange(6):
                for p in iterate_cube(start.trans(x,-x,1),
                                      start.trans(x,-x,4)):
                    self.parent.parent.setblock(p,
                                                materials.StoneStairs)
                    self.parent.parent.setblock(p.trans(0,1,0),
                                                materials.meta_mossycobble)

class TreasureRoom(Blank):
    _name = 'treasureroom'

    def render (self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) > 24):
            center = self.parent.loc.trans(self.parent.parent.room_size/2,
                                           self.parent.parent.room_height-2,
                                           self.parent.parent.room_size/2)
            # Fix the floor. Clear an area 
            for p in iterate_disc(center.trans(-4, 0, 3),
                                  center.trans(3, 0, -4)):
                self.parent.parent.setblock(p, materials.Air)
            for p in iterate_ellipse(center.trans(-4, 0, 3),
                                  center.trans(3, 0, -4)):
                self.parent.parent.setblock(p, materials.StoneSlab)
            # Treasure!
            self.parent.parent.setblock(center,
                                        materials.Chest)
            self.parent.parent.addchest(center, 
                                        loottable._maxtier)

class MultiVersePortal(Blank):
    _name = 'multiverseportal'
    target = 'World1'

    def render (self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) > 24):
            center = self.parent.loc.trans(self.parent.parent.room_size/2,
                                           self.parent.parent.room_height-2,
                                           self.parent.parent.room_size/2)
            # Fix the floor. Clear an area for the portal.
            for p in iterate_disc(center.trans(-4, 0, 3),
                                  center.trans(3, 0, -4)):
                self.parent.parent.setblock(p, materials.Air)
            for p in iterate_ellipse(center.trans(-4, 0, 3),
                                  center.trans(3, 0, -4)):
                self.parent.parent.setblock(p, materials.StoneSlab)
            # Obsidian portal frame.
            for p in iterate_cube(center.trans(-2,1,0), center.trans(1,-3,0)):
                self.parent.parent.setblock(p, materials.Obsidian)
            # Portal stuff.
            for p in iterate_cube(center.trans(-1,0,0), center.trans(0,-2,0)):
                self.parent.parent.setblock(p, materials.NetherPortal)
            # Signs.
            self.parent.parent.setblock(center.trans(1,-1,-1),
                                        materials.WallSign)
            self.parent.parent.blocks[center.trans(1,-1,-1)].data = 3
            self.parent.parent.setblock(center.trans(-2,-1,1),
                                        materials.WallSign)
            self.parent.parent.blocks[center.trans(-2,-1,1)].data = 2
            # Create the tile entities for the signs.
            self.parent.parent.addsign(center.trans(1,-1,-1),
                                       '[multiverse]',
                                       self.target,
                                       '','')
            self.parent.parent.addsign(center.trans(-2,-1,1),
                                       '[multiverse]',
                                       self.target,
                                       '', '')
            # Treasure!
            self.parent.parent.setblock(center.trans(-2,0,-3),
                                        materials.Chest)
            self.parent.parent.addchest(center.trans(-2,0,-3),
                                        loottable._maxtier)


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
        (materials.Stone,0),  # Stone
        (materials.meta_mossycobble,0),  # Mossy Cobble
        (materials.Wood,0), # Wood
        (materials.Wood,1), # Redwood
        (materials.Bedrock,0), # Bedrock
        (materials.Sandstone,0), # Sandstone
        (materials.DoubleSlab,0), # DoubleSlab
        (materials.Obsidian,0), # Obsidian
        (materials.Glowstone,0) # Glowstone
    )

    def render (self):
        if (self.parent.canvasWidth() < 6 or self.parent.canvasLength() < 6):
            return
        c = self.parent.canvasCenter()
        y = self.parent.canvasHeight()
        start = random.randint(0, int(self.parent.canvasWidth() / 2)-1)
        stop = int(self.parent.canvasWidth() / 2)
        step = random.randint(2, 3)
        mat = random.choice(self.mats)
        for x in xrange(start, stop, step):
            for p in iterate_cube(Vec(c.x-x, 1, c.z-x),
                                  Vec(c.x-x, 4, c.z-x)):
                self.parent.parent.setblock(self.parent.loc+p, mat[0])
                self.parent.parent.blocks[self.parent.loc+p].data = mat[1]
            for p in iterate_cube(Vec(c.x+x+1, 1, c.z-x),
                                  Vec(c.x+x+1, 4, c.z-x)):
                self.parent.parent.setblock(self.parent.loc+p, mat[0])
                self.parent.parent.blocks[self.parent.loc+p].data = mat[1]
            for p in iterate_cube(Vec(c.x-x, 1, c.z+x+1),
                                  Vec(c.x-x, 4, c.z+x+1)):
                self.parent.parent.setblock(self.parent.loc+p, mat[0])
                self.parent.parent.blocks[self.parent.loc+p].data = mat[1]
            for p in iterate_cube(Vec(c.x+x+1, 1, c.z+x+1),
                                  Vec(c.x+x+1, 4, c.z+x+1)):
                self.parent.parent.setblock(self.parent.loc+p, mat[0])
                self.parent.parent.blocks[self.parent.loc+p].data = mat[1]


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
        for p in iterate_cube(c.north(4), c.south(4)):
            sb(p, materials.RedStoneWire)
        for p in iterate_cube(c.east(4), c.west(4)):
            sb(p, materials.RedStoneWire)
        for p in iterate_four_walls(c.trans(-2,0,-2), c.trans(2,0,2),0):
            sb(p, materials.RedStoneWire)


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
        platform = random.choice([materials.WoodPlanks,
                                  materials.meta_mossycobble,
                                  materials.Stone,
                                  materials.Sandstone])
        steps = random.choice([materials.WoodenSlab,
                               materials.CobblestoneSlab,
                               materials.StoneSlab,
                               materials.SandstoneSlab])
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

    def render(self):
        o = self.parent.loc.trans(2,0,2)
        sb = self.parent.parent.setblock

        # Reform the room.
        # Air space
        for p in iterate_cube(o.trans(1,1,1), o.trans(10,3,10)):
            sb(p, materials.Air)
        # Walls
        for p in iterate_four_walls(o, o.trans(11,0,11),-4):
            sb(p, materials._wall)
        # Ceiling
        for p in iterate_cube(o, o.trans(11,0,11)):
            sb(p, materials._ceiling)
        # Floor
        for p in iterate_cube(o.trans(0,4,0), o.trans(11,4,11)):
            sb(p, materials._floor)
        # Book cases
        for p in iterate_four_walls(o.trans(1,1,1), o.trans(10,1,10),-2):
            sb(p, materials.Bookshelf)
        for p in (Vec(1,1,3), Vec(1,1,8),
                  Vec(3,1,1), Vec(3,1,10),
                  Vec(8,1,1), Vec(8,1,10),
                  Vec(10,1,3), Vec(10,1,8)):
            for q in iterate_cube(o+p, o+p.down(2)):
                sb(q, materials.Air)
        # Torches
        for p in (Vec(2,3,2), Vec(2,3,9),
                  Vec(9,3,2), Vec(9,3,9)):
            sb(o+p, materials.Fence)
            sb(o+p.up(1), materials.Torch, 5)

        # Desk
        mats = [
            materials.Air,          # 0
            materials.WoodPlanks,   # 1
            materials.Chest,        # 2
            materials.CraftingTable,# 3
            materials.WallSign,     # 4
            materials.WoodenStairs  # 5
        ]
        template = [
            [2,1,1,3],
            [0,4,5,4]
        ]
        oo = o.trans(5,3,4)
        for x in xrange(2):
            for z in xrange(4):
                p = oo.trans(x,0,z)
                sb(p, mats[template[x][z]])
        self.parent.parent.blocks[o+Vec(6,3,5)].data = 3
        self.parent.parent.blocks[o+Vec(6,3,6)].data = 0
        self.parent.parent.blocks[o+Vec(6,3,7)].data = 2
        sb(o.trans(5,2,5), materials.Torch)
        self.parent.parent.addchest(oo)

        # Hallway
        # Find the direction, room, and connecting room.
        # room = this room
        # d = direction out of this room
        # offset = offset of the hallways
        # oroom = connecting room
        # od = direction out of the connecting room
        # length = legth of the opposite hall

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

        # Figure our out deltas. There are 8 possibilities based on direction
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
        spos = spos + dl*length - dw

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
            [materials.Bookshelf,0],    # 2
            [materials.Stone,0],        # 3
            [materials._wall,0],        # 4
            [materials.RedStoneWire,0], # 5
            [materials.StickyPiston,2], # 6 - toggle piston
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
            [ 8, 8, 8, 8, 8]],
           [[ 1, 1, 1,12, 4],
            [ 2, 4, 4, 4, 4],
            [ 2, 1, 1, 1, 4],
            [ 2, 1, 1, 1, 4],
            [ 2, 1, 1, 1, 4]],
           [[ 1, 7, 1 ,1,13],
            [ 2, 4, 6, 1, 4],
            [ 2,11, 9, 9, 4],
            [ 2, 5,10,10, 4],
            [ 2, 5, 5, 5, 4]],
           [[ 1, 1, 1, 1,13],
            [ 2, 4, 6, 1, 4],
            [ 2, 3, 9, 9, 4],
            [ 2, 3, 3, 3, 4],
            [ 2, 3, 3, 3, 4]],
           [[14,14,14,14,14],
            [14,14,14,14,14],
            [14,14,14,14,14],
            [14,14,14,14,14],
            [14,14,14,14,14]],
           [[15,15,15,15,15],
            [15,15,15,15,15],
            [15,15,15,15,15],
            [15,15,15,15,15],
            [15,15,15,15,15]],
        ]
        bdata = 4

        # Data adjustments for directions. There are 8, but the defaults are
        # for East, low offset. 

        # West
        if d == 0:
            bdata = 3
            if offset >= 7:
                mats[6][1] = 3
                mats[7][1] = 1
                mats[9][1] = 5
                mats[10][1] = 1
                mats[11][1] = 5
            else:
                mats[6][1] = 3

        # South
        if d == 1:
            bdata = 1
            if offset >= 7:
                mats[6][1] = 5
                mats[7][1] = 4
                mats[9][1] = 2
                mats[10][1] = 0
                mats[11][1] = 4
            else:
                mats[6][1] = 5
                mats[7][1] = 3
                mats[9][1] = 3
                mats[10][1] = 2
                mats[11][1] = 6

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
                mats[7][1] = 4
                mats[9][1] = 2
                mats[10][1] = 0
                mats[11][1] = 4
            else:
                mats[6][1] = 4
                mats[7][1] = 3
                mats[9][1] = 3
                mats[10][1] = 2
                mats[11][1] = 6

        # Draw the mechanism
        for y in xrange(6):
            for w in xrange(5):
                for l in xrange(5):
                    p = spos+dl*l+dw*w+Vec(0,1,0)*y
                    sb(p, mats[template[y][w][l]][0],
                          mats[template[y][w][l]][1])

        # The button.
        p = spos+dl*3+dw*4+Vec(0,1,0)*2
        blocks = self.parent.parent.blocks
        while blocks[p+dl].material != materials.Air:
            sb(p.up(1), materials.Air)
            sb(p, materials.RedStoneWire)
            sb(p.down(1), materials.Stone)
            p = p + dl
        sb(p+dl, materials.StoneButton, bdata)

        # Clear out extra space inside the room
        p = spos.down(1)
        for q in iterate_cube(p, p-dl*2+Vec(0,2,0)):
            sb(q, materials.Air)

        # Clear out any doors or extra torches in this room
        for p in iterate_cube(o, o.trans(11,4,11)):
            if p in self.parent.parent.doors:
                del(self.parent.parent.doors[p])
            if p in self.parent.parent.torches:
                del(self.parent.parent.torches[p])

        # Clear doors and torches from the entry way
        p = spos+dl*4
        for q in iterate_cube(p.trans(-1,0,-1), p.trans(1,4,1)):
            if q in self.parent.parent.doors:
                del(self.parent.parent.doors[q])
            if q in self.parent.parent.torches:
                del(self.parent.parent.torches[q])

        # Kill the canvas to prevent spawners and chests from appearing
        self.parent.canvas = (
            Vec(0,0,0),
            Vec(0,0,0),
            Vec(0,0,0))

        # Cobwebs
        webs = {}
        for p in iterate_cube(o, o.trans(11,3,11)):
            count = 0
            perc = 80 - (p.y - o.y) * (70/5)
            if (p not in blocks or
                blocks[p].material != materials.Air):
                continue
            for q in (Vec(1,0,0), Vec(-1,0,0),
                      Vec(0,1,0), Vec(0,-1,0),
                      Vec(0,0,1), Vec(0,0,-1)):
                if (p+q in blocks and
                    blocks[p+q].material != materials.Air and
                    random.randint(1,100) <= perc):
                    count += 1
            if count >= 3:
                webs[p] = True
        for p, q in webs.items():
            sb(p, materials.Cobweb)


class Forge(Blank):
    _name = 'forge'

    def render(self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return

        sb = self.parent.parent.setblock

        mats = [
            materials.Air,          # 0
            materials.Furnace,      # 1
            materials.DoubleSlab,   # 2
            materials.Water,        # 3
            materials.BrickBlock,   # 4
            materials.StoneSlab,    # 5
            materials.Lava,         # 6
            materials.Chest,        # 7
            materials.CraftingTable # 8
        ]

        template = [
            [7,2,5,2,2,1],
            [2,3,4,6,6,2],
            [2,3,4,6,6,2],
            [8,2,5,2,2,1]
        ]

        o = self.parent.loc.trans(6, 3, 5)

        for x in xrange(4):
            for z in xrange(6):
                p = o.trans(x,0,z)
                sb(p, mats[template[x][z]])

        sb (o.trans(0,-2,3), materials.StoneStairs, 0)
        sb (o.trans(0,-2,4), materials.StoneStairs, 0)
        sb (o.trans(3,-2,3), materials.StoneStairs, 1)
        sb (o.trans(3,-2,4), materials.StoneStairs, 1)
        sb (o.trans(1,-2,5), materials.StoneStairs, 2)
        sb (o.trans(2,-2,5), materials.StoneStairs, 2)
        sb (o.trans(1,-2,2), materials.StoneStairs, 3)
        sb (o.trans(2,-2,2), materials.StoneStairs, 3)

        sb (o.trans(0,0,3), materials.StoneStairs, 0)
        sb (o.trans(0,0,4), materials.StoneStairs, 0)
        sb (o.trans(3,0,3), materials.StoneStairs, 1)
        sb (o.trans(3,0,4), materials.StoneStairs, 1)
        sb (o.trans(1,0,5), materials.StoneStairs, 2)
        sb (o.trans(2,0,5), materials.StoneStairs, 2)

class Pool(Blank):
    _name = 'pool'

    def render (self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return
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
            self.parent.parent.setblock(p.up(1), materials.StoneSlab)


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
