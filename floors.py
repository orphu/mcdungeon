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
		if (area(self.parent.canvas[0], self.parent.canvas[1]) > 0):
			for x in iterate_plane(self.parent.canvas[0], self.parent.canvas[1].trans(-1,-1,-1)):
				self.parent.parent.setblock(x+self.parent.loc, materials.Cobblestone)

def new (name, parent):
        if (name == 'Cobble'):
                return Cobble(parent)
        return Blank(parent)
