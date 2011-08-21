import sys
import inspect

import materials
import halls
import floors
import features
import ruins
import cfg
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

class CellBlock(Basic2x2):
    _name = 'cellblock'
    _is_entrance = False
    _is_stairwell = False
    combo = 0

    def setData(self):
        Basic2x2.setData(self)
        self.features.append(features.new('blank', self))
        self.floors.append(floors.new('brokendoubleslab', self))
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
                                     materials._ceiling)
            # Extra chests for solving the combo
            if (random.randint(1,100) <= chest_rate):
                chest_rate /= 2
                cp = ss+doffset+Vec(-3,0,0)
                if p.x > 1:
                    cp = ss+doffset+Vec(3,0,0)
                self.parent.setblock(cp, materials.Chest)
                self.parent.addchest(cp)
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
                    ctext2 += 'X '
                else:
                    charge = 0
                    torch = materials.RedStoneWire
                    repeater = materials.RedStoneRepeaterOff
                    ctext2 += 'O '
                self.parent.setblock(p.up(1),
                                     materials.RedStoneWire, 0, lock=True)
                self.parent.setblock(p.east(1),
                                     torch, 1, lock=True)
                self.parent.setblock(p.east(2),
                                     repeater, 1, lock=True)
                self.parent.setblock(p.east(3),
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
                    ctext1 += 'X '
                else:
                    charge = 0
                    torch = materials.RedStoneWire
                    repeater = materials.RedStoneRepeaterOff
                    ctext1 += 'O '
                self.parent.setblock(p.up(1),
                                     materials.RedStoneWire, 15, lock=True)
                self.parent.setblock(p.west(1),
                                     torch, 2, lock=True)
                self.parent.setblock(p.west(2),
                                     repeater, 3, lock=True)
                self.parent.setblock(p.west(3),
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
            's3': ctext1+'  ',
            's4': ctext2
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
        # North / South Bus
        for p in iterate_cube(self.c1+Vec(6,1,6), self.c4+Vec(6,1,-6)):
            self.parent.setblock(p, materials.RedStoneWire, 15, lock=True)
            self.parent.setblock(p.east(15), materials.RedStoneWire, 15,
                                 lock=True)
        for p in iterate_cube(Vec(7,1,7), Vec(12,1,7)):
            q = self.c1+p
            self.parent.setblock(q, materials.RedStoneWire, 15, lock=True)
            self.parent.setblock(q.east(8), materials.RedStoneWire, 15,
                                 lock=True)
            q = self.c4+Vec(p.x, p.y, -p.z)
            self.parent.setblock(q, materials.RedStoneWire, 15, lock=True)
            self.parent.setblock(q.east(8), materials.RedStoneWire, 15,
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
                             materials.RedStoneRepeaterOn, 2, lock=True)
        self.parent.setblock(self.c1+Vec(6,1,17),
                             materials.RedStoneRepeaterOn, 0, lock=True)
        self.parent.setblock(self.c1+Vec(21,1,10),
                             materials.RedStoneRepeaterOn, 2, lock=True)
        self.parent.setblock(self.c1+Vec(21,1,17),
                             materials.RedStoneRepeaterOn, 0, lock=True)
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
                                     materials.RedStoneRepeaterOff, 6, lock=True)
                self.parent.setblock(p+Vec(-1,0,-1),
                                     materials.RedStoneWire, 0, lock=True)
        self.parent.setblock(self.c1+Vec(2,1,3),
                             materials.RedStoneRepeaterOff, 6, lock=True)
        self.parent.setblock(self.c1+Vec(1,1,2),
                             materials.RedStoneWire, 0, lock=True)
        self.parent.setblock(self.c1+Vec(2,1,5),
                             materials.RedStoneRepeaterOff, 6, lock=True)
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
            [materials.Cobblestone, materials.CobblestoneSlab],
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
            ssb(Vec(6,5+x,1+x), materials.Cobblestone)
            ssb(Vec(7,5+x,1+x), materials.Cobblestone)
            ssb(Vec(6,5+x,2+x), materials.Cobblestone)
            ssb(Vec(7,5+x,2+x), materials.Cobblestone)
            ssb(Vec(6,5+x,3+x), materials.StoneStairs, 2)
            ssb(Vec(7,5+x,3+x), materials.StoneStairs, 2)
        # Skip this is ther is no door to the West
        if self.parent.halls[pos.x][pos.y][pos.z][0] == 1:
            for p in iterate_cube(Vec(6,4,1), Vec(7,4,1)):
                ssb(p, materials.StoneStairs, 2)

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
            ssb(Vec(7,10-x,24+x), materials.StoneStairs, 3)
            ssb(Vec(7,10-x,25+x), materials.Cobblestone)
            ssb(Vec(7,10-x,26+x), materials.Cobblestone)
        # Platform
        for p in iterate_cube(Vec(6,8,27), Vec(7,10,27)):
            ssb(p, materials.Bedrock)
        for p in iterate_cube(Vec(5,8,28), Vec(7,10,29)):
            ssb(p, materials.Bedrock)
        # Lava bucket
        ssb(Vec(6,10,30), materials.Cobblestone)
        ssb(Vec(6,9,30), materials.Cobblestone)
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
               [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,1,1,0,0,1,1,0,0,0,0,0],
                [0,0,0,0,0,1,1,0,0,1,1,0,0,0,0,0],
                [0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0],
                [0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],

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
                self.parent.addspawner(p, 'Spider')
                count += 1

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
            self.parent.setblock(center.trans(-2,-1,1),
                                        materials.WallSign)
            self.parent.blocks[center.trans(-2,-1,1)].data = 2
            # Create the tile entities for the signs.
            self.parent.addsign(center.trans(1,-1,-1),
                                       '<== Exit',
                                       '[MultiVerse]',
                                       cfg.mvportal,
                                       '<== Exit')
            self.parent.addsign(center.trans(-2,-1,1),
                                       '<== Exit',
                                       '[MultiVerse]',
                                       cfg.mvportal,
                                       '<== Exit')
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
