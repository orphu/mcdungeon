# Landmarks for Treasure Hunts
# These have a world location in voxels (not relative to the start), and live in a single chunk

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

    # pos is the corner of the chunk containing the location, ground level
    def __init__ (self, parent, pos):
        self.parent = parent
        self.pos = pos
        self.chestdesc = 'nowhere'

    def placed(self):
        return [self.pos]

    # return the chest location, so items can be added to it
    def chestplaced(self):
        return [self.chest]

    # update the blocks in the parent object
    # All renders are done relative to the location chunk origin,
    # in y-reversed voxel coordinates!
    def render (self):
        pass

    # return a string describing this location for use in clues
	def describe (self):
		return "a place"

    # Add a chest to this location, with specified loot
    # this should only be called after render()
	def addchest (self, tier=0, name=''):
		# Add a chest to the map: this is called after rendering
		# only one possible location (at varying depth) in this feature
        # position is y-reversed voxels relative to pos
		self.chest = Vec( 8, random.randint(1,4) , 8 )
		self.chestdesc = "in the middle"
		self.parent.addchest( self.chest, tier, [] , name )

    # add an item to the chest, if one exists
    def addchestitem_tag ( self, item_tag ):
        if self.chest is None:
            self.addchest
        self.parent.addchestitem_tag( self.chest, item_tag )

    # return a string describing where the chest is hidden for use in clues
	def chestlocdesc (self):
        if self.chestdesc is None:
            return 'nowhere'
		return self.chestdesc
		
# An empty, flat circular area, with a circle of skulls on sticks
# chest can be under the centre of the circle
class CircleOfSkulls(Blank):
    _name = 'circleofskulls'

    # Render relative to chunk origin in y-reversed coords
    def render (self):
        center = Vec(8,0,8)
        size = random.randint(6,12)

		# Now need to flatten the circle in case it is on a slope
		# find ground type at centre, and change all heights within circle
		# to be the same, and the same ground type
		# center is ground level.
        p0 = Vec(center.x - size/2 ,
                 center.y,
                 center.z - size/2 ) 
        p1 = p0.trans(size+1, 0, size+1)
		mat = self.parent.getblock(center)
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
                self.parent.setblock(p.up(1), materials.Torch)
				
	def describe (self):
		return "a circle of skulls"

    # could define addchest and allow chest to be in alternative locations?		
    # def addchest( self, tier=0, name='' )
	
	
class SmallCottage(Blank):
	_name = 'smallcottage'
	_ruined = False
	_abandoned = False
	
	def render (self):
        # create cottage; add bed and table
        # if not abandoned, add torches
        # if abandoned, add cobwebs
        # if ruined, no roof and window
	
	def describe (self):
		return "a small cottage"

    def addchest ( self, tier=0, name='' )
		# Add a chest to the map: this is called after rendering
		# only one possible location (at varying depth) in this feature
        # position is y-reversed voxels relative to pos
		self.chest = Vec( 8, random.randint(1,4) , 8 )
		self.chestdesc = "in the middle"
		self.parent.addchest( self.chest, tier, [] , name )
        # chest could be under doormat, under bed, under fireplace, in rafters (if not ruined)

class AbandonedCottage(SmallCottage):
    _name = 'abandonedcottage'
    _abandoned = True

class RuinedCottage(SmallCottage):
    _name = 'ruinedcottage'
    _abandoned = True
    _ruined = True

class SignPost(Blank):
    _name = 'signpost'
	
	def render (self):
        # add a signpost at groundlevel
	
	def describe (self):
		return "a signpost"

    def addchest ( self, tier=0, name='' )
		# Add a chest to the map: this is called after rendering
		# only one possible location (at varying depth) in this feature
        # position is y-reversed voxels relative to pos
		self.chest = Vec( 8, random.randint(1,4) , 8 )
		self.chestdesc = "below"
		self.parent.addchest( self.chest, tier, [] , name )
	
				
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
	
def pickLandmark(thunt, pos,
             landmark_list=None,
             default='basic'):
    '''Returns a pointer to a landmark instance given the current set. Landmarks
    will be chosen from a weighted list based on cfg.master_landmarks, with a
    fall back to Basic. Pass the location position as a parameter'''
    landmarks = thunt.landmarks
    if (landmark_list is None):
        # Identify biome of this chunk
        cdata = rset.get_chunk(pos.x << 4, pos.z << 4)
        biome = numpy.argmax(numpy.bincount((cdata['Biomes'].flatten())))
        # do we have a special landmark list for this biome, or take default list?
        try:
            landmark_list = weighted_shuffle(cfg.master_landmarks[biome])
        except KeyError:
            landmark_list = weighted_shuffle(cfg.default_landmarks)
    else:
        landmark_list = weighted_shuffle(landmark_list)
    name = ''
    # Cycle through the weighted shuffled list of names.
	# Some landmarks are not valid in certain biomes
    # take the first valid one we find
    while (len(landmark_list) and name == ''):
        newlm = landmark_list.pop()
        # If the name doesn't really exist, ignore it.
        if newlm not in _landmarks:
            continue
        name = newlm

    # If we didn't find a candidate, fall back to basic.
    if name == '':
        name = default
    # print 'picked:', name
    # Return the landmark instance 
    return new(name, thunt, pos)
