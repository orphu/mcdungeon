import sys
import inspect

import materials
import utils
import rooms
import loottable
import cfg
import perlin
from utils import *


class Blank(object):
    _name = 'blank'

    def __init__ (self, parent):
        self.parent = parent
        self.pos = parent.pos
        cx = (parent.parent.position.x + parent.loc.x) >>4
        cz = (parent.parent.position.z - parent.loc.z) >>4
        self.chunk = Vec(cx,0,cz)
        #print 'ruin chunk:', self.chunk

    def placed (self, world):
        self.depth = self.parent.parent.good_chunks[self.chunk.x, self.chunk.z]
        self.vtrans = max(self.parent.parent.position.y-1, self.depth) - \
                self.parent.parent.position.y
        #print 'ruin depth:', self.parent.parent.position.y, self.depth, -vtrans
        self.loc = Vec(self.pos.x * self.parent.parent.room_size,
                       -self.vtrans,
                       self.pos.z * self.parent.parent.room_size)
        self.setData()

    def setData (self):
        pass

    def render (self):
        pass


class RoundTowerEntrance(Blank):
    _name = 'roundtowerentrance'
    _ruin = False

    def render (self):
        # The room floor Y location
        room_floor = self.parent.loc.y+self.parent.parent.room_height-3
        # The height of one room
        rheight = self.parent.parent.room_height
        # Entrance Level
        elev = room_floor - self.parent.parent.entrance.low_height
        # Ground level
        glev = room_floor - self.parent.parent.entrance.high_height
        # Chest level
        clev = glev - rheight
        # Battlement level
        blev = glev  - rheight * 2 * cfg.tower
        maxlev = 127 - self.parent.parent.position.y
        if -blev >= maxlev:
            blev = -maxlev+2

        # corner of the inner shaft
        start = Vec(self.parent.loc.x+6,
                    glev,
                    self.parent.loc.z+6)
        # Corner of the inner wall
        wstart = start.trans(-1,0,-1)
        # B Level is the upper battlements level
        b1 = Vec(wstart.x-1, blev, wstart.z-1)
        b2 = b1.trans(7,0,0)
        b3 = b1.trans(7,0,7)
        b4 = b1.trans(0,0,7)
        # C level is the chest level
        c1 = Vec(wstart.x-4, clev, wstart.z-4)
        c2 = c1.trans(13,0,0)
        c3 = c1.trans(13,0,13)
        c4 = c1.trans(0,0,13)
        # lower tower from ground up to chest level. 
        #    The floor
        for p in iterate_cylinder(Vec(c1.x, glev, c1.z),Vec(c3.x, elev+1, c3.z)):
            self.parent.parent.setblock(p, materials._wall)
        #    The ceiling
        for p in iterate_cylinder(Vec(c1.x, clev+1, c1.z),Vec(c3.x, clev+1, c3.z)):
            self.parent.parent.setblock(p, materials._wall)
        #    Outer wall and airspace
        for p in iterate_cylinder(c1.down(2),Vec(c3.x, glev, c3.z)):
            self.parent.parent.setblock(p, materials.Air)
        for p in iterate_tube(Vec(c1.x,elev,c1.z),
                              Vec(c3.x,elev,c3.z),
                              abs(elev-clev)):
            self.parent.parent.setblock(p, materials._wall)
        #    Battlements
        for p in iterate_cube(Vec(0,0,0), Vec(5,0,5)):
            if (((p.x+p.z)&1) == 1):
                self.parent.parent.setblock(c1+p, materials.Air)
                self.parent.parent.setblock(c2.trans(-p.x,p.y,p.z),
                                            materials.Air)
                self.parent.parent.setblock(c3.trans(-p.x,p.y,-p.z),
                                            materials.Air)
                self.parent.parent.setblock(c4.trans(p.x,p.y,-p.z),
                                            materials.Air)
        # Upper tower from chest level to battlement
        for p in iterate_cylinder(b1,Vec(b3.x, clev, b3.z)):
            self.parent.parent.setblock(p, materials._wall)
        for p in iterate_cube(Vec(0,0,0), Vec(4,0,4)):
            if (((p.x+p.z)&1) == 1):
                self.parent.parent.setblock(b1+p, materials.Air)
                self.parent.parent.setblock(b2.trans(-p.x,p.y,p.z),
                                            materials.Air)
                self.parent.parent.setblock(b3.trans(-p.x,p.y,-p.z),
                                            materials.Air)
                self.parent.parent.setblock(b4.trans(p.x,p.y,-p.z),
                                            materials.Air)
        # Chest level openings
        # W/E
        for p in iterate_cube(Vec(b1.x+3,clev,b1.z),
                              Vec(b1.x+4,clev-2,b1.z+7)):
                self.parent.parent.setblock(p, materials.Air)
        # N/S 
        for p in iterate_cube(Vec(b1.x,clev,b1.z+3),
                              Vec(b1.x+7,clev-2,b1.z+4)):
                self.parent.parent.setblock(p, materials.Air)
        # Ground level openings
        # W side
        for p in iterate_cube(wstart.trans(2,0,0), wstart.trans(3,-2,-4)):
                self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(wstart.trans(2,0,5), wstart.trans(3,-2,9)):
                self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(wstart.trans(0,0,2), wstart.trans(-4,-2,3)):
                self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(wstart.trans(5,0,2), wstart.trans(9,-2,3)):
                self.parent.parent.setblock(p, materials.Air)
        # Clear air space inside the stairwell shaft
        for p in iterate_cube(Vec(wstart.x+1, elev+1, wstart.z+1),
                              Vec(wstart.x+4, blev-2, wstart.z+4)):
            self.parent.parent.setblock(p, materials.Air)
        # Internal columns
        for p in iterate_cube(Vec(b1.x+1, elev, b1.z+1),
                              Vec(b1.x+1, clev, b1.z+1)):
            self.parent.parent.setblock(p, materials.DoubleSlab)
        for p in iterate_cube(Vec(b2.x-1, elev, b2.z+1),
                              Vec(b2.x-1, clev, b2.z+1)):
            self.parent.parent.setblock(p, materials.DoubleSlab)
        for p in iterate_cube(Vec(b3.x-1, elev, b3.z-1),
                              Vec(b3.x-1, clev, b3.z-1)):
            self.parent.parent.setblock(p, materials.DoubleSlab)
        for p in iterate_cube(Vec(b4.x+1, elev, b4.z-1),
                              Vec(b4.x+1, clev, b4.z-1)):
            self.parent.parent.setblock(p, materials.DoubleSlab)
        # (re)draw the staircase
        mat1 = materials.WoodenSlab
        mat2 = materials.WoodPlanks
        if random.randint(1,100) <= 50:
            mat1 = materials.StoneSlab
            mat2 = materials.DoubleSlab
        for p in iterate_spiral(Vec(start.x,room_floor+4,start.z),
                                Vec(start.x+4,room_floor+4,start.z+4),
                                (room_floor-blev)*2):
            mat = mat1
            if ((p.y%2) == 0):
                mat = mat2
            self.parent.parent.setblock(Vec(p.x,
                                        p.y/2,
                                        p.z), mat)
        # Supply chest
        pos = Vec(b1.x, clev, b1.z-1)
        self.parent.parent.setblock(pos, materials.Chest)
        self.parent.parent.addchest(pos, 0)

        # Ruin
        if self._ruin == True:
            ruinBlocks(b1.trans(0,rheight-1,0),
                       b3.trans(0,rheight-1,0),
                       rheight,
                       self.parent.parent)
        # Sandbar island
        if (self.parent.parent.entrance.inwater is False):
            return
        d = 2
        s1 = Vec(wstart.x-3, glev+1, wstart.z-3)
        s3 = Vec(wstart.x+8, glev+1, wstart.z+8)
        for y in xrange(rheight):
            for p in iterate_disc(s1.trans(-d,y,-d),
                                  s3.trans(d,y,d)):
                if (p not in self.parent.parent.blocks):
                    self.parent.parent.setblock(p, materials._sandbar)
            d += 1


