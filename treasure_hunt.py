import sys
import os
import operator
from pprint import pprint
import random
from random import *
import logging

import cfg
import loottable
import materials
import landmarks
import pmeter
import namegenerator
import inventory
from utils import *
from disjoint_set import DisjointSet
from pymclevel import nbt

from dungeon import Dungeon, RelightHandler, Block

# The Treasure Hunt class is a subclass of Dungeon and uses the same 
# utility functions.  However, unlike Dungeon, self.position only holds the
# location of the config cache chest.  self.xsize and self.zsize are always 1
# The landmarks[] array holds the actual locations of the landmarks (including
# the start position) with positions in voxels relative to self.position
# These offsets can become very large although a landmark itself uses a single
# chunk.
# The d_info and dungeon_name vars are used for compatibility instead of changing
# them to tinfo and thunt_name
class TreasureHunt (Dungeon):

    def __init__(self,
                 args,
                 world,
                 chunk_cache,
                 thunt_cache,
                 good_chunks,
                 mapstore):

        self.world = world
        self.chunk_cache = chunk_cache
        self.thunt_cache = thunt_cache
        self.good_chunks = good_chunks
        self.mapstore = mapstore
        self.inventory = inventory.new(mapstore)
        self.pm = pmeter.ProgressMeter()
        self.blocks = {}
        self.landmarks = []
        self.tile_ents = {}
        self.ents = []
        self.placed_items = []
        self.entrance = None
        self.room_size = 16
        self.room_height = 6
        self.position = Vec(0, 0, 0)
        self.args = args
        self.dinfo = {}
        self.dinfo['fill_caves'] = cfg.fill_caves
        self.dinfo['dungeon_name'] = cfg.dungeon_name
        # this is needed to trick the bury() routine and others
        self.levels = 4

    def generate(self, cache_path, version):
        '''Generate a treasure hunt'''
        # the treasure hunt name is stored in dungeon_name and is built here
        # because we don't have a ruins[] section
        _thnames = (
            ('{owners} booty',20),
            ('{owners} treasure',20),
            ('{owners} loot', 20),
            ('{owners} chest', 20),
            ('{owners} locker', 20),
            ('{owners} college fund',1)
        )
        # Pick a starting size.
        self.xsize = 1
        self.zsize = 1
        self.steps = randint(cfg.min_steps, cfg.max_steps)
        self.min_distance = cfg.min_distance
        self.max_distance = cfg.max_distance

        located = False
        result = False
        # Find a landmark, if we can.
        # Manual landmark
        if cfg.offset is not '':
            print 'Treasure hunt step: {1}'.format(self.steps)

            self.position = str2Vec(cfg.offset)
            self.position.x = self.position.x & ~15
            self.position.z = self.position.z & ~15
            # XXX bury the chest below ground
            self.bury()
            print "Location set to: ", self.position
        # Search for a location.
        else:
            print "Searching for a suitable location..."
            located = self.findlocation()
            if (located is False):
                print 'Unable to place any more treasure hunts.'
            else:
                print 'Treasure hunt steps: {0}'.format(self.steps)
                print "Location: ", self.position
        # Generate!
        if (located is True):
            # We have a final size, so let's initialize some things.

            self.heightmap = numpy.zeros(( self.room_size,
                                           self.room_size))

            # Set the seed if requested.
            if (self.args.seed is not None):
                seed(self.args.seed)
                print 'Seed:', self.args.seed

            # Now we know the biome, we can setup a name generator
            self.namegen = namegenerator.namegenerator(None, theme='pirate')
            print 'Theme:', self.namegen.theme
            self.owner = self.namegen.genroyalname()
            print 'Owner:', self.owner
            print "Location: ", self.position
            print "Generating landmarks..."
            self.genlandmarks()
            # Name this place
            if self.owner.endswith("s"):
                owners = self.owner + "'"
            else:
                owners = self.owner + "'s"
            self.dinfo['dungeon_name'] = weighted_choice( _thnames )
            self.dungeon_name = self.dinfo['dungeon_name'].format(
                owner=self.owner,
                owners=owners)
            self.dungeon_name = self.dungeon_name[:32]
            self.dinfo['full_name'] = self.dungeon_name
            print "Treasure hunt name:", self.dungeon_name
            self.renderlandmarks()

            self.placechests()
            if cfg.th_spawners is True:
                self.placespawners()
            self.processBiomes()

            # Signature
            self.setblock(Vec(0, 0, 0), materials.Chest, 0, hide=True)
            self.tile_ents[Vec(0, 0, 0)] = encodeTHuntInfo(self,version)
            # Add to the dungeon cache.
            key = '%s,%s' % (
                self.position.x,
                self.position.z,
            )
            # we need the info if making multiple hunts, to avoid
            # all previous landmarks
            self.thunt_cache[key] = encodeTHuntInfo(self, version)

            # copy results to the world
            self.applychanges()

            # Relight these chunks.
            if (self.args.write is True and self.args.skiprelight is False):
                # Super ugly, but does progress bars for lighting.
                for handler in logging.root.handlers[:]:
                    logging.root.removeHandler(handler)
                h = RelightHandler()
                logging.basicConfig(stream=h, level=logging.INFO)
                self.world.generateLights()
                h.done()
                logging.getLogger().level = logging.CRITICAL
                for handler in logging.root.handlers[:]:
                    logging.root.removeHandler(handler)

            # Saving here allows us to pick up where we left off if we stop.
            if (self.args.write is True):
                print "Saving..."
                self.world.saveInPlace()
                saveTHuntCache(cache_path, self.thunt_cache)
                saveChunkCache(cache_path, self.chunk_cache)
                # make sure commandBlockOutput is false.
                root_tag = nbt.load(self.world.filename)
                root_tag['Data']['GameRules'][
                    'commandBlockOutput'].value = 'false'
                root_tag.save(self.world.filename)
            else:
                print "Skipping save! (--write disabled)"

            result = True

        return result

    # identify a free and available chunk. Returns absolute world coords
    # if given previous position, keep it in line with that
    def findlandmarklocation(self, previous=None):
        positions = {}
        sorted_p = []
        world = self.world
        if self.args.debug:
            print 'Filtering possible chunks...'
        # At this point, we should exclude ExtremeHills biomes XXXX
		# Also exclude items not in NSEW lines from previous, if set
        for key, value in self.good_chunks.iteritems():
            d = 2^64
            if previous is not None:
                if(( key[0] == (previous.x>>4) )
                    and (key[1] == (previous.z>>4))
                ):
                    continue
                if((key[0] != (previous.x >> 4))
                    and( key[1] != (previous.z >> 4))
                    and( abs(key[1]-(previous.z>>4)) != abs(key[0]-(previous.x>>4)) )
                ):
                    continue
                dist = max(abs(key[0] - (previous.x >> 4)),abs(key[1] - (previous.z >> 4)))
                if (dist < self.min_distance) or (dist > self.max_distance):
                    continue
                for lm in self.landmarks:
                    dpos = Vec(lm.pos.x>>4,0,lm.pos.z>>4)
                    d = min(d, (dpos - Vec(key[0],0,key[1])).mag2d())
            if d >= self.min_distance:
                positions[key] = 1

        if (cfg.maximize_distance and len(self.thunt_cache) > 0):
            if self.args.debug:
                print 'Marking distances...'
            for key in positions.keys():
                d = 2 ^ 64
                chunk = Vec(key[0], 0, key[1])
                for thunt in self.thunt_cache:
                    (x, z) = thunt.split(",")
                    dpos = Vec(int(x) >> 4, 0, int(z) >> 4)
                    d = min(d, (dpos - chunk).mag2d())
                    try:
                        tileEntity = self.thunt_cache[thunt]
                        if tileEntity is not True:
                            info = decodeTHuntInfo(tileEntity)
                            for lm in info['landmarks']:
                                dpos = Vec(lm.x>>4,0,lm.z>>4)
                                d = min(d, (dpos - chunk).mag2d())
                    except:
                        #print 'Invalid treasure hunt cache item ignored.'
                        pass
                for lm in self.landmarks:
                    dpos = Vec(lm.pos.x>>4,0,lm.pos.z>>4)
                    d = min(d, (dpos - chunk).mag2d())
                positions[key] = d

            sorted_p = sorted(positions.iteritems(),
                              reverse=True,
                              key=operator.itemgetter(1))
        else:
            sorted_p = positions.items()
            random.shuffle(sorted_p)

        all_chunks = set(positions.keys())

        # Offset is fill caves. Expand the size of the start location if fill_caves is
        # set. When recording the position, we'll center the chunk in this
        # area.
        offset = 0
        #if self.dinfo['fill_caves']:
        #    offset = 2
        for p, d in sorted_p:
            d_chunks = set()
            for x in xrange(1 + offset):
                for z in xrange(1 + offset):
                    d_chunks.add((p[0] + x, p[1] + z))
            if d_chunks.issubset(all_chunks):
                # is this chunk valid?  Check for too steep, water, lava
                chunk = world.getChunk(p[0],p[1])
                miny = 256
                maxy = -256
                hasliquid = False
                for x in xrange(16):
                    for z in xrange(16):
                        y = chunk.HeightMap[x,z]
                        #print '  check - x,z = y %d,%d = %d'%(x,z,y)
                        while y>-64 and chunk.Blocks[x,z,y] not in heightmap_solids:
                            mat = chunk.Blocks[x,z,y]
                            if mat in (materials.Lava.val,
                                       materials.Water.val,
                                       materials.StillWater.val):
                                hasliquid = True
                            y = y - 1
                        #print '  check - x,z = y %d,%d = %d'%(x,z,y)
                        miny = min(miny,y)
                        maxy = max(maxy,y)

                # avoid anywhere not flat enough
                if (maxy - miny) > 4:
                    if self.args.debug:
                        print 'Reject: %d,%d: flatness = %d ' % (p[0],p[1], maxy - miny)
                    continue
                # avoid liquids
                if hasliquid is True:
                    if self.args.debug:
                        print 'Reject: %d,%d: has liquids.' % (p[0],p[1])
                    continue
                if self.args.debug:
                    print 'Found: ', p
                pos = Vec(p[0]<<4, miny, p[1]<<4)
                if self.args.debug:
                    self.worldmap(world, positions, note = pos)
                del(self.good_chunks[p])
                return pos
        return None

    def findlocation (self):
        if self.args.debug:
            print 'Selecting a start location...'
        p = self.findlandmarklocation()
        if p is not None:
            self.position = p
            self.position.y -= 20;
            if self.args.debug:
                print 'Final: ', self.position
            return True
        if self.args.debug:
            print 'No positions', p
        return False

    def genlandmarks(self):
        # Generate the landmarks, one per step
        # when a chunk is chosen, identify height of chunk centre.
        count = self.steps
        self.pm.init(count, label='Creating landmarks:')
        pos = None
        for s in xrange( self.steps ):
            self.pm.update_left(count)
            if pos is None:
                pos = Vec(self.position.x, self.position.y, self.position.z)
            else:
                pos = self.findlandmarklocation(previous=pos)
            if pos is not None:
                # float to surface
                try:
                    chunk = self.world.getChunk(pos.x>>4, pos.z>>4)
                except:
                    self.steps -= count
                    break
                y = chunk.HeightMap[8,8] - 1
                while (y > -64 and
                       chunk.Blocks[8, 8, y] not in heightmap_solids):
                   y = y - 1
                pos.y = min(y, self.world.Height)
				# print 'placed [%d,%d,%d]' % (pos.x, pos.y, pos.z)
                lm = landmarks.pickLandmark( self, pos  ) 
                self.landmarks.append( lm )
                #del(self.good_chunks[Vec(pos.x>>4,0,pos.z>>4)])
            else:
                self.steps -= count
                break
            count -= 1

        self.pm.set_complete()
        print 'Placed %d landmarks.' % ( self.steps )
        if self.args.debug:
            for lm in self.landmarks:
                print '  %d, %d: %s' % ( lm.pos.x, lm.pos.z, lm.describe() )
            print 'Complete'

    def placechests(self, level=0):
        # Place chests, create clue books and keys
        _directions = (
            ( 'Wander {D} til ye find {L}, which be the next step in thy search.', 1 ),
            ( 'Walk as the crow flies {D} without rest until ye find {L}.', 1 ),
            ( 'Travel towards the {D} to {L}, then follow the next step.', 1 ),
            ( 'I hid the next step at {L}, {D} of here.', 1 ),
            ( 'Find {L} to the {D}, and be wary of zombies as ye travel.', 1 ),
            ( 'Now walk ye {D}, and do keep thy eyes peeled for {L}.', 1 ),
            ( 'To the {D} there do lie {L}.  Thy next step be to find it.', 1 ),
            ( 'There do lie {L} to the {D}, and that is where ye must needs go next.', 1 ),
            ( 'Turn ye to the {D}, and march forrard \'til ye find {L}.', 1),
        )
        # Iterate through the landmarks from the end back.
        # Generate a clue book and possible key as we go as extra chest loot.
        # At each location, randomly either make a chest and store items or
        # continue one.
        fromstep=1
        tostep=1
        pages = []
        pages.append( self.dungeon_name )
        # If necessary, we create a key to lock the chests with
        if cfg.th_locked is True:
            keyname = self.keyName()
            print "Creating key: %s" % ( keyname )
            chestkey = nbt.TAG_Compound()
            chestkey['Count'] = nbt.TAG_Byte(1)
            chestkey['id'] = nbt.TAG_String('minecraft:stick') # ID 280
            chestkey['tag'] = nbt.TAG_Compound()
            chestkey['tag']['Unbreakable'] = nbt.TAG_Byte(1) 
            chestkey['tag']['display'] = nbt.TAG_Compound()
            chestkey['tag']['display']['Name'] = nbt.TAG_String( keyname )
            chestkey['tag']['display']['Lore'] = nbt.TAG_List()
            chestkey['tag']['display']['Lore'].append( nbt.TAG_String( '"Key found with treasure map"' ) )
        else:
            keyname = None

        # fromstep = step where we're placing the clue chest
        # tostep = step we are calculating clue for relative to tostep-1
        # There are 1-based but the landmarks[] array is 0-based.
        # If we place an intermediate chest, fromstep is changed else stays as 1
        self.pm.init(self.steps, label='Placing chests:')
        while tostep < self.steps:
            self.pm.update_left(self.steps - tostep)
            tostep += 1
            if self.args.debug:
                print 'Processing step %d' % ( tostep )
            if self.landmarks[tostep-2].pos.z < self.landmarks[tostep-1].pos.z:
                direction = 'South'
            elif self.landmarks[tostep-2].pos.z > self.landmarks[tostep-1].pos.z:
                direction = 'North'
            else:
                direction = ''
            if self.landmarks[tostep-2].pos.x < self.landmarks[tostep-1].pos.x:
                direction = '%sEast' % ( direction )
            elif self.landmarks[tostep-2].pos.x > self.landmarks[tostep-1].pos.x:
                direction = '%sWest' % ( direction )
            landmark_name = self.landmarks[tostep-1].describe()
            p = weighted_choice(_directions).format(D=direction,L=landmark_name)
            if self.args.debug:
                print "%d: %d, %d, %d\n   %s" % ( tostep-1, self.landmarks[tostep-1].pos.x, 
                    self.landmarks[tostep-1].pos.y, self.landmarks[tostep-1].pos.z, p )
            pages.append( p )
            if tostep == self.steps:
                break
            thistier = int(tostep*loottable._maxtier/self.steps)
            if self.args.debug:
                print "Tier: %d * %d / %d = %d" % ( loottable._maxtier, tostep, self.steps, thistier )
            if random.randint(1,100) > cfg.th_intermediate:
                if random.randint(1,100) < cfg.th_bonus:
                    if self.args.debug:
                        print "Adding a bonus treasure chest at step %d, tier %d" % ( tostep, thistier)
                    self.landmarks[tostep-1].addcluechest(tier=thistier)
                continue
			# save book and restart 
            self.landmarks[tostep-1].addchest(name=self.dungeon_name,tier=thistier,locked=keyname)
            if self.args.debug:
                print 'Placed an intermediate clue chest at step %d, tier %d' % ( tostep, thistier )
                print 'Location: %s' % ( self.landmarks[tostep-1].chestlocdesc() )
            pages.append( 'When ye reach this place, seek ye another clue %s.' 
                % ( self.landmarks[tostep-1].chestlocdesc() ) )
            if cfg.th_locked is True:
                pages.append( 'But take ye heed -- tis only %s as can open the chest.' % ( keyname ) )
            cluebook_tag = nbt.TAG_Compound()
            cluebook_tag['title'] = nbt.TAG_String( self.dungeon_name )
            cluebook_tag['author'] = nbt.TAG_String(self.owner)
            cluebook_tag['pages'] = nbt.TAG_List()
            for p in pages:
                cluebook_tag['pages'].append(nbt.TAG_String(encodeJSONtext(p)))
            cluebook = nbt.TAG_Compound()
            cluebook['Count'] = nbt.TAG_Byte(1)
            cluebook['id'] = nbt.TAG_String('minecraft:written_book')
            cluebook['Damage'] = nbt.TAG_Short(0)
            cluebook['tag'] = cluebook_tag
            # write clue for this stage
            if fromstep == 1:
                self.landmarks[fromstep-1].addcluechest(name=self.dungeon_name,tier=0)
                self.landmarks[fromstep-1].addcluechestitem_tag(cluebook)
                if cfg.th_locked is True:
                    self.landmarks[fromstep-1].addcluechestitem_tag(chestkey)
            else:
                self.landmarks[fromstep-1].addchestitem_tag(cluebook)
            if self.args.debug:
                print 'Placed a clue chest at step %d!' % ( fromstep )
            fromstep = tostep
            pages = []
            pages.append( self.dungeon_name )

        # write treasure
        self.landmarks[tostep-1].addchest(name=self.dungeon_name,tier=loottable._maxtier,locked=keyname)
        if self.args.debug:
            print 'Placed a treasure chest at step %d, tier %d!' % ( tostep, loottable._maxtier )
            print 'Location: %s' % ( self.landmarks[tostep-1].chestlocdesc() )
        pages.append( 'Now that ye have reached thy destination, ye may find the treasure %s.' 
            % ( self.landmarks[tostep-1].chestlocdesc() ) )
        if cfg.th_locked is True:
            pages.append( 'Take heed!  For \'tis only %s that can open the chest that holds my treasure.' % ( keyname ) )
        cluebook_tag = nbt.TAG_Compound()
        cluebook_tag['title'] = nbt.TAG_String( self.dungeon_name )
        cluebook_tag['author'] = nbt.TAG_String(self.owner)
        cluebook_tag['pages'] = nbt.TAG_List()
        for p in pages:
            cluebook_tag['pages'].append(nbt.TAG_String(encodeJSONtext(p)))
        cluebook = nbt.TAG_Compound()
        cluebook['Count'] = nbt.TAG_Byte(1)
        cluebook['id'] = nbt.TAG_String('minecraft:written_book')
        cluebook['Damage'] = nbt.TAG_Short(0)
        cluebook['tag'] = cluebook_tag
        # write clue for this stage
        if fromstep == 1:
            self.landmarks[fromstep-1].addcluechest(name=self.dungeon_name,tier=0)
            self.landmarks[fromstep-1].addcluechestitem_tag(cluebook)
            if cfg.th_locked is True:
                self.landmarks[fromstep-1].addcluechestitem_tag(chestkey)
        else:
            self.landmarks[fromstep-1].addchestitem_tag(cluebook)
        if self.args.debug:
            print 'Placed a clue chest at step %d!' % ( fromstep )
        self.pm.set_complete()

    def placespawners(self, level=0):
        self.pm.init(self.steps, label='Placing spawners:')
        count = self.steps
        for lm in self.landmarks:
            count -= 1
            self.pm.update_left(count)
            loc = lm.spawnerloc()
            if loc is None:
                continue
            loc = lm.offset + loc
            self.setblock(loc, materials.Spawner)
            entity = weighted_choice(cfg.master_landmark_mobs)
            root_tag = self.getspawnertags(entity, tier=1, loc=loc)
            self.tile_ents[loc] = root_tag
            print root_tag
        self.pm.set_complete()

    def renderlandmarks(self):
        '''Call render() on all landmarks to populate the block buffer'''
        count = len(self.landmarks)
        self.pm.init(count, label='Rendering landmarks:')
        for lm in self.landmarks:
            self.pm.update_left(count)
            count -= 1
            lm.render()
        self.pm.set_complete()
