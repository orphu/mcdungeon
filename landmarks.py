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
    def __init__ (self, parent, pos, biome=None):
        self.parent = parent
        self.pos = pos
        self.chestdesc = 'nowhere'
        self.offset = pos - parent.position
        self.offset.y = -self.offset.y
        self.biome = biome
        self.stone = materials.meta_stonedungeon
        self.stonesteps = materials.StoneStairs
        self.stoneslab = materials.StoneSlab
        # If we're in a desert biome, change to sandstone
        if biome is not None and ( biome == 2 or biome == 130 ):
            self.stone = materials.Sandstone
            self.stonesteps = materials.SandstoneStairs
            self.stoneslab = materials.SandstoneSlab
        # If we're in a mesa biome, change to red clay

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
    def addchest (self, tier=0, name='', locked=None):
        # Add a chest to the map: this is called after rendering
        # only one possible location (at varying depth) in this feature
        # position is y-reversed voxels relative to pos
        self.chest = Vec( 8, random.randint(1,3) , 8 ) + self.offset
        self.chestdesc = "in the middle"
        self.parent.setblock( self.chest, materials.Chest, lock=True)
        self.parent.addchest( self.chest, tier=tier, name=name, lock=locked )

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
            mat = materials.meta_stonedungeon
        if mat is materials.Air:
            mat = materials.Dirt
        for p in iterate_disc(p0,p1):
            self.parent.setblock(p,mat,lock=True)
            self.parent.setblock(p.up(1),materials.Air)
            self.parent.setblock(p.up(2),materials.Air)
            self.parent.setblock(p.up(3),materials.Air)
            self.parent.setblock(p.up(4),materials.Air)
            self.parent.setblock(p.down(1),mat,soft=True)
            self.parent.setblock(p.down(2),mat,soft=True)
            self.parent.setblock(p.down(3),mat,soft=True)
            i = 5
            while chunk.Blocks[p.x & 15, p.z & 15, center.y - i] == materials.Wood.val:
                # delete the tree
              	self.parent.setblock(p.up(i), materials.Air)
                i = i + 1

    def addcluechest (self, tier=0, name='', items=[], locked=None):
        # Add a chest to the map: this is called after rendering
        # only one possible location (at varying depth) in this feature
        # position is y-reversed voxels relative to pos
        self.cluechest = Vec( 8, -1 , 8 ) + self.offset
        self.parent.setblock( self.cluechest, materials.Chest, lock=True)
        self.parent.addchest( self.cluechest, tier=tier, loot=items , name=name, lock=locked )

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
            (0, 100), # Plain Skull
            (1, 5),  # Wither Skull
            (3, 1),  # Steve Head
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
            elif( random.randint(0,100) < 10 ):
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
        for p in iterate_four_walls(Vec(6,0,6), Vec(11,0,10),2):
            self.parent.setblock(self.offset + p, self.stone, soft=False)
        for p in iterate_plane(Vec(6,0,6), Vec(11,0,10)):
            self.parent.setblock(self.offset + p, self.stone, soft=False)
        self.parent.setblock(self.offset+Vec(6,-3,7),self.stone)
        self.parent.setblock(self.offset+Vec(6,-3,8),self.stone)
        self.parent.setblock(self.offset+Vec(6,-4,8),self.stone)
        self.parent.setblock(self.offset+Vec(6,-3,9),self.stone)
        self.parent.setblock(self.offset+Vec(6,-5,8),self.stone)
        self.parent.setblock(self.offset+Vec(11,-3,7),self.stone)
        self.parent.setblock(self.offset+Vec(11,-3,8),self.stone)
        self.parent.setblock(self.offset+Vec(11,-4,8),self.stone)
        self.parent.setblock(self.offset+Vec(11,-3,9),self.stone)
        # doorway
        self.parent.setblock(self.offset+Vec(9,-1,10),materials.Air)
        self.parent.setblock(self.offset+Vec(9,-2,10),materials.Air)
        # window
        self.parent.setblock(self.offset+Vec(7,-2,10),materials.Air)
        # fireplace
        self.parent.setblock(self.offset+Vec(6,-1,8),materials.Air)
        self.parent.setblock(self.offset+Vec(5,-1,8),self.stone)

        # add bed and table
        self.parent.setblock(self.offset+Vec(9 ,-1,7),materials.BedBlock,3)
        self.parent.setblock(self.offset+Vec(10,-1,7),materials.BedBlock,11)
        self.parent.setblock(self.offset+Vec(8,-1,8),materials.Fence)
        self.parent.setblock(self.offset+Vec(8,-2,8),materials.WoodenPressurePlate)
		
        if self._ruined is False:
            # if not ruined, add roof, door and window
            self.parent.setblock(self.offset+Vec(10,-1,9),materials.CraftingTable)
            self.parent.setblock(self.offset+Vec(7,-2,10),materials.GlassPane)
            self.parent.setblock(self.offset+Vec(9,-1,10),materials.WoodenDoor,3)
            self.parent.setblock(self.offset+Vec(9,-2,10),materials.WoodenDoor,11)
            for x in xrange(6):
                self.parent.setblock(self.offset+Vec(6+x,-3,10),materials.SpruceWoodStairs,3)
                self.parent.setblock(self.offset+Vec(6+x,-4,9),materials.SpruceWoodStairs,3)
                self.parent.setblock(self.offset+Vec(6+x,-3,6),materials.SpruceWoodStairs,2)
                self.parent.setblock(self.offset+Vec(6+x,-4,7),materials.SpruceWoodStairs,2)
                self.parent.setblock(self.offset+Vec(6+x,-5,8),materials.SpruceWoodSlab,soft=True)
            
            if self._abandoned is True:
                # if abandoned, add cobwebs (parent function) voxels relative
                self.parent.cobwebs(self.offset + Vec(8,0,8) + Vec(-2,0,2), self.offset + Vec(8,0,8) + Vec(3,-4,-2))
            else:
                # if not abandoned, add torches inside
                self.parent.setblock(self.offset + Vec(8,0,8) + Vec(2,-3,0), materials.Torch, 2)
                self.parent.setblock(self.offset + Vec(8,0,8) + Vec(-1,-3,0), materials.Torch, 1)
        # chimney
        self.parent.setblock(self.offset+Vec(6,-5,8),self.stone)

    
    def describe (self):
        return "a small cottage"

    def addchest ( self, tier=0, name='', locked=None ):
        _chestpos = (
            ('under the fireplace"',Vec(-2,1,0)),
            ('under the bed',Vec(2,1,1)),
            ('under the doorstep',Vec(1,1,-2)),
            ('in the rafters',Vec(2,-4,0))
        )
        c = random.choice(_chestpos)
        self.chest = self.offset + c[1]
        self.chestdesc = c[0]
        self.parent.setblock( self.chest, materials.Chest, lock=True, soft=False)
        self.parent.addchest( self.chest, tier=tier, name=name, lock=locked )

    def addcluechest ( self, tier=0, name='', items=[], locked=None ):
        self.cluechest = self.offset + Vec(10,-1,9)
        self.parent.setblock( self.cluechest, materials.Chest, lock=True)
        self.parent.addchest( self.cluechest, tier=tier, loot=items , name=name, lock=locked )

		
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
        try:
            chunk = self.parent.world.getChunk(self.pos.x>>4, self.pos.z>>4)
            mat = materials.materialById(chunk.Blocks[8,8,self.pos.y])
            if mat is materials.Air:
                self.parent.setblock(self.offset + Vec(8, 0, 8), self.stone,0)
        except:
            print 'Cannot identify central material'
        self.parent.setblock(self.offset + Vec(8, -1, 8), materials.SignPost, random.randint(0,7))
        self.parent.addsign(self.offset + Vec(8,-1,8), "", self.parent.owner, "- was here -", "Keep away!")
		
    def describe (self):
        return "a signpost"

    def addchest ( self, tier=0, name='', locked=None ):
        # Add a chest to the map: this is called after rendering
        # only one possible location (at varying depth) in this feature
        # position is y-reversed voxels relative to pos
        if random.randint(0,100) < 5:
            self.chest = self.offset + Vec( 8, random.randint(1,2) , 8 )
            self.chestdesc = "right below"
        else:
            xoff = random.randint(1,6)
            zoff = random.randint(1,6)
            if random.randint(0,1) < 1:
                ew = 'East'
            else:
                ew = 'West'
                xoff = -xoff
            if random.randint(0,1) < 1:
                ns = 'South'
            else:
                ns = 'North'
                zoff = -zoff
            self.chest = self.offset + Vec( 8 + xoff, random.randint(1,2), 8 + zoff )
            self.chestdesc = "%d steps to the %s, then %d steps to the %s" % ( xoff, ew, zoff, ns )
        self.parent.setblock( self.chest, materials.Chest, lock=True, soft=False)
        self.parent.addchest( self.chest, tier=tier, name=name, lock=locked )
    
    def addcluechest ( self, tier=0, name='', items=[], locked=None ):
        self.cluechest = self.offset + Vec(9,-1,9)
        self.parent.setblock( self.cluechest, materials.Chest, lock=True, soft=False)
        self.parent.addchest( self.cluechest, tier=tier, loot=items , name=name, lock=locked )

