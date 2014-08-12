# Landmarks for Treasure Hunts
# These have location in voxels relative to the parent.position, and live in a single chunk
# y values reversed.  THis is so they can utilise the Dungeon.Block functions

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

class Clearing(object):
    _name = 'clearing'

    # pos is the corner of the chunk containing the location, ground level,
    # in y-reversed voxels relative to parent.position
    def __init__ (self, parent, pos):
        self.parent = parent
        self.pos = pos
        self.chestdesc = 'nowhere'
        self.offset = pos - parent.position
        self.offset.y = -self.offset.y

    def placed(self):
        return [self.pos]

    # return the chest location, so items can be added to it
    def chestplaced(self):
        return [self.chest]

    # update the blocks in the parent object
    # All renders are done relative to the location chunk origin,
    # in y-reversed voxel coordinates!
    def render (self):
        self.addclearing(self.pos+Vec(8,0,8),12)

    # return a string describing this location for use in clues
    def describe (self):
        return "a clearing"

    # Add a chest to this location, with specified loot
    # this should only be called after render()
    def addchest (self, tier=0, name=''):
        # Add a chest to the map: this is called after rendering
        # only one possible location (at varying depth) in this feature
        # position is y-reversed voxels relative to pos
        self.chest = Vec( 8, random.randint(1,3) , 8 ) + self.offset
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

    # center is in world voxels 
    def addclearing (self, center, diam):
        p0 = Vec(center.x - diam/2 - self.parent.position.x,
                 self.parent.position.y - center.y,
                 center.z - diam/2 - self.parent.position.z ) 
        p1 = p0.trans(diam+1, 0, diam+1)
        #mat = self.parent.getblock(center)
        try:
            chunk = self.parent.world.getChunk(center.x>>4, center.z>>4)
            mat = materials.materialById(chunk.Blocks[center.x & 15, center.z & 15, center.y])
        except:
            print 'Cannot identify central material'
            mat = materials.Dirt
        if mat is None or mat is False: # or mat not in materials.heightmap_solids:
            print 'Center material is %s' % mat
            mat = materials.Stone
        for p in iterate_disc(p0,p1):
            self.parent.setblock(p,mat,lock=True)
            self.parent.setblock(p.up(1),materials.Air)
            self.parent.setblock(p.up(2),materials.Air)
            self.parent.setblock(p.up(3),materials.Air)
            self.parent.setblock(p.up(4),materials.Air)
            self.parent.setblock(p.down(1),mat,soft=True)
            self.parent.setblock(p.down(2),mat,soft=True)
            self.parent.setblock(p.down(3),mat,soft=True)    

    def addcluechest (self, tier=0, name='', items=[]):
        # Add a chest to the map: this is called after rendering
        # only one possible location (at varying depth) in this feature
        # position is y-reversed voxels relative to pos
        self.cluechest = Vec( 8, -1 , 8 ) + self.offset
        self.parent.addchest( self.cluechest, tier, items , name )

    def addcluechestitem_tag ( self, item_tag ):
        if self.cluechest is None:
            self.addcluechest
        self.parent.addchestitem_tag( self.cluechest, item_tag )


        
# An empty, flat circular area, with a circle of skulls on sticks
# chest can be under the centre of the circle
class CircleOfSkulls(Clearing):
    _name = 'circleofskulls'

    # Render relative to TreasureHunt position in y-reversed coords
    def render (self):
        center = self.pos + Vec(8,0,8)
        size = random.randint(6,10)

        # Now need to flatten the circle in case it is on a slope
        # find ground type at centre, and change all heights within circle
        # to be the same, and the same ground type
        # center is ground level.
        self.addclearing(center,size)
                
        # Create the circle of skulls
        p0 = Vec(center.x - size/2 + 1 - self.parent.position.x,
                 self.parent.position.y - center.y,
                 center.z - size/2 + 1 - self.parent.position.z) 
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
    
class SmallCottage(Clearing):
    _name = 'smallcottage'
    _ruined = False
    _abandoned = False
    # randomise NS or EW
    
    def render (self):
        center = self.pos + Vec(8,0,8)
        size = 12
        self.addclearing(center,size)
		
        # create cottage
        # XXXXX

        # add bed and table
        # XXXXX
		
        if not self._ruined:
            # if not ruined, add roof, door and window
            # XXXXX
            if self._abandoned:
                # if abandoned, add cobwebs (parent function) voxels relative
                self.parent.cobwebs(self.offset+Vec(-2,0,2), self.offset+Vec(2,-4,2))
            else:
                # if not abandoned, add torches inside (parent fn?)
                self.parent.setblock(self.offset + Vec(2,-3,0), materials.Torch, 2)
                self.parent.setblock(self.offset + Vec(-2,-3,0), materials.Torch, 1)
    
    def describe (self):
        return "a small cottage"

    def addchest ( self, tier=0, name='' ):
        _chestpos = (
            ('under the fireplace"',Vec(-2,1,0)),
            ('under the bed',Vec(2,1,1)),
            ('under the doorstep',Vec(1,1,-2)),
            ('in the rafters',Vec(2,-4,0))
        )
        c = random.choice(_chestpos)
        self.chest = self.offset + c[1]
        self.chestdesc = c[0]
        self.parent.addchest( self.chest, tier, [] , name )

    def addcluechest ( self, tier=0, name='', items=[] ):
        self.cluechest = self.offset + Vec(10,-1,9)
        self.parent.addchest( self.cluechest, tier, items , name )

		
class AbandonedCottage(SmallCottage):
    _name = 'abandonedcottage'
    _abandoned = True

class RuinedCottage(SmallCottage):
    _name = 'ruinedcottage'
    _abandoned = True
    _ruined = True

class SignPost(Clearing):
    _name = 'signpost'
    
    def render (self):
        # add a signpost at groundlevel
        self.parent.addsign(self.offset + Vec(8,-1,8), "", self.parent.owner, "was here", "")
		
    def describe (self):
        return "a signpost"

    def addchest ( self, tier=0, name='' ):
        # Add a chest to the map: this is called after rendering
        # only one possible location (at varying depth) in this feature
        # position is y-reversed voxels relative to pos
        self.chest = self.offset + Vec( 8, random.randint(1,3) , 8 )
        self.chestdesc = "below"
        self.parent.addchest( self.chest, tier, [] , name )
    
    def addcluechest ( self, tier=0, name='', items=[] ):
        self.cluechest = self.offset + Vec(9,-1,9)
        self.parent.addchest( self.cluechest, tier, items , name )

                
# Catalog the features we know about. 
_landmarks = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses of landmarks.Blank
    if issubclass(obj, Clearing):
        _landmarks[obj._name] = obj

def new (name, parent, pos):
    '''Return a new instance of the feature of a given name. Supply the parent
    treasurehunt object.'''
    if name in _landmarks.keys():
        return _landmarks[name](parent,pos)
    return Blank(parent,pos)
    
def pickLandmark(thunt, pos,
             landmark_list=None,
             default='clearing'):
    '''Returns a pointer to a landmark instance given the current set. Landmarks
    will be chosen from a weighted list based on cfg.master_landmarks, with a
    fall back to Basic. Pass the location position as a parameter'''
    landmarks = thunt.landmarks
    if (landmark_list is None):
        # Identify biome of this chunk
        # print 'identify biome for %d, %d' % ( thunt.position.x + pos.x, thunt.position.z + pos.z )
        rset = thunt.oworld.get_regionset(None)
        cdata = rset.get_chunk(pos.x >> 4, pos.z >> 4)
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
