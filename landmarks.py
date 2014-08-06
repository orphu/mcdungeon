# Landmarks for Treasure Hunts

import sys
import inspect

import materials
import loottable
import items
import cfg
import random
from utils import *
import perlin
from pymclevel import nbt

class Blank(object):
    _name = 'blank'

    def __init__ (self, parent, pos):
        self.parent = parent
        self.pos = pos

    def placed(self):
        return [self.pos]

    def chestplaced(self):
        return [self.chest]

    def render (self):
        pass
		
	def describe (self):
		return "a clearing"
	
	def addchest (self, tier=-1, name=''):
		# Add a chest to the map: this is called after rendering
		# only one possible location (at varying depth) in this feature
		self.chest = self.pos + Vec( 0, random.randint(-5,-2) , 0 )
		self.chestdesc = "in the middle"
		self.parent.addchest( self.chest, tier, [] , name )
		
	def chestlocdesc (self):
		return [self.chestdesc]
		

class CircleOfSkulls(Blank):
    _name = 'circleofskulls'

    def render (self):
        center = self.pos
        size = random.randint(6,12)

		# Now need to flatten the circle in case it is on a slope
		# find ground type at centre, and change all heights within circle
		# to be the same, and the same ground type
        p0 = Vec(center.x - size/2 ,
                 center.y,
                 center.z - size/2 ) 
        p1 = p0.trans(size+1, 0, size+1)
		mat = self.parent.getblock(self.pos)
		for p in iterate_disc(p0,p1):
			self.parent.setblock(p,mat,0,False,True)
			self.parent.delblock(p.up(1))
			self.parent.delblock(p.up(2))
			self.parent.delblock(p.up(3))
			self.parent.delblock(p.up(4))
			self.parent.setblock(p.down(1),mat,0,False,True,True)
			self.parent.setblock(p.down(2),mat,0,False,True,True)
			self.parent.setblock(p.down(3),mat,0,False,True,True)	
				
		# Create the circle of skulls
        p0 = Vec(center.x - size/2 + 1,
                 center.y,
                 center.z - size/2 + 1) 
        p1 = p0.trans(size-1, 0, size-1)
        skulls = (
            (0, 50), # Plain Skull
            (1, 1),  # Wither Skull
        )
        counter = 0
        for p in iterate_ellipse(p0, p1):
            if( (p.x + p.z) % 2 == 0 ):
                #self.parent.setblock(p, materials._floor)
                self.parent.setblock(p.up(1), materials.Fence)
                # Abort if there is no skull here
                if (random.randint(0,100) < 33):
                    continue
                SkullType = weighted_choice(skulls)
                self.parent.setblock(p.up(2), materials.MobHead, 1)
                root_tag = nbt.TAG_Compound()
                root_tag['id'] = nbt.TAG_String('Skull')
                root_tag['x'] = nbt.TAG_Int(p.x)
                root_tag['y'] = nbt.TAG_Int(p.y-2)
                root_tag['z'] = nbt.TAG_Int(p.z)
                root_tag['SkullType'] = nbt.TAG_Byte(SkullType)
                root_tag['Rot'] = nbt.TAG_Byte(random.randint(0,15))
                self.parent.tile_ents[p.up(2)] = root_tag
            elif( random.randint(0,100) < 33 ):
                self.parent.setblock(p, materials._floor)
                self.parent.setblock(p.up(1), materials.Torch)
				
	def describe (self):
		return "a circle of skulls"
	

	
	
class SmallCottage(Blank):
	_name = 'smallcottage'
	
	def render (self):
	
	def describe (self):
		return "a small cottage"
	
				
# Catalog the features we know about. 
_landmarks = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses of landmarks.Blank
    if issubclass(obj, Blank):
        _landmarks[obj._name] = obj

def new (name, parent, pos):
    '''Return a new instance of the feature of a given name. Supply the parent
    treasurehunt object.'''
    if name in _landmarks.keys():
        return _landmarks[name](parent,pos)
    return Blank(parent,pos)
	
