import sys
import inspect

import materials
import halls
import floors
import features
import ruins
import cfg
import items
import loottable
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
    _pistontrap = True

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

class CBlank(Blank):
    _name = 'cblank'

class BlankStairwell(Blank):
    _name = 'blankstairwell'
    _is_stairwell = True

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
        self.c2 = self.c1 + Vec(sx-5, 0, 0)
        self.c3 = self.c1 + Vec(sx-5, 0, sz-5)
        self.c4 = self.c1 + Vec(0, 0, sz-5)

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

class GreatHallNS(Basic):
    _name = 'greathallns'
    _min_size = Vec(1,2,2)
    _max_size = Vec(1,2,2)
    size = Vec(1,2,2)
    _is_entrance = False
    _is_stairwell = False

    def placed(self):
        rooms = []
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        # Fix our halls. Northern upper room.
        # North, East, South, West
        pos = self.pos
        rooms.append(pos)
        self.hallLength = [1,1,0,1]
        self.hallSize = [[2,sx-2],
                         [6,sx-6],
                         [2,sz-2],
                         [6,sz-6]]
        self.parent.halls[pos.x][pos.y][pos.z][2] = 1
        # place three more blank rooms to hold the hallways
        # This is the upper floor, Southern room
        pos = self.pos + Vec(0,0,1)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [0,1,2,1]
        room.hallSize = [[2,sx-2],
                         [6,sx-6],
                         [2,sz-2],
                         [6,sz-6]]
        room.parent.halls[pos.x][pos.y][pos.z][0] = 1

        # Northern lower room.
        pos = self.pos + Vec(0,1,0)
        room = new('blankstairwell', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [1,1,0,1]
        room.hallSize = [[2,sx-2],
                         [6,sx-6],
                         [2,sz-2],
                         [6,sz-6]]
        room.parent.halls[pos.x][pos.y][pos.z][2] = 1
        # Southern lower room.
        pos = self.pos + Vec(0,1,1)
        room = new('blankstairwell', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [0,1,2,1]
        room.hallSize = [[2,sx-2],
                         [6,sx-6],
                         [2,sz-2],
                         [6,sz-6]]
        room.parent.halls[pos.x][pos.y][pos.z][0] = 1
        return rooms

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
        self.c1 = self.loc + Vec(0,sy-2,0)
        self.c2 = self.c1 + Vec(sx-1, 0, 0)
        self.c3 = self.c1 + Vec(sx-1, 0, sz-1)
        self.c4 = self.c1 + Vec(0, 0, sz-1)
        if sz > sx:
            self.c3 = self.c3.n(1)
            self.c4 = self.c4.n(1)
            sz -= 1
        else:
            self.c2 = self.c2.w(1)
            self.c3 = self.c3.w(1)
            sx -=1

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

    def render(self):
        height = self.size.y * self.parent.room_height - 2
        # Air space
        for x in self.air_func(self.c1, self.c3.up(height)):
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
        # balcony
        mat = random.choice((
            (materials.StoneBrickSlab,materials.StoneBrick,materials.IronBars),
            (materials.WoodenSlab,materials.WoodPlanks,materials.Fence)
        ))
        for p in iterate_four_walls(self.c1+Vec(1,-6,1),
                                    self.c3+Vec(-1,-6,-1),0):
            self.parent.setblock(p, mat[0])
        for p in iterate_four_walls(self.c1+Vec(2,-6,2),
                                    self.c3+Vec(-2,-6,-2),0):
            self.parent.setblock(p, mat[0])
        for p in iterate_four_walls(self.c1+Vec(3,-6,3),
                                    self.c3+Vec(-3,-6,-3),0):
            self.parent.setblock(p, mat[1])
        for p in iterate_four_walls(self.c1+Vec(3,-7,3),
                                    self.c3+Vec(-3,-7,-3),0):
            self.parent.setblock(p, mat[2])
        # Columns
        mat = random.choice((
            materials.StoneBrick,
            materials.meta_mossycobble,
            materials.meta_mossystonebrick,
            materials.DoubleSlab,
            materials.meta_stonedungeon
        ))
        for n in xrange(0, 26, 3):
            if self.size.x > self.size.z:
                p = self.c1+Vec(3+n,-1,3)
                d = Vec(0,0,9)
            else:
                p = self.c1+Vec(3,-1,3+n)
                d = Vec(9,0,0)
            for q in iterate_cube(p, p.up(height)):
                self.parent.setblock(q, mat)
                self.parent.setblock(q+d, mat)
            self.parent.setblock(p, materials.DoubleSlab)
            self.parent.setblock(p+d, materials.DoubleSlab)
        # Chandeliers
        mat = random.choice((
            materials.Fence,
            materials.IronBars
        ))
        s = self.parent.room_size-1
        for x in xrange(self.size.x):
            for z in xrange(self.size.z):
                p = self.c1+Vec(x*s+s/2+random.randint(0,1),
                                -height+1,
                                z*s+s/2+random.randint(0,1))
                for y in xrange(random.randint(1,2)):
                    self.parent.setblock(p, mat)
                    p = p.down(1)
                for q in iterate_cube(p+Vec(-1,0,-1), p+Vec(1,0,1)):
                    self.parent.setblock(q, mat)
                if (random.randint(1,100) <= 33):
                    self.parent.setblock(p, materials.Torch)
                self.parent.setblock(p.down(1), materials.Fence)
        # Vines
        if (random.randint(1,100) <= 25):
            for p in iterate_cube(self.c1+Vec(1,-1,1),
                                  self.c3+Vec(-1, -height+1, -1)):
                if random.randint(1,100) <= 20:
                    self.parent.vines(p, grow=True)
        # Cobwebs
        if (random.randint(1,100) > 25):
            return
        webs = {}
        for p in iterate_cube(self.c1+Vec(1,-1,1),
                              self.c3+Vec(-1, -height+1, -1)):
            count = 0
            perc = 90 - (p.y - self.loc.down(1).y) * (70/3)
            if (p not in self.parent.blocks or
                self.parent.blocks[p].material != materials.Air):
                continue
            for q in (Vec(1,0,0), Vec(-1,0,0),
                      Vec(0,1,0), Vec(0,-1,0),
                      Vec(0,0,1), Vec(0,0,-1)):
                if (p+q in self.parent.blocks and
                    self.parent.blocks[p+q].material != materials.Air and
                    random.randint(1,100) <= perc):
                    count += 1
            if count >= 3:
                webs[p] = True
        for p, q in webs.items():
            self.parent.setblock(p, materials.Cobweb)


class GreatHallEW(GreatHallNS):
    _name = 'greathallew'
    _min_size = Vec(2,2,1)
    _max_size = Vec(2,2,1)
    size = Vec(2,2,1)
    _is_entrance = False
    _is_stairwell = False

    def placed(self):
        rooms = []
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        # Fix our halls. Western upper room.
        # North, East, South, West
        pos = self.pos
        rooms.append(pos)
        self.hallLength = [1,0,1,1]
        self.hallSize = [[6,sx-6],
                         [2,sx-2],
                         [6,sz-6],
                         [2,sz-2]]
        self.parent.halls[pos.x][pos.y][pos.z][1] = 1
        # place three more blank rooms to hold the hallways
        # This is the upper floor, Eastern room
        pos = self.pos + Vec(1,0,0)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [1,2,1,0]
        room.hallSize = [[6,sx-6],
                         [2,sx-2],
                         [6,sz-6],
                         [2,sz-2]]
        room.parent.halls[pos.x][pos.y][pos.z][3] = 1

        # Western lower room.
        pos = self.pos + Vec(0,1,0)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [1,0,1,1]
        room.hallSize = [[6,sx-6],
                         [2,sx-2],
                         [6,sz-6],
                         [2,sz-2]]
        room.parent.halls[pos.x][pos.y][pos.z][1] = 1
        # Easterb lower room.
        pos = self.pos + Vec(1,1,0)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [1,2,1,0]
        room.hallSize = [[6,sx-6],
                         [2,sx-2],
                         [6,sz-6],
                         [2,sz-2]]
        room.parent.halls[pos.x][pos.y][pos.z][3] = 1
        return rooms


class CellBlock(Basic2x2):
    _name = 'cellblock'
    _is_entrance = False
    _is_stairwell = False
    combo = 0

    def setData(self):
        Basic2x2.setData(self)
        self.features.append(features.new('blank', self))
        #self.floors.append(floors.new('brokendoubleslab', self))
        self.combo = random.randint(1,62)

    def placed(self):
        rooms = Basic2x2.placed(self)
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        for room in rooms:
            r = self.parent.rooms[room]
            r.hallSize = [[6,sx-6],
                          [6,sx-6],
                          [6,sz-6],
                          [6,sz-6]]
        return rooms

    def render(self):
        # We start with the basics...
        Basic2x2.render(self)
        # Most floors are okay, excelt mud
        if self.floors[0]._name == 'mud':
            self.floors = []
            self.floors.append(floors.new('brokenstonebrick', self))
        # Build some cells. They have doors.
        s = self.c1+Vec(2,-1,2)
        chest_rate = 80
        spawner_rate = 80
        for p in iterate_cube(Vec(0,0,0), Vec(3,0,3)):
            if p in ([Vec(1,0,1), Vec(1,0,2),
                      Vec(2,0,1), Vec(2,0,2)]):
                continue
            ss = s+p*6
            if p.x > 1:
                ss = ss + Vec(1,0,0)
            if p.z > 1:
                ss = ss + Vec(0,0,1)
            for pp in iterate_four_walls(ss, ss+Vec(4,0,4), 2):
                self.parent.setblock(pp, materials._wall)
                doffset = Vec(4,0,2)
                ddata = 3
                if p.x > 1:
                    doffset = Vec(0,0,2)
                    ddata = 1
                self.parent.setblock(ss+doffset,
                                     materials.IronDoor, ddata+4)
                self.parent.setblock(ss+doffset.up(1),
                                     materials.IronDoor, ddata+4+8)
                self.parent.setblock(ss+doffset.up(2),
                                     materials._wall, hide=True)
            # Extra chests for solving the combo.
            if (random.randint(1,100) <= chest_rate):
                chest_rate /= 2
                cp = ss+doffset+Vec(-3,0,0)
                if p.x > 1:
                    cp = ss+doffset+Vec(3,0,0)
                self.parent.setblock(cp, materials.Chest)
                self.parent.addchest(cp)
            # Extra spawners becuase I'm a bastard.
            elif (random.randint(1,100) <= spawner_rate):
                spawner_rate /= 2
                cp = ss+doffset+Vec(-3,0,0)
                if p.x > 1:
                    cp = ss+doffset+Vec(3,0,0)
                self.parent.setblock(cp, materials.Spawner)
                self.parent.addspawner(cp)

        # A central dais with a slab step around it. 
        # Hollow out the area under for circuits. 
        for p in iterate_cube(self.c1+Vec(10,-1,10),
                              self.c3-Vec(10, 1,10)):
            self.parent.setblock(p, materials._floor)
            self.parent.setblock(p.down(1), materials.Air, lock=True)
        for p in iterate_four_walls(self.c1+Vec(10,-1,10),
                                    self.c3-Vec(10, 1,10), 0):
            self.parent.setblock(p, materials.StoneSlab)
        # Redstone triggers under the plates
        # Build a lookup table for the combo lock
        # True == on (plate depressed)
        # False == off
        cbits = {'0': self.combo&1>0,
                 '1': self.combo&2>0,
                 '2': self.combo&4>0,
                 '3': self.combo&8>0,
                 '4': self.combo&16>0,
                 '5': self.combo&32>0,
                }
        ctext1 = ''
        ctext2 = ''
        # South
        bit = 1
        for p in iterate_cube(self.c1+Vec(14, 1,11),
                              self.c3-Vec(13,-1,11)):
            if ((p.x+p.z)%2 == 0):
                if cbits[str(bit)] == True:
                    charge = 15
                    torch = materials.RedStoneTorchOn
                    repeater = materials.RedStoneRepeaterOn
                    ctext2 = 'X ' + ctext2
                else:
                    charge = 0
                    torch = materials.RedStoneWire
                    repeater = materials.RedStoneRepeaterOff
                    ctext2 = 'O ' + ctext2
                self.parent.setblock(p.up(1),
                                     materials.RedStoneWire, 0, lock=True)
                self.parent.setblock(p.e(1),
                                     torch, 1, lock=True)
                self.parent.setblock(p.e(2),
                                     repeater, 1, lock=True)
                self.parent.setblock(p.e(3),
                                     materials.RedStoneWire, charge, lock=True)
                bit += 2
        # North
        bit = 0
        for p in iterate_cube(self.c1+Vec(13, 1,11),
                              self.c3-Vec(14,-1,11)):
            if ((p.x+p.z)%2 == 0):
                if cbits[str(bit)] == True:
                    charge = 15
                    torch = materials.RedStoneTorchOn
                    repeater = materials.RedStoneRepeaterOn
                    ctext1 = 'X ' + ctext1
                else:
                    charge = 0
                    torch = materials.RedStoneWire
                    repeater = materials.RedStoneRepeaterOff
                    ctext1 = 'O ' + ctext1
                self.parent.setblock(p.up(1),
                                     materials.RedStoneWire, 15, lock=True)
                self.parent.setblock(p.w(1),
                                     torch, 2, lock=True)
                self.parent.setblock(p.w(2),
                                     repeater, 3, lock=True)
                self.parent.setblock(p.w(3),
                                     materials.RedStoneWire, charge, lock=True)
                bit += 2
        self.parent.setblock(self.c1+Vec(7,-2,12), materials.WallSign, 5)
        self.parent.addsign(self.c1+Vec(7,-2,12),
                            '--==+==--',
                            'Cell Block',
                            str(self.combo),
                            '--==+==--')
        self.parent.signs.append({
            's1': 'Level '+str(self.pos.y+1),
            's2': '',
            's3': ctext1,
            's4': ctext2+'  ',
                            })
        #print 'Cell block: '+str(self.combo)+'\n',ctext1+'\n',' '+ctext2+'\n'
        # Inner bus
        for p in iterate_four_walls(self.c1+Vec(9, 1,9),
                                 self.c3-Vec(9,-1,9),0):
            self.parent.setblock(p, materials.RedStoneWire, 15, lock=True)
        self.parent.setblock(self.c1+Vec(10,1,18),
                             materials.RedStoneRepeaterOff, 1, lock=True)
        self.parent.setblock(self.c3-Vec(10,-1,18),
                             materials.RedStoneRepeaterOff, 3, lock=True)
        # East / West Bus
        for p in iterate_cube(self.c1+Vec(6,1,6), self.c4+Vec(6,1,-6)):
            self.parent.setblock(p, materials.RedStoneWire, 15, lock=True)
            self.parent.setblock(p.e(15), materials.RedStoneWire, 15,
                                 lock=True)
        for p in iterate_cube(Vec(7,1,7), Vec(12,1,7)):
            q = self.c1+p
            self.parent.setblock(q, materials.RedStoneWire, 15, lock=True)
            self.parent.setblock(q.e(8), materials.RedStoneWire, 15,
                                 lock=True)
            q = self.c4+Vec(p.x, p.y, -p.z)
            self.parent.setblock(q, materials.RedStoneWire, 15, lock=True)
            self.parent.setblock(q.e(8), materials.RedStoneWire, 15,
                                 lock=True)
        for p in [Vec(6,0,6), Vec(6,0,8), Vec(12,0,6)]:
            q = self.c1+p
            self.parent.setblock(q, materials.Air, lock=True)
            q = self.c2+Vec(-p.x, p.y, p.z)
            self.parent.setblock(q, materials.Air, lock=True)
            q = self.c3+Vec(-p.x, p.y, -p.z)
            self.parent.setblock(q, materials.Air, lock=True)
            q = self.c4+Vec(p.x, p.y, -p.z)
            self.parent.setblock(q, materials.Air, lock=True)
        for p in [Vec(6,0,5), Vec(6,0,9), Vec(12,0,5), Vec(12,1,6)]:
            q = self.c1+p
            self.parent.setblock(q, materials.RedStoneWire, 15, lock=True)
            self.parent.setblock(q.down(1), materials._ceiling, lock=True)
            q = self.c2+Vec(-p.x, p.y, p.z)
            self.parent.setblock(q, materials.RedStoneWire, 15, lock=True)
            self.parent.setblock(q.down(1), materials._ceiling, lock=True)
            q = self.c3+Vec(-p.x, p.y, -p.z)
            self.parent.setblock(q, materials.RedStoneWire, 15, lock=True)
            self.parent.setblock(q.down(1), materials._ceiling, lock=True)
            q = self.c4+Vec(p.x, p.y, -p.z)
            self.parent.setblock(q, materials.RedStoneWire, 15, lock=True)
            self.parent.setblock(q.down(1), materials._ceiling, lock=True)
        self.parent.setblock(self.c1+Vec(6,1,10),
                             materials.RedStoneRepeaterOn, 0, lock=True)
        self.parent.setblock(self.c1+Vec(6,1,17),
                             materials.RedStoneRepeaterOn, 2, lock=True)
        self.parent.setblock(self.c1+Vec(21,1,10),
                             materials.RedStoneRepeaterOn, 0, lock=True)
        self.parent.setblock(self.c1+Vec(21,1,17),
                             materials.RedStoneRepeaterOn, 2, lock=True)
        self.parent.setblock(self.c1+Vec(8,1,13),
                             materials.RedStoneRepeaterOn, 3, lock=True)
        self.parent.setblock(self.c1+Vec(19,1,14),
                             materials.RedStoneRepeaterOn, 1, lock=True)
        self.parent.setblock(self.c1+Vec(7,1,13),
                             materials.RedStoneWire, 15, lock=True)
        self.parent.setblock(self.c1+Vec(20,1,14),
                             materials.RedStoneWire, 15, lock=True)
        # Wooden pressure plates
        for p in iterate_cube(self.c1+Vec(13,-2,11),
                              self.c3-Vec(13, 2,11)):
            if ((p.x+p.z)%2 == 0):
                self.parent.setblock(p,
                                     materials.WoodenPressurePlate)
        # Torches
        for p in [self.c1+Vec(11,-2,11), self.c2+Vec(-11,-2,11),
                  self.c3+Vec(-11,-2,-11), self.c4+Vec(11,-2,-11)]:
            self.parent.setblock(p, materials.Fence)
            self.parent.setblock(p.up(1), materials.Torch)
        # Zelda tune
        # 13,12,9,3,2,10,14,18
        self.parent.setblock(self.c1+Vec(5,1,19),
                             materials.RedStoneRepeaterOn, 15, lock=True)
        self.parent.setblock(self.c1+Vec(3,1,19),
                             materials.RedStoneTorchOn, 2, lock=True)
        self.parent.setblock(self.c1+Vec(2,1,19),
                             materials.RedStoneWire, 0, lock=True)
        self.parent.setblock(self.c1+Vec(1,1,18),
                             materials.RedStoneWire, 0, lock=True)
        for p in iterate_cube(self.c1+Vec(2,1,19), self.c1+Vec(2,1,2)):
            self.parent.setblock(p,
                                 materials.RedStoneWire, 0, lock=True)
        for p in iterate_cube(self.c1+Vec(2,1,17), self.c1+Vec(2,1,9)):
            if (p.z%2 == 1):
                self.parent.setblock(p,
                                     materials.RedStoneRepeaterOff, 4, lock=True)
                self.parent.setblock(p+Vec(-1,0,-1),
                                     materials.RedStoneWire, 0, lock=True)
        self.parent.setblock(self.c1+Vec(2,1,3),
                             materials.RedStoneRepeaterOff, 4, lock=True)
        self.parent.setblock(self.c1+Vec(1,1,2),
                             materials.RedStoneWire, 0, lock=True)
        self.parent.setblock(self.c1+Vec(2,1,5),
                             materials.RedStoneRepeaterOff, 4, lock=True)
        self.parent.setblock(self.c1+Vec(1,1,4),
                             materials.RedStoneWire, 0, lock=True)
        for z, p in [(18,13),(16,12),(14,9),(12,3),(10,2),(8,10),(4,14),(2,18)]:
            self.parent.setblock(self.c1+Vec(0,2,z),
                                 materials.Dirt, lock=True, hide=True)
            self.parent.setblock(self.c1+Vec(0,1,z),
                                 materials.NoteBlock, lock=True)
            self.parent.addnoteblock(self.c1+Vec(0,1,z), p)
            self.parent.setblock(self.c1+Vec(0,0,z),
                                 materials.Air, lock=True)

class ThroneRoom(Basic):
    _name = 'throneroom'
    _is_entrance = False
    _is_stairwell = False
    _is_treasureroom = True
    _min_size = Vec(1,1,2)
    _max_size = Vec(1,1,2)
    size = Vec(1,1,2)

    def placed(self):
        self.canvas = (
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0))
        rooms = []
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        # This room contains no halls, but is connected to the East  
        # West, South, East, North
        pos = self.pos
        rooms.append(pos)
        self.hallLength = [1,1,0,1]
        self.hallSize = [[6,sx-6],
                         [6,sx-6],
                         [6,sz-6],
                         [6,sz-6]]
        self.parent.halls[pos.x][pos.y][pos.z] = [0,0,1,0]

        # Place one room to the East
        # This room can have halls N, E, or S and is connected to the West
        pos = self.pos + Vec(0,0,1)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [0,0,0,0]
        room.hallSize = [[6,sx-6],
                         [6,sx-6],
                         [6,sz-6],
                         [6,sz-6]]
        room.parent.halls[pos.x][pos.y][pos.z] = [1,1,1,1]
        # This room cannot connect. Make the depth < 0
        room.parent.maze[pos].depth = -1
        return rooms

    def render(self):
        sx = 16
        sy = 12
        sz = 32
        o = self.loc
        pos = self.pos

        # alias for setblock
        sb = self.parent.setblock

        # symmetrical setblock. A lot of this room will be symmetrical. 
        def ssb (p, mat, data=0):
            sb(o+p, mat, data)
            sb(Vec(o.x+sx-1-p.x, o.y+p.y, o.z+p.z), mat, data)

        # Column materials
        cmat = random.choice([
            [materials.Sandstone, materials.SandstoneSlab],
            [materials.meta_mossycobble, materials.CobblestoneSlab],
            [materials.Stone, materials.StoneSlab]
        ])

        # Decoration colors
        # inner color, trim color
        dmat = random.choice([
            [materials.RedWool, materials.YellowWool],
            [materials.RedWool, materials.LightGrayWool],
            [materials.BlueWool, materials.YellowWool],
            [materials.DarkGreenWool, materials.YellowWool],
            [materials.DarkGreenWool, materials.BlackWool],
            [materials.PurpleWool, materials.YellowWool],
            [materials.CyanWool, materials.YellowWool],
            [materials.LightBlueWool, materials.LightGrayWool]
        ])

        # Basic room
        # Air space
        for p in iterate_cube(o, o+Vec(sx-1,sy-1,sz-1)):
            sb(p, materials.Air)
        # Walls
        for p in iterate_four_walls(o, o+Vec(sx-1,0,sz-1), -sy+1):
            sb(p, materials._wall)
        # Ceiling and floor
        for p in iterate_cube(o, o+Vec(sx-1,0,sz-1)):
            sb(p, materials._ceiling)
            sb(p.down(sy-1), materials._floor)

        # Wooden balcony
        for p in iterate_cube(Vec(1,4,1), Vec(3,4,9)):
            ssb(p, materials.WoodPlanks)
        for p in iterate_cube(Vec(1,4,1), Vec(5,4,3)):
            ssb(p, materials.WoodPlanks)
        for p in iterate_cube(Vec(1,4,1), Vec(2,4,8)):
            ssb(p, materials.WoodenSlab)
        for p in iterate_cube(Vec(1,4,1), Vec(5,4,2)):
            ssb(p, materials.WoodenSlab)
        for p in iterate_cube(Vec(1,3,9), Vec(2,3,9)):
            ssb(p, materials.Fence)
        for p in iterate_cube(Vec(4,3,3), Vec(5,3,3)):
            ssb(p, materials.Fence)
        for p in iterate_cube(Vec(3,3,3), Vec(3,3,9)):
            ssb(p, materials.Fence)

        # Entry stairs
        for x in xrange(6):
            ssb(Vec(6,5+x,1+x), materials.meta_mossycobble)
            ssb(Vec(7,5+x,1+x), materials.meta_mossycobble)
            ssb(Vec(6,5+x,2+x), materials.meta_mossycobble)
            ssb(Vec(7,5+x,2+x), materials.meta_mossycobble)
            ssb(Vec(6,5+x,3+x), materials.StoneStairs, 3)
            ssb(Vec(7,5+x,3+x), materials.StoneStairs, 3)
        # Skip this is ther is no door to the West
        if self.parent.halls[pos.x][pos.y][pos.z][0] == 1:
            for p in iterate_cube(Vec(6,4,1), Vec(7,4,1)):
                ssb(p, materials.StoneStairs, 3)

        # Columns
        for i in xrange(6):
            j = i*4
            for p in iterate_cube(Vec(3,0,4+j), Vec(3,11,5+j)):
                ssb(p, cmat[0])
            ssb(Vec(4,10,4+j), cmat[1])
            ssb(Vec(4,10,5+j), cmat[1])

        # Rug
        for p in iterate_cube(Vec(6,11,9), Vec(6,11,25)):
            ssb(p, dmat[1])
        for p in iterate_cube(Vec(7,11,9), Vec(7,11,25)):
            ssb(p, dmat[0])
        for x in xrange(20):
            p = Vec(random.randint(6,9), 11, random.randint(9,25))
            sb(o+p, materials._floor)

        # Throne
        # Stairs
        for x in xrange(3):
            ssb(Vec(7,10-x,24+x), materials.StoneStairs, 2)
            ssb(Vec(7,10-x,25+x), materials.meta_mossycobble)
            ssb(Vec(7,10-x,26+x), materials.meta_mossycobble)
        # Platform
        for p in iterate_cube(Vec(6,8,27), Vec(7,10,27)):
            ssb(p, materials.Bedrock)
        for p in iterate_cube(Vec(5,8,28), Vec(7,10,29)):
            ssb(p, materials.Bedrock)
        # Lava bucket
        ssb(Vec(6,10,30), materials.meta_mossycobble)
        ssb(Vec(6,9,30), materials.meta_mossycobble)
        ssb(Vec(7,11,30), materials.Lava)
        # The throne
        ssb(Vec(7,7,29), materials.WoodPlanks)
        ssb(Vec(7,6,29), materials.WoodPlanks)
        sb(o+Vec(7,7,28), materials.WoodenStairs, 1)
        sb(o+Vec(8,7,28), materials.WoodenStairs, 0)
        sb(o+Vec(6,6,29), materials.RedStoneTorchOn, 2)
        sb(o+Vec(9,6,29), materials.RedStoneTorchOn, 1)
        ssb(Vec(7,5,29), materials.Fence)
        ssb(Vec(7,4,29), materials.RedStoneTorchOn, 5)

        # Back wall
        wall = random.choice(
            [
                # Creeper
               [[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [0,0,0,0,0,1,1,0,0,1,1,0,0,0,0,0],
                [0,0,0,0,0,1,1,0,0,1,1,0,0,0,0,0],
                [0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],

                # Wings
               [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,1,1,1,1,1,1,0,0,1,1,1,1,1,1,0],
                [0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0],
                [0,0,1,1,1,1,1,0,0,1,1,1,1,1,0,0],
                [0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0],
                [0,0,0,1,1,1,0,0,0,0,1,1,1,0,0,0],
                [0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],

                # Triforce
               [[0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
                [0,0,0,0,0,2,0,2,2,0,2,0,0,0,0,0],
                [0,0,0,0,3,0,2,2,2,2,0,3,0,0,0,0],
                [0,0,0,3,3,3,0,0,0,0,3,3,3,0,0,0],
                [0,0,3,0,0,0,3,0,0,3,0,0,0,3,0,0],
                [0,3,3,3,0,3,3,3,3,3,3,0,3,3,3,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],

                # Banners
               [[0,3,2,2,3,0,3,2,2,3,0,3,2,2,3,0],
                [0,3,2,2,3,0,3,2,2,3,0,3,2,2,3,0],
                [0,3,2,2,3,0,3,2,2,3,0,3,2,2,3,0],
                [0,3,2,2,3,0,3,2,2,3,0,3,2,2,3,0],
                [0,0,2,2,0,0,3,2,2,3,0,0,2,2,0,0],
                [0,0,0,0,0,0,3,2,2,3,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,2,2,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
            ]
        )
        w = random.choice([materials.BlackWool,
                           materials.RedWool])
        for y in xrange(10):
            for x in xrange(16):
                if wall[y][x] == 1:
                    sb(o+Vec(x,y+1,31), w)
                elif wall[y][x] == 2:
                    sb(o+Vec(x,y+1,31), dmat[0])
                elif wall[y][x] == 3:
                    sb(o+Vec(x,y+1,31), dmat[1])
        # Chest. Maxtier plus a level zero.
        sb(o+Vec(7,7,30), materials.Chest)
        self.parent.addchest(o+Vec(7,7,30), loottable._maxtier)
        sb(o+Vec(8,7,30), materials.Chest)
        self.parent.addchest(o+Vec(8,7,30), 0)

        # Spawners
        for i in xrange(7):
            j = i*4
            if (random.random() < 0.5):
                sb(o+Vec(0,10,4+j), materials.Spawner)
                self.parent.addspawner(o+Vec(0,10,4+j))
            if (random.random() < 0.5):
                sb(o+Vec(15,10,4+j), materials.Spawner)
                self.parent.addspawner(o+Vec(15,10,4+j))
        # Ropes
        for p in iterate_cube(o.trans(5,1,5), o.trans(10,1,30)):
            if random.random() < 0.07:
                for q in iterate_cube(p, p.down(random.randint(0,2))):
                    sb(q, materials.Fence)

        # Portal
        if (cfg.mvportal != ''):
            # Obsidian portal frame.
            for p in iterate_cube(Vec(6,7,1), Vec(9,11,1)):
                sb(o+p, materials.Obsidian)
            # Portal stuff.
            for p in iterate_cube(Vec(7,8,1), Vec(8,10,1)):
                sb(o+p, materials.NetherPortal)
            # Sign.
            sb(o+Vec(6,9,2), materials.WallSign, 3)
            self.parent.addsign(o+Vec(6,9,2),
                                       '[multiverse]',
                                       cfg.mvportal,
                                       '','')

        # Cobwebs
        webs = {}
        for p in iterate_cube(o.down(1), o.trans(15,4,31)):
            count = 0
            perc = 90 - (p.y - self.loc.down(1).y) * (70/3)
            if (p not in self.parent.blocks or
                self.parent.blocks[p].material != materials.Air):
                continue
            for q in (Vec(1,0,0), Vec(-1,0,0),
                      Vec(0,1,0), Vec(0,-1,0),
                      Vec(0,0,1), Vec(0,0,-1)):
                if (p+q in self.parent.blocks and
                    self.parent.blocks[p+q].material != materials.Air and
                    random.randint(1,100) <= perc):
                    count += 1
            if count >= 3:
                webs[p] = True
        for p, q in webs.items():
            self.parent.setblock(p, materials.Cobweb)


class SpiderLair(Basic):
    _name = 'spiderlair'
    _is_entrance = False
    _is_stairwell = False
    _is_treasureroom = True
    _min_size = Vec(1,1,2)
    _max_size = Vec(1,1,2)
    size = Vec(1,1,2)

    def placed(self):
        self.canvas = (
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0))
        rooms = []
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        # This room contains no halls, but is connected to the East  
        # West, South, East, North
        pos = self.pos
        rooms.append(pos)
        self.hallLength = [0,0,0,0]
        self.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        self.parent.halls[pos.x][pos.y][pos.z] = [1,1,1,1]
        # This room cannot connect. Make the depth < 0
        self.parent.maze[pos].depth = -1

        # Place one room to the East
        # This room can have halls N, E, or S and is connected to the West
        pos = self.pos + Vec(0,0,1)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [0,1,1,1]
        room.hallSize = [[2,sx-2],
                         [2,sx-2],
                         [2,sz-2],
                         [2,sz-2]]
        room.parent.halls[pos.x][pos.y][pos.z][0] = 1
        return rooms

    def render(self):
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        height = sy - 2
        outer_cave = cave_factory.new(sx, sz)
        inner_cave = cave_factory.new(sx, sz)

        # Add halls
        inner_room = self.parent.rooms[self.pos]
        outer_room = self.parent.rooms[self.pos + Vec(0,0,1)]
        # South side
        if (outer_room.halls[1].size > 0):
            outer_cave.add_exit((outer_room.halls[1].offset, sx-1),
                          (outer_room.halls[1].offset+outer_room.halls[1].size, sx-1))
        # East side
        if (outer_room.halls[2].size > 0):
            outer_cave.add_exit((sz-1, outer_room.halls[2].offset),
                          (sz-1, outer_room.halls[2].offset+outer_room.halls[2].size))
        # North side
        if (outer_room.halls[3].size > 0):
            outer_cave.add_exit((outer_room.halls[3].offset, 0),
                          (outer_room.halls[3].offset+outer_room.halls[3].size, 0))
        # Center
        inner_cave.add_exit((15,1), (15,15))
        outer_cave.add_exit((0,0),  (0,15))

        # Portal
        if (cfg.mvportal != ''):
            inner_cave.add_exit((0,1), (0,4))

        # Carve caves
        outer_cave.gen_map()
        inner_cave.gen_map(mode='room')

        # Air space, Floor, and Ceiling
        q = self.loc+Vec(0,4,15)
        for p in outer_cave.iterate_map(cave_factory.FLOOR):
            self.parent.setblock(q+Vec(p[0],-3,p[1]), materials.Air)
            self.parent.setblock(q+Vec(p[0],-2,p[1]), materials.Air)
            self.parent.setblock(q+Vec(p[0],-1,p[1]), materials.Air)
            self.parent.setblock(q+Vec(p[0],0,p[1]), materials._floor)
            self.parent.setblock(q+Vec(p[0],-height,p[1]),
                                 materials._ceiling, 0, True)
        q = self.loc+Vec(0,4,0)
        for p in inner_cave.iterate_map(cave_factory.FLOOR):
            self.parent.setblock(q+Vec(p[0],-3,p[1]), materials.Air)
            self.parent.setblock(q+Vec(p[0],-2,p[1]), materials.Air)
            self.parent.setblock(q+Vec(p[0],-1,p[1]), materials.Air)
            self.parent.setblock(q+Vec(p[0],0,p[1]), materials._floor)
            self.parent.setblock(q+Vec(p[0],-height,p[1]),
                                 materials._ceiling, 0, True)
        # Walls
        q = self.loc+Vec(0,4,15)
        for p in outer_cave.iterate_walls():
            self.parent.setblock(q+Vec(p[0],-4,p[1]), materials._wall,
                                0, True)
            self.parent.setblock(q+Vec(p[0],-3,p[1]), materials._wall)
            self.parent.setblock(q+Vec(p[0],-2,p[1]), materials._wall)
            self.parent.setblock(q+Vec(p[0],-1,p[1]), materials._wall)
        outer_cave.grow_map()
        for p in outer_cave.iterate_walls():
            self.parent.setblock(q+Vec(p[0],-3,p[1]), materials._wall,
                                0, True)
        q = self.loc+Vec(0,4,0)
        for p in inner_cave.iterate_walls():
            self.parent.setblock(q+Vec(p[0],-4,p[1]), materials._wall,
                                0, True)
            self.parent.setblock(q+Vec(p[0],-3,p[1]), materials._wall)
            self.parent.setblock(q+Vec(p[0],-2,p[1]), materials._wall)
            self.parent.setblock(q+Vec(p[0],-1,p[1]), materials._wall)
        inner_cave.grow_map()
        for p in inner_cave.iterate_walls():
            self.parent.setblock(q+Vec(p[0],-3,p[1]), materials._wall,
                                0, True)
        # Spider pit
        pit_blocks = []
        inner_cave.purge_exits()
        inner_cave.add_exit((15,5), (15,11))
        inner_cave.grow_map()
        pit_depth = self.parent.position.y - self.parent.levels * \
            self.parent.room_height
        q = self.loc+Vec(0,4,0)
        for p in inner_cave.iterate_map(cave_factory.FLOOR):
            for x in xrange(pit_depth+1):
                self.parent.setblock(q+Vec(p[0],x,p[1]), materials.Air)
            self.parent.setblock(q+Vec(p[0],0,p[1]), materials.Cobweb)
            pit_blocks.append(q+Vec(p[0],0,p[1]))
            self.parent.setblock(q+Vec(p[0],pit_depth+1,p[1]), materials.Lava)
        # Chest
        c = random.choice(pit_blocks)
        pit_blocks.remove(c)
        self.parent.setblock(c, materials.Chest)
        self.parent.addchest(c, loottable._maxtier)
        # Spider spawners
        # In the future, maybe spiders will walk on web
        #for x in xrange(3):
        #    s = random.choice(pit_blocks)
        #    pit_blocks.remove(s)
        #    self.parent.setblock(s, materials.Spawner)
        #    self.parent.addspawner(s, 'Spider')
        # Spiders in teh walls!
        count = 0
        while count < 5:
            p = self.loc+Vec(random.randint(0,15),3,random.randint(0,32))
            if p not in self.parent.blocks:
                self.parent.setblock(p, materials.Spawner)
                self.parent.setblock(p.up(1), materials.Air)
                self.parent.setblock(p.up(2), materials.Air)
                self.parent.setblock(p.up(3), materials.Air)
                self.parent.addspawner(p, 'CaveSpider')
                count += 1

        # Portal
        if (cfg.mvportal != ''):
            o = self.loc
            sb = self.parent.setblock
            # Obsidian portal frame.
            for p in iterate_cube(Vec(1,0,0), Vec(4,4,0)):
                sb(o+p, materials.Obsidian)
            # Portal stuff.
            for p in iterate_cube(Vec(2,1,0), Vec(3,3,0)):
                sb(o+p, materials.NetherPortal)
            # Sign.
            sb(o+Vec(1,2,1), materials.WallSign, 3)
            self.parent.addsign(o+Vec(1,2,1),
                                       '[multiverse]',
                                       cfg.mvportal,
                                       '', '')

        # Cobwebs
        webs = {}
        for p in iterate_cube(self.loc.down(1), self.loc.trans(15,3,31)):
            count = 0
            perc = 90 - (p.y - self.loc.down(1).y) * (70/3)
            if (p not in self.parent.blocks or
                self.parent.blocks[p].material != materials.Air):
                continue
            for q in (Vec(1,0,0), Vec(-1,0,0),
                      Vec(0,1,0), Vec(0,-1,0),
                      Vec(0,0,1), Vec(0,0,-1)):
                if (p+q in self.parent.blocks and
                    self.parent.blocks[p+q].material != materials.Air and
                    random.randint(1,100) <= perc):
                    count += 1
            if count >= 3:
                webs[p] = True
        for p, q in webs.items():
            self.parent.setblock(p, materials.Cobweb)


class PitWithArchers(Basic2x2):
    _name = 'pitwitharchers'
    _is_entrance = False
    _is_stairwell = False
    _is_treasureroom = True

    def placed(self):
        rooms = Basic2x2.placed(self)
        # Narrow the hall connections a little to make room for the skeleton
        # balconies.
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        for room in rooms:
            r = self.parent.rooms[room]
            r.hallSize = [[6,sx-6],
                             [6,sx-6],
                             [6,sz-6],
                             [6,sz-6]]
        return rooms

    def render(self):
        pit_depth = self.parent.position.y - self.parent.levels * \
            self.parent.room_height
        # We start with the basics...
        Basic2x2.render(self)
        # Clear out an air space.
        for p in iterate_cube(self.c1+Vec(1,0,1),
                              self.c3+Vec(-1,pit_depth,-1)):
            self.parent.setblock(p, materials.Air)
        # Lava!
        for p in iterate_cube(self.c1.down(pit_depth+1),
                              self.c3.down(pit_depth+1)):
            self.parent.setblock(p, materials.Lava)
        # Build a bridge around the edge
        for p in iterate_four_walls(self.c1+Vec(1,0,1),
                                    self.c3+Vec(-1,0,-1),0):
            self.parent.setblock(p, materials.WoodenSlab)
        # Make some island areas
        cave = cave_factory.new(22, 22)
        cave.gen_map()
        for p in cave.iterate_map(cave_factory.FLOOR):
            pp = Vec(p[0],0,p[1])+self.c1+Vec(3,1,3)
            for x in iterate_cube(pp, pp.down(pit_depth)):
                self.parent.setblock(x, materials._floor)
        # Some tasteful recessed lighting
        for p in iterate_cube(self.c1+Vec(14,-4,14),
                              self.c3-Vec(14,4,14)):
            self.parent.setblock(p, materials.Air)
            self.parent.setblock(p.up(1), materials.Glowstone)
        # Central pillar
        for p in iterate_cylinder(self.c1+Vec(10,2,10),
                                  self.c3-Vec(10,-pit_depth,10)):
            self.parent.setblock(p, materials._subfloor)
        for p in iterate_disc(self.c1+Vec(10,1,10),
                                  self.c3-Vec(10,-1,10)):
            self.parent.setblock(p, materials.Air)
        for p in iterate_ellipse(self.c1+Vec(10,1,10),
                                  self.c3-Vec(10,-1,10)):
            self.parent.setblock(p, materials.CobblestoneSlab)
        center = self.c1+Vec(14,1,12)
        if (cfg.mvportal != ''):
            # Obsidian portal frame.
            for p in iterate_cube(center.trans(-2,1,0), center.trans(1,-3,0)):
                self.parent.setblock(p, materials.Obsidian)
            # Portal stuff.
            for p in iterate_cube(center.trans(-1,0,0), center.trans(0,-2,0)):
                self.parent.setblock(p, materials.NetherPortal)
            # Signs.
            self.parent.setblock(center.trans(1,-1,-1),
                                        materials.WallSign)
            self.parent.blocks[center.trans(1,-1,-1)].data = 3
            # Create the tile entities for the signs.
            self.parent.addsign(center.trans(1,-1,-1),
                                       '[multiverse]',
                                       cfg.mvportal,
                                       '', '')
        # Treasure!
        self.parent.setblock(center.trans(0,0,3),
                                    materials.Chest)
        self.parent.addchest(center.trans(0,0,3),
                                    loottable._maxtier)
        # Oh fuck! Skeletons!
        for x in (self.c1+Vec(1,0,1), self.c2+Vec(-1,0,1),
                  self.c3+Vec(-1,0,-1), self.c4+Vec(1,0,-1)):
            b1 = x-Vec(3,0,3)
            b2 = x+Vec(3,0,3)
            for p in iterate_tube(b1, b2, 1):
                if (p in self.parent.blocks and (
                    self.parent.blocks[p].material == materials.Air or
                    self.parent.blocks[p].material == materials.WoodenSlab or
                    self.parent.blocks[p].material == materials.Fence)):
                    self.parent.setblock(p, materials.Fence)
            for p in iterate_disc(b1, b2):
                if (p in self.parent.blocks and (
                    self.parent.blocks[p].material == materials.Air or
                    self.parent.blocks[p].material == materials.WoodenSlab or
                    self.parent.blocks[p].material == materials.Fence)):
                    self.parent.setblock(p, materials._floor)
            self.parent.addspawner(x.up(1), 'Skeleton')
            self.parent.setblock(x.up(1), materials.Spawner)

class EndPortal(Basic2x2):
    _name = 'endportal'
    _is_entrance = False
    _is_stairwell = False
    _is_treasureroom = True
    _pistontrap = False

    def placed(self):
        rooms = Basic2x2.placed(self)
        # Narrow the hall connections 
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        for room in rooms:
            r = self.parent.rooms[room]
            r._pistontrap = False
            for h in xrange(4):
                if r.hallLength[h] > 0:
                    if (h == 0 or h == 3):
                        r.hallLength[h] = 3
                    else:
                        r.hallLength[h] = 4
            r.hallSize = [[6,sx-7],
                          [6,sx-7],
                          [6,sz-7],
                          [6,sz-7]]
        return rooms

    def setData(self):
        Basic2x2.setData(self)
        self.canvas = (
            Vec(0,0,0),
            Vec(0,0,0),
            Vec(0,0,0))

    def render(self):
        sx = 31
        sy = 9
        sz = 31
        o = self.loc
        pos = self.pos

        # custom setblock
        def sb(p, mat, data=0, hide=False, stairdat=False, flip=False):
            if stairdat == True:
                x = p.x-o.x-(sx-1)/2
                z = p.z-o.z-(sz-1)/2
                if (abs(x) == abs(z)):
                    mat = materials.StoneBrick
                    data = 0
                else:
                    if (abs(x) > abs(z)):
                        if x > 0:
                            data = 0 # Ascending East
                        else:
                            data = 1 # Ascending West
                    else:
                        if z > 0:
                            data = 2 # Ascending South
                        else:
                            data = 3 # Ascending North
                    if flip == True:
                        data = data ^ 1
            self.parent.setblock(p, mat, data, hide)

        # symmetrical setblock. A lot of this room will be symmetrical. 
        def ssb (p, mat, data=0, hide=False, stairdat=False, flip=False):
            sb(o+p, mat, data, hide, stairdat, flip)
            sb(Vec(o.x+sx-1-p.x, o.y+p.y, o.z+p.z), mat, data, hide,
               stairdat, flip)
            sb(Vec(o.x+p.x, o.y+p.y, o.z+sz-1-p.z), mat, data, hide,
               stairdat, flip)
            sb(Vec(o.x+sx-1-p.x, o.y+p.y, o.z+sz-1-p.z), mat, data, hide,
               stairdat, flip)

        # Basic room
        # Air space
        for p in iterate_cylinder(o, o+Vec(sx-1,sy-1,sz-1)):
            sb(p, materials.Air)
        # Walls
        for p in iterate_tube(o+Vec(0,sy-1,0), o+Vec(sx-1,sy-1,sz-1), sy-1):
            sb(p, materials._wall)
        # Ceiling and floor
        for p in iterate_cylinder(o, o+Vec(sx-1,0,sz-1)):
            sb(p, materials._ceiling, hide=True)
            sb(p.down(sy-1), materials.meta_mossystonebrick)

        # Lava pit
        for p in iterate_cube(o+Vec(12,sy-2,12), o+Vec(18,sy-2,18)):
            sb(p, materials.Lava)
        for p in iterate_cube(Vec(14,sy-2,13), Vec(15,sy-2,13)):
            ssb (p, materials.meta_mossystonebrick)
        for p in iterate_cube(Vec(13,sy-2,14), Vec(13,sy-2,15)):
            ssb (p, materials.meta_mossystonebrick)
        ssb (Vec(11, sy-2, 13), materials.meta_mossystonebrick)
        ssb (Vec(12, sy-2, 12), materials.meta_mossystonebrick)
        ssb (Vec(13, sy-2, 11), materials.meta_mossystonebrick)
        for p in iterate_cube(Vec(14,sy-2,10), Vec(15,sy-2,12)):
            ssb (p, materials.meta_mossystonebrick)
        for p in iterate_cube(Vec(10,sy-2,14), Vec(12,sy-2,15)):
            ssb (p, materials.meta_mossystonebrick)

        # Lava pit stairs
        for p in iterate_cube(Vec(14,sy-2,9), Vec(16,sy-2,9)):
            q = p.s(1)
            ssb(p, materials.StoneBrickStairs, stairdat=True, flip=True)
            ssb(q, materials.meta_mossystonebrick)
            ssb(Vec(p.z, p.y, p.x), materials.StoneBrickStairs, stairdat=True,
                flip=True)
            ssb(Vec(q.z, q.y, q.x), materials.meta_mossystonebrick)
        for p in iterate_cube(Vec(14,sy-3,10), Vec(16,sy-3,10)):
            q = p.s(1)
            ssb(p, materials.StoneBrickStairs, stairdat=True, flip=True)
            ssb(q, materials.meta_mossystonebrick)
            ssb(Vec(p.z, p.y, p.x), materials.StoneBrickStairs, stairdat=True,
                flip=True)
            ssb(Vec(q.z, q.y, q.x), materials.meta_mossystonebrick)
        for p in iterate_cube(Vec(14,sy-4,11), Vec(16,sy-4,11)):
            q = p.s(1)
            ssb(p, materials.StoneBrickStairs, stairdat=True, flip=True)
            ssb(q, materials.meta_mossystonebrick)
            ssb(Vec(p.z, p.y, p.x), materials.StoneBrickStairs, stairdat=True,
                flip=True)
            ssb(Vec(q.z, q.y, q.x), materials.meta_mossystonebrick)

        # Portal
        for p in iterate_cube(Vec(14,sy-4,13), Vec(16,sy-4,13)):
            # North Edge
            eye = random.choice([0,0,0,0,0,0,0,0,0,4])
            sb(o+p, materials.EndPortalFrame, 0+eye)
            # South Edge
            eye = random.choice([0,0,0,0,0,0,0,0,0,4])
            sb(o+p.trans(0,0,4), materials.EndPortalFrame, 2+eye)
            # West Edge
            eye = random.choice([0,0,0,0,0,0,0,0,0,4])
            sb(o+Vec(p.z, p.y, p.x), materials.EndPortalFrame, 3+eye)
            # East Edge
            eye = random.choice([0,0,0,0,0,0,0,0,0,4])
            sb(o+Vec(p.z, p.y, p.x).trans(4,0,0),materials.EndPortalFrame,1+eye)

        # Entry stairs
        for p in iterate_cube(Vec(7,4,3), Vec(8,4,3)):
            ssb(p, materials.StoneBrickStairs, stairdat=True)
            ssb(Vec(p.z, p.y, p.x), materials.StoneBrickStairs, stairdat=True)
            for q in iterate_cube(p.down(1), p.down(3)):
                ssb(q, materials.meta_mossystonebrick)
                ssb(Vec(q.z, q.y, q.x), materials.meta_mossystonebrick)
        for p in iterate_cube(Vec(6,5,4), Vec(8,5,4)):
            ssb(p, materials.StoneBrickStairs, stairdat=True)
            ssb(Vec(p.z, p.y, p.x), materials.StoneBrickStairs, stairdat=True)
            for q in iterate_cube(p.down(1), p.down(2)):
                ssb(q, materials.meta_mossystonebrick)
                ssb(Vec(q.z, q.y, q.x), materials.meta_mossystonebrick)
        for p in iterate_cube(Vec(5,6,5), Vec(8,6,5)):
            ssb(p, materials.StoneBrickStairs, stairdat=True)
            ssb(Vec(p.z, p.y, p.x), materials.StoneBrickStairs, stairdat=True)
            for q in iterate_cube(p.down(1), p.down(1)):
                ssb(q, materials.meta_mossystonebrick)
                ssb(Vec(q.z, q.y, q.x), materials.meta_mossystonebrick)
        for p in iterate_cube(Vec(6,7,6), Vec(8,7,6)):
            ssb(p, materials.StoneBrickStairs, stairdat=True)
            ssb(Vec(p.z, p.y, p.x), materials.StoneBrickStairs, stairdat=True)

        # Candelabra
        for p in [
            Vec(9,sy-2,10), Vec(11,sy-2,10), Vec(10,sy-2,9), Vec(10,sy-2,11),
            Vec(10,sy-2,10), Vec(10,sy-3,10),
            Vec(9,sy-4,10), Vec(11,sy-4,10), Vec(10,sy-4,9), Vec(10,sy-4,11),
            Vec(10,sy-4,10),
            Vec(9,sy-5,10), Vec(11,sy-5,10), Vec(10,sy-5,9), Vec(10,sy-5,11),
            ]:
            ssb(p, materials.IronBars)
        ssb(Vec(10,sy-5,10), materials.Netherrack)
        ssb(Vec(10,sy-6,10), materials.Fire)

        # Fancy iron bars
        for p in iterate_cube(Vec(5,1,5), Vec(5,5,5)):
            ssb(p, materials.IronBars)
        for p in iterate_cube(Vec(10,2,1), Vec(10,sy-3,1)):
            ssb(p, materials.IronBars)
            ssb(Vec(p.z, p.y, p.x), materials.IronBars)

        # Decoration colors
        # inner color, trim color
        dmat = random.choice([
            #[materials.RedWool, materials.OrangeWool],
            #[materials.PurpleWool, materials.BlackWool],
            [materials.IronBars, materials.IronBars],
            [materials.IronBars, materials.IronBars]
        ])

        # Wall decor
        wall = random.choice(
            [
                # Banner
               [[3,2,2,2,2,2,3],
                [0,3,2,2,2,3,0],
                [0,0,3,2,3,0,0],
                [0,0,3,2,3,0,0],
                [0,0,0,3,0,0,0],
                [0,0,0,3,0,0,0],
                [0,0,0,3,0,0,0]],
                # Banner
               [[3,2,2,2,2,2,3],
                [0,3,2,2,2,3,0],
                [0,0,3,2,3,0,0],
                [0,0,3,2,3,0,0],
                [0,0,0,3,0,0,0],
                [0,0,0,3,0,0,0],
                [0,0,0,3,0,0,0]]
            ])
        for y in xrange(7):
            for x in xrange(7):
                if wall[y][x] == 2:
                    sb(o+Vec(x+12,y+1,0), dmat[0])
                    sb(o+Vec(x+12,y+1,30), dmat[0])
                    sb(o+Vec(0,y+1,x+12), dmat[0])
                    sb(o+Vec(30,y+1,x+12), dmat[0])
                elif wall[y][x] == 3:
                    sb(o+Vec(x+12,y+1,0), dmat[1])
                    sb(o+Vec(x+12,y+1,30), dmat[1])
                    sb(o+Vec(0,y+1,x+12), dmat[1])
                    sb(o+Vec(30,y+1,x+12), dmat[1])

        # Treasure!
        sb(o+Vec(15,sy-2,1), materials.Chest)
        self.parent.addchest(o+Vec(15,sy-2,1), loottable._maxtier)

        # Endermen
        sb(o+Vec(0,sy-2,15), materials.Spawner)
        self.parent.addspawner(o+Vec(0,sy-2,15), 'Enderman')
        sb(o+Vec(30,sy-2,15), materials.Spawner)
        self.parent.addspawner(o+Vec(30,sy-2,15), 'Enderman')


class Arena(Basic2x2):
    _name = 'arena'
    _is_entrance = False
    _is_stairwell = False
    _is_treasureroom = True

    def placed(self):
        rooms = Basic2x2.placed(self)
        # Narrow the hall connections a little to make room for the skeleton
        # balconies.
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        for room in rooms:
            r = self.parent.rooms[room]
            for h in xrange(4):
                if r.hallLength[h] > 0:
                    r.hallLength[h] = 1
            r.hallSize = [[1,sx-1],
                             [6,sx-6],
                             [1,sz-1],
                             [6,sz-6]]
        return rooms

    def render(self):
        sx = 32
        sy = 12
        sz = 32
        o = self.loc
        pos = self.pos

        # alias for setblock
        sb = self.parent.setblock

        # symmetrical setblock. A lot of this room will be symmetrical. 
        def ssb (p, mat, data=0, hide=False):
            sb(o+p, mat, data, hide)
            sb(Vec(o.x+sx-1-p.x, o.y+p.y, o.z+p.z), mat, data, hide)
            sb(Vec(o.x+p.x, o.y+p.y, o.z+sz-1-p.z), mat, data, hide)
            sb(Vec(o.x+sx-1-p.x, o.y+p.y, o.z+sz-1-p.z), mat, data, hide)

        # Decoration colors
        # inner color, trim color
        dmat = random.choice([
            [materials.RedWool, materials.YellowWool],
            [materials.RedWool, materials.LightGrayWool],
            [materials.BlueWool, materials.YellowWool],
            [materials.DarkGreenWool, materials.YellowWool],
            [materials.DarkGreenWool, materials.BlackWool],
            [materials.PurpleWool, materials.YellowWool],
            [materials.CyanWool, materials.YellowWool],
            [materials.LightBlueWool, materials.LightGrayWool]
        ])

        # Basic room
        # Air space
        for p in iterate_cube(o, o+Vec(sx-1,sy-1,sz-1)):
            sb(p, materials.Air)
        # Walls
        for p in iterate_four_walls(o, o+Vec(sx-1,0,sz-1), -sy+1):
            sb(p, materials._wall)
        # Ceiling and floor
        for p in iterate_cube(o, o+Vec(sx-1,0,sz-1)):
            sb(p, materials._ceiling, hide=True)
            sb(p.down(sy-1), materials._floor)
            sb(p.down(sy-2), materials._floor)
            sb(p.down(sy-3), materials._floor)
        ssb(Vec(15,0,15), materials.Glowstone, hide=True)

        # Spawners
        ssb(Vec(1,sy-4,1), materials.Spawner)
        ssb(Vec(1,sy-5,1), materials.StoneSlab)
        ssb(Vec(1,sy-6,1), materials.Fence)
        for p in iterate_cube(Vec(2,sy-4,1), Vec(3,sy-5,2)):
            ssb(p, materials.Fence)
        for p in iterate_cube(Vec(1,sy-4,2), Vec(2,sy-5,3)):
            ssb(p, materials.Fence)
        self.parent.addspawner(o+Vec(1,sy-4,1))
        self.parent.addspawner(o+Vec(sx-2,sy-4,1))
        self.parent.addspawner(o+Vec(1,sy-4,sz-2))
        self.parent.addspawner(o+Vec(sx-2,sy-4,sz-2))

        # Wooden balcony
        for p in iterate_cube(Vec(1,4,1), Vec(3,4,9)):
            ssb(p, materials.WoodPlanks)
        for p in iterate_cube(Vec(1,4,1), Vec(14,4,3)):
            ssb(p, materials.WoodPlanks)
        for p in iterate_cube(Vec(1,4,1), Vec(2,4,8)):
            ssb(p, materials.WoodenSlab)
        for p in iterate_cube(Vec(1,4,1), Vec(15,4,2)):
            ssb(p, materials.WoodenSlab)
        for p in iterate_cube(Vec(1,3,9), Vec(2,3,9)):
            ssb(p, materials.Fence)
        for p in iterate_cube(Vec(4,3,3), Vec(14,3,3)):
            ssb(p, materials.Fence)
        for p in iterate_cube(Vec(3,3,3), Vec(3,3,9)):
            ssb(p, materials.Fence)
        ssb(Vec(15,4,3), materials.WoodenSlab)
        ssb(Vec(15,4,4), materials.WoodenSlab)
        ssb(Vec(15,4,5), materials.WoodenSlab)

        # Stairs
        for y in xrange(5, sy-3):
            p = Vec(25-2*y, y, 4)
            for q in iterate_cube(p, p.trans(-1,0,1)):
                ssb(q, materials.WoodPlanks)
            for q in iterate_cube(p.trans(-2,0,0), p.trans(-2,0,1)):
                ssb(q, materials.WoodenSlab)

        # Banners
        for p in iterate_cube(Vec(0,0,15), Vec(0,sy-5,15)):
            ssb(p, dmat[0])
        for p in iterate_cube(Vec(0,0,14), Vec(0,sy-7,14)):
            ssb(p, dmat[1])

        # Center arena
        for p in iterate_cylinder(Vec(4,sy-3,4), Vec(sx-5,sy-3,sz-5)):
            sb(o+p, materials.StoneSlab)
        for p in iterate_cylinder(Vec(5,sy-4,5), Vec(sx-6,sy-3,sz-6)):
            sb(o+p, materials.Air)
        for p in iterate_cylinder(Vec(7,sy-2,7), Vec(sx-8,sy-2,sz-8)):
            sb(o+p, materials.StoneSlab)
        for p in iterate_cylinder(Vec(8,sy-3,8), Vec(sx-9,sy-2,sz-9)):
            sb(o+p, materials.Air)
        for p in iterate_cylinder(Vec(9,sy-1,9), Vec(sx-10,sy-1,sz-10)):
            sb(o+p, materials.StoneSlab)

        # Pit
        depth = self.parent.position.y - (self.parent.levels-1) * \
            self.parent.room_height
        for p in iterate_cylinder(Vec(10,sy-2,10), Vec(sx-11,depth,sz-11)):
            sb(o+p, materials.Air)
        for p in iterate_cube(Vec(10,depth,10), Vec(sx-11,depth,sz-11)):
            sb(o+p, materials.Lava)

        pn = perlin.SimplexNoise(256)
        for p in iterate_cylinder(Vec(10,sy,10), Vec(sx-11,sy,sz-11)):
            n = pn.noise3(p.x/4.0, p.y/4.0, p.z/4.0)
            if (n > 0):
                sb(o+p, materials.Sand)
            else:
                sb(o+p, materials.Sandstone)

        # Treasure and more spawners
        sb(o+Vec(15,sy-1,15), materials.Chest)
        self.parent.addchest(o+Vec(15,sy-1,15), loottable._maxtier)
        sb(o+Vec(16,sy-1,16), materials.Chest)
        self.parent.addchest(o+Vec(16,sy-1,16))
        sb(o+Vec(15,sy-1,16), materials.Spawner)
        self.parent.addspawner(o+Vec(15,sy-1,16), 'Blaze')
        sb(o+Vec(16,sy-1,15), materials.Spawner)
        self.parent.addspawner(o+Vec(16,sy-1,15), 'Blaze')

        # Portal
        if (cfg.mvportal != ''):
            # Obsidian portal frame.
            for p in iterate_cube(Vec(1,sy-7,14), Vec(1,sy-3,17)):
                sb(p, materials.Obsidian)
            # Portal stuff.
            for p in iterate_cube(Vec(1,sy-6,15), Vec(1,sy-4,16)):
                sb(p, materials.NetherPortal)
            # Sign.
            sb(Vec(2,sy-5,17), materials.WallSign, 5)
            self.parent.addsign(o+Vec(2,sy-5,17),
                                       '<== Exit',
                                       '[multiverse]',
                                       cfg.mvportal,
                                       '<== Exit')


class Crypt(Basic):
    _name = 'crypt'
    _is_entrance = False
    _is_stairwell = False
    _is_treasureroom = True
    _min_size = Vec(1,1,2)
    _max_size = Vec(1,1,2)
    size = Vec(1,1,2)

    def placed(self):
        self.canvas = (
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0))
        rooms = []
        sx = self.parent.room_size
        sz = self.parent.room_size
        sy = self.parent.room_height
        # This room contains no halls, but is connected to the South  
        pos = self.pos
        rooms.append(pos)
        self.hallLength = [1,1,0,1]
        self.hallSize = [[6,sx-6],
                         [6,sx-6],
                         [6,sz-6],
                         [6,sz-6]]
        self.parent.halls[pos.x][pos.y][pos.z] = [0,0,1,0]

        # Place one room to the South
        pos = self.pos + Vec(0,0,1)
        room = new('blank', self.parent, pos)
        rooms.extend(self.parent.setroom(pos, room))
        room.hallLength = [0,0,0,0]
        room.hallSize = [[6,sx-6],
                         [6,sx-6],
                         [6,sz-6],
                         [6,sz-6]]
        room.parent.halls[pos.x][pos.y][pos.z] = [1,1,1,1]
        # This room cannot connect. Make the depth < 0
        room.parent.maze[pos].depth = -1
        return rooms

    def render(self):
        sx = 16
        sy = 12
        sz = 32
        o = self.loc
        pos = self.pos

        # alias for setblock
        sb = self.parent.setblock

        # symmetrical setblock. A lot of this room will be symmetrical. 
        def ssb (p, mat, data=0):
            sb(o+p, mat, data)
            sb(Vec(o.x+sx-1-p.x, o.y+p.y, o.z+p.z), mat, data)

        # Decoration colors
        # inner color, trim color
        dmat = random.choice([
            [materials.StoneBrick, materials.StoneBrick]
        ])

        # Basic room
        # Air space
        for p in iterate_cube(o, o+Vec(sx-1,sy-1,sz-1)):
            sb(p, materials.Air)
        # Walls
        for p in iterate_four_walls(o, o+Vec(sx-1,0,sz-1), -sy+1):
            sb(p, materials.meta_mossycobble)
        # Ceiling and floor
        for p in iterate_cube(o, o+Vec(sx-1,0,sz-1)):
            sb(p, materials._ceiling)
            sb(p.down(sy-1), materials._floor)

        # balcony
        for p in iterate_cube(Vec(1,4,1), Vec(3,4,9)):
            ssb(p, materials.meta_mossystonebrick)
        for p in iterate_cube(Vec(1,4,1), Vec(5,4,3)):
            ssb(p, materials.meta_mossystonebrick)
        for p in iterate_cube(Vec(1,4,1), Vec(2,4,8)):
            ssb(p, materials.StoneBrickSlab)
        for p in iterate_cube(Vec(1,4,1), Vec(5,4,2)):
            ssb(p, materials.StoneBrickSlab)
        for p in iterate_cube(Vec(1,3,9), Vec(2,3,9)):
            ssb(p, materials.IronBars)
        for p in iterate_cube(Vec(4,3,3), Vec(5,3,3)):
            ssb(p, materials.IronBars)
        for p in iterate_cube(Vec(3,3,3), Vec(3,3,9)):
            ssb(p, materials.IronBars)
        for p in iterate_cube(Vec(4,2,3), Vec(6,2,3)):
            ssb(p, materials.IronBars)
            ssb(p+Vec(1,-1,0), materials.IronBars)

        # Entry stairs
        for x in xrange(6):
            ssb(Vec(6,5+x,1+x), materials.meta_mossystonebrick)
            ssb(Vec(7,5+x,1+x), materials.meta_mossystonebrick)
            ssb(Vec(6,5+x,2+x), materials.meta_mossystonebrick)
            ssb(Vec(7,5+x,2+x), materials.meta_mossystonebrick)
            ssb(Vec(6,5+x,3+x), materials.StoneBrickStairs, 3)
            ssb(Vec(7,5+x,3+x), materials.StoneBrickStairs, 3)
        # Skip this is there is no door to the West
        if self.parent.halls[pos.x][pos.y][pos.z][0] == 1:
            for p in iterate_cube(Vec(6,4,1), Vec(7,4,1)):
                ssb(p, materials.StoneBrickStairs, 3)

        # Rug
        for p in iterate_cube(Vec(6,11,9), Vec(6,11,25)):
            ssb(p, dmat[1])
        for p in iterate_cube(Vec(7,11,9), Vec(7,11,25)):
            ssb(p, dmat[0])
        for x in xrange(20):
            p = Vec(random.randint(6,9), 11, random.randint(9,25))
            sb(o+p, materials._floor)

        # Back wall
        wall = random.choice(
            [
                # Creeper
               [[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                [0,0,0,0,0,1,1,0,0,1,1,0,0,0,0,0],
                [0,0,0,0,0,1,1,0,0,1,1,0,0,0,0,0],
                [0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],

                # Wings
               [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,1,1,1,1,1,1,0,0,1,1,1,1,1,1,0],
                [0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0],
                [0,0,1,1,1,1,1,0,0,1,1,1,1,1,0,0],
                [0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0],
                [0,0,0,1,1,1,0,0,0,0,1,1,1,0,0,0],
                [0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],

                # Triforce
               [[0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0],
                [0,0,0,0,0,2,0,2,2,0,2,0,0,0,0,0],
                [0,0,0,0,3,0,2,2,2,2,0,3,0,0,0,0],
                [0,0,0,3,3,3,0,0,0,0,3,3,3,0,0,0],
                [0,0,3,0,0,0,3,0,0,3,0,0,0,3,0,0],
                [0,3,3,3,0,3,3,3,3,3,3,0,3,3,3,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],

                # Banners
               [[0,3,2,2,3,0,3,2,2,3,0,3,2,2,3,0],
                [0,3,2,2,3,0,3,2,2,3,0,3,2,2,3,0],
                [0,3,2,2,3,0,3,2,2,3,0,3,2,2,3,0],
                [0,3,2,2,3,0,3,2,2,3,0,3,2,2,3,0],
                [0,0,2,2,0,0,3,2,2,3,0,0,2,2,0,0],
                [0,0,0,0,0,0,3,2,2,3,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,2,2,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
            ]
        )
        w = materials.StoneBrick
        for y in xrange(10):
            for x in xrange(16):
                if wall[y][x] == 1:
                    sb(o+Vec(x,y+1,31), w)
                elif wall[y][x] == 2:
                    sb(o+Vec(x,y+1,31), dmat[0])
                elif wall[y][x] == 3:
                    sb(o+Vec(x,y+1,31), dmat[1])

        # Loot for the small sarcophagi
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

        # Random stuff to be buried with.
        lootc = [(items.byName('bone'), 20),
                 (items.byName('book'), 10),
                 (items.byName('bow'), 10),
                 (items.byName('diamond'), 5),
                 (items.byName('gold ingot'), 5),
                 (items.byName('bowl'), 10),
                 (items.byName('feather'), 10),
                 (items.byName('golden apple'), 5),
                 (items.byName('paper'), 10),
                 (items.byName('clock'), 10),
                 (items.byName('compass'), 10),
                 (items.byName('gold nugget'), 10),
                 (items.byName('ender pearl'), 1),
                 (items.byName('blaze rod'), 1),
                 (items.byName('ghast tear'), 1),
                 (items.byName('glass bottle'), 10),
                 (items.byName('blaze powder'), 1),
                 (items.byName('magma cream'), 1),
                 (items.byName('eye of ender'), 1)]

        # Small sarcophagi
        for zoff in xrange(0, 24, 6):
            ssb(Vec(2,10,1+zoff), materials.EndStone)
            ssb(Vec(1,10,2+zoff), materials.EndStone)
            ssb(Vec(3,10,2+zoff), materials.EndStone)
            ssb(Vec(1,10,3+zoff), materials.EndStone)
            ssb(Vec(3,10,3+zoff), materials.EndStone)
            ssb(Vec(1,10,4+zoff), materials.EndStone)
            ssb(Vec(3,10,4+zoff), materials.EndStone)
            ssb(Vec(2,10,5+zoff), materials.EndStone)

            ssb(Vec(1,10,1+zoff), materials.SandstoneSlab)
            ssb(Vec(3,10,1+zoff), materials.SandstoneSlab)
            ssb(Vec(1,10,5+zoff), materials.SandstoneSlab)
            ssb(Vec(3,10,5+zoff), materials.SandstoneSlab)

            ssb(Vec(2,10,2+zoff), materials.Chest,4)
            i = weighted_choice(lootc)
            loota[7].id = i.value
            loota[7].data = i.data
            self.parent.addchest(o+Vec(2,10,2+zoff), 0, loot=loota)
            i = weighted_choice(lootc)
            loota[7].id = i.value
            loota[7].data = i.data
            self.parent.addchest(o+Vec(13,10,2+zoff), 0, loot=loota)
            ssb(Vec(2,10,3+zoff), materials.Chest,4)
            i = weighted_choice(lootc)
            lootb[7].id = i.value
            lootb[7].data = i.data
            self.parent.addchest(o+Vec(2,10,3+zoff), 0, loot=lootb)
            i = weighted_choice(lootc)
            lootb[7].id = i.value
            lootb[7].data = i.data
            self.parent.addchest(o+Vec(13,10,3+zoff), 0, loot=lootb)

            ssb(Vec(2,9,2+zoff), materials.StoneBrickStairs, 3)
            ssb(Vec(2,9,3+zoff), materials.StoneBrickSlab)
            ssb(Vec(2,9,4+zoff), materials.meta_mossystonebrick)

        # Spawners
        for p in [Vec(2,10,4),Vec(2,10,4+6),Vec(2,10,4+12),Vec(2,10,4+18),
                  Vec(13,10,4),Vec(13,10,4+6),Vec(13,10,4+12),Vec(13,10,4+18)]:
            if random.randint(1,100) >= 33:
                continue
            self.parent.addspawner(o+p, 'Skeleton')
            self.parent.setblock(o+p, materials.Spawner)

        # Dais
        for p in iterate_cube(o.trans(1,10,25), o.trans(14,10,25)):
            sb(p, materials.StoneBrickStairs, 2)
            sb(p+Vec(0,-1,1), materials.StoneBrickSlab)
        for p in iterate_cube(o.trans(1,9,27), o.trans(14,9,30)):
            sb(p, materials.meta_mossystonebrick)

        # Large Sarcophagus
        for p in iterate_cube(o.trans(5,8,28), o.trans(10,8,30)):
            sb(p, materials.EndStone)
        ssb(Vec(5,8,28), materials.SandstoneSlab)
        ssb(Vec(5,8,30), materials.SandstoneSlab)
        sb(o+Vec(6,7,29), materials.StoneBrick)
        sb(o+Vec(7,7,29), materials.StoneBrickSlab)
        sb(o+Vec(8,7,29), materials.StoneBrickSlab)
        sb(o+Vec(9,7,29), materials.StoneBrickStairs, 0)

        # Chest. Maxtier plus a level zero.
        sb(o+Vec(7,8,29), materials.Chest, 2)
        self.parent.addchest(o+Vec(7,8,29), loottable._maxtier)
        sb(o+Vec(8,8,29), materials.Chest, 2)
        self.parent.addchest(o+Vec(8,8,29), 0)

        # Statues
        # Legs/body
        for p in iterate_cube(Vec(1,8,29), Vec(1,4,29)):
            ssb(p, materials.StoneBrick)
            ssb(p+Vec(1,0,1), materials.StoneBrick)
        # Sword
        ssb(Vec(2,8,29), materials.GlassPane)
        ssb(Vec(2,7,29), materials.GlassPane)
        ssb(Vec(2,6,29), materials.GlassPane)
        ssb(Vec(2,5,29), materials.Fence)
        # Arms
        ssb(Vec(1,5,28), materials.StoneBrick)
        ssb(Vec(1,4,28), materials.StoneBrickSlab)
        ssb(Vec(3,5,30), materials.StoneBrick)
        ssb(Vec(3,4,30), materials.StoneBrickSlab)
        # Head
        ssb(Vec(2,3,29), materials.StoneBrick)
        # Feet
        sb(o+Vec(1,8,28), materials.StoneBrickStairs, 2)
        sb(o+Vec(3,8,30), materials.StoneBrickStairs, 1)
        sb(o+Vec(14,8,28), materials.StoneBrickStairs, 2)
        sb(o+Vec(12,8,30), materials.StoneBrickStairs, 0)
        # Hands
        sb(o+Vec(2,5,28), materials.StoneBrickStairs, 1)
        sb(o+Vec(3,5,29), materials.StoneBrickStairs, 2)
        sb(o+Vec(13,5,28), materials.StoneBrickStairs, 0)
        sb(o+Vec(12,5,29), materials.StoneBrickStairs, 2)
        # Eyes
        ssb(Vec(2,3,28), materials.StoneButton, 4)
        sb(o+Vec(3,3,29), materials.StoneButton, 1)
        sb(o+Vec(12,3,29), materials.StoneButton, 2)
        # Torches
        ssb(Vec(1,5,30), materials.Torch)

        # Webs
        for p in iterate_cube(o.trans(5,1,5), o.trans(10,1,30)):
            if random.random() < 0.07:
                for q in iterate_cube(p, p.down(random.randint(0,2))):
                    sb(q, materials.Cobweb)

        # Portal
        if (cfg.mvportal != ''):
            # Obsidian portal frame.
            for p in iterate_cube(Vec(6,7,1), Vec(9,11,1)):
                sb(o+p, materials.Obsidian)
            # Portal stuff.
            for p in iterate_cube(Vec(7,8,1), Vec(8,10,1)):
                sb(o+p, materials.NetherPortal)
            # Sign.
            sb(o+Vec(6,9,2), materials.WallSign, 3)
            self.parent.addsign(o+Vec(6,9,2),
                                       '[multiverse]',
                                       cfg.mvportal,
                                       '','')

        # Vines
        for p in iterate_cube(o+Vec(1,1,1), o+Vec(14,9,30)):
            if random.randint(1,100) <= 20:
                self.parent.vines(p, grow=True)

        # Cobwebs
        webs = {}
        for p in iterate_cube(o.down(1), o.trans(15,4,31)):
            count = 0
            perc = 90 - (p.y - self.loc.down(1).y) * (70/3)
            if (p not in self.parent.blocks or
                self.parent.blocks[p].material != materials.Air):
                continue
            for q in (Vec(1,0,0), Vec(-1,0,0),
                      Vec(0,1,0), Vec(0,-1,0),
                      Vec(0,0,1), Vec(0,0,-1)):
                if (p+q in self.parent.blocks and
                    self.parent.blocks[p+q].material != materials.Air and
                    random.randint(1,100) <= perc):
                    count += 1
            if count >= 3:
                webs[p] = True
        for p, q in webs.items():
            self.parent.setblock(p, materials.Cobweb)


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
        room = new('cblank', self.parent, pos)
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
        room = new('cblank', self.parent, pos)
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
        room = new('cblank', self.parent, pos)
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
                                             materials.meta_mossycobble)
                    if (self.parent.getblock(x.trans(-1,0,0)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(-1,0,0),
                                             materials.meta_mossycobble)
                    if (self.parent.getblock(x.trans(0,0,1)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(0,0,1),
                                             materials.meta_mossycobble)
                    if (self.parent.getblock(x.trans(0,0,-1)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(0,0,-1),
                                             materials.meta_mossycobble)
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
                                             materials.meta_mossycobble)
                    if (self.parent.getblock(x.trans(-1,0,0)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(-1,0,0),
                                             materials.meta_mossycobble)
                    if (self.parent.getblock(x.trans(0,0,1)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(0,0,1),
                                             materials.meta_mossycobble)
                    if (self.parent.getblock(x.trans(0,0,-1)) is
                        materials.Lava):
                        self.parent.setblock(x.trans(0,0,-1),
                                             materials.meta_mossycobble)
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
                (materials.meta_mossycobble,150),
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
              stairwell=False,
              room_list = None,
              default = 'basic'):
    '''Returns a pointer to a room instance given the current room set. Rooms
    will be chosen from a weighted list based on cfg.master_rooms, with a
    fall back to Basic. Restrictions on size, entrance, treasure, and stairwell
    can be specified.'''
    rooms = dungeon.rooms
    if (room_list == None):
        room_list = weighted_shuffle(cfg.master_rooms)
    else:
        room_list = weighted_shuffle(room_list)
    name = ''
    fpos = pos
    # print 'finding room @:', fpos
    # Cycle through the weighted shuffled list of room names.
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
        # print 'trying:', newroom, '(', 'E:', entrance_test,\
        #                                'S:', stairwell_test,\
        #                                'T:', treasure_test,\
        #                                ')'
        # Generate a list of horizontal offsets to test, and test them in a
        # random order.
        of = []
        for x in xrange(size.x+1):
            for z in xrange(size.z+1):
                of.append(Vec(-x,0,-z))
        random.shuffle(of)
        for o in of:
            ppos = pos + o
            # print ' ppos:',ppos
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
        name = default
    # print 'picked:', name, '@', fpos
    # Return the room instance and the new offset location. 
    return new(name, dungeon, fpos), fpos
