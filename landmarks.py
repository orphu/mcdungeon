# Landmarks for Treasure Hunts
# These have location in voxels relative to the parent.position, and live in a single chunk
# y values reversed.  This is so they can utilise the Dungeon.Block functions

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
    def addclearing (self, center, diam, clear_surface=True):
        # flatten a disc of ground, erase any trees
        # centre is in world coordinates
        # identify the ground material at the centre
        try:
            chunk = self.parent.world.getChunk(center.x>>4, center.z>>4)
            mat = materials.materialById(chunk.Blocks[center.x & 15, center.z & 15, center.y])
        except:
            print 'Cannot identify central material'
            mat = materials.Dirt
        # Now make sure we have something solid
        if mat is None or mat is False or not isinstance(mat, materials.Material):
            print 'Center material is %s' % mat
            mat = materials.Dirt
        if mat.val == materials.Air.val or mat.val == materials.StillWater.val:
            mat = materials.Dirt
            self.offset.y -= 1
            sel.pos.y += 1
            center.y -= 1

        p0 = Vec(center.x - diam/2 - self.parent.position.x,
                 self.parent.position.y - center.y,
                 center.z - diam/2 - self.parent.position.z ) 
        p1 = p0.trans(diam+1, 0, diam+1)
        # Iterate around the entire disc
        for p in iterate_disc(p0,p1):
            if clear_surface:
                # At least 10 clear blocks above
                # this should delete any trees; there should be nothing above anyway
                for i in xrange(10):
                    self.parent.setblock(p.up(i),materials.Air)
            # Set the disc to the base material
            self.parent.setblock(p,mat)
            # In case ground is sloping or has gaps, add underlying blocks
            self.parent.setblock(p.down(1),mat,soft=True)
            self.parent.setblock(p.down(2),mat,soft=True)
            self.parent.setblock(p.down(3),mat,soft=True)

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
        
    def spawnerloc ( self ):
        # return offset where spawner should be placed: up is -ve y
        # Note that spawners can only spawn at their own level or 1 above/below
        # in a radius of 4.  Thus, you cannot bury them.
        return Vec(7,-1,7)


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
                self.parent.setblock(p.up(1), materials.Torch, 5)

    def describe (self):
        return "a circle of skulls"

