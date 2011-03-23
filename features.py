import materials
import rooms
import loottable
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
        for p in iterate_cube(c1,c3):
            self.parent.parent.setblock(p, materials._wall)
        for p in iterate_cube(c1.trans(1,1,1),c3.trans(-1, 1, -1)):
            self.parent.parent.setblock(p, materials._wall)
        for p in iterate_cube(Vec(0,-1,0), Vec(4,-1,4)):
            if (((p.x+p.z)&1) == 0):
                self.parent.parent.setblock(c1+p, materials._wall)
                self.parent.parent.setblock(c2.trans(-p.x,p.y,p.z),
                                            materials._wall)
                self.parent.parent.setblock(c3.trans(-p.x,p.y,-p.z),
                                            materials._wall)
                self.parent.parent.setblock(c4.trans(p.x,p.y,-p.z),
                                            materials._wall)
        for p in iterate_cube(c1.trans(1,0,1),
                              c3.trans(-1,-10,-1)):
            self.parent.parent.setblock(p, materials.Air)
        # Battlements (top of the tower)
        for p in iterate_cube(b1,b3):
            self.parent.parent.setblock(p, materials._wall)
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
                                    wstart.trans(5,0,0),
                                    wstart.trans(5,0,5),
                                    wstart.trans(0,0,5),
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
                              wstart.trans(3,-3,0)):
                self.parent.parent.setblock(p.trans(0,-self.height,0),
                                            materials.Air)
        # E side
        for p in iterate_cube(wstart.trans(2,0,5), wstart.trans(3,-3,5)):
                self.parent.parent.setblock(p.trans(0,-self.height,0),
                                            materials.Air)
        # N side
        for p in iterate_cube(wstart.trans(0,0,2), wstart.trans(0,-3,3)):
                self.parent.parent.setblock(p.trans(0,-self.height,0),
                                            materials.Air)
        # S side
        for p in iterate_cube(wstart.trans(5,0,2), wstart.trans(5,-3,3)):
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


class Stairwell(Blank):
    _name = 'stairwell'

    def render (self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
            start = self.parent.loc.trans(5,self.parent.parent.room_height-3,5)
            # Clear a stairwell
            for x in iterate_cube(start.trans(0,0,1), start.trans(5,-6,4)):
                self.parent.parent.setblock(x, materials.Air)
            # Draw the steps
            for x in xrange(6):
                for p in iterate_cube(start.trans(x,-x,1),
                                      start.trans(x,-x,4)):
                    self.parent.parent.setblock(p,
                                                materials.StoneStairs)
                    self.parent.parent.setblock(p.trans(0,1,0),
                                                materials.Cobblestone)

class MultiVersePortal(Blank):
    _name = 'multiverseportal'
    target = 'World1'

    def render (self):
        if (sum_points_inside_flat_poly(*self.parent.canvas) > 24):
            center = self.parent.loc.trans(self.parent.parent.room_size/2,
                                           self.parent.parent.room_height-2,
                                           self.parent.parent.room_size/2)
            centerf = Vec2f(float(self.parent.loc.x) +
                            self.parent.canvasCenter().x,
                            float(self.parent.loc.z) +
                            self.parent.canvasCenter().z)
            # Fix the floor. Clear an area for the portal.
            for p in iterate_disc(centerf, 4.5, 3.5):
                self.parent.parent.setblock(Vec(int(p.x+.5),
                                                center.y,int(p.z+.5)),
                                            materials.StoneSlab)
            for p in iterate_disc(centerf, 3.5, 2.5):
                self.parent.parent.setblock(Vec(int(p.x+.5),
                                                center.y,int(p.z+.5)),
                                            materials.Air)
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
                                       '<== Exit',
                                       '[MultiVerse]',
                                       self.target,
                                       '<== Exit')
            self.parent.parent.addsign(center.trans(-2,-1,1),
                                       '<== Exit',
                                       '[MultiVerse]',
                                       self.target,
                                       '<== Exit')
            # Treasure!
            self.parent.parent.setblock(center.trans(-3,0,0),
                                        materials.Chest)
            self.parent.parent.addchest(center.trans(-3,0,0), 
                                        loottable._maxtier)


class Chasm(Blank):
    _name = 'chasm'
    material = materials.Air
    depth = 2

    def render (self):
        if (self.parent.canvasWidth() < 4 or
            self.parent.canvasLength() < 4):
            return
        # We'll render across the while block, since that will look cool
        y = self.parent.canvasHeight()
        flip = random.randint(0,1)
        for x in xrange(2, self.parent.parent.room_size-2):
            if (flip == 1):
                for p in iterate_cube(self.parent.loc +
                                      Vec(self.parent.parent.room_size-x-1,
                                          y,
                                          x+random.randint(-1,0)),
                                      self.parent.loc +
                                      Vec(self.parent.parent.room_size-x-1,
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
        (materials.Cobblestone,0),  # Cobblestone
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

class Pool(Blank):
    _name = 'pool'

    def render (self):
        if (self.parent.canvasWidth() < 8 or self.parent.canvasLength() < 8):
            return
        y = self.parent.loc.y + self.parent.canvasHeight() - 1
        center = self.parent.canvasCenter()
        d = random.randint(5, 8)/2.0
        for p in iterate_disc(center, d, d):
            pp = Vec(self.parent.loc.x+p.x, y, self.parent.loc.z+p.z)
            self.parent.parent.setblock(pp, materials.DoubleSlab)
        for p in iterate_disc(center, d-1.0, d-1.0):
            pp = Vec(self.parent.loc.x+p.x, y, self.parent.loc.z+p.z)
            self.parent.parent.setblock(pp, materials.Water)


def new (name, parent):
    if (name == 'entrance'):
        return Entrance(parent)
    if (name == 'stairwell'):
        return Stairwell(parent)
    if (name == 'columns'):
        return Columns(parent)
    if (name == 'chasm'):
        return Chasm(parent)
    if (name == 'lavachasm'):
        return LavaChasm(parent)
    if (name == 'river'):
        return River(parent)
    if (name == 'multiverseportal'):
        return MultiVersePortal(parent)
    if (name == 'pool'):
        return Pool(parent)
    return Blank(parent)
