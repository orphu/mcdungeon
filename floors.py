import materials
from mymath import * 

class Blank(object):
	_name = 'Blank'
	def __init__ (self, parent):
		self.parent = parent
	def render (self):
		pass
		
class Cobble(Blank):
	_name = 'Cobble'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
			for x in iterate_points_inside_flat_poly(*self.parent.canvas):
				self.parent.parent.setblock(x+self.parent.loc, materials.Cobblestone)

class DoubleSlab(Blank):
	_name = 'DoubleSlab'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
			for x in iterate_points_inside_flat_poly(*self.parent.canvas):
				self.parent.parent.setblock(x+self.parent.loc, materials.DoubleSlab)

class WoodTile(Blank):
	_name = 'WoodTile'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
			for x in iterate_points_inside_flat_poly(*self.parent.canvas):
				if ((x.x+x.z)&1 == 1):
					self.parent.parent.setblock(x+self.parent.loc, materials.Wood)
				else:
					self.parent.parent.setblock(x+self.parent.loc, materials.WoodPlanks)
					

def new (name, parent):
        if (name == 'Cobble'):
                return Cobble(parent)
        if (name == 'DoubleSlab'):
                return DoubleSlab(parent)
        if (name == 'WoodTile'):
                return WoodTile(parent)
        return Blank(parent)