# This class handles the cottage, either occupied, abandoned, or ruined        
class SmallCottage(Clearing):
    _name = 'smallcottage'
    _ruined = False
    _abandoned = False
    # randomise NS or EW - to be done
    
    def render (self):
        center = self.pos + Vec(8,0,8)
        size = 12
        self.addclearing(center,size)
		
        # create cottage
        # walls
        for p in iterate_four_walls(Vec(6,0,6), Vec(11,0,10),2):
            self.parent.setblock(self.offset + p, self.stone, soft=False)
        # floor - this seems to not be working?
        for p in iterate_plane(Vec(6,0,6), Vec(11,0,10)):
            self.parent.setblock(self.offset + p, self.stone, soft=False)
        # Gable ends
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
        self.parent.setblock(self.offset+Vec(9,-2,6),materials.Air)
        # fireplace
        self.parent.setblock(self.offset+Vec(6,-1,8),materials.Air)
        self.parent.setblock(self.offset+Vec(5,-1,8),self.stone)
        self.parent.setblock(self.offset+Vec(5,-2,8),self.stonesteps, 0)

        # add bed
        self.parent.setblock(self.offset+Vec(9 ,-1,7),materials.BedBlock,3)
        self.parent.setblock(self.offset+Vec(10,-1,7),materials.BedBlock,11)
		
        if self._ruined is False:
            # if not ruined, add roof, door and window
            self.parent.setblock(self.offset+Vec(10,-1,9),materials.CraftingTable)
            self.parent.setblock(self.offset+Vec(7,-2,10),materials.GlassPane)
            self.parent.setblock(self.offset+Vec(9,-2,6),materials.GlassPane)
            self.parent.setblock(self.offset+Vec(9,-1,10),materials.WoodenDoor,3)
            self.parent.setblock(self.offset+Vec(9,-2,10),materials.WoodenDoor,11)
            for x in xrange(6):
                self.parent.setblock(self.offset+Vec(6+x,-3,10),materials.SpruceWoodStairs,3)
                self.parent.setblock(self.offset+Vec(6+x,-4,9),materials.SpruceWoodStairs,3)
                self.parent.setblock(self.offset+Vec(6+x,-3,6),materials.SpruceWoodStairs,2)
                self.parent.setblock(self.offset+Vec(6+x,-4,7),materials.SpruceWoodStairs,2)
                self.parent.setblock(self.offset+Vec(6+x,-5,8),materials.SpruceWoodSlab,soft=False)
            # add table
            self.parent.setblock(self.offset+Vec(8,-1,8),materials.Fence)
            self.parent.setblock(self.offset+Vec(8,-2,8),materials.WoodenPressurePlate)

            if self._abandoned is True:
                # if abandoned, add cobwebs (parent function) voxels relative
                self.parent.cobwebs(self.offset + Vec(8,0,8) + Vec(-2,0,2), self.offset + Vec(8,0,8) + Vec(3,-4,-2))
            else:
                # if not abandoned, add torches inside
                self.parent.setblock(self.offset + Vec(8,0,8) + Vec(2,-3,0), materials.Torch, 2)
                self.parent.setblock(self.offset + Vec(8,0,8) + Vec(-1,-3,0), materials.Torch, 1)
                # add villager
                shopkeeper_name = self.parent.namegen.genname()
                pos = self.offset + Vec(8,-1,8)
                tags = get_entity_mob_tags('villager',
                                   Pos=pos,
                                   Profession=0, # farmer always
                                   CustomName=shopkeeper_name)
                self.parent.addentity(tags)
                if self.parent.args.debug:
                    print "Added farmer '%s'" % ( shopkeeper_name )
        # chimney
        self.parent.setblock(self.offset+Vec(6,-5,8),self.stone)

    def describe (self):
        return "a small cottage"

    def addchest ( self, tier=0, name='', locked=None ):
        _chestpos = [
            ('under the fireplace',Vec(6,1,8)),
            ('under the bed',Vec(10,1,7)),
            ('under the doorstep',Vec(9,1,11)),
        ]
        if self._ruined is False:
            _chestpos.append( ['in the rafters',Vec(10,-4,8)] )
        c = random.choice(_chestpos)
        self.chest = self.offset + c[1]
        self.chestdesc = c[0]
        self.parent.setblock( self.chest, materials.Chest, lock=True, soft=False)
        self.parent.addchest( self.chest, tier=tier, name=name, lock=locked )

    def addcluechest ( self, tier=0, name='', items=[], locked=None ):
        self.cluechest = self.offset + Vec(10,-1,9)
        self.parent.setblock( self.cluechest, materials.Chest, lock=True)
        self.parent.addchest( self.cluechest, tier=tier, loot=items , name=name, lock=locked )
     
    def spawnerloc ( self ):
        return Vec( 9, -1, 5 )
		
class AbandonedCottage(SmallCottage):
    _name = 'abandonedcottage'
    _abandoned = True

    def spawnerloc ( self ):
        return Vec( 7, -1, 9 )

class RuinedCottage(SmallCottage):
    _name = 'ruinedcottage'
    _abandoned = True
    _ruined = True

    def spawnerloc ( self ):
        return Vec( 7, -1, 9 )

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
        self.parent.addsign(self.offset + Vec(8,-1,8), "", 
            self.parent.owner, 
            '- was here -', 
            'Keep away!')
		
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
            self.chestdesc = "%d steps to the %s, then %d steps to the %s" % ( abs(xoff), ew, abs(zoff), ns )
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
        
    def spawnerloc ( self ):
        return Vec( 8, -1, 6 )


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
        framed_painting = get_entity_other_tags("item_frame",
                                         Pos=self.offset + Vec(8.0,-3,8), # block frame is IN
                                         Facing="S", # 0=south
                                         ItemRotation=0,
                                         ItemTags=painting)
        # Place the item frame.
        self.parent.addentity(framed_painting)

        self.parent.setblock(self.offset + Vec(8,-2,9), materials.WallSign, 3) # 3=south
        self.parent.addsign(self.offset + Vec(8,-2,9), 
            'In memory of', 
            picof, 
            '',
            self.parent.owner)

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

    def spawnerloc ( self ):
        return Vec( 7, -1, 7 )

