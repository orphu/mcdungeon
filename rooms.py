import sys
import inspect

import materials
import halls
import floors
import features
import ruins
import cfg
from utils import *
import random
import perlin
import cave_factory


class Blank(object):
    _name = 'blank'
    _min_size = Vec(1,1,1)
    _max_size = Vec(1,1,1)
    size = Vec(1,1,1)
    _is_entrance = False
    _is_stairwell = False
    _is_treasureroom = False

    def __init__ (self, parent, pos):
        self.parent = parent
        self.pos = pos
        self.loc = Vec(
            self.pos.x * self.parent.room_size,
            self.pos.y * self.parent.room_height,
            self.pos.z * self.parent.room_size)
        self.halls = [None, None, None, None]
        self.features = []
        self.floors = []
        self.ruins = []
        self.setData()
        for x in xrange(4):
            if self.hallLength[x] == 0:
                self.halls[x] = halls.new('Blank', self, x, 0)

    def placed(self):
        return [self.pos]

    def setData(self):
        # West, South, East, North
        self.hallLength = [0,0,0,0]
        self.hallSize = [[1,15], [1,15], [1,15], [1,15]]
        self.canvas = (
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0))

    def canvasWidth(self):
        x1 = min([p.x for p in self.canvas])
        x2 = max([p.x for p in self.canvas])
        if (x1 == 0 and x2 == 0):
            return 0
        return x2 - x1 + 1

    def canvasLength(self):
        z1 = min([p.z for p in self.canvas])
        z2 = max([p.z for p in self.canvas])
        if (z1 == 0 and z2 == 0):
            return 0
        return z2 - z1 + 1

    def canvasHeight(self):
        return min([p.y for p in self.canvas])

    def canvasCenter(self):
        cx = (self.canvasWidth()-1)/2.0+min([p.x for p in self.canvas])
        cz = (self.canvasLength()-1)/2.0+min([p.z for p in self.canvas])
        return Vec2f(cx,cz)

    def render (self):
        pass

    def testHall (self, side, size, a1, b1):
        ''' Test to see if a hall will fit. return false if not, else
        return a range of valid offsets'''
        # This side is not allowed to have a hallway
        if (self.hallLength[side] == 0):
            return False
        # Edge of the map
        if (self.isOnEdge(side)):
            return False
        b1 -= size
        a2 = self.hallSize[side][0]
        b2 = self.hallSize[side][1] - size
        a3 = max(a1, a2)
        b3 = min(b1, b2)
        if (b3 - a3 < 0):
            return False
        return (a3, b3)

    def isOnEdge (self, side):
        # North edge of the map
        if (side == 0 and self.pos.z == 0):
            return True
        # East edge of the map
        if (side == 1 and self.pos.x == self.parent.xsize-1):
            return True
        # South edge of the map
        if (side == 2 and self.pos.z == self.parent.zsize-1):
            return True
        # West edge of the map
        if (side == 3 and self.pos.x == 0):
            return True
        return False


class Basic(Blank):
    _name = 'basic'
    _is_entrance = True
    _is_stairwell = True

    def setData(self):
        self.wall_func = iterate_four_walls
        self.ceil_func = iterate_cube
        self.floor_func = iterate_cube
        self.air_func = iterate_cube

        # size of the room
        sx = self.size.x * self.parent.room_size
        sz = self.size.z * self.parent.room_size
        sy = self.size.y * self.parent.room_height

        # Some paramters. 
        self.c1 = self.loc + Vec(2,sy-2,2)
        self.c3 = self.c1 + Vec(sx-5, 0, sz-5)

        self.hallLength = [3,3,3,3]
        self.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        self.canvas = (
            Vec(4   ,sy-2, 4),
            Vec(sx-5,sy-2, 4),
            Vec(sx-5,sy-2, sz-5),
            Vec(4   ,sy-2, sz-5))

    def render (self):
        height = self.size.y * self.parent.room_height - 2
        # Air space
        for x in self.air_func(self.c1.up(1), self.c3.up(3)):
            self.parent.setblock(x, materials.Air)
        # Floor
        for x in self.floor_func(self.c1, self.c3):
            self.parent.setblock(x, materials._floor)
        # Ceiling
        for x in self.ceil_func(self.c1.up(height), self.c3.up(height)):
            self.parent.setblock(x, materials._ceiling)
        # Walls
        for x in self.wall_func(self.c1, self.c3, height):
            self.parent.setblock(x, materials._wall)
        # Subfloor
        sf1 = self.loc.trans(0,
                             self.size.y * self.parent.room_height - 1,
                             0)
        sf2 = sf1.trans(self.size.x * self.parent.room_size-1,
                       0,
                       self.size.z * self.parent.room_size-1)
        for x in iterate_plane(sf1, sf2):
            self.parent.setblock(x, materials._subfloor)

