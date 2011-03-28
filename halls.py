import materials
import doors
import portcullises
import cfg
from utils import *
from random import *

class Blank(object):
    size = 0
    def __init__(self, parent, direction, offset):
        self.parent = parent
        self.direction = direction
        self.offset = offset
    def render (self):
        pass


class Single(Blank):
    size = 3
    def render (self):
        drawHall(self)


class Double(Blank):
    size = 4
    def render (self):
        drawHall(self)



class Triple(Blank):
    size = 5
    def render (self):
        drawHall(self)


class Four(Blank):
    size = 6
    def render (self):
        drawHall(self)


class Ten(Blank):
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
        start = start.east(hall.offset)
        stepw = Vec(1,0,0)
        stepl = Vec(0,0,1)
        dd1 = 5
        dd2 = 4
    elif(hall.direction == 1):
        start += Vec(hall.parent.parent.room_size-1,0,0)
        start = start.south(hall.offset)
        stepw = Vec(0,0,1)
        stepl = Vec(-1,0,0)
        dd1 = 2
        dd2 = 3
    elif(hall.direction == 2):
        start += Vec(0,0,hall.parent.parent.room_size-1)
        start = start.east(hall.offset)
        stepw = Vec(1,0,0)
        stepl = Vec(0,0,-1)
        dd1 = 5
        dd2 = 4
    else:
        start += Vec(0,0,0)
        start = start.south(hall.offset)
        stepw = Vec(0,0,1)
        stepl = Vec(1,0,0)
        dd1 = 2
        dd2 = 3
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
            if (trap == 1 and j < length-1):
                hall.parent.parent.setblock(
                    pen.down(hall.parent.parent.room_height-1),
                    materials.RedStoneWire)
                if (randint(1,100) <= 33):
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
    hall.parent.parent.torches[pen.down(1)] = True
    hall.parent.parent.torches[pen.down(1)+(stepw*(hall.size-1))] = True

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
            # All portcullises are fences.
            # They can be 1 (open) or 3 (closed) blocks high
            hall.parent.parent.portcullises[port] = portcullises.Portcullis()
            hall.parent.parent.portcullises[port].material = materials.Fence
            hall.parent.parent.portcullises[port].size = 1 + randint(0,1)*2
            # place the actual portcullis positions
            for x in xrange(hall.size-2):
                pen += stepw
                hall.parent.parent.portcullises[port].portcullises[pen] = True

def new (name, parent, direction, offset):
    if (name == 'single'):
            return Single(parent, direction, offset)
    if (name == 'double'):
            return Double(parent, direction, offset)
    if (name == 'triple'):
            return Triple(parent, direction, offset)
    if (name == 'four'):
            return Four(parent, direction, offset)
    if (name == 'ten'):
            return Ten(parent, direction, offset)
    return Blank(parent, direction, offset)

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
