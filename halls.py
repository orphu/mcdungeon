import sys
import inspect

import materials
import doors
import portcullises
import cfg
from utils import *
from random import *

class Blank(object):
    _name = 'blank'
    size = 0
    def __init__(self, parent, direction, offset):
        self.parent = parent
        self.direction = direction
        self.offset = offset
    def render (self):
        pass


class Single(Blank):
    _name = 'single'
    size = 3
    def render (self):
        drawHall(self)


class Double(Blank):
    _name = 'double'
    size = 4
    def render (self):
        drawHall(self)



class Triple(Blank):
    _name = 'triple'
    size = 5
    def render (self):
        drawHall(self)


class Four(Blank):
    _name = 'four'
    size = 6
    def render (self):
        drawHall(self)


class Ten(Blank):
    _name = 'ten'
    size = 12
    def render (self):
        drawHall(self)


def drawHall (hall):
    length = hall.parent.hallLength[hall.direction]
    start = hall.parent.loc
    trap = 0
    if (randint(1,100) <= cfg.arrow_traps):
        trap = 1
    if (hall.direction == 0):
        start += Vec(0,0,0)
        start = start.e(hall.offset)
        stepw = Vec(1,0,0)
        stepl = Vec(0,0,1)
        dd1 = 5
        dd2 = 4
        torch_dat = 3
    elif(hall.direction == 1):
        start += Vec(hall.parent.parent.room_size-1,0,0)
        start = start.s(hall.offset)
        stepw = Vec(0,0,1)
        stepl = Vec(-1,0,0)
        dd1 = 3
        dd2 = 2
        torch_dat = 2
    elif(hall.direction == 2):
        start += Vec(0,0,hall.parent.parent.room_size-1)
        start = start.e(hall.offset)
        stepw = Vec(1,0,0)
        stepl = Vec(0,0,-1)
        dd1 = 5
        dd2 = 4
        torch_dat = 4
    else:
        start += Vec(0,0,0)
        start = start.s(hall.offset)
        stepw = Vec(0,0,1)
        stepl = Vec(1,0,0)
        dd1 = 3
        dd2 = 2
        torch_dat = 1
    for j in xrange(length):
        pen = start+stepl*j
        # First wall
        for k in xrange(hall.parent.parent.room_height-1):
            hall.parent.parent.setblock(pen.down(k), materials._wall)
        if (trap == 1 and (j%2) == 0 and j > 0 and j < length-1):
            for k in iterate_cube(pen.down(1),
                                  pen.down(hall.parent.parent.room_height-1)-
                                  (stepw*2)):
                hall.parent.parent.setblock(k, materials._wall)
        elif (trap == 1 and (j%2) == 1 and j > 0 and j < length-1):
            for k in iterate_cube(pen.down(1),
                                  pen.down(hall.parent.parent.room_height-1)-
                                  (stepw*2)):
                hall.parent.parent.setblock(k, materials._wall)
            tpen = pen.down(2)
            hall.parent.parent.setblock(tpen, materials.Dispenser, dd1)
            hall.parent.parent.addtrap(tpen)
            hall.parent.parent.setblock(tpen-stepw,
                                        materials.RedStoneTorchOff, 5)
            tpen = tpen.down(2)
            hall.parent.parent.setblock(tpen, materials.Air)
            hall.parent.parent.setblock(tpen-stepw,
                                        materials.RedStoneTorchOn, 5)
            tpen = tpen.down(1)
            hall.parent.parent.setblock(tpen, materials.RedStoneWire)
        # hallway (ceiling and floor)
        for x in xrange(hall.size-2):
            pen += stepw
            hall.parent.parent.setblock(pen, materials._ceiling)
            for k in xrange(1, hall.parent.parent.room_height-2):
                hall.parent.parent.setblock(pen.down(k), materials.Air)
            hall.parent.parent.setblock(
                pen.down(hall.parent.parent.room_height-2),
                materials._floor)
            # Arrow trap place redstone under the floor, and a button.
            # For TNT traps, redstone might be TNT instead
            if (trap == 1 and j < length-1):
                if (randint(1,100) <= cfg.arrow_trap_defects):
                    hall.parent.parent.setblock(
                        pen.down(hall.parent.parent.room_height-1),
                        materials.TNT)
                    hall.parent.parent.setblock(
                        pen.down(hall.parent.parent.room_height-3),
                        materials.StonePressurePlate)
                else:
                    hall.parent.parent.setblock(
                        pen.down(hall.parent.parent.room_height-1),
                        materials.RedStoneWire)
                    if (randint(1,100) <= 66):
                        hall.parent.parent.setblock(
                            pen.down(hall.parent.parent.room_height-3),
                            materials.StonePressurePlate)
        # Second wall
        pen += stepw
        for k in xrange(hall.parent.parent.room_height-1):
            hall.parent.parent.setblock(pen.down(k), materials._wall)
        if (trap == 1 and (j%2) == 1 and j > 0 and j < length-1):
            for k in iterate_cube(pen.down(1),
                                  pen.down(hall.parent.parent.room_height-1)+
                                  (stepw*2)):
                hall.parent.parent.setblock(k, materials._wall)
        elif (trap == 1 and (j%2) == 0 and j > 0 and j < length-1):
            for k in iterate_cube(pen.down(1),
                                  pen.down(hall.parent.parent.room_height-1)+
                                  (stepw*2)):
                hall.parent.parent.setblock(k, materials._wall)
            tpen = pen.down(2)
            hall.parent.parent.setblock(tpen, materials.Dispenser, dd2)
            hall.parent.parent.addtrap(tpen)
            hall.parent.parent.setblock(tpen+stepw,
                                        materials.RedStoneTorchOff, 5)
            tpen = tpen.down(2)
            hall.parent.parent.setblock(tpen, materials.Air)
            hall.parent.parent.setblock(tpen+stepw,
                                        materials.RedStoneTorchOn, 5)
            tpen = tpen.down(1)
            hall.parent.parent.setblock(tpen, materials.RedStoneWire)

    # Possible torches.
    pen = start+stepl*length
    hall.parent.parent.torches[pen.down(1)] = torch_dat
    hall.parent.parent.torches[pen.down(1)+(stepw*(hall.size-1))] = torch_dat

    # Possible doors
    # Only halls of width 1 and 2 can have doors (single and double doors)
    if (3 <= hall.size <= 4):
        # find a starting position at the end of the hall
        pen = start+stepl*(length-1)
        pen = pen.down(1)
        door = pen
        # Look for adjacent doors. We don't want doors upon doors. 
        box = Box(door,0,0,0)
        abort = False
        for x in iterate_points_surrounding_box(box):
            if (x in hall.parent.parent.doors):
                abort = True
        # Create the door
        if (abort == False):
            # All doors are wood. Give this door a direction.
            hall.parent.parent.doors[door] = doors.Door()
            hall.parent.parent.doors[door].material = materials.WoodenDoor
            hall.parent.parent.doors[door].direction = hall.direction
            # place the actual door positions
            for x in xrange(hall.size-2):
                pen += stepw
                hall.parent.parent.doors[door].doors.append(pen)

    # Possible portcullises. Portcullises can appear for any width hall 
    # between 2 and 10.
    if (4 <= hall.size <= 12):
        # find a starting position at the end of the hall
        pen = start+stepl*(length-1)
        pen = pen.down(1)
        port = pen
        # Looks for adjacent portcullises.
        box = Box(port,0,0,0)
        abort = False
        for x in iterate_points_surrounding_box(box):
            if (x in hall.parent.parent.portcullises):
                abort = True
        # Create the portcullis.
        if (abort == False):
            # Portcullises can be makde from fence, nether fence, or iron bars.
            # They can be 1 (open) or 3 (closed) blocks high
            mat = choice([materials.Fence, materials.NetherBrickFence,
                         materials.IronBars])
            hall.parent.parent.portcullises[port] = portcullises.Portcullis()
            hall.parent.parent.portcullises[port].material = mat
            if (randint(1,100) <= cfg.portcullis_closed):
                hall.parent.parent.portcullises[port].size = 3
            else:
                hall.parent.parent.portcullises[port].size = 1
            # Make this a web instead
            if (randint(1,100) <= cfg.portcullis_web):
                hall.parent.parent.portcullises[port].material = \
                    materials.Cobweb
                hall.parent.parent.portcullises[port].size = 3
            # place the actual portcullis positions
            for x in xrange(hall.size-2):
                pen += stepw
                hall.parent.parent.portcullises[port].portcullises[pen] = True

def sizeByName (name):
    if (name == 'single'):
            return Single.size
    if (name == 'double'):
            return Double.size
    if (name == 'triple'):
            return Triple.size
    if (name == 'four'):
            return Four.size
    if (name == 'ten'):
            return Ten.size
    return Blank.size

# Catalog the halls we know about. 
_halls = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses if of halls.Blank
    if issubclass(obj, Blank):
        _halls[obj._name] = obj

def new (name, parent, direction, offset):
    '''Return a new instance of the hall of a given name. Supply the parent
    dungeon object.'''
    if name in _halls.keys():
        return _halls[name](parent, direction, offset)
    return Blank(parent, direction, offset)

def sizeByName(name):
    if name in _halls:
        return _halls[name].size
    return Blank.size
