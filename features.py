import materials
import rooms
from mymath import * 

class Blank(object):
	_name = 'Blank'
	def __init__ (self, parent):
		self.parent = parent
	def placed (self):
		pass
	def render (self):
		pass
		
class Entrance(Blank):
	_name = 'Entrance'
	def __init__ (self, parent):
                self.parent = parent
                self.height = parent.parent.room_height
		self.u = parent.parent.room_height
	def render (self):
		start = self.parent.loc.trans(6,self.parent.parent.room_height-3,6)
		wstart = start.trans(-1,0,-1)
		# Battlements
		for p in iterate_cube(wstart.trans(-1,-self.height-(self.u*2),-1), wstart.trans(6,-self.height-(self.u*2),6)):
			self.parent.parent.setblock(p, materials._wall)
		for p in iterate_cube(wstart.trans(-1,-self.height-(self.u*2)-1,-1), wstart.trans(6,-self.height-(self.u*2)-1,6)):
			if (((p.x+p.z)&1) == 1):
				self.parent.parent.setblock(p, materials._wall)
		# Clear a stairwell
		for p in iterate_cube(start, start.trans(3,-self.height-(self.u*2)-2,3)):
			self.parent.parent.setblock(p, materials.Air)
		# Walls
		for p in iterate_four_walls(wstart, wstart.trans(5,0,0), wstart.trans(5,0,5), wstart.trans(0,0,5), self.u*2+self.height):
			self.parent.parent.setblock(p, materials._wall)
		# Lower level openings
		# N side
		for p in iterate_cube(wstart.trans(1,0,0), wstart.trans(4,-3,0)):
			self.parent.parent.setblock(p, materials.Air)
			self.parent.parent.setblock(p.trans(0,-self.height,0), materials.Air)
		# S side
		for p in iterate_cube(wstart.trans(1,0,5), wstart.trans(4,-3,5)):
			self.parent.parent.setblock(p, materials.Air)
			self.parent.parent.setblock(p.trans(0,-self.height,0), materials.Air)
		# W side
		for p in iterate_cube(wstart.trans(0,0,1), wstart.trans(0,-3,4)):
			self.parent.parent.setblock(p, materials.Air)
			self.parent.parent.setblock(p.trans(0,-self.height,0), materials.Air)
		# E side
		for p in iterate_cube(wstart.trans(5,0,1), wstart.trans(5,-3,4)):
			self.parent.parent.setblock(p, materials.Air)
			self.parent.parent.setblock(p.trans(0,-self.height,0), materials.Air)
		# Draw the staircase
		for p in iterate_spiral(Vec(0,0,0), Vec(4,0,4), (self.u*2+self.height)*2):
			mat = materials.StoneSlab
			dat = 0
			if ((p.y%2) == 1):
				mat = materials.DoubleSlab
				dat = 0
			self.parent.parent.setblock(start.trans(p.x, floor(float(p.y)/2.0), p.z), mat)
			self.parent.parent.blocks[start.trans(p.x, floor(float(p.y)/2.0),p.z)].data = dat


class Stairwell(Blank):
	_name = 'Stairwell'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
			start = self.parent.loc.trans(5,self.parent.parent.room_height-3,5)
			# Clear a stairwell
			for x in iterate_cube(start.trans(0,0,1), start.trans(5,-6,4)):
				self.parent.parent.setblock(x, materials.Air)
			# Draw the steps
			for x in xrange(6):
				for p in iterate_cube(start.trans(x,-x,1),start.trans(x,-x,4)):
					self.parent.parent.setblock(p, materials.StoneStairs)
					self.parent.parent.setblock(p.trans(0,1,0), materials.Cobblestone)

def new (name, parent):
        if (name == 'Entrance'):
                return Entrance(parent)
        if (name == 'Stairwell'):
                return Stairwell(parent)
        return Blank(parent)
