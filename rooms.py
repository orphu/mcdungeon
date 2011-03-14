import materials
import halls
import floors
from utils import * 
import random


class Blank(object):
    _name = 'blank'

    def __init__ (self, parent, pos):
        self.parent = parent
        self.pos = pos
        self.loc = Vec(
            self.pos.x * self.parent.room_size,
            self.pos.y * self.parent.room_height,
            self.pos.z * self.parent.room_size)
        self.halls = [None, None, None, None]
        self.setData()
        self.features = []
        self.floors = []
        for x in xrange(4):
            if self.hallLength[x] == 0:
                self.halls[x] = halls.new('Blank', self, x, 0)

    def placed(self):
        pass

    def setData(self):
        # North, East, South, West
        self.hallLength = [0,0,0,0]
        self.hallSize = [[1,15], [1,15], [1,15], [1,15]]
        self.canvas = (
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0),
            Vec(0,self.parent.room_height-2,0))

    def canvasWidth(self):
        x1 = min([p.x for p in self.canvas])
        x2 = max([p.x for p in self.canvas])
        return x2 - x1 + 1

    def canvasLength(self):
        z1 = min([p.z for p in self.canvas])
        z2 = max([p.z for p in self.canvas])
        return z2 - z1 + 1

    def canvasHeight(self):
        return min([p.y for p in self.canvas])

    def canvasCenter(self):
        cx = self.canvasWidth()/2.0+min([p.x for p in self.canvas])-1
        cz = self.canvasLength()/2.0+min([p.z for p in self.canvas])-1
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

    def setData(self):
        # North, East, South, West
        self.hallLength = [3,3,3,3]
        self.hallSize = [[2,self.parent.room_size-2],
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

    def render (self):
        c1 = self.loc + Vec(2,self.parent.room_height-1,2)
        c2 = c1 + Vec(self.parent.room_size-5,0,0)
        c3 = c1 + Vec(self.parent.room_size-5,0,self.parent.room_size-5)
        c4 = c1 + Vec(0,0,self.parent.room_size-5)
        # Air space
        for x in iterate_cube(c1.up(1),c3.up(4)):
            self.parent.setblock(x, materials.Air)
        # Walls
        for x in iterate_four_walls(c1, c2, c3, c4, self.parent.room_height-1):
            self.parent.setblock(x, materials._wall)
        # Floor
        for x in iterate_cube(c1.trans(1,0,1),c3.trans(-1,-1,-1)):
            self.parent.setblock(x, materials._floor)
        # Ceiling
        for x in iterate_cube(c1.trans(1,-5,1),c3.trans(-1,-5,-1)):
            self.parent.setblock(x, materials._ceiling)

class Pit(Blank):
    _name = 'pit'

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
        self.lava = False

    def placed(self):
        # This room needs bridges.
        self.floors.append(floors.new('bridges', self))
        # Extend downward. First, figure out where we are and how far down
        # we would like to go. 
        thisfloor = self.pos.y+1
        targetdepth = random.randint(1, self.parent.levels-thisfloor+1)
        depth = 1
        # Place lower rooms.
        pos = self.pos
        while (depth < targetdepth):
            pos = pos.down(1)
            if (pos in self.parent.rooms):
                break
            if (pos.down(1) in self.parent.rooms or
               depth+1 == targetdepth):
                room = new('pitbottom', self.parent, pos)
                self.parent.setroom(pos, room)
                depth += 1
                break
            room = new('pitmid', self.parent, pos)
            self.parent.setroom(pos, room)
            depth += 1
        print "Pit, depth",depth
        # If this is the only level, make it a lava pit.
        if (depth == 1):
            self.lava = True
            print "Lava!"

    def render (self):
        c1 = self.loc + Vec(2,self.parent.room_height-1,2)
        c2 = c1 + Vec(self.parent.room_size-5,0,0)
        c3 = c1 + Vec(self.parent.room_size-5,0,self.parent.room_size-5)
        c4 = c1 + Vec(0,0,self.parent.room_size-5)
        # Air space
        for x in iterate_cube(c1,c3.up(4)):
            self.parent.setblock(x, materials.Air)
        # Walls
        for x in iterate_four_walls(c1, c2, c3, c4, self.parent.room_height-1):
                self.parent.setblock(x, materials._wall)
        # Lava
        if (self.lava is True):
            for x in iterate_cube(c1.trans(1,0,1),c3.trans(-1,0,-1)):
                self.parent.setblock(x, materials.Lava)
        # Ceiling
        for x in iterate_cube(c1.trans(1,-5,1),c3.trans(-1,-5,-1)):
            self.parent.setblock(x, materials._ceiling)

class PitMid(Blank):
    _name = 'pitmid'

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

    def placed(self):
        # This room needs bridges
        self.floors.append(floors.new('bridges', self))

    def render (self):
        c1 = self.loc + Vec(2,self.parent.room_height-1,2)
        c2 = c1 + Vec(self.parent.room_size-5,0,0)
        c3 = c1 + Vec(self.parent.room_size-5,0,self.parent.room_size-5)
        c4 = c1 + Vec(0,0,self.parent.room_size-5)
        # Air space
        for x in iterate_cube(c1,c3.up(5)):
            self.parent.setblock(x, materials.Air)
        # Walls
        for x in iterate_four_walls(c1, c2, c3, c4, self.parent.room_height-1):
            self.parent.setblock(x, materials._wall)


class PitBottom(Blank):
    _name = 'pitbottom'

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
        self.floor = 'floor'

    def placed(self):
        self.floor = random.choice(('floor','lava','cactus'))
        if (self.floor == 'floor'):
            self.canvas = (
                Vec(4,self.parent.room_height-2,4),
                Vec(self.parent.room_size-5,self.parent.room_height-2,4),
                Vec(self.parent.room_size-5,
                    self.parent.room_height-2,
                    self.parent.room_size-5),
                Vec(4,self.parent.room_height-2,self.parent.room_size-5))
        if (self.floor is not 'cactus'):
            # This room needs bridges
            self.floors.append(floors.new('bridges', self))
        if (self.floor is 'cactus'):
            print 'Cactus!'
        if (self.floor is 'lava'):
            print 'Lava!'
    def render (self):
        c1 = self.loc + Vec(2,self.parent.room_height-1,2)
        c2 = c1 + Vec(self.parent.room_size-5,0,0)
        c3 = c1 + Vec(self.parent.room_size-5,0,self.parent.room_size-5)
        c4 = c1 + Vec(0,0,self.parent.room_size-5)
        # Air space
        for x in iterate_cube(c1,c3.up(5)):
            self.parent.setblock(x, materials.Air)
        # Walls
        for x in iterate_four_walls(c1, c2, c3, c4, self.parent.room_height-1):
            self.parent.setblock(x, materials._wall)
        # Lava
        if (self.floor == 'lava'):
            for x in iterate_cube(c1.trans(1,0,1),c3.trans(-1,0,-1)):
                self.parent.setblock(x, materials.Lava)
        # Cactus (spike trap)
        elif (self.floor == 'cactus'):
            for x in iterate_cube(c1.trans(1,0,1),c3.trans(-1,0,-1)):
                self.parent.setblock(x, materials.Sand)
            for x in iterate_cube(c1.trans(2,-1,2),c3.trans(-2,-1,-2)):
                if ((x.x+x.z)%2 == 0):
                    for p in iterate_cube(x, x.up(random.randint(0,2))):
                        self.parent.setblock(p, materials.Cactus)
        # Floor
        else:
            for x in iterate_cube(c1.trans(1,0,1),c3.trans(-1,-1,-1)):
                self.parent.setblock(x, materials._floor)

class Circular(Blank):
    _name = 'circular'

    def setData(self):
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

    def render (self):
        c1 = self.loc + Vec(0,self.parent.room_height-1,0)
        # Solid (walls)
        for x in iterate_cube(c1.trans(5,0,0),
                              c1.trans(10,-self.parent.room_height+1,0)):
            self.parent.setblock(x, materials._wall)
        for x in iterate_cube(c1.trans(3,0,1),
                              c1.trans(12,-self.parent.room_height+1,1)):
            self.parent.setblock(x, materials._wall)
        for x in iterate_cube(c1.trans(2,0,2),
                              c1.trans(13,-self.parent.room_height+1,2)):
            self.parent.setblock(x, materials._wall)
        for x in iterate_cube(c1.trans(1,0,3),
                              c1.trans(14,-self.parent.room_height+1,4)):
            self.parent.setblock(x, materials._wall)
        for x in iterate_cube(c1.trans(0,0,5),
                              c1.trans(15,-self.parent.room_height+1,10)):
            self.parent.setblock(x, materials._wall)
        for x in iterate_cube(c1.trans(5,0,15),
                              c1.trans(10,-self.parent.room_height+1,15)):
            self.parent.setblock(x, materials._wall)
        for x in iterate_cube(c1.trans(3,0,14),
                              c1.trans(12,-self.parent.room_height+1,14)):
            self.parent.setblock(x, materials._wall)
        for x in iterate_cube(c1.trans(2,0,13),
                              c1.trans(13,-self.parent.room_height+1,13)):
            self.parent.setblock(x, materials._wall)
        for x in iterate_cube(c1.trans(1,0,12),
                              c1.trans(14,-self.parent.room_height+1,11)):
            self.parent.setblock(x, materials._wall)
        # Air space
        for x in iterate_cube(c1.trans(5,-2,1),
                              c1.trans(10,-self.parent.room_height+2,1)):
            self.parent.setblock(x, materials.Air)
        for x in iterate_cube(c1.trans(3,-2,2),
                              c1.trans(12,-self.parent.room_height+2,2)):
            self.parent.setblock(x, materials.Air)
        for x in iterate_cube(c1.trans(2,-2,3),
                              c1.trans(13,-self.parent.room_height+2,4)):
            self.parent.setblock(x, materials.Air)
        for x in iterate_cube(c1.trans(1,-2,5),
                              c1.trans(14,-self.parent.room_height+2,10)):
            self.parent.setblock(x, materials.Air)
        for x in iterate_cube(c1.trans(5,-2,14),
                              c1.trans(10,-self.parent.room_height+2,14)):
            self.parent.setblock(x, materials.Air)
        for x in iterate_cube(c1.trans(3,-2,13),
                              c1.trans(12,-self.parent.room_height+2,13)):
            self.parent.setblock(x, materials.Air)
        for x in iterate_cube(c1.trans(2,-2,11),
                              c1.trans(13,-self.parent.room_height+2,12)):
            self.parent.setblock(x, materials.Air)
        # Ceiling
        clevel = -self.parent.room_height+1
        for x in iterate_cube(c1.trans(5,clevel,1),c1.trans(10,clevel,1)):
            self.parent.setblock(x, materials._ceiling)
        for x in iterate_cube(c1.trans(3,clevel,2),c1.trans(12,clevel,2)):
            self.parent.setblock(x, materials._ceiling)
        for x in iterate_cube(c1.trans(2,clevel,3),c1.trans(13,clevel,4)):
            self.parent.setblock(x, materials._ceiling)
        for x in iterate_cube(c1.trans(1,clevel,5),c1.trans(14,clevel,10)):
            self.parent.setblock(x, materials._ceiling)
        for x in iterate_cube(c1.trans(5,clevel,14),c1.trans(10,clevel,14)):
            self.parent.setblock(x, materials._ceiling)
        for x in iterate_cube(c1.trans(3,clevel,13),c1.trans(12,clevel,13)):
            self.parent.setblock(x, materials._ceiling)
        for x in iterate_cube(c1.trans(2,clevel,11),c1.trans(13,clevel,12)):
            self.parent.setblock(x, materials._ceiling)
        # Floor
        clevel = 0
        for x in iterate_cube(c1.trans(5,clevel,1),c1.trans(10,clevel-1,1)):
            self.parent.setblock(x, materials._floor)
        for x in iterate_cube(c1.trans(3,clevel,2),c1.trans(12,clevel-1,2)):
            self.parent.setblock(x, materials._floor)
        for x in iterate_cube(c1.trans(2,clevel,3),c1.trans(13,clevel-1,4)):
            self.parent.setblock(x, materials._floor)
        for x in iterate_cube(c1.trans(1,clevel,5),c1.trans(14,clevel-1,10)):
            self.parent.setblock(x, materials._floor)
        for x in iterate_cube(c1.trans(5,clevel,14),c1.trans(10,clevel-1,14)):
            self.parent.setblock(x, materials._floor)
        for x in iterate_cube(c1.trans(3,clevel,13),c1.trans(12,clevel-1,13)):
            self.parent.setblock(x, materials._floor)
        for x in iterate_cube(c1.trans(2,clevel,11),c1.trans(13,clevel-1,12)):
            self.parent.setblock(x, materials._floor)


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
        # Lets take a look at our halls and try to connect them
        # x1 bounds (West side)
        if (self.halls[0].size):
            x1 = self.halls[0].offset
        if (self.halls[2].size):
            x1 = min(x1, self.halls[2].offset)
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
        if (self.halls[3].size):
            z1 = min(z1, self.halls[3].offset)
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
        # Extend the halls
        self.hallLength[0] = z1+1
        self.hallLength[1] = self.parent.room_size - x2
        self.hallLength[2] = self.parent.room_size - z2
        self.hallLength[3] = x1+1
        # Canvas
        self.canvas = (
            Vec(x1,self.parent.room_height-2,z1),
            Vec(x2,self.parent.room_height-2,z1),
            Vec(x2,self.parent.room_height-2,z2),
            Vec(x1,self.parent.room_height-2,z2))
        # Figure out our corners
        c1 = self.loc+Vec(x1,self.parent.room_height-1,z1)
        c2 = self.loc+Vec(x2,self.parent.room_height-1,z1)
        c3 = self.loc+Vec(x2,self.parent.room_height-1,z2)
        c4 = self.loc+Vec(x1,self.parent.room_height-1,z2)
        # Air space
        for x in iterate_cube(c1.up(1),c3.up(4)):
            self.parent.setblock(x, materials.Air)
        # Walls
        for x in iterate_four_walls(c1, c2, c3, c4, self.parent.room_height-1):
            self.parent.setblock(x, materials._wall)
        # Floor
        for x in iterate_cube(c1.trans(1,0,1),c3.trans(-1,-1,-1)):
            self.parent.setblock(x, materials._floor)
        # Ceiling
        for x in iterate_cube(c1.trans(1,-5,1),c3.trans(-1,-5,-1)):
            self.parent.setblock(x, materials._ceiling)


def new (name, parent, pos):
    if (name == 'basic'):
            return Basic(parent, pos)
    if (name == 'corridor'):
            return Corridor(parent, pos)
    if (name == 'circular'):
            return Circular(parent, pos)
    if (name == 'pit'):
            return Pit(parent, pos)
    if (name == 'pitmid'):
            return PitMid(parent, pos)
    if (name == 'pitbottom'):
            return PitBottom(parent, pos)
    return Blank(parent, pos)