class SquareTowerEntrance(Blank):
    _name = 'squaretowerentrance'
    _ruin = False

    def render (self):
        # The room floor Y location
        room_floor = self.parent.loc.y+self.parent.parent.room_height-3
        # The height of one room
        rheight = self.parent.parent.room_height
        # Entrance Level
        elev = room_floor - self.parent.parent.entrance.low_height
        # Ground level
        glev = room_floor - self.parent.parent.entrance.high_height
        # Chest level
        clev = glev - rheight
        # Battlement level
        blev = glev  - rheight * 2 * cfg.tower
        maxlev = 127 - self.parent.parent.position.y
        if -blev >= maxlev:
            blev = -maxlev+2

        # corner of the inner shaft
        start = Vec(self.parent.loc.x+6,
                    glev,
                    self.parent.loc.z+6)
        # Corner of the inner wall
        wstart = start.trans(-1,0,-1)
        # B Level is the upper battlements level
        b1 = Vec(wstart.x-1, blev, wstart.z-1)
        b2 = b1.trans(7,0,0)
        b3 = b1.trans(7,0,7)
        b4 = b1.trans(0,0,7)
        # C level is the chest level
        c1 = Vec(wstart.x-2, clev, wstart.z-2)
        c2 = c1.trans(9,0,0)
        c3 = c1.trans(9,0,9)
        c4 = c1.trans(0,0,9)
        # Chest level battlements
        #    This is the solid outer wall right under the battlements
        for p in iterate_cube(c1,c3):
            self.parent.parent.setblock(p, materials._wall)
        #    The "floor" This extends to the ground to make the base thicker. 
        for p in iterate_cube(c1.trans(1,1,1),Vec(c3.x-1,
                                                  elev,
                                                  c3.z-1)):
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
        for p in iterate_cube(Vec(wstart.x, elev, wstart.z),
                              Vec(wstart.x+5, blev-2, wstart.z+5)):
            self.parent.parent.setblock(p, materials.Air)
        # Walls
        for p in iterate_four_walls(Vec(wstart.x, elev, wstart.z),
                                    Vec(wstart.x+5, elev, wstart.z+5),
                                    elev-blev-1):
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
        # Ground level openings
        # W side
        for p in iterate_cube(wstart.trans(2,0,0),
                              wstart.trans(3,-3,-1)):
                self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(wstart.trans(2,0,5), wstart.trans(3,-3,6)):
                self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(wstart.trans(0,0,2), wstart.trans(-1,-3,3)):
                self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(wstart.trans(5,0,2), wstart.trans(6,-3,3)):
                self.parent.parent.setblock(p, materials.Air)
        # (re)draw the staircase
        mat1 = materials.WoodenSlab
        mat2 = materials.WoodPlanks
        if random.randint(1,100) <= 50:
            mat1 = materials.StoneSlab
            mat2 = materials.DoubleSlab
        for p in iterate_spiral(Vec(start.x,room_floor+4,start.z),
                                Vec(start.x+4,room_floor+4,start.z+4),
                                (room_floor-blev)*2):
            mat = mat1
            if ((p.y%2) == 0):
                mat = mat2
            self.parent.parent.setblock(Vec(p.x,
                                        p.y/2,
                                        p.z), mat)
        # Supply chest
        pos = c1.trans(1, 0, 1)
        self.parent.parent.setblock(pos, materials.Chest)
        self.parent.parent.addchest(pos, 0)

        # Ruin
        if self._ruin == True:
            ruinBlocks(b1.trans(0,rheight-1,0),
                       b3.trans(0,rheight-1,0),
                       rheight,
                       self.parent.parent)
        # Sandbar island
        if (self.parent.parent.entrance.inwater is False):
            return
        d = 2
        s1 = Vec(wstart.x-3, glev+1, wstart.z-3)
        s3 = Vec(wstart.x+8, glev+1, wstart.z+8)
        for y in xrange(rheight):
            for p in iterate_disc(s1.trans(-d,y,-d),
                                  s3.trans(d,y,d)):
                if (p not in self.parent.parent.blocks):
                    self.parent.parent.setblock(p, materials._sandbar)
            d += 1