class Monolith(Clearing):
    _name = 'monolith'
    
    def render (self):
        # add a monolith
        center = self.pos + Vec(8,0,8)
        size = 3
        self.addclearing(center,size)

        self.parent.setblock(self.offset + Vec(8, -1, 8), self.stone)
        for p in iterate_plane(Vec(7,-1,7), Vec(9,-1,9)):
            self.parent.setblock(self.offset + p, self.stone)
        h = -random.randint(7,14)
        for p in iterate_plane(Vec(8,-2,8), Vec(8,h,8)):
            self.parent.setblock(self.offset + p, self.stone)
        self.parent.setblock(self.offset + Vec(8,-2,7), self.stonesteps,2)
        self.parent.setblock(self.offset + Vec(9,-2,7), self.stonesteps,2)
        self.parent.setblock(self.offset + Vec(7,-2,9), self.stonesteps,3)
        self.parent.setblock(self.offset + Vec(8,-2,9), self.stonesteps,3)
        self.parent.setblock(self.offset + Vec(9,-2,9), self.stonesteps,3)
        self.parent.setblock(self.offset + Vec(7,-2,8), self.stonesteps,0)
        self.parent.setblock(self.offset + Vec(9,-2,8), self.stonesteps,1)
        self.parent.setblock(self.offset + Vec(7,-2,7), self.stonesteps,2)
        self.parent.setblock(self.offset + Vec(8,h-1,8), materials.CobblestoneWall)

    def describe (self):
        return "a monolith"

    def addchest ( self, tier=0, name='', locked=None ):
        # Add a chest to the map: this is called after rendering
        # position is y-reversed voxels relative to pos
        _position = (
            ( 'below', Vec(0,random.randint(1,3),0)),
            ( 'buried to the North', Vec(0,random.randint(1,3),-2)),
            ( 'buried to the South', Vec(0,random.randint(1,3),2)),
            ( 'buried to the East', Vec(2,random.randint(1,3),0)),
            ( 'buried to the West', Vec(-2,random.randint(1,3),0)),
        )
        p = random.choice(_position)
        self.chest = self.offset + Vec( 8, 0 , 8 ) + p[1]
        self.chestdesc = p[0]
        self.parent.setblock( self.chest, materials.Chest, lock=True, soft=False)
        self.parent.addchest( self.chest, tier=tier, name=name, lock=locked )
    
    def addcluechest ( self, tier=0, name='', items=[], locked=None ):
        self.cluechest = self.offset + Vec(8,-1,6)
        self.parent.setblock( self.cluechest, materials.Chest, lock=True)
        self.parent.addchest( self.cluechest, tier=tier, loot=items , name=name, lock=locked )

