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
        if (name == 'Stairwell'):
                return Stairwell(parent)
        return Blank(parent)
