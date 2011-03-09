import materials
import random
from noise import * 
from mymath import * 

class Blank(object):
	_name = 'blank'
	def __init__ (self, parent):
		self.parent = parent
	def render (self):
		pass
		
class Cobble(Blank):
	_name = 'cobble'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
			for x in iterate_points_inside_flat_poly(*self.parent.canvas):
				self.parent.parent.setblock(x+self.parent.loc, materials.Cobblestone)

class DoubleSlab(Blank):
	_name = 'doubleSlab'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
			for x in iterate_points_inside_flat_poly(*self.parent.canvas):
				self.parent.parent.setblock(x+self.parent.loc, materials.DoubleSlab)

class WoodTile(Blank):
	_name = 'woodtile'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
			for x in iterate_points_inside_flat_poly(*self.parent.canvas):
				if ((x.x+x.z)&1 == 1):
					self.parent.parent.setblock(x+self.parent.loc, materials.Wood)
				else:
					self.parent.parent.setblock(x+self.parent.loc, materials.WoodPlanks)
					
class CheckerRug(Blank):
	_name = 'checkerrug'
	colors = (
		(7,8),   # dark grey / light grey
		(9,3),   # cyan / light blue
		#(14,10), # red / purple
		(11,9),  # dark blue / cyan
		(1,14),  # red / orange
		(7,15),  # dark grey / black
		#(3,4),   # light blue  / yellow
		(11,10), # dark blue  / purple
		(12,13), # brown  / dark green
		(15,13), # black  / dark green
		)
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
			color = random.choice(self.colors)
			for x in iterate_points_inside_flat_poly(*self.parent.canvas):
				self.parent.parent.setblock(x+self.parent.loc, materials.Wool)
				if ((x.x+x.z)&1 == 1):
					self.parent.parent.blocks[x+self.parent.loc].data = color[0]
				else:
					self.parent.parent.blocks[x+self.parent.loc].data = color[1]
class BrokenDoubleSlab(Blank):
	_name = 'brokendoubleslab'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) <= 0):
			return
		c = self.parent.canvasCenter()
		y = self.parent.canvasHeight()
		r = random.randint(1,1000)
		maxd = max(self.parent.canvasWidth(), self.parent.canvasLength())
		if (maxd < 1):
			maxd = 1
		for x in iterate_points_inside_flat_poly(*self.parent.canvas):
			p = x+self.parent.loc
			d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
			n = (pnoise3((p.x+r) / 2.3, y / 2.3, p.z / 2.3, 2) + 1.0) / 2.0
			if (n >= d):
				self.parent.parent.setblock(p, materials.DoubleSlab)

class Mud(Blank):
	_name = 'mud'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) <= 0):
			return
		c = self.parent.canvasCenter()
		y = self.parent.canvasHeight()
		r = random.randint(1,1000)
		maxd = max(self.parent.canvasWidth(), self.parent.canvasLength())
		if (maxd < 1):
			maxd = 1
		for x in iterate_points_inside_flat_poly(*self.parent.canvas):
			p = x+self.parent.loc
			d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
			n = (pnoise3((p.x+r) / 2.3, y / 2.3, p.z / 2.3, 2) + 1.0) / 2.0
			if (n >= d+.20):
				self.parent.parent.setblock(p, materials.SoulSand)
			elif (n >= d):
				self.parent.parent.setblock(p, materials.Dirt)

class Sand(Blank):
	_name = 'sand'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) <= 0):
			return
		c = self.parent.canvasCenter()
		y = self.parent.canvasHeight()
		r = random.randint(1,1000)
		maxd = max(self.parent.canvasWidth(), self.parent.canvasLength())
		if (maxd < 1):
			maxd = 1
		for x in iterate_points_inside_flat_poly(*self.parent.canvas):
			p = x+self.parent.loc
			d = ((Vec2f(x.x, x.z) - c).mag()) / maxd
			n = (pnoise3((p.x+r) / 2.3, y / 2.3, p.z / 2.3, 2) + 1.0) / 2.0
			if (n >= d+.20):
				self.parent.parent.setblock(p, materials.Sandstone)
			elif (n >= d+.10):
				self.parent.parent.setblock(p, materials.Sand)
			elif (n >= d):
				self.parent.parent.setblock(p, materials.Gravel)
	
def new (name, parent):
        if (name == 'cobble'):
                return Cobble(parent)
        if (name == 'doubleslab'):
                return DoubleSlab(parent)
        if (name == 'woodtile'):
                return WoodTile(parent)
        if (name == 'checkerrug'):
                return CheckerRug(parent)
        if (name == 'brokendoubleslab'):
                return BrokenDoubleSlab(parent)
        if (name == 'mud'):
                return Mud(parent)
        if (name == 'sand'):
                return Sand(parent)
        return Blank(parent)