# An empty, flat circular area, with a circle of mushrooms
# chest can be under the centre of the circle
class FairyRing(Clearing):
    _name = 'fairyring'

    # Render relative to TreasureHunt position in y-reversed coords
    def render (self):
        center = self.pos + Vec(8,0,8)
        size = random.randint(6,10)
        # Now need to flatten the circle in case it is on a slope
        self.addclearing(center,size)
                
        # Create the circle of shrooms
        p0 = Vec(center.x - size/2 + 1 - self.parent.position.x,
                 self.parent.position.y - center.y,
                 center.z - size/2 + 1 - self.parent.position.z) 
        p1 = p0.trans(size-1, 0, size-1)
        _mush = (
            (materials.RedMushroom, 5),
            (materials.BrownMushroom, 1),
        )
        for p in iterate_ellipse(p0, p1):
            # Abort if there is no shroom here
            if (random.randint(0,100) < 20):
                continue
            Shroom = weighted_choice(_mush)
            self.parent.setblock(p.up(1), Shroom, 0)
                
    def describe (self):
        return "a fairy ring"

class FlowerGarden(Clearing):
    _name = 'flowergarden'

    # Render relative to TreasureHunt position in y-reversed coords
    def render (self):
        center = self.pos + Vec(8,0,8)
        size = random.randint(10,14)
        # Now need to flatten the circle in case it is on a slope
        self.addclearing(center,size)

        # Create the flower garden
        p0 = Vec(center.x - size/2 + 1 - self.parent.position.x,
                 self.parent.position.y - center.y,
                 center.z - size/2 + 1 - self.parent.position.z) 
        p1 = p0.trans(size-1, 0, size-1)
        _flowers = (
            (materials.Sunflower, 20),
            (materials.Lilac, 10),
            (materials.RoseBush, 10),
            (materials.Peony, 10),
            (materials.Dandelion, 5),
            (materials.Poppy, 5),
            (materials.RedTulip, 2),
            (materials.OrangeTulip, 2),
            (materials.WhiteTulip, 2),
            (materials.PinkTulip, 2),
            (materials.RedMushroom, 1),
        )
        for p in iterate_disc(p0, p1):
            self.parent.setblock(p,materials.Dirt,lock=True)
            # Abort if there is no flower here
            if (random.randint(0,100) < 10):
                continue
            flower = weighted_choice(_flowers)
            self.parent.setblock(p.up(1), flower, 0)
            if ( flower.val == 175 or flower.val == 'minecraft:double_plant' ):
                self.parent.setblock(p.up(2), flower, 8)

    def describe (self):
        return "a flower garden"

