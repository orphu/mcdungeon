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

class Rug(Blank):
	name = 'Rug'
	def render (self):
		pass

def new (name, parent, pos):
        if (name == 'Stairwell'):
                return Rug(parent, pos)
        if (name == 'Rug'):
                return Rug(parent, pos)
        return Blank(parent, pos)