class Memorial(Clearing):
    _name = 'memorial'
    description = 'a memorial'

    def render (self):
        # add a memorial
        center = self.pos + Vec(8,0,8)
        size = 3
        self.addclearing(center,size)

        self.parent.setblock(self.offset + Vec(8, -4, 8), self.stone)
        for p in iterate_plane(Vec(7,-1,8), Vec(9,-3,8)):
            self.parent.setblock(self.offset + p, self.stone)
        self.parent.setblock(self.offset + Vec(7,-4,8), self.stonesteps,0)
        self.parent.setblock(self.offset + Vec(9,-4,8), self.stonesteps,1)
        self.parent.setblock(self.offset + Vec(6,-1,8), self.stonesteps,0)
        self.parent.setblock(self.offset + Vec(10,-1,8), self.stonesteps,1)
        self.parent.setblock(self.offset + Vec(6,-1,9), self.stonesteps,3)
        self.parent.setblock(self.offset + Vec(7,-1,9), self.stonesteps,3)
        self.parent.setblock(self.offset + Vec(8,-1,9), self.stonesteps,3)
        self.parent.setblock(self.offset + Vec(9,-1,9), self.stonesteps,3)
        self.parent.setblock(self.offset + Vec(10,-1,9), self.stonesteps,3)

        picof = 'a picture'
        painting = self.parent.inventory.mapstore.add_painting(random.choice(self.parent.inventory.paintlist))
        picof = painting['tag']['display']['Name'].value
        self.description = 'a memorial to %s' % ( picof )
        framed_painting = get_entity_other_tags("ItemFrame",
                                         Pos=self.offset + Vec(8,-3,8),
                                         Direction=0,
                                         ItemRotation=0,
                                         ItemTags=painting)
        framed_painting['Motive'] = painting['tag']['display']['Name']
        framed_painting['Invulnerable'] = nbt.TAG_Byte(1)
        # Place the item frame.
        self.parent.addentity(framed_painting)

        self.parent.setblock(self.offset + Vec(8, -2, 9), materials.WallSign, 0)
        self.parent.addsign(self.offset + Vec(8,-2,9), "In memory of", picof, "",self.parent.owner)

    def describe (self):
        return self.description

    def addchest ( self, tier=0, name='', locked=None ):
        # Add a chest to the map: this is called after rendering
        # position is y-reversed voxels relative to pos
        _position = (
            ( 'buried behind', Vec(0,random.randint(1,3),-1)),
            ( 'buried in front', Vec(0,random.randint(1,3),2)),
            ( 'buried to the right', Vec(3,random.randint(1,3),0)),
            ( 'buried to the left', Vec(-3,random.randint(1,3),0)),
        )
        p = random.choice(_position)
        self.chest = self.offset + Vec( 8, 0 , 8 ) + p[1]
        self.chestdesc = p[0]
        self.parent.setblock( self.chest, materials.Chest, lock=True)
        self.parent.addchest( self.chest, tier=tier, name=name, lock=locked )
    
    def addcluechest ( self, tier=0, name='', items=[], locked=None ):
        self.cluechest = self.offset + Vec(8,-1,7)
        self.parent.setblock( self.cluechest, materials.Chest, lock=True)
        self.parent.addchest( self.cluechest, tier=tier, loot=items , name=name, lock=locked )

#class Well(Clearing):
#    _name = 'well'		               

#class Forge(Clearing):
#    _name = 'forge'

# Catalog the features we know about. 
_landmarks = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses of landmarks.Blank
    if issubclass(obj, Clearing):
        _landmarks[obj._name] = obj

def new (name, parent, pos, biome=None):
    '''Return a new instance of the feature of a given name. Supply the parent
    treasurehunt object.'''
    if name in _landmarks.keys():
        return _landmarks[name](parent,pos,biome)
    return Clearing(parent,pos,biome)
    
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
        if thunt.args.debug:
            print "Landmark biome ID is %d" % biome
    else:
        biome = None
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
    return new(name, thunt, pos, biome)