class Well(Clearing):
    _name = 'well'	
    _description = "a well"    
    # The well has a hidden secret room down under the water, using wallsigns 
    # to hold the water back.  Chest may be in room, or in roof, or at
    # bottom of well, or buried nearby.  Should we put something interesting
    # into the room, like a horde of silverfish or a zombie, or a spawner?
    def render (self):
        center = self.pos + Vec(8,0,8)
        size = 6
        self.addclearing(center,size)
		
        # well - remember +ve Y is down
        for i in xrange(-1,7):
          for x in xrange(7,10):
            for z in xrange(7,10):
              self.parent.setblock(self.offset+Vec(x,i,z),self.stone, soft=False)
        for i in xrange(0,6):
          self.parent.setblock(self.offset+Vec(8,i,8),materials.StillWater, soft=False)
        # mouth
        self.parent.setblock(self.offset+Vec(8,-1,8),materials.Air)
        # secret room
        for p in iterate_hollow_cube(self.offset+Vec(4,5,6),self.offset+Vec(7,2,9)):
          self.parent.setblock(p,self.stone)
        for p in iterate_cube(self.offset+Vec(5,4,7),self.offset+Vec(6,3,8)):
          self.parent.setblock(p,materials.Air)
        self.parent.setblock(self.offset + Vec(5,4,8), materials.Torch,5)
                
        # secret door
        self.parent.setblock(self.offset+Vec(7,3,8),materials.WallSign,2)
        self.parent.setblock(self.offset+Vec(7,4,8),materials.WallSign,2)
        self.parent.addsign(self.offset+Vec(7,3,8), "", 
            self.parent.owner, 
            "- was here -", 
            "Keep away!")
        self.parent.addsign(self.offset+Vec(7,4,8), "", 
            "Secret", 
            "Treasure", 
            "Room")
        # roof
        self.parent.setblock(self.offset+Vec(7,-2,8),materials.Fence)
        self.parent.setblock(self.offset+Vec(9,-2,8),materials.Fence)
        for x in xrange(7,10):
            self.parent.setblock(self.offset+Vec(x,-3,7),materials.SpruceWoodStairs,2)
            self.parent.setblock(self.offset+Vec(x,-3,9),materials.SpruceWoodStairs,3)
            self.parent.setblock(self.offset+Vec(x,-4,8),materials.SpruceWoodSlab)
        self.parent.setblock(self.offset+Vec(7,-3,8),materials.SpruceWoodPlanks)
        self.parent.setblock(self.offset+Vec(9,-3,8),materials.SpruceWoodPlanks)
        
        _descs = ( 
            'a well',
            'a well',
            'an old well',
            'a deep well',
            'a source of water',
            'Jack and Jill\'s bane',
        )
        self._description = random.choice(_descs)
    
    def describe (self):
        return self._description

    def addchest ( self, tier=0, name='', locked=None ):
        _chestpos = (
            ('in the roof',Vec(0,-3,0)),
            ('at the bottom of the well',Vec(0,6,0)),
            ('buried to the east',Vec(2,1,0)),
            ('down the well',Vec(-3,3,-1)),
            ('in a hidden room down the well',Vec(-3,3,-1)),
            ('in my secret room',Vec(-3,3,-1)),
        )
        c = random.choice(_chestpos)
        self.chest = self.offset + c[1] + Vec(8,0,8)
        self.chestdesc = c[0]
        self.parent.setblock( self.chest, materials.Chest, lock=True, soft=False)
        self.parent.addchest( self.chest, tier=tier, name=name, lock=locked )

    def addcluechest ( self, tier=0, name='', items=[], locked=None ):
        self.cluechest = self.offset + Vec(6,-1,8)
        self.parent.setblock( self.cluechest, materials.Chest, lock=True, soft=False)
        self.parent.addchest( self.cluechest, tier=tier, loot=items , name=name, lock=locked )

    def spawnerloc ( self ):
        return Vec( 6, -1, 6 )

        
