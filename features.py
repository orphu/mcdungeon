import materials
from mymath import * 

class Blank(object):
	name = 'Blank'
	def __init__ (self, parent):
		self.parent = parent
	def render (self):
		pass
		
class Stairwell(Blank):
	name = 'Stairwell'
	def render (self):
		if (sum_points_inside_flat_poly(*self.parent.canvas) > 0):
			start = self.parent.loc.trans(5,self.parent.parent.room_height-3,5)
			# Clear a stairwell
			for x in iterate_cube(start, start.trans(5,-5,5)):
				self.parent.parent.setblock(x, materials.Air)
			# Draw the steps
			for x in xrange(6):
				for p in iterate_cube(start.trans(x,-x,0),start.trans(x,-x,5)):
					self.parent.parent.setblock(p, materials.Cobblestone)
					self.parent.parent.setblock(p.trans(-1,0,0), materials.StoneStairs)
			

def new (name, parent):
        if (name == 'Stairwell'):
                return Stairwell(parent)
        return Blank(parent)