class Basic2x2(Basic):
    _name = 'basic2x2'
    _min_size = Vec(2,1,2)
    _max_size = Vec(2,1,2)
    size = Vec(2,1,2)
    _is_entrance = True
    _is_stairwell = True
    _is_treasureroom = True

    def placed(self):
        rooms = []
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        # Fix our halls so they only show N and W sides
        # West, South, East, North
        pos = self.pos
        rooms.append(pos)
        self.hallLength = [3,0,0,3]
        self.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        self.parent.halls[pos.x][pos.y][pos.z][1] = 1
        self.parent.halls[pos.x][pos.y][pos.z][2] = 1
        # place three more blank rooms to hold the hallways
        # This is the Southern room
        pos = self.pos + Vec(1,0,0)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [3,3,0,0]
        room.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        room.parent.halls[pos.x][pos.y][pos.z][2] = 1
        room.parent.halls[pos.x][pos.y][pos.z][3] = 1
        #room.canvas = (
        #    Vec(4   ,sy-2, 4),
        #    Vec(sx-5,sy-2, 4),
        #    Vec(sx-5,sy-2, sz-5),
        #    Vec(4   ,sy-2, sz-5))

        # Eastern room.
        pos = self.pos + Vec(0,0,1)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [0,0,3,3]
        room.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        room.parent.halls[pos.x][pos.y][pos.z][0] = 1
        room.parent.halls[pos.x][pos.y][pos.z][1] = 1
        # South East room.
        pos = self.pos + Vec(1,0,1)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [0,3,3,0]
        room.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        room.parent.halls[pos.x][pos.y][pos.z][0] = 1
        room.parent.halls[pos.x][pos.y][pos.z][3] = 1
        return rooms

class SandstoneCavern(Blank):
    _name = 'sandstonecavern'
    _walls = materials.Sandstone
    _floor = materials._floor
    _subfloor = materials._subfloor
    _floortype = 'sand'

    def setData(self):
        # size of the room
        self.sx = self.size.x * self.parent.room_size
        self.sz = self.size.z * self.parent.room_size
        self.sy = self.size.y * self.parent.room_height

        self.c1 = self.loc + Vec(0,self.sy-2,0)
        self.c3 = self.c1 + Vec(self.sx-1, 0, self.sz-1)

        self.hallLength = [1,1,1,1]
        self.hallSize = [[2,self.sx-2],
                         [2,self.sx-2],
                         [2,self.sz-2],
                         [2,self.sz-2]]

        self.canvas = (
            Vec(0   ,self.sy-2, 0),
            Vec(self.sx-1,self.sy-2, 0),
            Vec(self.sx-1,self.sy-2, self.sz-1),
            Vec(0   ,self.sy-2, self.sz-1))
        self.features.append(features.new('blank', self))
        if self._floortype is not '':
            self.floors.append(floors.new(self._floortype, self))

    def placeCavernHalls(self, cave):
        # West side
        if (self.halls[0].size > 0):
            cave.add_exit((0, self.halls[0].offset),
                          (0, self.halls[0].offset+self.halls[0].size))
        # South side
        if (self.halls[1].size > 0):
            cave.add_exit((self.halls[1].offset, self.sz-1),
                          (self.halls[1].offset+self.halls[1].size, self.sz-1))
        # East side
        if (self.halls[2].size > 0):
            cave.add_exit((self.sx-1, self.halls[2].offset),
                          (self.sx-1, self.halls[2].offset+self.halls[2].size))
        # North side
        if (self.halls[3].size > 0):
            cave.add_exit((self.halls[3].offset, 0),
                          (self.halls[3].offset+self.halls[3].size, 0))

    def render(self):
        height = self.size.y * self.parent.room_height - 2
        cave = cave_factory.new(self.sx, self.sz)

        # Layer in the halls
        self.placeCavernHalls(cave)

        cave.gen_map()
        # Air space, Floor, and Ceiling
        for p in cave.iterate_map(cave_factory.FLOOR):
            self.parent.setblock(self.c1+Vec(p[0],-3,p[1]), materials.Air)
            self.parent.setblock(self.c1+Vec(p[0],-2,p[1]), materials.Air)
            self.parent.setblock(self.c1+Vec(p[0],-1,p[1]), materials.Air)
            self.parent.setblock(self.c1+Vec(p[0],0,p[1]), self._floor)
            self.parent.setblock(self.c1+Vec(p[0],-height,p[1]),
                                 self._walls, 0, True)
        # Walls
        for p in cave.iterate_walls():
            self.parent.setblock(self.c1+Vec(p[0],-4,p[1]), self._walls,
                                0, True)
            self.parent.setblock(self.c1+Vec(p[0],-3,p[1]), self._walls)
            self.parent.setblock(self.c1+Vec(p[0],-2,p[1]), self._walls)
            self.parent.setblock(self.c1+Vec(p[0],-1,p[1]), self._walls)
        cave.grow_map()
        for p in cave.iterate_walls():
            self.parent.setblock(self.c1+Vec(p[0],-3,p[1]), self._walls,
                                0, True)
        # Subfloor
        sf1 = self.loc.trans(0,
                             self.size.y * self.parent.room_height - 1,
                             0)
        sf2 = sf1.trans(self.size.x * self.parent.room_size-1,
                       0,
                       self.size.z * self.parent.room_size-1)
        for x in iterate_plane(sf1, sf2):
            self.parent.setblock(x, self._subfloor)