class Forge(Clearing):
    # This is similar to the Cottage
    _name = 'forge'
    _ruined = False
    _abandoned = False
    
    def render (self):
        center = self.pos + Vec(8,0,8)
        size = 12
        self.addclearing(center,size)
		
        # create forge
        # walls
        for p in iterate_plane(Vec(6,-1,6), Vec(6,-3,10)):
            self.parent.setblock(self.offset + p, self.stone, soft=False)
        for p in iterate_plane(Vec(11,-1,6), Vec(11,-3,10)):
            self.parent.setblock(self.offset + p, self.stone, soft=False)
        for p in iterate_plane(Vec(7,-1,6), Vec(10,-3,6)):
            self.parent.setblock(self.offset + p, self.stone, soft=False)
        # doorway
        self.parent.setblock(self.offset+Vec(11,-1,8),materials.Air)
        self.parent.setblock(self.offset+Vec(11,-2,8),materials.Air)
        # floor 
        for p in iterate_plane(Vec(6,0,6), Vec(11,0,10)):
            self.parent.setblock(self.offset + p, self.stone, soft=False)
        # forge
        self.parent.setblock(self.offset+Vec(8,-1,7),self.stonesteps,1)
        self.parent.setblock(self.offset+Vec(8,-1,8),self.stonesteps,3)
        self.parent.setblock(self.offset+Vec(7,-1,8),self.stonesteps,3)
		
        if self._ruined is False:
            # if not ruined, add table and roof
            self.parent.setblock(self.offset+Vec(10,-1,10),materials.CraftingTable)
            for x in xrange(6):
                self.parent.setblock(self.offset+Vec(6+x,-4,10),materials.SpruceWoodStairs,3)
                self.parent.setblock(self.offset+Vec(6+x,-4,6),materials.SpruceWoodStairs,2)
                for i in xrange(3):
                    self.parent.setblock(self.offset+Vec(6+x,-5,7+i),materials.SpruceWoodSlab,soft=False)
            for i in xrange(3):
                self.parent.setblock(self.offset+Vec(6,-4,7+i),materials.SpruceWoodPlanks,soft=False)
                self.parent.setblock(self.offset+Vec(11,-4,7+i),materials.SpruceWoodPlanks,soft=False)
            # add table
            self.parent.setblock(self.offset+Vec(7,-1,10),materials.Fence)
            self.parent.setblock(self.offset+Vec(7,-2,10),materials.WoodenPressurePlate)
            # add door
            self.parent.setblock(self.offset+Vec(11,-1,8),materials.WoodenDoor,2)
            self.parent.setblock(self.offset+Vec(11,-2,8),materials.WoodenDoor,8)
            # Add fence
            self.parent.setblock(self.offset+Vec(6,-1,11),materials.Fence)
            self.parent.setblock(self.offset+Vec(11,-1,11),materials.Fence)
            for i in xrange(6,12):
                self.parent.setblock(self.offset+Vec(i,-1,12),materials.Fence)
            self.parent.setblock(self.offset+Vec(9,-1,12),materials.FenceGate,0)

            if self._abandoned is True:
                # if abandoned, add cobwebs (parent function) voxels relative
                self.parent.cobwebs(self.offset + Vec(7,-1,7), self.offset + Vec(10,-4,10))
                # obsidian in forge
                self.parent.setblock(self.offset+Vec(7,-1,7),materials.Obsidian)
                # anvil
                self.parent.setblock(self.offset+Vec(9,-1,7),materials.Anvil,5)
            else:
                # if not abandoned, add torches inside
                self.parent.setblock(self.offset + Vec(10,-3,10), materials.Torch, 2)
                self.parent.setblock(self.offset + Vec(7,-3,10), materials.Torch, 1)
                # lava in forge
                self.parent.setblock(self.offset+Vec(7,-1,7),materials.StillLava)
                # anvil
                self.parent.setblock(self.offset+Vec(9,-1,7),materials.Anvil,1)
                # add villager
                villager_name = self.parent.namegen.genname()
                pos = self.offset + Vec(9,-1,9)
                tags = get_entity_mob_tags('villager',
                                   Pos=pos,
                                   Profession=3, # blacksmith always
                                   CustomName=villager_name)
                self.parent.addentity(tags)
                if self.parent.args.debug:
                    print "Added blacksmith '%s'" % ( villager_name )
        else:
            # obsidian in forge
            self.parent.setblock(self.offset+Vec(7,-1,7),materials.Obsidian)
            # anvil
            self.parent.setblock(self.offset+Vec(9,-1,7),materials.Anvil,9)

    def describe (self):
        return "a blacksmith's forge"

    def addchest ( self, tier=0, name='', locked=None ):
        _chestpos = [
            ('under the anvil',Vec(9,1,7)),
            ('under the crafting table',Vec(10,1,10)),
            ('under the forge',Vec(7,1,7)),
        ]
        if self._ruined is False:
            _chestpos.append( ['in the rafters',Vec(10,-4,9)] )
        c = random.choice(_chestpos)
        self.chest = self.offset + c[1]
        self.chestdesc = c[0]
        self.parent.setblock( self.chest, materials.Chest, lock=True, soft=False)
        self.parent.addchest( self.chest, tier=tier, name=name, lock=locked )

    def addcluechest ( self, tier=0, name='', items=[], locked=None ):
        self.cluechest = self.offset + Vec(10,-1,7)
        self.parent.setblock( self.cluechest, materials.Chest, 1, lock=True)
        self.parent.addchest( self.cluechest, tier=tier, loot=items , name=name, lock=locked )

    def spawnerloc ( self ):
        return Vec( 9, -1, 5 )

class AbandonedForge(Forge):
    _name = 'abandonedforge'
    _ruined = False
    _abandoned = True

    def spawnerloc ( self ):
        return Vec( 7, -1, 9 )

class RuinedForge(Forge):
    _name = 'ruinedforge'
    _ruined = True
    _abandoned = True

    def spawnerloc ( self ):
        return Vec( 7, -1, 9 )

