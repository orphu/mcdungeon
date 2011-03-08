import materials
import doors
import portcullises
from mymath import * 
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
		# Torches
		#pen = start+stepl*(length-1)
		#pen += stepw
		#pen = pen.down(1);
		#self.parent.parent.setblock(pen, materials.Cobblestone)
		#pen += stepl
		#self.parent.parent.setblock(pen, materials.Torch)

class Double(Blank):
	size = 4	
	def render (self):
		drawHall(self)
					
class Triple(Blank):
	size = 5	
	def render (self):
		drawHall(self)

class Ten(Blank):
	size = 12	
	def render (self):
		drawHall(self)

def drawHall (hall):
	length = hall.parent.hallLength[hall.direction]
	start = hall.parent.loc
	if (hall.direction == 0):
		start += Vec(0,0,0)
		start = start.east(hall.offset)
		stepw = Vec(1,0,0)
		stepl = Vec(0,0,1)
	elif(hall.direction == 1):
		start += Vec(hall.parent.parent.room_size-1,0,0)
		start = start.south(hall.offset)
		stepw = Vec(0,0,1)
		stepl = Vec(-1,0,0)
	elif(hall.direction == 2):
		start += Vec(0,0,hall.parent.parent.room_size-1)
		start = start.east(hall.offset)
		stepw = Vec(1,0,0)
		stepl = Vec(0,0,-1)
	else:
		start += Vec(0,0,0)
		start = start.south(hall.offset)
		stepw = Vec(0,0,1)
		stepl = Vec(1,0,0)
	for j in xrange(length):
		pen = start+stepl*j
		# First wall
		for k in xrange(hall.parent.parent.room_height):
			hall.parent.parent.setblock(pen.down(k), materials._wall)
		# hallway (ceiling and floor)
		for x in xrange(hall.size-2):
			pen += stepw
			hall.parent.parent.setblock(pen, materials._ceiling)
			for k in xrange(1, hall.parent.parent.room_height-2):
				hall.parent.parent.setblock(pen.down(k), materials.Air)
			hall.parent.parent.setblock(pen.down(hall.parent.parent.room_height-2), materials._floor)
			hall.parent.parent.setblock(pen.down(hall.parent.parent.room_height-1), materials._floor)

		# Second wall
		pen += stepw
		for k in xrange(hall.parent.parent.room_height):
			hall.parent.parent.setblock(pen.down(k), materials._wall)
	# Possible torches
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
		# Looks for adjacent doors.
		box = Box(door,0,0,0)
		abort = False
		for x in iterate_points_surrounding_box(box):
			if (x in hall.parent.parent.doors):
				abort = True
		# We don't want doors one right after another for short halls
		if (abort == False):
			# Make the door. All doors are wood. 
			hall.parent.parent.doors[door] = doors.Door()
			hall.parent.parent.doors[door].material = materials.WoodenDoor
			hall.parent.parent.doors[door].direction = hall.direction
			# place the actual door positions
			for x in xrange(hall.size-2):
				pen += stepw
				hall.parent.parent.doors[door].doors.append(pen)
	# Possible portcullises
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
		# We don't want portcullises one right after another for short halls
		if (abort == False):
			# Make the portcullis. All portcullises are fences. 
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
        if (name == 'ten'):
                return Ten.size
        return Blank.size	