class SandstoneCavernLarge(SandstoneCavern):
    _name = 'sandstonecavernlarge'
    _min_size = Vec(2,1,2)
    _max_size = Vec(2,1,2)
    size = Vec(2,1,2)
    _spread_chance = .30
    _small_cavern = 'sandstonecavern'

    def placed(self):
        rooms = []
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        # Fix our halls so they only show N and W sides
        # West, South, East, North
        pos = self.pos
        rooms.append(pos)
        self.hallLength = [1,0,0,1]
        self.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        self.parent.halls[pos.x][pos.y][pos.z][1] = 1
        self.parent.halls[pos.x][pos.y][pos.z][2] = 1
        # place three more blank rooms to hold the hallways
        # This is the Southern room
        pos = self.pos + Vec(1,0,0)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [1,1,0,0]
        room.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        room.parent.halls[pos.x][pos.y][pos.z][2] = 1
        room.parent.halls[pos.x][pos.y][pos.z][3] = 1

        # Eastern room.
        pos = self.pos + Vec(0,0,1)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [0,0,1,1]
        room.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        room.parent.halls[pos.x][pos.y][pos.z][0] = 1
        room.parent.halls[pos.x][pos.y][pos.z][1] = 1
        # South East room.
        pos = self.pos + Vec(1,0,1)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [0,1,1,0]
        room.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        room.parent.halls[pos.x][pos.y][pos.z][0] = 1
        room.parent.halls[pos.x][pos.y][pos.z][3] = 1
        # There's a chance large caverns will spawn adjacent small cavern rooms.
        h = self.parent.halls
        s = self.pos
        for p in (Vec(-1, 0, 0), Vec(-1, 0, 1),  # North
                  Vec( 2, 0, 0), Vec( 2, 0, 1),  # South
                  Vec( 0, 0, 2), Vec( 1, 0, 2),  # East
                  Vec( 0, 0,-1), Vec( 1, 0,-1)): # West
            pos = self.pos + p
            if (pos.x >= 0 and
                pos.z >= 0 and
                pos.x < self.parent.xsize and
                pos.z < self.parent.zsize and
                pos not in self.parent.rooms and
                random.random() < self._spread_chance):
                room = new(self._small_cavern, self.parent, pos)
                rooms.extend(self.parent.setroom(pos, room))
                # Connect teh halls for each case
                # North
                if (p == Vec(-1, 0, 0)):
                    h[s.x][s.y][s.z][3] = 1
                    h[s.x-1][s.y][s.z][1] = 1
                elif (p == Vec(-1, 0, 1)):
                    h[s.x][s.y][s.z+1][3] = 1
                    h[s.x-1][s.y][s.z+1][1] = 1
                # South
                elif (p == Vec(2, 0, 0)):
                    h[s.x+1][s.y][s.z][1] = 1
                    h[s.x+2][s.y][s.z][3] = 1
                elif (p == Vec(2, 0, 1)):
                    h[s.x+1][s.y][s.z+1][1] = 1
                    h[s.x+2][s.y][s.z+1][3] = 1
                # East
                elif (p == Vec(0, 0, 2)):
                    h[s.x][s.y][s.z+1][2] = 1
                    h[s.x][s.y][s.z+2][0] = 1
                elif (p == Vec(1, 0, 2)):
                    h[s.x+1][s.y][s.z+1][2] = 1
                    h[s.x+1][s.y][s.z+2][0] = 1
                # West
                elif (p == Vec(0, 0, -1)):
                    h[s.x][s.y][s.z][0] = 1
                    h[s.x][s.y][s.z-1][2] = 1
                elif (p == Vec(1, 0, -1)):
                    h[s.x+1][s.y][s.z][0] = 1
                    h[s.x+1][s.y][s.z-1][2] = 1
                else:
                    sys.exit('Cavern connected to unknown room! Aiiee!')

        return rooms

    def placeCavernHalls(self, cave):
        ''' Used when rendering to set exit zones for the cave factory'''
        # NE room
        room_ne = self.parent.rooms[self.pos + Vec(0,0,1)]
        # SE room
        room_se = self.parent.rooms[self.pos + Vec(1,0,1)]
        # SW room
        room_sw = self.parent.rooms[self.pos + Vec(1,0,0)]

        # West side
        if (self.halls[0].size > 0):
            cave.add_exit((0, self.halls[0].offset),
                          (0, self.halls[0].offset+self.halls[0].size))
        if (room_sw.halls[0].size > 0):
            cave.add_exit((0, 16+room_sw.halls[0].offset),
                          (0, 16+room_sw.halls[0].offset+room_sw.halls[0].size))
        # South side
        if (room_se.halls[1].size > 0):
            cave.add_exit((16+room_se.halls[1].offset, self.sz-1),
                          (16+room_se.halls[1].offset+room_se.halls[1].size, self.sz-1))
        if (room_sw.halls[1].size > 0):
            cave.add_exit((room_sw.halls[1].offset, self.sz-1),
                          (room_sw.halls[1].offset+room_sw.halls[1].size, self.sz-1))
        # East side
        if (room_ne.halls[2].size > 0):
            cave.add_exit((self.sx-1, room_ne.halls[2].offset),
                          (self.sx-1, room_ne.halls[2].offset+room_ne.halls[2].size))
        if (room_se.halls[2].size > 0):
            cave.add_exit((self.sx-1, 16+room_se.halls[2].offset),
                          (self.sx-1, 16+room_se.halls[2].offset+room_se.halls[2].size))
        # North side
        if (self.halls[3].size > 0):
            cave.add_exit((self.halls[3].offset, 0),
                          (self.halls[3].offset+self.halls[3].size, 0))
        if (room_ne.halls[3].size > 0):
            cave.add_exit((16+room_ne.halls[3].offset, 0),
                          (16+room_ne.halls[3].offset+room_ne.halls[3].size, 0))