class Graveyard(Clearing):
    _name = 'graveyard'
    _graves = []
    # We build several graves.  Use the 1.8 json-style sign labels to
    # make a grave marker show the current player's name.
    # Each grave fits in a 3x3 block, with the sign facing East
    # Only add to the _graves array if we can hide a chest here
    def add_grave( self, pos ):
        # 10% chance of a vacant plot
        if random.randint(0,100) < 10:
            return
        # Randomise name of grave
        _grave_name = [
            (self.parent.namegen.genname(), 100), 
            ("unknown miner", 5),  
            ("Steve", 1),  
            ("Herobrine", 1),  
        ]
        grave_name = weighted_choice(_grave_name)
        # Different materials: red sandstone is 1.8 only
        mtype = random.randint(1,4)
        if mtype==0:
            stone = materials.RedSandstone
            steps = materials.RedSandstoneStairs
            slab  = materials.RedSandstoneSlab
        elif mtype==1:
            stone = materials.ChiseledQuartz
            steps = materials.QuartzStairs
            slab  = materials.QuartzSlab  
        elif mtype==2:
            stone = materials.Obsidian
            steps = self.stonesteps
            slab  = self.stoneslab
        elif mtype==3:
            stone = materials.OakWoodPlanks
            steps = materials.OakWoodStairs
            slab  = materials.OakWoodSlab
        else:
            stone = self.stone
            steps = self.stonesteps
            slab  = self.stoneslab

        # What material do we fill the grave with?
        if self.biome is not None and ( self.biome == 2 or self.biome == 130 ):
            dirt = materials.RedSand
        else:
            dirt = materials.Gravel

        # Different gravestone designs
        gtype = random.randint(0,4)
        if gtype==0:
            self.parent.setblock(self.offset + pos + Vec(0,-1,1), steps, 0)
        elif gtype==1:
            self.parent.setblock(self.offset + pos + Vec(0,-1,1), stone)
            self.parent.setblock(self.offset + pos + Vec(0,-2,1), stone)
        elif gtype==2:
            self.parent.setblock(self.offset + pos + Vec(0,-1,1), stone)
            self.parent.setblock(self.offset + pos + Vec(0,-2,1), materials.Fence)                  
        elif gtype==3:
            self.parent.setblock(self.offset + pos + Vec(0,-1,1), stone)
            self.parent.setblock(self.offset + pos + Vec(0,-2,1), slab)
        else:
            self.parent.setblock(self.offset + pos + Vec(0,-1,1), stone)
    
        # Grave itself
        if random.randint(0,100) < 5:
            # open grave
            self.parent.setblock(self.offset + pos + Vec(1,0,1), materials.Air, soft=False)
            self.parent.setblock(self.offset + pos + Vec(1,1,1), materials.Air, soft=False)
            self.parent.setblock(self.offset + pos + Vec(2,0,1), materials.Air, soft=False)
            self.parent.setblock(self.offset + pos + Vec(2,1,1), materials.Air, soft=False)
        else:
            # dirt
            self.parent.setblock(self.offset + pos + Vec(1,0,1), dirt, soft=False)
            self.parent.setblock(self.offset + pos + Vec(2,0,1), dirt, soft=False)
            # coffin
            self.parent.setblock(self.offset + pos + Vec(1,1,1), materials.OakWoodPlanks, soft=False)
            self.parent.setblock(self.offset + pos + Vec(2,1,1), materials.OakWoodPlanks, soft=False)
            # flower on grave
            if random.randint(0,100) < 50:
                flowers = ("poppy", "blue orchid", "allium", "azure bluet",
                           "red tulip", "orange tulip", "white tulip", "pink tulip",
                           "oxeye daisy", "dandelion", "dead bush", "air")
                self.parent.setblock(self.offset + pos + Vec(2,-1,1), materials.FlowerPot, 0)
                self.parent.addflowerpot(self.offset + pos + Vec(2,-1,1),
                                         itemname=random.choice(flowers))

        # marker: same graves are unmarked
        if random.randint(0,100)>5:
            self._graves.append( [ grave_name, pos + Vec(0,1,1) ] )
            self.parent.setblock(self.offset + pos + Vec(1,-1,1), materials.WallSign, 5) # face east
            self.parent.addsign(self.offset + pos + Vec(1,-1,1), 
			    'Here lies', 
			    grave_name, 
			    "R.I.P.",
			    '')
        
    def render (self):
        # add a graveyard
        center = self.pos + Vec(8,0,8)
        size = 14
        self.addclearing(center,size)
        
        for x in xrange(5,13,4):
            for z in xrange(4,14,2):
                self.add_grave(Vec(x,0,z))
        for p in iterate_four_walls(self.offset + Vec(3,-1,3), self.offset + Vec(13,-1,14), 0):
            self.parent.setblock(p, materials.Fence)
        self.parent.setblock(self.offset+Vec(13,-1,9), materials.FenceGate,3)

    def describe (self):
        return "a graveyard"

    def addchest ( self, tier=0, name='', locked=None ):
        # position is y-reversed voxels relative to pos
        if self._graves == []:
            # unlikely, but there may be no (named) graves
            self.chest = self.offset + Vec(8,1,8)
            self.chestdesc = "buried in the middle of the graveyard"
        else:
            p = random.choice(self._graves)
            self.chest = self.offset + p[1]
            self.chestdesc = "sleeping with the body of %s" % ( p[0] )
        self.parent.setblock( self.chest, materials.Chest, lock=True)
        self.parent.addchest( self.chest, tier=tier, name=name, lock=locked )
    
    def addcluechest ( self, tier=0, name='', items=[], locked=None ):
        self.cluechest = self.offset + Vec(12,-1,8)
        self.parent.setblock( self.cluechest, materials.Chest, lock=True)
        self.parent.addchest( self.cluechest, tier=tier, loot=items , name=name, lock=locked )

    def spawnerloc ( self ):
        return Vec( 8, -1, 8 )
        
