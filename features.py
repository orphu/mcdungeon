import materials
import rooms
from mymath import * 

class Blank(object):
	_name = 'blank'
	def __init__ (self, parent):
		self.parent = parent
	def placed (self):
		pass
	def render (self):
		pass
		
class Entrance(Blank):
	_name = 'entrance'
	def __init__ (self, parent):
                self.parent = parent
                self.height = parent.parent.room_height
		# height of the tower above entry
		self.u = parent.parent.room_height
		self.inwater = False
	def render (self):
		start = self.parent.loc.trans(6,self.parent.parent.room_height-3,6)
		wstart = start.trans(-1,0,-1)
		b1 = wstart.trans(-1,-self.height-(self.u*2),-1)
		b2 = b1.trans(7,0,0)
		b3 = b1.trans(7,0,7)
		b4 = b1.trans(0,0,7)
		# Battlements
		for p in iterate_cube(b1,b3):
			self.parent.parent.setblock(p, materials._wall)
		for p in iterate_cube(Vec(0,-1,0), Vec(2,-1,2)):
			if (((p.x+p.z)&1) == 0):
				self.parent.parent.setblock(b1+p, materials._wall)
				self.parent.parent.setblock(b2.trans(-p.x,p.y,p.z), materials._wall)
				self.parent.parent.setblock(b3.trans(-p.x,p.y,-p.z), materials._wall)
				self.parent.parent.setblock(b4.trans(p.x,p.y,-p.z), materials._wall)
		# Clear a stairwell
		for p in iterate_cube(wstart, wstart.trans(5,-self.height-(self.u*2)-2,5)):
			self.parent.parent.setblock(p, materials.Air)
		# Walls
		for p in iterate_four_walls(wstart, wstart.trans(5,0,0), wstart.trans(5,0,5), wstart.trans(0,0,5), self.u*2+self.height):
			self.parent.parent.setblock(p, materials._wall)
		# Lower level openings
		# N side
		for p in iterate_cube(wstart.trans(1,0,0), wstart.trans(4,-3,0)):
			self.parent.parent.setblock(p, materials.Air)
		# S side
		for p in iterate_cube(wstart.trans(1,0,5), wstart.trans(4,-3,5)):
			self.parent.parent.setblock(p, materials.Air)
		# W side
		for p in iterate_cube(wstart.trans(0,0,1), wstart.trans(0,-3,4)):
			self.parent.parent.setblock(p, materials.Air)
		# E side
		for p in iterate_cube(wstart.trans(5,0,1), wstart.trans(5,-3,4)):
			self.parent.parent.setblock(p, materials.Air)
                # Upper level openings
                # N side
                for p in iterate_cube(wstart.trans(2,0,0), wstart.trans(3,-3,0)):
                        self.parent.parent.setblock(p.trans(0,-self.height,0), materials.Air)
                # S side
                for p in iterate_cube(wstart.trans(2,0,5), wstart.trans(3,-3,5)):
                        self.parent.parent.setblock(p.trans(0,-self.height,0), materials.Air)
                # W side
                for p in iterate_cube(wstart.trans(0,0,2), wstart.trans(0,-3,3)):
                        self.parent.parent.setblock(p.trans(0,-self.height,0), materials.Air)
                # E side
                for p in iterate_cube(wstart.trans(5,0,2), wstart.trans(5,-3,3)):
                        self.parent.parent.setblock(p.trans(0,-self.height,0), materials.Air)
		# Draw the staircase
		for p in iterate_spiral(Vec(0,0,0), Vec(4,0,4), (self.u*2+self.height)*2+1):
			mat = materials.StoneSlab
			dat = 0
			if ((p.y%2) == 1):
				mat = materials.DoubleSlab
				dat = 0
			self.parent.parent.setblock(start.trans(p.x, floor(float(p.y)/2.0), p.z), mat)
			self.parent.parent.blocks[start.trans(p.x, floor(float(p.y)/2.0),p.z)].data = dat


class Stairwell(Blank):
	_name = 'stairwell'
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
class Columns(Blank):
        _name = 'columns'
	mats = (
		(materials.Stone,0),  # Stone
		(materials.Cobblestone,0),  # Cobblestone
		(materials.Wood,0), # Wood
		(materials.Wood,1), # Redwood
		(materials.Bedrock,0), # Bedrock
		(materials.Sandstone,0), # Sandstone
		(materials.DoubleSlab,0), # DoubleSlab
		(materials.Obsidian,0), # Obsidian
		(materials.Glowstone,0) # Glowstone
	)
        def render (self):
		if (self.parent.canvasWidth() < 6 or self.parent.canvasLength() < 6):
			return
		c = self.parent.canvasCenter()
		y = self.parent.canvasHeight()
		start = random.randint(0,int(self.parent.canvasWidth()/2))
		stop = int(self.parent.canvasWidth()/2)+1
		step = random.randint(2,4)
		mat = random.choice(self.mats)
		for x in xrange(start, stop, step):
			for p in iterate_cube(Vec(c.x-x, 1, c.z-x), Vec(c.x-x, 4, c.z-x)):
				self.parent.parent.setblock(self.parent.loc+p, mat[0])
				self.parent.parent.blocks[self.parent.loc+p].data = mat[1]
			for p in iterate_cube(Vec(c.x+x+1, 1, c.z-x), Vec(c.x+x+1, 4, c.z-x)):
				self.parent.parent.setblock(self.parent.loc+p, mat[0])
				self.parent.parent.blocks[self.parent.loc+p].data = mat[1]
			for p in iterate_cube(Vec(c.x-x, 1, c.z+x+1), Vec(c.x-x, 4, c.z+x+1)):
				self.parent.parent.setblock(self.parent.loc+p, mat[0])
				self.parent.parent.blocks[self.parent.loc+p].data = mat[1]
			for p in iterate_cube(Vec(c.x+x+1, 1, c.z+x+1), Vec(c.x+x+1, 4, c.z+x+1)):
				self.parent.parent.setblock(self.parent.loc+p, mat[0])
				self.parent.parent.blocks[self.parent.loc+p].data = mat[1]

def new (name, parent):
        if (name == 'entrance'):
                return Entrance(parent)
        if (name == 'stairwell'):
                return Stairwell(parent)
        if (name == 'columns'):
                return Columns(parent)
        return Blank(parent)