class RuinedSquareTowerEntrance(SquareTowerEntrance):
    _name = 'ruinedsquaretowerentrance'
    _ruin = True

class RuinedRoundTowerEntrance(RoundTowerEntrance):
    _name = 'ruinedroundtowerentrance'
    _ruin = True

class CircularTower(Blank):
    _name = 'circulartower'

    def setData(self):
        self.wallsf = iterate_tube

    def render(self):
        c1 = self.loc.trans(3, 0, 3)
        c3 = c1 + Vec(self.parent.parent.room_size-7,
                      0,
                      self.parent.parent.room_size-7)
        height = int(self.parent.parent.room_height*1.5)
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
                    if (cfg.ruin_ruins == False or
                        random.randint(1,100) <= 50):
                        if (random.randint(1,100) <= 25):
                            sb(p, materials.StoneSlab)
                        else:
                            sb(p, materials.CobblestoneSlab)

                # Maybe ruin this section
                if (random.randint(1,100) <= 50):
                    ruinBlocks(c1, c3, height, self.parent.parent)


def ruinBlocks (p1, p2, height, dungeon, override=False):
    pn = perlin.SimplexNoise(256)
    if (override == True or
        cfg.ruin_ruins == False):
        return
    for x in xrange(p1.x, p2.x+1):
        for z in xrange(p1.z, p2.z+1):
            depth = (pn.noise3(x / 4.0, 0, z / 4.0) + 1.0) / 2.0 * height
            for p in iterate_cube(Vec(x, p1.y-depth, z),
                                  Vec(x, p1.y-height, z)):
                dungeon.delblock(p)
                #dungeon.setblock(p, materials.TNT)

# Catalog the ruins we know about. 
_ruins = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses if of ruins.Blank
    if issubclass(obj, Blank):
        _ruins[obj._name] = obj

def new (name, parent):
    '''Return a new instance of the ruin of a given name. Supply the parent
    dungeon object.'''
    if name in _ruins.keys():
        return _ruins[name](parent)
    return Blank(parent)