class BigTree(Clearing):
    _name = 'bigtree'
    _treetype = ""
    
    # Render relative to TreasureHunt position in y-reversed coords
    def render (self):
        # We set 4 spaces of earth in the middle.  Clear the sky above,
        # and plant 4 saplings there to grow.
        # Only DarkOak, JungleTree and Spruce can make a big tree this way
        tree_dv = 5
        self._treetype = "dark oak "
        # Should select a different tree if necessary to make it NOT
        # match the biome.  Spruce is DV=1
        if ( self.biome in [3,4,6,21,29,157,131,132,149,151] ):
            # in jungle, or oak forest
            tree_dv = 1
            self._treetype = "spruce "

        for x in xrange(-1,3):
            for z in xrange(-1,3):
                self.parent.setblock(self.offset+Vec(8+x,0,8+z), materials.Dirt, lock=True)
                self.parent.setblock(self.offset+Vec(8+x,-1,8+z), materials.Air)
        
        # Set the counter to 8 (b1000) so it grows very soon
        # This is not very well documented: the 0x8 bit and higher are apparently
        # where the Counter is held, and when this gets 'large enough' and the other
        # conditions are met, (space above and to the side, light level) the tree will grow.
        for x in xrange(0,2):
            for z in xrange(0,2):
                self.parent.setblock(self.offset+Vec(8+x,-1,8+z), materials.Sapling, tree_dv + 8, lock=True, soft=False)

        # Need to clear a 4x4 space, 16 spaces above the ground.
        for i in xrange(2,17):
            for x in xrange(-1,3):
                for z in xrange(-1,3):
                    self.parent.setblock(self.offset+Vec(8+x,-i,8+z), materials.Air)

    def addchest (self, tier=0, name='', locked=None):
        # Add a chest to the map: this is called after rendering
        # only one possible location (at varying depth) in this feature
        # position is y-reversed voxels relative to pos
        self.chest = Vec(random.randint(7,10),random.randint(1,3),random.randint(7,10)) + self.offset
        self.chestdesc = "in the roots"
        self.parent.setblock( self.chest, materials.Chest, lock=True)
        self.parent.addchest( self.chest, tier=tier, name=name, lock=locked )

    def addcluechest (self, tier=0, name='', items=[], locked=None):
        # Add a chest to the map: this is called after rendering
        # only one possible location in this feature
        # position is y-reversed voxels relative to pos
        # Not too close to the tree or it will not grow
        self.cluechest = Vec( 6, -1 , 7 ) + self.offset
        self.parent.setblock( self.cluechest, materials.Chest, lock=True)
        self.parent.addchest( self.cluechest, tier=tier, loot=items , name=name, lock=locked )
                
    def describe (self):
        return "a large "+self._treetype+"tree"

    def spawnerloc ( self ):
        return Vec( 6, -1, 9 )
        
# ----------------------------------------------------------------------------

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
        cdata = thunt.world.getChunk(pos.x >> 4, pos.z >> 4)
        biome = numpy.argmax(numpy.bincount((cdata.Biomes.flatten())))
        # do we have a special landmark list for this biome, or take default list?
        try:
            landmark_list = weighted_shuffle(cfg.master_landmarks[biome])
        except KeyError:
            landmark_list = weighted_shuffle(cfg.default_landmarks)
        if thunt.args.debug:
            print "\nLandmark biome ID is %d" % biome
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
