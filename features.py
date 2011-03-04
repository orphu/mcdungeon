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
		start = self.parent.loc.trans(4,self.parent.room_height-3,4)
		for x in iterate_cube(start, start.trans(6,-6,6)):
			self.parent.setblock(x, materials.Air)

def new (name, parent):
        if (name == 'Stairwell'):
                return Rug(parent)
        if (name == 'Rug'):
                return Rug(parent)
        return Blank(parent)
