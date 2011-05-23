import materials
import utils
import rooms
import loottable
from noise import pnoise3
from utils import *


class Blank(object):
    _name = 'blank'

    def __init__ (self, parent):
        self.parent = parent
        self.pos = parent.pos
        cx = (parent.parent.position.x + parent.loc.x) >>4
        cz = (parent.parent.position.z - parent.loc.z + 1) >>4
        self.chunk = Vec(cx,0,cz)
        #print 'ruin chunk:', self.chunk

    def placed (self, world):
        c = self.chunk
        cd = self.parent.parent.depths
        if (c not in cd):
            cd[c] = findChunkDepth(c, world)
        self.depth = cd[c]
        vtrans = max(self.parent.parent.position.y-1, self.depth) - \
                self.parent.parent.position.y
        #print 'ruin depth:', self.parent.parent.position.y, self.depth, -vtrans
        self.loc = Vec(self.pos.x * self.parent.parent.room_size,
                       -vtrans,
                       self.pos.z * self.parent.parent.room_size)
        self.setData()

    def setData (self):
        pass

    def render (self):
        pass


class CircularTower(Blank):
    _name = 'circulartower'

    def setData(self):
        self.wallsf = iterate_tube

    def render(self):
        c1 = self.loc.trans(3, 0, 3)
        c3 = c1 + Vec(self.parent.parent.room_size-7,
                      0,
                      self.parent.parent.room_size-7)
        height = self.parent.parent.room_height*2
        #print 'ruin:', c1, c3, height
        for p in self.wallsf(c1, c3, height):
            self.parent.parent.setblock(p, materials._wall)
        ruinBlocks(c1, c3, height, self.parent.parent)


class SquareTower(CircularTower):
    _name = 'squaretower'

    def setData(self):
        self.wallsf = iterate_four_walls


class Arches(Blank):
    _name = 'arches'

    def render(self):
        height = self.parent.parent.room_height*2
        sb = self.parent.parent.setblock
        mat = materials._wall
        for xo in xrange(2):
            for zo in xrange(2):
                c1 = self.loc + Vec(8*xo, 0, 8*zo)
                c3 = c1 + Vec(7, 0, 7)
                # columns
                for p in iterate_cube(c1, c1.trans(0,-height,0)):
                    sb(p, materials._wall)
                    sb(p.trans(7,0,0), mat)
                    sb(p.trans(7,0,7), mat)
                    sb(p.trans(0,0,7), mat)
                # First level
                p = c1.trans(0,-height+2,0)
                sb(p.trans(1,0,0), mat)
                sb(p.trans(6,0,0), mat)
                sb(p.trans(0,0,1), mat)
                sb(p.trans(7,0,1), mat)
                sb(p.trans(0,0,6), mat)
                sb(p.trans(7,0,6), mat)
                sb(p.trans(1,0,7), mat)
                sb(p.trans(6,0,7), mat)
                # Second level
                p = p.trans(0,-1,0)
                sb(p.trans(1,0,0), mat)
                sb(p.trans(6,0,0), mat)
                sb(p.trans(0,0,1), mat)
                sb(p.trans(7,0,1), mat)
                sb(p.trans(0,0,6), mat)
                sb(p.trans(7,0,6), mat)
                sb(p.trans(1,0,7), mat)
                sb(p.trans(6,0,7), mat)
                # ---
                sb(p.trans(2,0,0), mat)
                sb(p.trans(5,0,0), mat)
                sb(p.trans(0,0,2), mat)
                sb(p.trans(7,0,2), mat)
                sb(p.trans(0,0,5), mat)
                sb(p.trans(7,0,5), mat)
                sb(p.trans(2,0,7), mat)
                sb(p.trans(5,0,7), mat)
                # Top layer
                p = p.trans(0,-1,0)
                for p in iterate_four_walls(p, p.trans(7,0,7), 0):
                    if (random.randint(1,100) <= 50):
                        sb(p, materials.StoneSlab)
                # Maybe ruin this section
                if (random.randint(1,100) <= 50):
                    ruinBlocks(c1, c3, height, self.parent.parent)


def ruinBlocks (p1, p2, height, dungeon):
    # pnoise3(x / 3.0, y / 3.0, z / 3.0, 1) + 1.0) / 2.0
    for x in xrange(p1.x, p2.x+1):
        for z in xrange(p1.z, p2.z+1):
            depth = (pnoise3(x / 3.0, 0, z / 3.0, 1) + 1.0) / 2.0 * height
            for p in iterate_cube(Vec(x, p1.y-depth, z),
                                  Vec(x, p1.y-height, z)):
                dungeon.delblock(p)
                #dungeon.setblock(p, materials.TNT)


def new (name, parent):
    if (name == 'blank'):
        return Blank(parent)
    if (name == 'circulartower'):
        return CircularTower(parent)
    if (name == 'squaretower'):
        return SquareTower(parent)
    if (name == 'arches'):
        return Arches(parent)
    return Blank(parent)