class Cavern(SandstoneCavern):
    _name = 'cavern'
    _walls = materials._wall
    _floor = materials._floor
    _subfloor = materials._subfloor
    _floortype = 'blank'


class CavernLarge(SandstoneCavernLarge):
    _name = 'cavernlarge'
    _walls = materials._wall
    _floor = materials._floor
    _subfloor = materials._subfloor
    _floortype = 'blank'
    _small_cavern = 'cavern'


class NaturalCavern(SandstoneCavern):
    _name = 'naturalcavern'
    _walls = materials._natural
    _floor = materials._natural
    _subfloor = materials._natural
    _floortype = 'blank'


class NaturalCavernLarge(SandstoneCavernLarge):
    _name = 'naturalcavernlarge'
    _walls = materials._natural
    _floor = materials._natural
    _subfloor = materials._natural
    _floortype = 'blank'
    _small_cavern = 'naturalcavern'


class Circular(Basic):
    _name = 'circular'
    _is_entrance = True
    _is_stairwell = True

    def setData(self):
        self.wall_func = iterate_tube
        self.ceil_func = iterate_disc
        self.floor_func = iterate_disc
        self.air_func = iterate_cylinder
        self.c1 = self.loc + Vec(0,self.parent.room_height-2,0)
        self.c3 = self.c1 + Vec(self.parent.room_size-1,
                                0,
                                self.parent.room_size-1)
        # North, East, South, West
        self.hallLength = [1,1,1,1]
        self.hallSize = [
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5]]
        self.canvas = (
            Vec(5,self.parent.room_height-2,2),
            Vec(self.parent.room_size-6,self.parent.room_height-2,2),
            Vec(self.parent.room_size-3,self.parent.room_height-2,5),
            Vec(self.parent.room_size-3,
                self.parent.room_height-2,
                self.parent.room_size-6),
            Vec(self.parent.room_size-6,
                self.parent.room_height-2,
                self.parent.room_size-3),
            Vec(5,self.parent.room_height-2,self.parent.room_size-3),
            Vec(2,self.parent.room_height-2,self.parent.room_size-6),
            Vec(2,self.parent.room_height-2,5))


