import materials
from mymath import * 

class Blank(object):
	name = 'Blank'
	def __init__ (self, parent):
		self.parent = parent
	def render (self):
		pass
		
class Cobble(Blank):
	name = 'Cobble'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
			for x in iterate_points_inside_flat_poly(*self.parent.canvas):
				self.parent.parent.setblock(x+self.parent.loc, materials.Cobblestone)

def new (name, parent):
        if (name == 'Cobble'):
                return Cobble(parent)
        return Blank(parent)