class Pit(Blank):
    _name = 'pit'
    _min_size = Vec(1,1,1)
    _max_size = Vec(1,18,1)
    size = Vec(1,1,1)

    def setData(self):
        self.midroom = 'pitmid'
        self.bottomroom = 'pitbottom'
        self.wall_func = iterate_four_walls
        self.ceil_func = iterate_cube
        self.floor_func = iterate_cube
        self.air_func = iterate_cube
        self.c1 = self.loc + Vec(2,self.parent.room_height-2,2)
        self.c3 = self.c1 + Vec(self.parent.room_size-5,
                                0,
                                self.parent.room_size-5)
        # North, East, South, West
        self.hallLength = [3,3,3,3]
        self.hallSize = [
                [2,self.parent.room_size-2],
                [2,self.parent.room_size-2],
                [2,self.parent.room_size-2],
                [2,self.parent.room_size-2]]
        self.canvas = (
            Vec(4,self.parent.room_height-2,4),
            Vec(self.parent.room_size-5,self.parent.room_height-2,4),
            Vec(self.parent.room_size-5,
                self.parent.room_height-2,
                self.parent.room_size-5),
            Vec(4,self.parent.room_height-2,self.parent.room_size-5))
        self.lava = False
        self.toLava = False
        self.sandpit = False
        self.features.append(features.new('blank', self))
        self.floors.append(floors.new('blank', self))

    def placed(self):
        rooms = []
        # Extend downward. First, figure out where we are and how far down
        # we would like to go. 
        thisfloor = self.pos.y+1
        targetdepth = random.randint(1, max(self.parent.levels-thisfloor,1))
        self.depth = 1
        # Place lower rooms.
        pos = self.pos
        rooms.append(pos)
        while (self.depth < targetdepth):
            pos = pos.down(1)
            if (pos in self.parent.rooms):
                break
            if (pos.down(1) in self.parent.rooms or
               self.depth+1 == targetdepth):
                room = new(self.bottomroom, self.parent, pos)
                rooms.extend(self.parent.setroom(pos, room))
                self.depth += 1
                if (room.floor == 'lava'):
                    self.toLava = True
                break
            room = new(self.midroom, self.parent, pos)
            rooms.extend(self.parent.setroom(pos, room))
            self.depth += 1
        # If this is the only level, make it a lava pit.
        if (self.depth == 1):
            self.lava = True
        # Otherwise build bridges. Or maybe a sand trap. 
        else:
            self.floors.append(floors.new('bridges', self))
        return rooms

    def render (self):
        pn = perlin.SimplexNoise(256)
        # Sand pit!
        # Restrict sandpits to rooms with small halls.
        maxhall = max(map(lambda x: x.size, self.halls))
        if (self.depth > 1 and
            maxhall<=4 and
            random.randint(1,100) <= cfg.sand_traps):
            self.sandpit = True
            if [f for f in self.floors if f._name == 'bridges']:
                f.sandpit = True
            # 50/50 chance of adding some columns to further the illusion.
            if ([f for f in cfg.master_features if (f[0] == 'columns' and
                                            f[1] > 0)] and
                random.randint(1,100) <= 50):
                self.features.append(features.new('columns', self))

        height = self.parent.room_height-2
        # Air space
        for x in self.air_func(self.c1.down(1), self.c3.up(4)):
            self.parent.setblock(x, materials.Air)
        # Lava
        if (self.lava is True):
            for x in self.floor_func(self.c1.trans(0,1,0),
                                     self.c3.trans(0,1,0)):
                self.parent.setblock(x, materials.Lava)
            r = random.randint(1,1000)
            for x in self.floor_func(self.c1.trans(0,1,0),
                                     self.c3.trans(0,1,0)):
                n = (pn.noise3(x.x/4.0, r/4.0, x.z/4.0) + 1.0) / 2.0
                if (n > 0.7):
                    self.parent.setblock(x.up(1), materials.CobblestoneSlab)
                    if (self.parent.getblock(x.trans(1,0,0)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(1,0,0),
                                             materials.Cobblestone)
                    if (self.parent.getblock(x.trans(-1,0,0)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(-1,0,0),
                                             materials.Cobblestone)
                    if (self.parent.getblock(x.trans(0,0,1)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(0,0,1),
                                             materials.Cobblestone)
                    if (self.parent.getblock(x.trans(0,0,-1)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(0,0,-1),
                                             materials.Cobblestone)
                if (n < 0.2):
                    self.parent.setblock(x, materials.Air)
        # Ceiling
        for x in self.ceil_func(self.c1.up(4), self.c3.up(4)):
            self.parent.setblock(x, materials._ceiling)
        # Lava streams from ceiling
        if (self.toLava == True and self.sandpit == False):
            p = self.loc + random_point_inside_flat_poly(*self.canvas)
            self.parent.setblock(p.up(4), materials.Lava)
        # Floor with no subfloor if this is a sand pit
        if (self.sandpit == True):
            for x in self.floor_func(self.c1.trans(0,0,0),
                                     self.c3.trans(0,0,0)):
                self.parent.setblock(x, materials._floor)
        # Walls
        for x in self.wall_func(self.c1.down(1), self.c3.down(1), height+1):
            self.parent.setblock(x, materials._wall)

class CircularPit(Pit):
    _name = 'circularpit'

    def setData(self):
        self.midroom = 'circularpitmid'
        self.bottomroom = 'circularpitbottom'
        self.wall_func = iterate_tube
        self.ceil_func = iterate_disc
        self.floor_func = iterate_disc
        self.air_func = iterate_cylinder
        self.c1 = self.loc + Vec(0,self.parent.room_height-2,0)
        self.c3 = self.c1 + Vec(self.parent.room_size-1,
                                0,
                                self.parent.room_size-1)
        # North, East, South, West
        self.hallLength = [1,1,1,1]
        self.hallSize = [
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5]]
        self.canvas = (
            Vec(5,self.parent.room_height-2,2),
            Vec(self.parent.room_size-6,self.parent.room_height-2,2),
            Vec(self.parent.room_size-3,self.parent.room_height-2,5),
            Vec(self.parent.room_size-3,
                self.parent.room_height-2,
                self.parent.room_size-6),
            Vec(self.parent.room_size-6,
                self.parent.room_height-2,
                self.parent.room_size-3),
            Vec(5,self.parent.room_height-2,self.parent.room_size-3),
            Vec(2,self.parent.room_height-2,self.parent.room_size-6),
            Vec(2,self.parent.room_height-2,5))
        self.lava = False
        self.toLava = False
        self.sandpit = False
        self.features.append(features.new('blank', self))
        self.floors.append(floors.new('blank', self))


class PitMid(Blank):
    _name = 'pitmid'

    def setData(self):
        self.wall_func = iterate_four_walls
        self.ceil_func = iterate_cube
        self.floor_func = iterate_cube
        self.air_func = iterate_cube
        self.c1 = self.loc + Vec(2,self.parent.room_height-2,2)
        self.c3 = self.c1 + Vec(self.parent.room_size-5,
                                0,
                                self.parent.room_size-5)
        # North, East, South, West
        self.hallLength = [3,3,3,3]
        self.hallSize = [
            [2,self.parent.room_size-2],
            [2,self.parent.room_size-2],
            [2,self.parent.room_size-2],
            [2,self.parent.room_size-2]]
        self.canvas = (
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0))

    def placed(self):
        # This room needs bridges
        self.floors.append(floors.new('bridges', self))
        self.features.append(features.new('blank', self))
        return [self.pos]

    def render (self):
        height = self.parent.room_height-2
        # Air space
        for x in self.air_func(self.c1.down(1), self.c3.up(4)):
            self.parent.setblock(x, materials.Air)
        # Skeleton balconies! (for circular pit rooms only)
        corner =  1 if self.halls[0].size>0 else 0
        corner += 2 if self.halls[1].size>0 else 0
        corner += 4 if self.halls[2].size>0 else 0
        corner += 8 if self.halls[3].size>0 else 0
        b1 = Vec(0,0,0)     # corner 1 of the balcony
        b2 = Vec(0,0,0)  # corner 2 of the balcony
        b3 = Vec(0,0,0) # Skeleton spawner
        balcony = False
        if (self._name == 'circularpitmid' and random.randint(1,100) <=
            cfg.skeleton_balconies):
            if (corner == 3):
                balcony = True
                b1 = self.loc.down(height+1)+Vec(0,0,self.parent.room_size-1)
                b2 = b1+Vec(6,0,-6)
                b3 = b1+Vec(2,-1,-2)
            if (corner == 6):
                balcony = True
                b1 = self.loc.down(height+1)
                b2 = b1+Vec(6,0,6)
                b3 = b1+Vec(2,-1,2)
            if (corner == 9):
                balcony = True
                b1 = self.loc.down(height+1)+Vec(self.parent.room_size-1,
                                                 0,
                                                 self.parent.room_size-1)
                b2 = b1+Vec(-6,0,-6)
                b3 = b1+Vec(-2,-1,-2)
            if (corner == 12):
                balcony = True
                b1 = self.loc.down(height+1)+Vec(self.parent.room_size-1,0,0)
                b2 = b1+Vec(-6,0,6)
                b3 = b1+Vec(-2,-1,2)
        if balcony == True:
            for p in iterate_tube(b1, b2, 1):
                self.parent.setblock(p, materials.Fence)
            for p in iterate_disc(b1, b2):
                self.parent.setblock(p, materials._floor)
        # Walls
        for x in self.wall_func(self.c1.down(1), self.c3.down(1), height+1):
            self.parent.setblock(x, materials._wall)
        # Skeleton balconies!
        if balcony == True:
            self.parent.addspawner(b3, 'Skeleton')
            self.parent.setblock(b3, materials.Spawner)


class CircularPitMid(PitMid):
    _name = 'circularpitmid'

    def setData(self):
        self.wall_func = iterate_tube
        self.ceil_func = iterate_disc
        self.floor_func = iterate_disc
        self.air_func = iterate_cylinder
        self.c1 = self.loc + Vec(0,self.parent.room_height-2,0)
        self.c3 = self.c1 + Vec(self.parent.room_size-1,
                                0,
                                self.parent.room_size-1)
        # North, East, South, West
        self.hallLength = [1,1,1,1]
        self.hallSize = [
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5]]
        #self.canvas = (
        #    Vec(0,self.parent.room_height-2,0),
        #    Vec(0,self.parent.room_height-2,0),
        #    Vec(0,self.parent.room_height-2,0))
        self.canvas = (
            Vec(5,self.parent.room_height-2,2),
            Vec(self.parent.room_size-6,self.parent.room_height-2,2),
            Vec(self.parent.room_size-3,self.parent.room_height-2,5),
            Vec(self.parent.room_size-3,
                self.parent.room_height-2,
                self.parent.room_size-6),
            Vec(self.parent.room_size-6,
                self.parent.room_height-2,
                self.parent.room_size-3),
            Vec(5,self.parent.room_height-2,self.parent.room_size-3),
            Vec(2,self.parent.room_height-2,self.parent.room_size-6),
            Vec(2,self.parent.room_height-2,5))


class PitBottom(Blank):
    _name = 'pitbottom'

    def setData(self):
        self.wall_func = iterate_four_walls
        self.ceil_func = iterate_cube
        self.floor_func = iterate_cube
        self.air_func = iterate_cube
        self.c1 = self.loc + Vec(2,self.parent.room_height-2,2)
        self.c3 = self.c1 + Vec(self.parent.room_size-5,
                                0,
                                self.parent.room_size-5)
        # North, East, South, West
        self.hallLength = [3,3,3,3]
        self.hallSize = [
            [2,self.parent.room_size-2],
            [2,self.parent.room_size-2],
            [2,self.parent.room_size-2],
            [2,self.parent.room_size-2]]
        self.canvas = (
            Vec(4,self.parent.room_height-2,4),
            Vec(self.parent.room_size-5,self.parent.room_height-2,4),
            Vec(self.parent.room_size-5,
                self.parent.room_height-2,
                self.parent.room_size-5),
            Vec(4,self.parent.room_height-2,self.parent.room_size-5))
        self.floor = 'floor'

    def placed(self):
        self.floor = random.choice(('floor','lava','cactus'))
        if (self.floor is not 'floor'):
            self.floors.append(floors.new('blank', self))
            self.features.append(features.new('blank', self))
        return [self.pos]

    def render (self):
        pn = perlin.SimplexNoise(256)
        height = self.parent.room_height-2
        # Air space
        for x in self.air_func(self.c1.down(1), self.c3.up(4)):
            self.parent.setblock(x, materials.Air)
        # Lava
        if (self.floor == 'lava'):
            for x in self.floor_func(self.c1.trans(0,1,0),
                                     self.c3.trans(0,1,0)):
                self.parent.setblock(x, materials.Lava)
            r = random.randint(1,1000)
            for x in self.floor_func(self.c1.trans(0,1,0),
                                     self.c3.trans(0,1,0)):
                n = (pn.noise3(x.x/4.0, r/4.0, x.z/4.0) + 1.0) / 2.0
                if (n > 0.7):
                    self.parent.setblock(x.up(1), materials.CobblestoneSlab)
                    if (self.parent.getblock(x.trans(1,0,0)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(1,0,0),
                                             materials.Cobblestone)
                    if (self.parent.getblock(x.trans(-1,0,0)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(-1,0,0),
                                             materials.Cobblestone)
                    if (self.parent.getblock(x.trans(0,0,1)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(0,0,1),
                                             materials.Cobblestone)
                    if (self.parent.getblock(x.trans(0,0,-1)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(0,0,-1),
                                             materials.Cobblestone)
                if (n < 0.2):
                    self.parent.setblock(x, materials.Air)
        # Cactus (spike trap)
        elif (self.floor == 'cactus'):
            for x in self.floor_func(self.c1.trans(0,0,0),
                                     self.c3.trans(0,0,0)):
                self.parent.setblock(x, materials.Sand)
                self.parent.setblock(x.down(1), materials._subfloor)
            for x in self.floor_func(self.c1.trans(2,-1,2),
                                     self.c3.trans(-2,-1,-2)):
                if ((x.x+x.z)%2 == 0):
                    for p in iterate_cube(x, x.up(random.randint(0,2))):
                        self.parent.setblock(p, materials.Cactus)
        # Floor
        else:
            for x in self.floor_func(self.c1.trans(0,0,0),
                                     self.c3.trans(0,0,0)):
                self.parent.setblock(x, materials._floor)
                self.parent.setblock(x.down(1), materials._subfloor)
        # Walls
        for x in self.wall_func(self.c1.down(1), self.c3.down(1), height+1):
            self.parent.setblock(x, materials._wall)


class CircularPitBottom(PitBottom):
    _name = 'circularpitbottom'

    def setData(self):
        self.wall_func = iterate_tube
        self.ceil_func = iterate_disc
        self.floor_func = iterate_disc
        self.air_func = iterate_cylinder
        self.c1 = self.loc + Vec(0,self.parent.room_height-2,0)
        self.c3 = self.c1 + Vec(self.parent.room_size-1,
                                0,
                                self.parent.room_size-1)
        # North, East, South, West
        self.hallLength = [1,1,1,1]
        self.hallSize = [
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5],
            [5,self.parent.room_size-5]]
        self.canvas = (
            Vec(5,self.parent.room_height-2,2),
            Vec(self.parent.room_size-6,self.parent.room_height-2,2),
            Vec(self.parent.room_size-3,self.parent.room_height-2,5),
            Vec(self.parent.room_size-3,
                self.parent.room_height-2,
                self.parent.room_size-6),
            Vec(self.parent.room_size-6,
                self.parent.room_height-2,
                self.parent.room_size-3),
            Vec(5,self.parent.room_height-2,self.parent.room_size-3),
            Vec(2,self.parent.room_height-2,self.parent.room_size-6),
            Vec(2,self.parent.room_height-2,5))
        self.floor = 'floor'


class Corridor(Blank):
    _name = 'corridor'

    def setData(self):
        # North, East, South, West
        self.hallLength = [3,3,3,3]
        self.hallSize = [
            [2,self.parent.room_size-2],
            [2,self.parent.room_size-2],
            [2,self.parent.room_size-2],
            [2,self.parent.room_size-2]]
        self.canvas = (
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0))
    def render (self):
        # default to a teeny tiny room
        x1 = 1000
        x2 = -1
        z1 = 1000
        z2 = -1
        numhalls = 0
        # Lets take a look at our halls and try to connect them
        # x1 bounds (West side)
        if (self.halls[0].size):
            x1 = self.halls[0].offset
            numhalls += 1
        if (self.halls[2].size):
            x1 = min(x1, self.halls[2].offset)
            numhalls += 1
        if (x1 is 1000):
            x1 = self.parent.room_size/2-2
        # x2 bounds (East side)
        if (self.halls[0].size):
            x2 = self.halls[0].offset+self.halls[0].size-1
        if (self.halls[2].size):
            x2 = max(x2, self.halls[2].offset+self.halls[2].size-1)
        if (x2 is -1):
            x2 = self.parent.room_size/2+2
        # z1 bounds (North side)
        if (self.halls[1].size):
            z1 = self.halls[1].offset
            numhalls += 1
        if (self.halls[3].size):
            z1 = min(z1, self.halls[3].offset)
            numhalls += 1
        if (z1 is 1000):
            z1 = self.parent.room_size/2-2
        # z2 bounds (South side)
        if (self.halls[1].size):
            z2 = self.halls[1].offset+self.halls[1].size-1
        if (self.halls[3].size):
            z2 = max(z2, self.halls[3].offset+self.halls[3].size-1)
        if (z2 is -1):
            z2 = self.parent.room_size/2+2
        # Orient the sides
        if (x1 > x2):
            t = x1
            x1= x2
            x2 = t
        if (z1 > z2):
            t = z1
            z1= z2
            z2 = t
        # If there is only one hall, override
        if (numhalls == 1):
            x1 = min(x1, 5)
            x2 = max(x2, self.parent.room_size-6)
            z1 = min(z1, 5)
            z2 = max(z2, self.parent.room_size-6)
        # Extend the halls
        self.hallLength[0] = z1+1
        self.hallLength[1] = self.parent.room_size - x2
        self.hallLength[2] = self.parent.room_size - z2
        self.hallLength[3] = x1+1
        # Canvas
        if (x2-x1 > 2 and z2-z1 > 2):
            self.canvas = (
                Vec(x1+1,self.parent.room_height-2,z1+1),
                Vec(x2-1,self.parent.room_height-2,z1+1),
                Vec(x2-1,self.parent.room_height-2,z2-1),
                Vec(x1+1,self.parent.room_height-2,z2-1))
        # Figure out our corners
        c1 = self.loc+Vec(x1,self.parent.room_height-2,z1)
        c2 = self.loc+Vec(x2,self.parent.room_height-2,z1)
        c3 = self.loc+Vec(x2,self.parent.room_height-2,z2)
        c4 = self.loc+Vec(x1,self.parent.room_height-2,z2)
        # Air space
        for x in iterate_cube(c1.up(1),c3.up(3)):
            self.parent.setblock(x, materials.Air)
        # Floor
        for x in iterate_cube(c1, c3):
            self.parent.setblock(x, materials._floor)
        # Ceiling
        for x in iterate_cube(c1.up(4),c3.up(4)):
            self.parent.setblock(x, materials._ceiling)
        # Walls
        for x in iterate_four_walls(c1, c3, self.parent.room_height-2):
            self.parent.setblock(x, materials._wall)
        # Subfloor
        for x in iterate_plane(self.loc.down(self.parent.room_height-1),
                                    self.loc.trans(self.parent.room_size-1,
                                                  self.parent.room_height-1,
                                                  self.parent.room_size-1)):
            self.parent.setblock(x, materials._subfloor)
        # Cave-in
        if (numhalls == 1):
            ores = (
                # Resource distribution
                (materials.Cobblestone,150),
                (materials._wall,150),
                (materials.CoalOre,90),
                (materials.IronOre,40),
                (materials.GoldOre,5),
                (materials.DiamondOre,5),
                (materials.RedStoneOre,40),
                (materials.LapisOre,5)
            )
            start = c4.trans(1,1,-2)
            width = x2-x1-1
            length = self.parent.room_height-3
            stepw = Vec(1,0,0)
            stepl = Vec(0,0,-1)
            if (self.halls[0].size):
                start = c1.trans(1,1,2)
                width = x2-x1-1
                stepw = Vec(1,0,0)
                stepl = Vec(0,0,1)
            elif (self.halls[1].size):
                start = c2.trans(-2,1,1)
                width = z2-z1-1
                stepw = Vec(0,0,1)
                stepl = Vec(-1,0,0)
            elif (self.halls[3].size):
                start = c1.trans(2,1,1)
                width = z2-z1-1
                stepw = Vec(0,0,1)
                stepl = Vec(1,0,0)
            h = 1
            for l in xrange(length):
                for w in xrange(width):
                    p = start + (stepw*w) + (stepl*l)
                    for x in iterate_cube(p, p.up(h+random.randint(0,1))):
                        mat = weighted_choice(ores)
                        self.parent.setblock(x, mat)
                h += 1

# Catalog the rooms we know about. 
_rooms = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses if of rooms.Blank
    if issubclass(obj, Blank):
        _rooms[obj._name] = obj

def new (name, parent, pos):
    '''Return a new instance of the room of a given name. Supply the parent
    dungeon object and maze position.'''
    if name in _rooms.keys():
        return _rooms[name](parent, pos)
    return Blank(parent, pos)

def pickRoom (dungeon, dsize, pos,
              maxsize=Vec(10,18,10),
              entrance=False,
              treasure=False,
              stairwell=False):
    '''Returns a pointer to a room instance given the current room set. Rooms
    will be chosen from a weighted list based on cfg.master_rooms, with a
    fall back to Basic. Restrictions on size, entrance, treasure, and stairwell
    can be specified.'''
    rooms = dungeon.rooms
    room_list = weighted_shuffle(cfg.master_rooms)
    name = ''
    fpos = pos
    print 'finding room @:', fpos
    # Cycle through the weithed shuffled list of room names.
    while (len(room_list) and name == ''):
        newroom = room_list.pop()
        # If the name doesn't really exist, ignore it.
        if newroom not in _rooms:
            continue
        # Find the room size.
        size = _rooms[newroom]._min_size - Vec(1,1,1)
        # Check if we need an entrance capable room.
        if (entrance == True):
            entrance_test = _rooms[newroom]._is_entrance
        else:
            entrance_test = True
        # Check if we need a treasure capable room.
        if (treasure == True):
            treasure_test = _rooms[newroom]._is_treasureroom
        else:
            treasure_test = True
        # Check if we need a stairwell capable room.
        if (stairwell == True):
            stairwell_test = _rooms[newroom]._is_stairwell
        else:
            stairwell_test = True
        print 'trying:', newroom, '(', 'E:', entrance_test,\
                                       'S:', stairwell_test,\
                                       'T:', treasure_test,\
                                       ')'
        # Generate a list of horizontal offsets to test, and test them in a
        # random order.
        of = []
        for x in xrange(size.x+1):
            for z in xrange(size.z+1):
                of.append(Vec(-x,0,-z))
        random.shuffle(of)
        for o in of:
            ppos = pos + o
            print ' ppos:',ppos
            if (entrance_test and
                stairwell_test and
                treasure_test and
                ppos.x >= 0 and
                ppos.y >= 0 and
                ppos.z >= 0 and
                ppos.x + size.x < dsize.x and
                ppos.y + size.y < dsize.y and
                ppos.z + size.z < dsize.z and
                size.x < maxsize.x and
                size.y < maxsize.y and
                size.z < maxsize.z and
                any(p in rooms for p in iterate_cube(ppos, ppos+size)) is False):
                name = newroom
                fpos = ppos
                break
    # If we didn't find a room, fall back to basic. 
    if name == '':
        name = 'basic'
    print 'picked:', name, '@', fpos
    # Return the room instance and the new offset location. 
    return new(name, dungeon, fpos), fpos
