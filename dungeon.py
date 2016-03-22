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
import rooms
import halls
import hall_traps
import floors
import features
import ruins
import pmeter
import namegenerator
import flaggenerator
import inventory
from utils import *
from disjoint_set import DisjointSet
from pymclevel import nbt
from overviewer_core import cache
from overviewer_core import world as ov_world


class Block(object):

    def __init__(self, loc):
        self.loc = loc
        self.material = None
        self.data = 0
        # Blank blocks are just drawn blank on the map
        self.blank = False
        # Hidden blocks are "see-though" on the map
        self.hide = False
        # Locked blocks cannot be overwritten later
        self.lock = False
        # Soft blocks are only rendered if the world block is air
        self.soft = False


class MazeCell(object):
    states = enum('BLANK', 'USED', 'CONNECTED', 'RESTRICTED')

    def __init__(self, loc):
        self.loc = loc
        self.depth = 0
        self.state = 0


class RelightHandler(object):
    _curr = 28
    _count = 0

    def __init__(self):
        self.pm = pmeter.ProgressMeter()
        self.pm.init(self._curr, label='Relighting chunks:')

    def write(self, buff=''):
        if 'Pass' in buff:
            self._curr -= 1
            self.pm.update_left(self._curr)

    def flush(self):
        pass

    def done(self):
        self.pm.set_complete()


class Dungeon (object):

    def __init__(self,
                 args,
                 world,
                 oworld,
                 chunk_cache,
                 dungeon_cache,
                 good_chunks,
                 mapstore):
        self.caches = []
        self.caches.append(cache.LRUCache(size=100))

        self.world = world
        self.oworld = oworld
        self.chunk_cache = chunk_cache
        self.dungeon_cache = dungeon_cache
        self.good_chunks = good_chunks
        self.mapstore = mapstore
        self.inventory = inventory.new(mapstore)
        self.pm = pmeter.ProgressMeter()
        self.rooms = {}
        self.halls = []
        self.hall_traps = []
        self.blocks = {}
        self.tile_ents = {}
        self.ents = []
        self.placed_items = []
        self.torches = {}
        self.doors = {}
        self.entrance = None
        self.entrance_pos = Vec(0, 0, 0)
        self.maze = {}
        self.stairwells = []
        self.room_size = 16
        self.room_height = 6
        self.doormaterial = materials.WoodenDoor
        self.position = Vec(0, 0, 0)
        self.args = args
        self.dinfo = {}
        self.dinfo['fill_caves'] = cfg.fill_caves
        self.dinfo['portal_exit'] = cfg.portal_exit
        self.dinfo['dungeon_name'] = cfg.dungeon_name

    def generate(self, cache_path, version):
        '''Generate a dungeon'''
        # Pick a starting size.
        self.xsize = randint(cfg.min_x, cfg.max_x)
        self.zsize = randint(cfg.min_z, cfg.max_z)
        self.levels = randint(cfg.min_levels, cfg.max_levels)

        located = False
        result = False
        # Find a location, if we can.
        # Manual location
        if cfg.offset is not '':
            print 'Dungeon size: {0} x {1} x {2}'.format(self.xsize,
                                                         self.zsize,
                                                         self.levels)

            self.position = str2Vec(cfg.offset)
            self.position.x = self.position.x & ~15
            self.position.z = self.position.z & ~15
            # Bury it if we need to
            located = self.bury(manual=bool(cfg.bury == False))
            if (located == False):
                print 'Unable to bury a dungeon of requested depth at', self.position
                print 'Try fewer levels, or a smaller size, or another location.'
                sys.exit(1)
            print "Location set to: ", self.position
        # Search for a location.
        else:
            print "Searching for a suitable location..."
            while (located is False):
                located = self.findlocation()
                if (located is False):
                    # Scale. Start with the largest axis and work down.
                    adjusted = False
                    while (
                        self.xsize > cfg.min_x or
                        self.zsize > cfg.min_z or
                        self.levels > cfg.min_levels
                    ):
                        # X Z L
                        if (
                            self.xsize >= self.zsize and
                            self.zsize >= self.levels
                        ):
                            if self.xsize > cfg.min_x:
                                self.xsize -= 1
                                adjusted = True
                            elif self.zsize > cfg.min_z:
                                self.zsize -= 1
                                adjusted = True
                            elif self.levels > cfg.min_levels:
                                self.levels -= 1
                                adjusted = True
                        # X L Z
                        elif (
                            self.xsize >= self.levels and
                            self.levels >= self.zsize
                        ):
                            if self.xsize > cfg.min_x:
                                self.xsize -= 1
                                adjusted = True
                            elif self.levels > cfg.min_levels:
                                self.levels -= 1
                                adjusted = True
                            elif self.zsize > cfg.min_z:
                                self.zsize -= 1
                                adjusted = True
                        # Z X L
                        elif (
                            self.zsize >= self.xsize and
                            self.xsize >= self.levels
                        ):
                            if self.zsize > cfg.min_z:
                                self.zsize -= 1
                                adjusted = True
                            elif self.xsize > cfg.min_x:
                                self.xsize -= 1
                                adjusted = True
                            elif self.levels > cfg.min_levels:
                                self.levels -= 1
                                adjusted = True
                        # Z L X
                        elif (
                            self.zsize >= self.levels and
                            self.levels >= self.xsize
                        ):
                            if self.zsize > cfg.min_z:
                                self.zsize -= 1
                                adjusted = True
                            elif self.levels > cfg.min_levels:
                                self.levels -= 1
                                adjusted = True
                            elif self.xsize > cfg.min_x:
                                self.xsize -= 1
                                adjusted = True
                        # L X Z
                        elif (
                            self.levels >= self.xsize and
                            self.xsize >= self.zsize
                        ):
                            if self.levels > cfg.min_levels:
                                self.levels -= 1
                                adjusted = True
                            elif self.xsize > cfg.min_x:
                                self.xsize -= 1
                                adjusted = True
                            elif self.zsize > cfg.min_z:
                                self.zsize -= 1
                                adjusted = True
                        # L Z X
                        elif (
                            self.levels >= self.zsize and
                            self.zsize >= self.xsize
                        ):
                            if self.levels > cfg.min_levels:
                                self.levels -= 1
                                adjusted = True
                            elif self.zsize > cfg.min_z:
                                self.zsize -= 1
                                adjusted = True
                            elif self.xsize > cfg.min_x:
                                self.xsize -= 1
                                adjusted = True

                    if (adjusted is False):
                        print 'Unable to place any more dungeons.'
                        break
                else:
                    print 'Dungeon size: {0} x {1} x {2}'.format(self.xsize,
                                                                 self.zsize,
                                                                 self.levels)
                    print "Location: ", self.position
        # Generate!
        if (located is True):
            # We have a final size, so let's initialize some things.
            for x in xrange(self.xsize):
                for y in xrange(self.levels):
                    for z in xrange(self.zsize):
                        self.maze[Vec(x, y, z)] = MazeCell(Vec(x, y, z))
            self.halls = [[[[None, None, None, None] for z in
                            xrange(self.zsize)] for y in
                           xrange(self.levels)] for x in
                          xrange(self.xsize)]

            self.heightmap = numpy.zeros((self.xsize * self.room_size,
                                          self.zsize * self.room_size))

            # Set the seed if requested.
            if (self.args.seed is not None):
                seed(self.args.seed)
                print 'Seed:', self.args.seed

            # Now we know the biome, we can setup a name generator
            self.namegen = namegenerator.namegenerator(self.biome)
            print 'Theme:', self.namegen.theme
            self.owner = self.namegen.genroyalname()
            print 'Owner:', self.owner

            # And generate a unique flag
            self.flagdesign = flaggenerator.generateflag()
            self.inventory.SetDungeonFlag(self.flagdesign)

            # Pick a common door material for the dungeon
            self.doormaterial = choice(
                [
                    materials.WoodenDoor,
                    materials.SpruceDoor,
                    materials.BirchDoor,
                    materials.JungleDoor,
                    materials.DarkOakDoor,
                    materials.AcaciaDoor,
                ]
            )

            print "Generating rooms..."
            self.genrooms()
            print "Generating halls..."
            self.genhalls()
            print "Generating floors..."
            self.genfloors()
            print "Generating features..."
            self.genfeatures()
            if self.args.command != 'regenerate':
                print "Generating ruins..."
                self.genruins()
                self.setentrance()
            else:
                self.entrance.height = self.args.entrance_height
            # Name this place
            if self.owner.endswith("s"):
                owners = self.owner + "'"
            else:
                owners = self.owner + "'s"
            self.dungeon_name = self.dinfo['dungeon_name'].format(
                owner=self.owner,
                owners=owners)
            self.dinfo['full_name'] = self.dungeon_name
            print "Dungeon name:", self.dungeon_name
            print "Finding secret rooms..."
            self.findsecretrooms()
            self.renderruins()
            self.renderrooms()
            self.renderhalls()
            self.renderfloors()
            self.renderfeatures()
            print "Generating hall traps..."
            self.genhalltraps()
            self.renderhalltraps()
            self.processBiomes()
            print "Placing doors..."
            self.placedoors(cfg.doors)
            print "Placing torches..."
            self.placetorches()
            print "Placing chests..."
            self.placechests()
            print "Placing spawners..."
            self.placespawners()

            # Signature
            self.setblock(Vec(0, 0, 0), materials.Chest, 0, hide=True)
            self.tile_ents[Vec(0, 0, 0)] = encodeDungeonInfo(self,
                                                             version)
            # Add to the dungeon cache.
            key = key = '%s,%s' % (
                self.position.x,
                self.position.z,
            )
            #self.dungeon_cache[key] = self.tile_ents[Vec(0,0,0)]
            self.dungeon_cache[key] = 1

            # Generate maps
            if (self.args.write and cfg.maps > 0):
                print "Generating maps..."
                self.generatemaps()
            print "Placing special items..."
            self.placeitems()

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
                saveDungeonCache(cache_path, self.dungeon_cache)
                saveChunkCache(cache_path, self.chunk_cache)
                # make sure commandBlockOutput is false.
                root_tag = nbt.load(self.world.filename)
                root_tag['Data']['GameRules'][
                    'commandBlockOutput'].value = 'false'
                root_tag.save(self.world.filename)
            else:
                print "Skipping save! (--write disabled)"

            if (self.args.html is not None):
                self.outputhtml()

            if (self.args.term is not None):
                self.outputterminal()

            result = True

        return result

    def printmaze(self, y, cursor=None):
        for z in xrange(self.zsize):
            line = u''
            for x in xrange(self.xsize):
                p = Vec(x, y, z)
                if p in self.rooms:
                    if self.halls[x][y][z][0] == 1:
                        line += (u'\u2554\u2569\u2557')
                    else:
                        line += (u'\u2554\u2550\u2557')
                else:
                    line += (u'\u2591\u2591\u2591')
            print line
            line = u''
            for x in xrange(self.xsize):
                p = Vec(x, y, z)
                if p in self.rooms:
                    if self.halls[x][y][z][3] == 1:
                        line += (u'\u2563')
                    else:
                        line += (u'\u2551')
                    if (cursor == p):
                        line += (u'X')
                    elif self.maze[p].state == MazeCell.states.CONNECTED:
                        line += (u' ')
                    elif self.maze[p].state == MazeCell.states.USED:
                        line += (u'U')
                    else:
                        line += (u'R')
                    if self.halls[x][y][z][1] == 1:
                        line += (u'\u2560')
                    else:
                        line += (u'\u2551')
                else:
                    line += (u'\u2591\u2591\u2591')
            print line
            line = u''
            for x in xrange(self.xsize):
                p = Vec(x, y, z)
                if p in self.rooms:
                    if self.halls[x][y][z][2] == 1:
                        line += (u'\u255a\u2566\u255d')
                    else:
                        line += (u'\u255a\u2550\u255d')
                else:
                    line += (u'\u2591\u2591\u2591')
            print line
            line = u''
        raw_input('continue...')

    def setblock(
            self,
            loc,
            material,
            data=0,
            hide=False,
            lock=False,
            soft=False,
            blank=False):
        # If material is None, remove this block
        if material is None:
            if loc in self.blocks:
                del(self.blocks[loc])
            return

        # Build a block if we need to
        if loc not in self.blocks:
            self.blocks[loc] = Block(loc)

        if (loc.x >= 0 and
                loc.z >= 0 and
                loc.x < self.xsize * self.room_size and
                loc.z < self.zsize * self.room_size):
            self.heightmap[loc.x][loc.z] = min(loc.y,
                                               self.heightmap[loc.x][loc.z])

        # If the existing block is locked, abort
        # Unless we are requesting a locked block
        if self.blocks[loc].lock and lock == False:
            return

        # Setup the material
        self.blocks[loc].material = material

        # Set the data value
        if (data == 0):
            self.blocks[loc].data = material.data
        else:
            self.blocks[loc].data = data

        # Hide this from the map generator if requested
        self.blocks[loc].hide = hide

        # Lock it
        self.blocks[loc].lock = lock

        # Soft blocks are only drawn when the world block is air
        self.blocks[loc].soft = soft

        # Blank blocks alway show as an empty cell.
        self.blocks[loc].blank = blank

    def delblock(self, loc):
        if loc in self.blocks:
            del self.blocks[loc]

    def getblock(self, loc):
        if loc in self.blocks:
            return self.blocks[loc].material
        return False

    def findlocation(self):
        positions = {}
        sorted_p = []
        world = self.world
        if self.args.debug:
            print 'Filtering for depth...'
        for key, value in self.good_chunks.iteritems():
            if value >= (self.levels + 1) * self.room_height:
                positions[key] = value

        if (cfg.maximize_distance and len(self.dungeon_cache) > 0):
            if self.args.debug:
                print 'Marking distances...'
            for key in positions.keys():
                d = 2 ^ 64
                chunk = Vec(key[0], 0, key[1])
                for dungeon in self.dungeon_cache:
                    (x, z) = dungeon.split(",")
                    dpos = Vec(int(x) >> 4, 0, int(z) >> 4)
                    d = min(d, (dpos - chunk).mag2d())
                positions[key] = d

            sorted_p = sorted(positions.iteritems(),
                              reverse=True,
                              key=operator.itemgetter(1))
        else:
            sorted_p = positions.items()
            random.shuffle(sorted_p)

        if self.args.debug:
            print 'Selecting a location...'
        all_chunks = set(positions.keys())
        # Offset is fill caves. Expand the size of the dungeon if fill_caves is
        # set. When recording the position, we'll center the dungeon in this
        # area.
        offset = 0
        if self.dinfo['fill_caves']:
            offset = 10
        for p, d in sorted_p:
            d_chunks = set()
            for x in xrange(self.xsize + offset):
                for z in xrange(self.zsize + offset):
                    d_chunks.add((p[0] + x, p[1] + z))
            if d_chunks.issubset(all_chunks):
                if self.args.debug:
                    print 'Found: ', p
                self.position = Vec((p[0] + (offset / 2)) * self.room_size,
                                    0,
                                    (p[1] + (offset / 2)) * self.room_size)
                if self.args.debug:
                    print 'Final: ', self.position
                if self.bury():
                    self.worldmap(world, positions)
                    return True
        if self.args.debug:
            print 'No positions', p
        return False

    def worldmap(self, world, positions, note=None):
        #rows, columns = os.popen('stty size', 'r').read().split()
        columns = 39
        bounds = world.bounds
        if self.args.spawn is None:
            scx = world.playerSpawnPosition()[0] >> 4
            scz = world.playerSpawnPosition()[2] >> 4
        else:
            scx = self.args.spawn[0]
            scz = self.args.spawn[1]
        spawn_chunk = Vec(scx, 0, scz)
        if note is not None:
            note_chunk = Vec( note.x >> 4, 0, note.z >> 4 )
        else:
            note_chunk = Vec(0,0,0)
        # Draw a nice little map of the dungeon location
        map_min_x = bounds.maxcx
        map_max_x = bounds.mincx
        map_min_z = bounds.maxcz
        map_max_z = bounds.mincz
        for p in self.good_chunks:
            map_min_x = min(map_min_x, p[0] + 1)
            map_max_x = max(map_max_x, p[0] - 1)
            map_min_z = min(map_min_z, p[1] + 1)
            map_max_z = max(map_max_z, p[1] - 1)

        # Include spawn
        map_min_x = min(map_min_x, spawn_chunk.x)
        map_max_x = max(map_max_x, spawn_chunk.x)
        map_min_z = min(map_min_z, spawn_chunk.z)
        map_max_z = max(map_max_z, spawn_chunk.z)

        if map_max_x - map_min_x + 1 >= int(columns):
            print 'Map too wide for terminal:', map_max_x - map_min_x
            return

        sx = self.position.x / self.room_size
        sz = self.position.z / self.room_size
        if self.args.debug:
            print 'spos:', Vec(sx, 0, sz)
        d_box = Box(Vec(sx, 0, sz), self.xsize, world.Height, self.zsize)

        for z in xrange(map_min_z - 1, map_max_z + 2):
            for x in xrange(map_min_x - 1, map_max_x + 2):
                if (Vec(x, 0, z) == spawn_chunk):
                    sys.stdout.write('SS')
                elif (x == 0 and z == 0):
                    sys.stdout.write('00')
                elif (Vec(x, 0, z) == Vec(sx, 0, sz)):
                    sys.stdout.write('XX')
                elif (Vec(x, 0, z) == note_chunk):
                    sys.stdout.write('@@')
                elif (d_box.containsPoint(Vec(x, 64, z))):
                    sys.stdout.write('##')
                elif ((x, z) in positions.keys()):
                    sys.stdout.write('++')
                elif ((x, z) in self.good_chunks.keys()):
                    sys.stdout.write('--')
                else:
                    sys.stdout.write('``')
            print

    def bury(self, manual=False):
        if self.args.debug:
            print 'Burying dungeon...'
        min_depth = (self.levels + 1) * self.room_height

        d_chunks = set()
        p = (self.position.x / self.room_size,
             self.position.z / self.room_size)
        for x in xrange(self.xsize):
            for z in xrange(self.zsize):
                d_chunks.add((p[0] + x, p[1] + z))

        # Calaculate the biome
        biomes = {}
        rset = self.oworld.get_regionset(None)
        for chunk in d_chunks:
            cdata = rset.get_chunk(chunk[0], chunk[1])
            key = numpy.argmax(numpy.bincount((cdata['Biomes'].flatten())))
            if key in biomes:
                biomes[key] += 1
            else:
                biomes[key] = 1
            self.biome = max(biomes, key=lambda k: biomes[k])
        if self.args.debug:
            print 'Biome: ', self.biome

        depth = self.world.Height
        for chunk in d_chunks:
            if (chunk not in self.good_chunks):
                d1 = findChunkDepth(Vec(chunk[0], 0, chunk[1]), self.world)
                self.good_chunks[chunk] = d1
            else:
                d1 = self.good_chunks[chunk]
            d1 -= 2
            if not manual:
                # Too shallow
                if (d1 < min_depth):
                    return False
                # Too high
                elif (d1 > self.world.Height - 27):
                    return False

            depth = min(depth, d1)

        if not manual:
            self.position = Vec(self.position.x,
                                depth,
                                self.position.z)
        return True

    def snow(self, pos, limit=16):
        b = self.getblock(pos)
        if (b and b != materials.Air):
            return

        count = 1
        b = self.getblock(pos.down(count))
        while (count <= limit and (b == False or b == materials.Air)):
            count += 1
            b = self.getblock(pos.down(count))

        if count > limit:
            return

        if not b:
            soft = True
        else:
            soft = False
        if self.getblock(pos.down(count)).val in materials.heightmap_solids:
            self.setblock(pos.down(count - 1), materials.Snow, soft=soft)
            # print 'snow placed: ',pos.down(count-1), soft

    def vines(self, pos, grow=False):
        # Data values (1.9p5)
        # 1 - South
        # 2 - West
        # 4 - North
        # 8 - East
        b = self.getblock(pos)
        # Something here already
        if (b and b != materials.Air):
            return

        if not b:
            soft = True
        else:
            soft = False

        # Look around for something to attach to
        data = 0
        b = self.getblock(pos.s(1))
        if (b and b.val in materials.vine_solids):
            data += 1
        b = self.getblock(pos.w(1))
        if (b and b.val in materials.vine_solids):
            data += 2
        b = self.getblock(pos.n(1))
        if (b and b.val in materials.vine_solids):
            data += 4
        b = self.getblock(pos.e(1))
        if (b and b.val in materials.vine_solids):
            data += 8
        # Nothing to attach to
        if data == 0:
            return
        self.setblock(pos, materials.Vines, data, soft=soft)
        if not grow:
            return
        pos = pos.down(1)
        b = self.getblock(pos)
        while ((b == False or b == materials.Air) and random.randint(1, 100) < 75):
            if not b:
                soft = True
            else:
                soft = False
            self.setblock(pos, materials.Vines, data, soft=soft)
            pos = pos.down(1)
            b = self.getblock(pos)

    def cobwebs(self, c1, c3):
        '''Grow cobwebs in a volume. They concentrate at the top, and are more
        likely to appear in air blocks bound by multiple solid blocks.'''
        webs = {}
        top = min(c1.y, c3.y)
        for p in iterate_cube(c1, c3):
            if (p not in self.blocks or
                    self.blocks[p].material != materials.Air):
                continue
            count = 0
            chance = 80 - (p.y - top) * 14
            for q in (Vec(1, 0, 0), Vec(-1, 0, 0),
                      Vec(0, 1, 0), Vec(0, -1, 0),
                      Vec(0, 0, 1), Vec(0, 0, -1)):
                if (p + q in self.blocks and
                        self.blocks[p + q].material != materials.Air and
                        random.randint(1, 100) <= chance):
                    count += 1
            if count >= 3:
                webs[p] = True
        for p, q in webs.items():
            self.setblock(p, materials.Cobweb)

    def processBiomes(self):
        '''Add vines and snow according to biomes.'''
        rset = self.oworld.get_regionset(None)
        r = ov_world.CachedRegionSet(rset, self.caches)
        wp = Vec(self.position.x, 0, self.position.z)
        count = self.xsize * 16 * self.zsize * 16
        self.pm.init(count, label='Processing biomes:')
        for p in iterate_cube(Vec(0, 0, 0),
                              Vec(self.xsize * 16 - 1, 0, self.zsize * 16 - 1)):
            self.pm.update_left(count)
            count -= 1
            cx = (p.x + wp.x) // 16
            cz = (p.z + wp.z) // 16
            chunk = r.get_chunk(cx, cz)
            biome = chunk['Biomes'][p.x % 16][p.z % 16]
            # Vines
            if biome in (6,     # Swampland
                         134,   # Swampland M
                         21,    # Jungle
                         149,   # Jungle M
                         22,    # Jungle Hills
                         23,    # Jungle Edge
                         151,   # Jungle Edge M
                         ):
                h = 0
                try:
                    h = min(self.heightmap[p.x - 1][p.z], h)
                except IndexError:
                    pass
                try:
                    h = min(self.heightmap[p.x + 1][p.z], h)
                except IndexError:
                    pass
                try:
                    h = min(self.heightmap[p.x][p.z - 1], h)
                except IndexError:
                    pass
                try:
                    h = min(self.heightmap[p.x][p.z + 1], h)
                except IndexError:
                    pass
                if h == 0:
                    continue
                for q in iterate_cube(Vec(p.x, h, p.z),
                                      Vec(p.x, 0, p.z)):
                    if random.randint(1, 100) < 20:
                        self.vines(q, grow=True)
            # Snow
            if biome in (10,    # Frozen Ocean
                         11,    # Frozen River
                         12,    # Ice Plains
                         140,   # Ice Plains Spikes
                         13,    # Ice Mountains
                         26,    # Cold Beach
                         30,    # Cold Taiga
                         158,   # Cold Taiga M
                         31,    # Cold Taiga Hills
                         ):
                h = self.heightmap[p.x][p.z]
                if (h < 0):
                    self.snow(Vec(p.x, h - 1, p.z), limit=abs(h - 1))

        self.pm.set_complete()

    def getspawnertags(self, entity):
        # See if we have a custom spawner match
        if entity.lower() in cfg.custom_spawners.keys():
            filepath = cfg.custom_spawners[entity.lower()]
            root_tag = nbt.load(filename=filepath)
            return root_tag
        else:
            root_tag = nbt.TAG_Compound()
            root_tag['SpawnData'] = nbt.TAG_Compound()

        SpawnData = root_tag['SpawnData']

        # Cases where the entity id doesn't match the config
        entity = entity.capitalize()
        if (entity == 'Pigzombie'):
            SpawnData['id'] = nbt.TAG_String('PigZombie')
        elif (entity == 'Cavespider'):
            SpawnData['id'] = nbt.TAG_String('CaveSpider')
        elif (entity == 'Lavaslime'):
            SpawnData['id'] = nbt.TAG_String('LavaSlime')
        elif (entity == 'Witherboss'):
            SpawnData['id'] = nbt.TAG_String('WitherBoss')
        # For everything else the input is the SpawnData id
        else:
            SpawnData['id'] = nbt.TAG_String(entity)

        return root_tag

    def addsign(self, loc, text1, text2, text3, text4):
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Sign')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)

        def JSONformat(text):
            if ( text.startswith('{') == True ):
                return text
            return '{"text":"'+text.replace('"','\"')+'"}'
        root_tag['Text1'] = nbt.TAG_String(JSONformat(text1))
        root_tag['Text2'] = nbt.TAG_String(JSONformat(text2))
        root_tag['Text3'] = nbt.TAG_String(JSONformat(text3))
        root_tag['Text4'] = nbt.TAG_String(JSONformat(text4))
        self.tile_ents[loc] = root_tag

    def addspawner(self, loc, entity='', tier=-1):
        if (entity == ''):
            level = loc.y / self.room_height
            if (cfg.max_mob_tier == 0 or level < 0):
                tier = 0
            elif tier == -1:
                if (self.levels > 1):
                    tier = (float(level) /
                            float(self.levels - 1) *
                            float(cfg.max_mob_tier - 2)) + 1.5
                    tier = int(min(cfg.max_mob_tier - 1, tier))
                else:
                    tier = cfg.max_mob_tier - 1
            entity = weighted_choice(cfg.master_mobs[tier])
            # print 'Spawner: lev=%d, tier=%d, ent=%s' % (level, tier, entity)
        root_tag = self.getspawnertags(entity)
        # Do generic spawner setup
        root_tag['id'] = nbt.TAG_String('MobSpawner')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        try:
            root_tag['Delay']
        except:
            root_tag['Delay'] = nbt.TAG_Short(0)
        # Calculate spawner tags from config
        if tier == cfg.max_mob_tier:
            SpawnCount = cfg.treasure_SpawnCount
            SpawnMaxNearbyEntities = cfg.treasure_SpawnMaxNearbyEntities
            SpawnMinDelay = cfg.treasure_SpawnMinDelay
            SpawnMaxDelay = cfg.treasure_SpawnMaxDelay
            SpawnRequiredPlayerRange = cfg.treasure_SpawnRequiredPlayerRange
        else:
            SpawnCount = cfg.SpawnCount
            SpawnMaxNearbyEntities = cfg.SpawnMaxNearbyEntities
            SpawnMinDelay = cfg.SpawnMinDelay
            SpawnMaxDelay = cfg.SpawnMaxDelay
            SpawnRequiredPlayerRange = cfg.SpawnRequiredPlayerRange
        # But don't overwrite tags from NBT files
        if (SpawnCount != 0):
            try:
                root_tag['SpawnCount']
            except:
                root_tag['SpawnCount'] = nbt.TAG_Short(SpawnCount)
        if (SpawnMaxNearbyEntities != 0):
            try:
                root_tag['MaxNearbyEntities']
            except:
                root_tag['MaxNearbyEntities'] = nbt.TAG_Short(
                    SpawnMaxNearbyEntities)
        if (SpawnMinDelay != 0):
            try:
                root_tag['MinSpawnDelay']
            except:
                root_tag['MinSpawnDelay'] = nbt.TAG_Short(SpawnMinDelay)
        if (SpawnMaxDelay != 0):
            try:
                root_tag['MaxSpawnDelay']
            except:
                root_tag['MaxSpawnDelay'] = nbt.TAG_Short(SpawnMaxDelay)
        if (SpawnRequiredPlayerRange != 0):
            try:
                root_tag['RequiredPlayerRange']
            except:
                root_tag['RequiredPlayerRange'] = nbt.TAG_Short(
                    SpawnRequiredPlayerRange)
        # Finally give the tag to the entity
        self.tile_ents[loc] = root_tag

    def addnoteblock(self, loc, clicks=0):
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Music')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        root_tag['note'] = nbt.TAG_Byte(clicks)
        self.tile_ents[loc] = root_tag

    def addchest(self, loc, tier=-1, loot=[], name='', lock=None):
        level = loc.y / self.room_height
        if (tier < 0):
            if (self.levels > 1):
                tierf = (float(level) /
                         float(self.levels - 1) *
                         float(loottable._maxtier - 2)) + 1.5
                tierf = min(loottable._maxtier - 1, tierf)
            else:
                tierf = loottable._maxtier - 1
            tier = max(1, int(tierf))
        elif tier > loottable._maxtier:
            tier = loottable._maxtier
        if self.args.debug:
            print 'Adding chest: level',level+1,'tier',tier
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Chest')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        if (name != ''):
            root_tag['CustomName'] = nbt.TAG_String(name)
        if (lock is not None and lock != ''):
            root_tag['Lock'] = nbt.TAG_String(lock)
        inv_tag = nbt.TAG_List()
        root_tag['Items'] = inv_tag
        if loot is None:
            loot = []
        elif len(loot) == 0:
            loot = list(loottable.rollLoot(tier, level + 1))
        for i in loot:
            item_tag = self.inventory.buildItemTag(i)
            inv_tag.append(item_tag)
        self.tile_ents[loc] = root_tag

    def addchestitem_tag(self, loc, item_tag):
        '''Add an item to an existing chest'''
        # No chest here!
        if (loc not in self.tile_ents or
                self.tile_ents[loc]['id'].value != 'Chest'):
            return False
        root_tag = self.tile_ents[loc]
        slot = len(root_tag['Items'])
        # Chest is full
        if slot > 26:
            return False
        item_tag['Slot'] = nbt.TAG_Byte(slot)
        root_tag['Items'].append(item_tag)
        return True

    def addchesttrap(self, loc, name=None, count=None):
        name = weighted_choice(cfg.master_chest_traps)
        count = int(cfg.lookup_chest_traps[name][1])
        self.addtrap(loc, name=name, count=count)

    def addtrap(self, loc, name=None, count=None):
        if name is None:
            name = weighted_choice(cfg.master_chest_traps)
        if count is None:
            count = int(cfg.lookup_chest_traps[name][1])
        # sanity check for count
        if count > 9 * 64:
            print '\nFATAL: Item count for dispenser trap too large! Max number of items is 9x64 = 576! Check config file.'
            print 'Item name:', name
            print 'Count:', count
            sys.exit()
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Trap')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        inv_tag = nbt.TAG_List()
        root_tag['Items'] = inv_tag
        # fill slots of dispenser trap
        slot = 0
        while count > 0:
            item_tag = nbt.TAG_Compound()
            item_tag['Slot'] = nbt.TAG_Byte(slot)
            if count > 64:
                item_tag['Count'] = nbt.TAG_Byte(64)
            else:
                item_tag['Count'] = nbt.TAG_Byte(count)
            count -= 64
            item_tag['id'] = nbt.TAG_String(loottable.items.byName(name).id)
            item_tag['Damage'] = nbt.TAG_Short(
                loottable.items.byName(name).data)
            inv_tag.append(item_tag)
            slot += 1
        self.tile_ents[loc] = root_tag

    def adddungeonbanner(self, loc):
        root_tag = get_tile_entity_tags(eid="Banner",Pos=loc,**self.flagdesign)
        self.addtileentity(root_tag)

    def addentity(self, root_tag):
        self.ents.append(root_tag)

    def addtileentity(self, root_tag):
        loc = Vec(
            root_tag['x'].value,
            root_tag['y'].value,
            root_tag['z'].value
        )
        self.tile_ents[loc] = root_tag

    def setroom(self, coord, room):
        if coord not in self.rooms:
            self.rooms[coord] = room
            # print 'setroom:', coord
            return room.placed()
        print 'FATAL: Tried to place a room in a filled location!'
        print coord
        for p in self.rooms.keys():
            print p,
        print
        sys.exit()

    def genrooms(self):
        # Generate the maze used for room and hall placement.
        # stairwells contains the lower half of a stairwell.
        self.stairwells = []
        entrance_pos = None
        exit_pos = None
        # The size of our dungeon. Note this is once less in the depth
        # dimension, because for most of the dungeon we don't want multilevel
        # rooms to extend to the last level.
        dsize = Vec(self.xsize, self.levels - 1, self.zsize)
        # Some convenient lookups.
        # dirs holds vectors for moving in a cardinal direction.
        dirs = {'N': Vec(0, 0, -1),
                'E': Vec(1, 0, 0),
                'S': Vec(0, 0, 1),
                'W': Vec(-1, 0, 0)}
        # sides maps a dir to a room side for hall placement.
        sides = {'N': 0,
                 'E': 1,
                 'S': 2,
                 'W': 3}
        # opposite sides for setting the matching hall in the adjacent room.
        osides = {'N': 2,
                  'E': 3,
                  'S': 0,
                  'W': 1}
        # dkeys holds our valid directions.
        dkeys = dirs.keys()
        # Our maze state flags
        state = MazeCell.states

        # Start in a random location on level 1, unless the -e
        # options was used.
        if (self.args.entrance is not None):
            x = self.args.entrance[0]
            z = self.args.entrance[1]
        else:
            x = random.randint(0, self.xsize - 1)
            z = random.randint(0, self.zsize - 1)

        # A maximum "depth" value. (depth being distance from the level
        # entrance) No one room can be this deep on a single # level.
        maxdepth = self.xsize * self.zsize * self.levels + 1
        # A disjoint set in which to keep our room sets.
        ds = DisjointSet()
        # Generate a maze for each level.
        for y in xrange(self.levels):
            # If we are on the last level, allow rooms on this level. Normally
            # we don't allow rooms to extend to the last level to prevent multi
            # level rooms from crossing the treasure chamber.
            if (y == self.levels - 1):
                dsize = dsize.down(1)
            # The level starts here.
            level_start = Vec(x, y, z)
            # The first cell contains an entrance. This is a tower if we are on
            # level 1, otherwise it's a stairwell.
            if (y == 0):
                # Add the entrance cell to the stairwells list.
                self.stairwells.append(Vec(x, y, z))
                # For all levels except the last level, rooms can be as big as
                # they want. For the last level it has to be 1x1x1.
                maxsize = Vec(10, 18, 10)
                if (y == self.levels - 1):
                    maxsize = Vec(1, 1, 1)
                # Pick an entrance capable room, place it, find the room that
                # contains the actual entrance (for multi-tile rooms) and place
                # the entrance feature there. Record the entrance feature for
                # later use.
                entrance_pos = level_start
                room, pos = rooms.pickRoom(self, dsize, level_start,
                                           entrance=True, maxsize=maxsize)
                ps = self.setroom(pos, room)
                eroom = self.rooms[entrance_pos]
                feature = features.new('entrance', eroom)
                eroom.features.append(feature)
                feature.placed()
                self.entrance = feature
                # Mark cell as connected or used.
                # Cells on this level are marked as connected so we can branch
                # off of them as needed. Cells on other levels are marked as
                # used, so they can be connected to later. Each set of cells on
                # other levels is its own set in the disjoint set so we can
                # mange connections to them later.
                roots = {}
                for p in ps:
                    if p.y == y:
                        self.maze[p].state = state.CONNECTED
                        self.maze[p].depth = maxdepth
                    else:
                        root1 = ds.find(p)
                        if p.y in roots.keys():
                            ds.union(root1, roots[p.y])
                        else:
                            roots[p.y] = root1
                        self.maze[p].state = state.USED
                        self.maze[p].depth = maxdepth
                # Pick a random cell as the current cell.
                p = choice(ps)
                x = p.x
                z = p.z
            else:
                # Any other start cell on a lower level is a stairwell
                self.stairwells.append(Vec(x, y, z))
                maxsize = Vec(10, 18, 10)
                if (y == self.levels - 1):
                    maxsize = Vec(1, 1, 1)
                room, pos = rooms.pickRoom(self, dsize, level_start,
                                           stairwell=True, maxsize=maxsize)
                ps = self.setroom(pos, room)
                eroom = self.rooms[level_start]
                feature = features.new(weighted_choice(cfg.master_stairwells),
                                       eroom)

                eroom.features.append(feature)
                feature.placed()
                roots = {}
                for p in ps:
                    if p.y == y:
                        self.maze[p].state = state.CONNECTED
                        self.maze[p].depth = maxdepth
                    else:
                        root1 = ds.find(p)
                        if p.y in roots.keys():
                            ds.union(root1, roots[p.y])
                        else:
                            roots[p.y] = root1
                        self.maze[p].state = state.USED
                        self.maze[p].depth = maxdepth
                p = choice(ps)
                x = p.x
                z = p.z
                # Upstairs. Override the feature of the room above to blank so
                # it can hold the stairwell.
                posup = level_start.up(1)
                room = self.rooms[posup]
                feature = features.new('blank', room)
                room.features.append(feature)
                feature.placed()
            # If we are on the last level, place a treasure room.
            if (y == self.levels - 1):
                # Try to find a location as far away from the level_start as
                # possible.
                pos = Vec(0, y, 0)
                if (level_start.x < self.xsize / 2):
                    pos.x = self.xsize - 1
                if (level_start.z < self.zsize / 2):
                    pos.z = self.zsize - 1
                exit_pos = pos
                # Pick a treasure capable room
                room, pos = rooms.pickRoom(self, dsize, pos, treasure=True,
                                           room_list=cfg.master_treasure,
                                           default='pitwitharchers')
                ps = self.setroom(pos, room)
                feature = features.new('blank', room)
                room.features.append(feature)
                floor = floors.new('blank', room)
                room.floors.append(floor)
                # Place all these cells into a RESTRICTED set for connection
                # later. These have a depth of zero, since we don't want to
                # count them in the depth calculation. This helps keep shortcuts
                # to the treasure room to a minimum.
                root1 = ds.find(pos)
                for p in ps:
                    root2 = ds.find(p)
                    if root1 != root2:
                        ds.union(root1, root2)
                    self.maze[p].state = state.RESTRICTED
                    if self.maze[p].depth >= 0:
                        self.maze[p].depth = 0
            while True:
                # Walk the maze.
                if self.args.debug:
                    self.printmaze(y, cursor=Vec(x, y, z))
                # Shuffle the directions.
                random.shuffle(dkeys)
                # Store the last known cell.
                lx = x
                lz = z
                # Work through all possible directions, looking for a valid
                # one.
                for d in dkeys:
                    # (nx, nz) is the next cell to consider.
                    nx = x + dirs[d].x
                    nz = z + dirs[d].z
                    # Check to see if the next cell is valid. It must
                    # be within the bounds of the level, and not yet connected.
                    if (nx >= 0 and
                        nz >= 0 and
                        nx < self.xsize and
                        nz < self.zsize and
                        (self.maze[Vec(nx, y, nz)].state == state.BLANK or
                         self.maze[Vec(nx, y, nz)].state == state.USED)):
                        # For blank cells, we generate a new room
                        if self.maze[Vec(nx, y, nz)].state == state.BLANK:
                            room, pos = rooms.pickRoom(
                                self, dsize, Vec(
                                    nx, y, nz))
                            ps = self.setroom(pos, room)
                            roots = {}
                            for p in ps:
                                # Set the depth to maxdepth. Later we will calculate
                                # this. Connect the new cells
                                if p.y == y:
                                    self.maze[p].state = state.CONNECTED
                                    self.maze[p].depth = maxdepth
                                else:
                                    root1 = ds.find(p)
                                    if p.y in roots.keys():
                                        ds.union(root1, roots[p.y])
                                    else:
                                        roots[p.y] = root1
                                    self.maze[p].state = state.USED
                                    self.maze[p].depth = maxdepth
                        # For used rooms, we grab the set of rooms and pick a
                        # random one. Reset all the room to connected.
                        else:
                            root = ds.find(Vec(nx, y, nz))
                            sets = ds.split_sets()
                            ps = sets[root]
                            for p in ps:
                                self.maze[p].state = state.CONNECTED
                        # Mark the halls leaving the current cell and the
                        # next cell as connected. We'll set the hall class
                        # later.
                        self.halls[x][y][z][sides[d]] = 1
                        self.halls[nx][y][nz][osides[d]] = 1
                        # Set the current cell.
                        p = choice(ps)
                        x = p.x
                        z = p.z
                        # We found a good cell, no need to look further.
                        break

                # If we're stuck, hunt for a new starting cell. If
                # the above loop found a direction to move then we skip
                # this. Otherwise we start at (0,0) and try to find an
                # disconnected cell that has a connected neighbor we can
                # connect to.
                if (lx == x and lz == z):
                    # print 'Hunting...'
                    for p in iterate_plane(Vec(0, y, 0),
                                           Vec(self.xsize - 1, y, self.zsize - 1)):
                        # Cell was connected, keep looking.
                        if (self.maze[Vec(p.x, y, p.z)].state ==
                                state.CONNECTED
                                or
                                self.maze[Vec(p.x, y, p.z)].state ==
                                state.RESTRICTED):
                            continue
                        # Cell is disconnected. Let's try to connect it to a
                        # neighbor. First, catalog which directions have a
                        # connected neighbor.
                        neighbors = []
                        for d in dkeys:
                            key = Vec(p.x, y, p.z) + dirs[d]
                            if(key in self.maze and
                               self.maze[key].state == state.CONNECTED):
                                neighbors.append(d)
                        # If there are no connected neighbors, keep looking.
                        if (len(neighbors) == 0):
                            continue
                        # We found one! Pick a random connected neighbor cell
                        # and connect the halls. Set our current cell and move
                        # on like nothing is wrong.
                        d = random.choice(neighbors)
                        x = p.x
                        z = p.z
                        ox = x + dirs[d].x
                        oz = z + dirs[d].z
                        # If this is a BLANK cell, generate a new room.
                        if (self.maze[Vec(x, y, z)].state == state.BLANK):
                            room, pos = rooms.pickRoom(
                                self, dsize, Vec(
                                    x, y, z))
                            ps = self.setroom(pos, room)
                            roots = {}
                            for p in ps:
                                if p.y == y:
                                    self.maze[p].state = state.CONNECTED
                                    self.maze[p].depth = maxdepth
                                else:
                                    root1 = ds.find(p)
                                    if p.y in roots.keys():
                                        ds.union(root1, roots[p.y])
                                    else:
                                        roots[p.y] = root1
                                    self.maze[p].state = state.USED
                                    self.maze[p].depth = maxdepth
                        # For used rooms, we grab the set of rooms and pick a
                        # random one. Set all the rooms to connected.
                        else:
                            root = ds.find(Vec(x, y, z))
                            sets = ds.split_sets()
                            ps = sets[root]
                            for p in ps:
                                self.maze[p].state = state.CONNECTED
                        self.halls[x][y][z][sides[d]] = 1
                        self.halls[ox][y][oz][osides[d]] = 1
                        p = choice(ps)
                        x = p.x
                        z = p.z
                        break

                # If the last cell and current cell are still the same (we could
                # not move, and the hunt failed) then we've filled the level.
                # Recalculate the depth tree, find the deepest cell on
                # this level, and use it for the stairwell (starting point)
                # on the next.
                if (lx == x and lz == z):
                    # Sprinkle some extra hallways into the dungeon using the
                    # loops config parameter.
                    for p in iterate_plane(Vec(0, y, 0),
                                           Vec(self.xsize - 1, y, self.zsize - 1)):
                        for d in dirs.keys():
                            nx = p.x + dirs[d].x
                            nz = p.z + dirs[d].z
                            if (nx >= 0 and
                                    nz >= 0 and
                                    nx < self.xsize and
                                    nz < self.zsize):
                                if (self.halls[p.x][y][p.z][sides[d]] is not 1 and
                                        self.halls[nx][y][nz][osides[d]] is not 1 and
                                        random.randint(1, 100) <= cfg.loops):
                                    self.halls[p.x][y][p.z][sides[d]] = 1
                                    self.halls[nx][y][nz][osides[d]] = 1
                    if self.args.debug:
                        print 'Post loops:'
                        self.printmaze(y, cursor=Vec(x, y, z))
                    # Rebuild the depth tree.
                    # The first room on this level has a depth of 1
                    self.maze[level_start].depth = 1
                    recurse = True
                    while (recurse):
                        recurse = False
                        for p in iterate_plane(Vec(0, y, 0),
                                               Vec(self.xsize - 1, y, self.zsize - 1)):
                            if (self.maze[Vec(p.x, y, p.z)].depth == maxdepth):
                                recurse = True
                                depth = maxdepth
                                for d in dirs.keys():
                                    if (self.halls[p.x][y][p.z][sides[d]] == 1):
                                        depth = min(
                                            self.maze[Vec(p.x, y, p.z) + dirs[d]].depth + 1,
                                            self.maze[Vec(p.x, y, p.z)].depth)
                                        self.maze[
                                            Vec(p.x, y, p.z)].depth = depth
                    # Find the deepest cell on this level that can contain a
                    # stairwell.
                    depth = 0
                    for p in iterate_plane(Vec(0, y, 0),
                                           Vec(self.xsize - 1, y, self.zsize - 1)):
                        if (self.maze[Vec(p.x, y, p.z)].depth > depth and
                                self.rooms[Vec(p.x, y, p.z)]._is_stairwell):
                            depth = self.maze[Vec(p.x, y, p.z)].depth
                            x = p.x
                            z = p.z
                    break

        # Connect the treasure room. Find the deepest cell that has a neighbor
        # with a depth of zero and connect it.
        depth = 0
        point = Vec(0, 0, 0)
        opoint = Vec(0, 0, 0)
        dr = 'N'
        for p in iterate_plane(Vec(0, y, 0), Vec(self.xsize - 1, y, self.zsize - 1)):
            if (self.maze[Vec(p.x, y, p.z)].depth > depth):
                for d, v in dirs.items():
                    if (p + v in self.maze and self.maze[p + v].depth == 0):
                        point = p
                        opoint = p + v
                        depth = self.maze[Vec(p.x, y, p.z)].depth
                        dr = d
        self.halls[point.x][y][point.z][sides[dr]] = 1
        self.halls[opoint.x][y][opoint.z][osides[dr]] = 1
        if self.args.debug:
            print 'Post treasure:'
            self.printmaze(y, cursor=Vec(x, y, z))

        self.entrance_pos = entrance_pos
        if self.args.debug:
            print 'Entrance:', entrance_pos
            print 'Exit:', exit_pos

    def genhalls(self):
        '''Step through all rooms and generate halls where possible'''
        for y in xrange(self.levels):
            for x in xrange(self.xsize):
                for z in xrange(self.zsize):
                    pos = Vec(x, y, z)
                    if (pos not in self.rooms):
                        continue
                    for d in xrange(4):
                        if (self.halls[x][y][z][d] == 1 and
                                self.rooms[pos].hallLength[d] > 0):
                            hall_list = weighted_shuffle(cfg.master_halls)
                            hall_list.insert(0, 'Blank')
                            while (len(hall_list)):
                                newhall = hall_list.pop()
                                newsize = halls.sizeByName(newhall)
                                nextpos = pos + pos.d(d)
                                nextd = (d + 2) % 4
                                # Get valid offsets for this room
                                # and the adjoining room.
                                # First test the current room.
                                result1 = self.rooms[pos].testHall(
                                    d,
                                    newsize,
                                    self.rooms[nextpos].hallSize[nextd][0],
                                    self.rooms[nextpos].hallSize[nextd][1])
                                result2 = self.rooms[nextpos].testHall(
                                    nextd,
                                    newsize,
                                    self.rooms[pos].hallSize[d][0],
                                    self.rooms[pos].hallSize[d][1])
                                if (result1 is not False and
                                        result2 is not False):
                                    offset = randint(min(result1[0],
                                                         result2[0]),
                                                     max(result1[1],
                                                         result2[1]))
                                    self.rooms[pos].halls[d] = \
                                        halls.new(newhall, self.rooms[pos], d,
                                                  offset)
                                    self.rooms[nextpos].halls[nextd] = \
                                        halls.new(newhall, self.rooms[nextpos],
                                                  nextd, offset)
                                    hall_list = []
                        else:
                            self.rooms[pos].halls[d] = halls.new(
                                'blank',
                                self.rooms[pos],
                                d,
                                6)

    def genhalltraps(self):
        '''Place hallway traps'''
        # Some lookups
        d = enum('N', 'E', 'S', 'W')
        dv = [
            Vec(0, 0, -1),
            Vec(1, 0, 0),
            Vec(0, 0, 1),
            Vec(-1, 0, 0)
        ]

        # First, lets create a list of E-W and N-S halls.
        # Record hall position (NW corner), width, ;ength, direction.
        halls = []
        for y in xrange(0, self.levels):
            for z in xrange(0, self.zsize):
                for x in xrange(0, self.xsize):
                    p1 = Vec(x, y, z)
                    r1 = self.rooms[p1]
                    # W-E hall
                    if (r1.halls[d.E]._name is not 'blank'):
                        r2 = self.rooms[p1 + dv[d.E]]
                        if (
                            r1.features[0]._is_secret is not True and
                            r2.features[0]._is_secret is not True
                        ):
                            offset = r1.halls[d.E].offset
                            size = r1.halls[d.E].size
                            pos = Vec(
                                p1.x * 16,
                                p1.y * 6,
                                p1.z * 16
                            ) + Vec(
                                16 - r1.hallLength[d.E],
                                0,
                                offset
                            )
                            length = r1.hallLength[d.E] + r2.hallLength[d.W]
                            halls.append({
                                'pos': pos,
                                'size': size,
                                'length': length,
                                'direction': d.E,
                            })
                    # N-S hall
                    if (r1.halls[d.S]._name is not 'blank'):
                        r2 = self.rooms[p1 + dv[d.S]]
                        if (
                            r1.features[0]._is_secret is not True and
                            r2.features[0]._is_secret is not True
                        ):
                            offset = r1.halls[d.S].offset
                            size = r1.halls[d.S].size
                            pos = Vec(
                                p1.x * 16,
                                p1.y * 6,
                                p1.z * 16
                            ) + Vec(
                                offset,
                                0,
                                16 - r1.hallLength[d.S]
                            )
                            length = r1.hallLength[d.S] + r2.hallLength[d.N]
                            halls.append({
                                'pos': pos,
                                'size': size,
                                'length': length,
                                'direction': d.S,
                            })

        # Assign a hall trap class to each hall.
        for hall in halls:
            # Weighted shuffle the traps, and default to Blank.
            trap_list = weighted_shuffle(cfg.master_hall_traps)
            trap_list.insert(0, 'Blank')

            while (len(trap_list)):
                trapname = trap_list.pop()
                trap = hall_traps.new(
                    trapname,
                    self,
                    hall['pos'],
                    hall['size'],
                    hall['length'],
                    hall['direction']
                )
                if (
                    trap._min_width <= hall['size'] <= trap._max_width and
                    trap._min_length <= hall['length'] <= trap._max_length
                ):
                    self.hall_traps.append(trap)
                    trap_list = []

    def genfloors(self):
        for pos in self.rooms:
            if (len(self.rooms[pos].floors) == 0):
                floor = floors.new(weighted_choice(cfg.master_floors),
                                   self.rooms[pos])
                self.rooms[pos].floors.append(floor)

    def genfeatures(self):
        for pos in self.rooms:
            if (len(self.rooms[pos].features) == 0):
                feature = features.new(weighted_choice(cfg.master_features),
                                       self.rooms[pos])
                self.rooms[pos].features.append(feature)
                feature.placed()

    def genruins(self):
        for pos in self.rooms:
            if (pos.y == 0 and
                    len(self.rooms[pos].ruins) == 0):
                if pos == self.entrance.parent.pos:
                    try:
                        ruin = ruins.new(
                            weighted_choice(
                                cfg.master_entrances[
                                    self.biome]),
                            self.rooms[pos])
                    except KeyError:
                        ruin = ruins.new(
                            weighted_choice(
                                cfg.default_entrances),
                            self.rooms[pos])
                    self.dinfo['dungeon_name'] = ruin.nameDungeon()
                else:
                    ruin = ruins.new(weighted_choice(cfg.master_ruins),
                                     self.rooms[pos])
                self.rooms[pos].ruins.append(ruin)
                ruin.placed(self.world)

    def placetorches(self, level=0):
        '''Place a proportion of the torches where possible'''
        if (self.levels > 1):
            perc = int(float(level) / float(self.levels - 1) *
                       (cfg.torches_bottom - cfg.torches_top) +
                       cfg.torches_top)
        else:
            perc = cfg.torches_top
        count = 0
        maxcount = 0
        for pos, val in self.torches.items():
            if (pos.up(1).y / self.room_height == level):
                maxcount += 1
        maxcount = perc * maxcount / 100
        offset = 3 - cfg.torches_position
        dirs = {
            '1': Vec(-1, 0, 0),
            '2': Vec(1, 0, 0),
            '3': Vec(0, 0, -1),
            '4': Vec(0, 0, 1)
        }
        for pos, val in self.torches.items():
            attach_pos = pos.down(offset) + dirs[str(val)]
            if (count < maxcount and
                    pos in self.blocks and
                    self.blocks[pos.down(offset)].material == materials.Air and
                    self.blocks[attach_pos].material == materials._wall and
                    pos.up(1).y / self.room_height == level):
                self.setblock(pos.down(offset), materials.Torch, val)
                count += 1
        if (level < self.levels - 1):
            self.placetorches(level + 1)

    def placedoors(self, perc):
        '''Place a proportion of the doors where possible'''
        count = 0
        # in MC space, 0=W, 1=N, 2=E, 3=S
        # doors are populated N->S and W->E
        # This holds direction and starting hinge side
        #           N      E      S      W
        doordat = ((1, 1), (2, 1), (3, 0), (0, 0))
        maxcount = perc * len(self.doors) / 100
        for pos, door in self.doors.items():
            if (count < maxcount):
                x = doordat[door.direction][1]
                for dpos in door.doors:
                    if(dpos in self.blocks and self.blocks[dpos].material == materials.Air):
                        self.setblock(dpos, materials._wall, hide=True)
                        self.blocks[dpos.down(1)].material = door.material
                        # self.blocks[dpos.down(1)].data =
                        # doordat[door.direction][x] | 8 # Top door
                        self.blocks[
                            dpos.down(1)].data = 8 + x  # Top door & hinge
                        self.blocks[dpos.down(2)].material = door.material
                        self.blocks[
                            dpos.down(2)].data = doordat[
                            door.direction][0]
                    x = 1 - x
                count += 1

    def placechests(self, level=0):
        '''Place chests in the dungeon. This is called with no arguments,
        and iterates over itself to fill each level'''
        # First we build a weighted list of rooms. Rooms are more likely to
        # contain a chest if they have fewer halls.
        candidates = []
        chests = ceil(cfg.chests * float(self.xsize * self.zsize) / 10.0)
        for room in self.rooms:
            # Only consider rooms on this level
            if (self.rooms[room].pos.y != level):
                continue
            hcount = 1
            for h in self.rooms[room].halls:
                if (h is not None and h.size == 0):
                    hcount += 1
            # If the canvas is too small, don't bother.
            if (self.rooms[room].canvasWidth() < 2 or
                    self.rooms[room].canvasLength() < 2):
                hcount = 0
            # The weight is exponential. Base 20 seems to work well.
            candidates.append((room, 20 ** hcount - 1))
        # Shuffle potential locations.
        locations = weighted_shuffle(candidates)
        while (len(locations) > 0 and chests > 0):
            spin()
            room = self.rooms[locations.pop()]
            points = []
            # Catalog all valid points in the room that can hold a chest.
            for point in iterate_points_inside_flat_poly(*room.canvas):
                point += room.loc
                if (point not in self.blocks or
                        point.up(1) not in self.blocks or
                        point.up(2) not in self.blocks or
                        point.down(1) not in self.blocks):
                    continue
                if(
                    self.blocks[point].material.val in materials.vine_solids and
                    self.blocks[point.up(1)].material.val == 0 and
                    self.blocks[point.up(2)].material.val == 0
                ):
                    points.append(point)
                if (
                    self.blocks[point.down(1)].material.val in materials.vine_solids and
                    self.blocks[point].material.val == 0 and
                    self.blocks[point.up(1)].material.val == 0
                ):
                    points.append(point.down(1))
            # Pick a spot, if one exists.
            if (len(points) > 0):
                point = random.choice(points)
                # Decide if we are a trap
                if randint(1, 100) <= cfg.chest_traps:
                    self.setblock(point.up(1), materials.TrappedChest)
                    self.setblock(point, materials.Dispenser, 1)
                    self.addchesttrap(point)
                else:
                    self.setblock(point.up(1), materials.Chest)
                # Add the chest entity either way
                self.addchest(point.up(1))
                chests -= 1
        if (level < self.levels - 1):
            self.placechests(level + 1)

    def placespawners(self, level=0):
        '''Place spawners in the dungeon. This is called with no arguments,
        and iterates over itself to fill each level'''
        # First we build a weighted list of rooms. Rooms are more likely to
        # contain a spawners if they have fewer halls.
        candidates = []
        spawners = ceil(cfg.spawners * float(self.xsize * self.zsize) / 10.0)
        for room in self.rooms:
            # Only consider rooms on this level
            if (self.rooms[room].pos.y != level):
                continue
            hcount = 1
            for h in self.rooms[room].halls:
                if (h is not None and h.size == 0):
                    hcount += 1
            # If the canvas is too small, don't bother.
            if (self.rooms[room].canvasWidth() < 2 or
                    self.rooms[room].canvasLength() < 2):
                hcount = 0
            # The weight is exponential. Base 20 seems to work well.
            candidates.append((room, 20 ** hcount - 1))
        # Shuffle potential locations.
        locations = weighted_shuffle(candidates)
        while (len(locations) > 0 and spawners > 0):
            spin()
            room = self.rooms[locations.pop()]
            points = []
            # Catalog all valid points in the room that can hold a spawner.
            if (cfg.hidden_spawners is False):
                # Spawners inside rooms
                for point in iterate_points_inside_flat_poly(*room.canvas):
                    point += room.loc
                    if (point not in self.blocks or
                            point.up(1) not in self.blocks or
                            point.up(2) not in self.blocks or
                            point.down(1) not in self.blocks):
                        continue
                    if(
                        self.blocks[point].material.val in materials.vine_solids and
                        self.blocks[point.up(1)].material.val == 0
                    ):
                        points.append(point)
            else:
                # Hidden spawners, just on the other side of walls.
                y = room.canvasHeight()
                for x in xrange(self.room_size):
                    for z in xrange(self.room_size):
                        p = room.loc + Vec(x, y, z)
                        adj = [Vec(1, 0, 0), Vec(0, 0, 1),
                               Vec(-1, 0, 0), Vec(0, 0, -1)]
                        walls = 0
                        for q in adj:
                            if (p + q in self.blocks and
                                    self.getblock(p + q) == materials._wall):
                                walls += 1
                        if (p.up(1) not in self.blocks and
                                walls > 0):
                            points.append(p)

            # Pick a spot, if one exists.
            if (len(points) > 0):
                point = random.choice(points).up(1)
                self.setblock(point, materials.Spawner)
                self.addspawner(point)
                spawners -= 1
        if (level < self.levels - 1):
            self.placespawners(level + 1)

    def renderhalltraps(self):
        '''Render hallway traps'''
        count = len(self.hall_traps)
        self.pm.init(count, label='Rendering hall_traps:')
        for trap in self.hall_traps:
            self.pm.update_left(count)
            count -= 1
            trap.render()
        self.pm.set_complete()

    def renderrooms(self):
        '''Call render() on all rooms to populate the block buffer'''
        count = len(self.rooms)
        self.pm.init(count, label='Rendering rooms:')
        for pos in self.rooms:
            self.pm.update_left(count)
            count -= 1
            self.rooms[pos].render()
        self.pm.set_complete()

    def renderhalls(self):
        ''' Call render() on all halls'''
        count = len(self.rooms) * 4
        self.pm.init(count, label='Rendering halls:')
        for pos in self.rooms:
            self.pm.update_left(count)
            count -= 4
            for x in xrange(0, 4):
                if (self.rooms[pos].halls[x]):
                    self.rooms[pos].halls[x].render()
        self.pm.set_complete()

    def renderfloors(self):
        ''' Call render() on all floors'''
        count = len(self.rooms)
        self.pm.init(count, label='Rendering floors:')
        for pos in self.rooms:
            self.pm.update_left(count)
            count -= 1
            for x in self.rooms[pos].floors:
                x.render()
        self.pm.set_complete()

    def renderfeatures(self):
        ''' Call render() on all features'''
        count = len(self.rooms)
        self.pm.init(count, label='Rendering features:')
        for pos in self.rooms:
            self.pm.update_left(count)
            count -= 1
            for x in self.rooms[pos].features:
                x.render()
        self.pm.set_complete()

    def renderruins(self):
        ''' Call render() on all ruins'''
        count = len(self.rooms)
        self.pm.init(count, label='Rendering ruins:')
        for pos in self.rooms:
            self.pm.update_left(count)
            count -= 1
            for x in self.rooms[pos].ruins:
                x.render()
        self.pm.set_complete()

    def outputterminal(self):
        '''Print a slice (or layer) of the dungeon block buffer to the termial.
        We "look-through" any air blocks to blocks underneath'''
        floor = self.args.term
        layer = (floor - 1) * self.room_height
        for z in xrange(self.zsize * self.room_size):
            for x in xrange(self.xsize * self.room_size):
                y = layer
                while (y < layer + self.room_height - 1 and
                       Vec(x, y, z) in self.blocks and
                       (self.blocks[Vec(x, y, z)].hide or
                        self.blocks[Vec(x, y, z)].material == materials.Air or
                        self.blocks[Vec(x, y, z)].material == materials._ceiling)):
                    y += 1
                if (Vec(x, y, z) in self.blocks and
                        self.blocks[Vec(x, y, z)].hide == False):
                    mat = self.blocks[Vec(x, y, z)].material
                    if (mat._meta):
                        mat.update(x, y, z,
                                   self.xsize * self.room_size,
                                   self.levels * self.room_height,
                                   self.zsize * self.room_size)
                    sys.stdout.write(mat.c)
                else:
                    sys.stdout.write(materials.NOBLOCK)
            print

    def outputhtml(self):
        '''Print all levels of the dungeon block buffer to html.
        We "look-through" any air blocks to blocks underneath'''
        dungeon_name = self.dungeon_name.replace(' ', '_')
        dungeon_name  = re.sub(r'[^a-zA-Z0-9_]', "", dungeon_name)
        basename = self.args.html.replace('__DUNGEON__', dungeon_name)
        force = self.args.force
        # First search for existing files
        if (force == False):
            for floor in xrange(self.levels):
                filename = basename + '-' + str(floor + 1) + '.html'
                if (os.path.isfile(filename)):
                    sys.exit('File %s exists. Use --force to overwrite.' %
                             (filename))
        # Construct headers and footers
        header = '''
        <html><head>
        <script language="javascript" type="text/javascript">
        <!--
            function menu_goto( menuform )
            {
                selecteditem = menuform.newurl.selectedIndex ;
                newurl = menuform.newurl.options[ selecteditem ].value ;
                if (newurl.length != 0) {
                    location.href = newurl ;
                }
            }
        //-->
        </script></head><body>'''
        footer = '''</body></html>'''
        # Output each level file.
        for floor in xrange(self.levels):
            layer = floor * self.room_height
            # Build the form.
            form = '''
            <form action="foo">
            <select name="newurl" onchange="menu_goto(this.form)">
            '''
            for menufloor in xrange(self.levels):
                path = basename + '-' + str(menufloor + 1) + '.html'
                (head, tail) = os.path.split(path)
                selected = ''
                if (floor == menufloor):
                    selected = ' selected="selected"'
                form += '<option value="%s"%s>%s - Level %d</option>' % (
                    tail, selected, self.dungeon_name, menufloor + 1)
            form += '</select></form><br>'
            # Write the floor file.
            filename = basename + '-' + str(floor + 1) + '.html'
            print 'Writing:', filename
            f = open(filename, 'w')
            f.write(header + form)
            f.write('<table border=0 cellpadding=0 cellspacing=0>')
            for z in xrange(self.zsize * self.room_size):
                f.write('<tr>')
                for x in xrange(self.xsize * self.room_size):
                    y = layer
                    while (Vec(x, y, z) in self.blocks and
                            (self.blocks[Vec(x, y, z)].hide or
                             self.blocks[Vec(x, y, z)].material ==
                             materials.Air or
                             self.blocks[Vec(x, y, z)].material ==
                             materials._ceiling)):
                        y += 1
                    if (Vec(x, y, z) in self.blocks):
                        mat = self.blocks[Vec(x, y, z)].material
                        if (mat._meta):
                            mat.update(x, y, z,
                                       self.xsize * self.room_size,
                                       self.levels * self.room_height,
                                       self.zsize * self.room_size)
                            self.blocks[Vec(x, y, z)].data = mat.data
                        dat = self.blocks[Vec(x, y, z)].data

                        # Doors are ... different
                        if (mat in [materials.WoodenDoor, materials.IronDoor,
                                    materials.SpruceDoor, materials.BirchDoor,
                                    materials.JungleDoor, materials.DarkOakDoor,
                                    materials.AcaciaDoor]):
                            dat2 = self.blocks[Vec(x, y + 1, z)].data
                            dat = ((dat & 1) << 3) + dat2

                        if self.blocks[Vec(x, y, z)].blank:
                            f.write('<td><img src=d/0.png>')
                        else:
                            f.write('<td><img src=d/%d-%d.png>' %
                                    (mat.val, dat))
                    else:
                        f.write('<td><img src=d/0.png>')
            f.write('</table>')
            f.write(footer)
            f.close()

    def findsecretrooms(self):
        # Secret rooms must satisfy the following...
        # 1. The room cannot be an entrance, stairwell, or above a stairwell
        # 2. Must be a 1x1x1 room.
        # 3. Must not be a blank room.
        # 4. Must have exactly one hallway.
        # 5. Must not connect to a corridor.
        # 6. ... That's it.
        #
        # If found, the room will have its feature overridden with SecretRoom
        # the hallway will be reduced to 1 and move away from the edge if
        # required.

        # hall positions to grid direction
        dirs = {3: Vec(-1, 0, 0),
                1: Vec(1, 0, 0),
                2: Vec(0, 0, 1),
                0: Vec(0, 0, -1)}

        # Find them
        for p in self.rooms:
            room = self.rooms[p]
            if room.features[0]._name == 'entrance':
                continue
            if room.features[0]._is_stairwell:
                continue
            if p.y < self.levels - 1:
                droom = self.rooms[p.down(1)]
                if droom.features[0]._is_stairwell:
                    continue
            if room.size != Vec(1, 1, 1):
                continue
            if (room._name == 'blank' or
                        room._name == 'cblank' or
                        room._name == 'blankstairwell' or
                        room._name == 'circularpit' or
                        room._name == 'circularpitmid' or
                        room._name == 'circularpitbottom' or
                        room._name == 'pit' or
                        room._name == 'pitmid' or
                        room._name == 'pitbottom'
                    ):
                continue
            hallsum = 0
            d = 0
            for x in xrange(4):
                if room.halls[x]._name != 'blank':
                    d = x
                    hallsum += 1
            if hallsum != 1:
                continue
            room2 = self.rooms[p + dirs[d]]
            if (room2._name == 'corridor' or
                        room2._name == 'cblank' or
                        room2._name == 'sandstonecavern' or
                        room2._name == 'sandstonecavernlarge' or
                        room2._name == 'cavern' or
                        room2._name == 'cavernlarge' or
                        room2._name == 'naturalcavern' or
                        room2._name == 'naturalcavernlarge'
                    ):
                continue
            if random.randint(1, 100) > cfg.secret_rooms:
                continue

            if self.args.debug:
                print 'Secret room from', room._name, 'to', room2._name
            # Override this room's feature
            room.features = []
            room.features.append(
                features.new(
                    weighted_choice(
                        cfg.master_srooms),
                    room))
            room.features[0].placed()
            # override this room's hallway
            offset = room.halls[d].offset
            if offset < 4:
                offset = 4
            if offset > 9:
                offset = 9
            room.halls[d] = halls.new('single', room, d, offset)
            room.hallLength[d] = 3
            # override the other room's hallway
            od = (d + 2) % 4
            offset = room2.halls[od].offset
            if offset < 4:
                offset = 4
            if offset > 9:
                offset = 9
            room2.halls[od] = halls.new('single', room2, od, offset)

    def setentrance(self):
        if self.args.debug:
            print 'Extending entrance to the surface...'
        wcoord = Vec(self.entrance.parent.loc.x + self.position.x,
                     self.position.y - self.entrance.parent.loc.y,
                     self.entrance.parent.loc.z + self.position.z)
        if self.args.debug:
            print '   World coord:', wcoord
        baseheight = wcoord.y + 2  # plenum + floor
        #newheight = baseheight
        low_height = self.world.Height
        high_height = baseheight
        if self.args.debug:
            print '   Base height:', baseheight
        chunk = self.world.getChunk(wcoord.x >> 4, wcoord.z >> 4)
        for x in xrange(wcoord.x + 4, wcoord.x + 12):
            for z in xrange(wcoord.z + 4, wcoord.z + 12):
                xInChunk = x & 0xf
                zInChunk = z & 0xf
                # Heightmap is a good starting place, but I need to look
                # down through foliage.
                y = chunk.HeightMap[zInChunk, xInChunk] - 1
                while (
                    chunk.Blocks[xInChunk, zInChunk, y] not in materials.heightmap_solids
                ):
                    y -= 1
                if (chunk.Blocks[xInChunk, zInChunk, y] == 9 or
                        chunk.Blocks[xInChunk, zInChunk, y] == 79):
                    self.entrance.inwater = True
                high_height = max(y, high_height)
                low_height = min(y, low_height)
        if self.args.debug:
            print "    Low height:", low_height
            print "   High height:", high_height
            if (self.entrance.inwater):
                print "   Entrance is in water."
        if (low_height - baseheight > 0):
            self.entrance.height += low_height - baseheight
            self.entrance.low_height += low_height - baseheight
        if (high_height - baseheight > 0):
            self.entrance.high_height += high_height - baseheight
        self.entrance.u = int(cfg.tower * self.entrance.u)
        # Check the upper bounds of the tower
        if (high_height + self.entrance.u >= self.world.Height):
            self.entrance.u = self.world.Height - 3 - high_height

    def generatemaps(self):
        for level in xrange(1, self.levels + 1):
            if randint(1, 100) > cfg.maps:
                next
            m = self.mapstore.generate_map(self, level)
            self.addplaceditem(m, max_lev=level)

    def addplaceditem(self, item_tags, min_lev=-100, max_lev=100):
        self.placed_items.append({
            'item': item_tags,
            'min_lev': min_lev,
            'max_lev': max_lev
        })

    def placeitems(self):
        for item in self.placed_items:
            ents = self.tile_ents.keys()
            random.shuffle(ents)
            for loc in ents:
                ent = self.tile_ents[loc]
                if (loc != Vec(0,0,0) and
                    loc.y // self.room_height >= item['min_lev'] - 1 and
                    loc.y // self.room_height <= item['max_lev'] - 1):
                    if self.addchestitem_tag(loc, item['item']):
                        break

    def applychanges(self):
        '''Write the block buffer to the specified world'''
        world = self.world
        changed_chunks = set()
        num_blocks = len(self.blocks)
        # Fill caves
        if (self.dinfo['fill_caves'] is True):
            num = (self.zsize + 10) * (self.xsize + 10)
            pm = pmeter.ProgressMeter()
            pm.init(num, label='Filling in caves:')
            for z in xrange((self.position.z >> 4) - 5,
                            (self.position.z >> 4) + self.zsize + 5):
                for x in xrange((self.position.x >> 4) - 5,
                                (self.position.x >> 4) + self.xsize + 5):
                    pm.update_left(num)
                    num -= 1
                    if ((x, z) in self.good_chunks):
                        p = Vec(x, 0, z)
                        chunk = world.getChunk(x, z)
                        miny = self.good_chunks[(x, z)]
                        air = (chunk.Blocks[:, :, 0:miny] == 0)
                        chunk.Blocks[air] = materials._floor.val
                        changed_chunks.add(chunk)
                        del(self.good_chunks[(x, z)])
            pm.set_complete()
        # Regeneration
        if self.args.command == 'regenerate':
            num = (self.zsize) * (self.xsize)
            pm = pmeter.ProgressMeter()
            pm.init(num, label='Regenerating resources/chests:')
            for z in xrange((self.position.z >> 4),
                            (self.position.z >> 4) + self.zsize):
                for x in xrange(self.position.x >> 4,
                                (self.position.x >> 4) + self.xsize):
                    pm.update_left(num)
                    num -= 1
                    p = Vec(x, 0, z)
                    chunk = world.getChunk(x, z)
                    # Repopulate any above ground chests
                    for tileEntity in chunk.TileEntities:
                        if (tileEntity["id"].value == "Chest"):
                            p = Vec(0, 0, 0)
                            for name, tag in tileEntity.items():
                                if (name == 'x'):
                                    p.x = int(tag.value) - self.position.x
                                if (name == 'y'):
                                    p.y = self.position.y - int(tag.value)
                                if (name == 'z'):
                                    p.z = int(tag.value) - self.position.z
                            if p.y < 0:
                                self.addchest(p, 0)
                    # Empty the tile entities from this chunk
                    chunk.TileEntities.value[:] = []
                    # Empty the entities from this chunk
                    chunk.Entities.value[:] = []
                    # Fake some ores. First fill with Stone (id=1) and then pick
                    # some random ones based on known ore distributions to fill
                    # in ores.
                    # Stone
                    chunk.Blocks[:, :, 0:self.position.y] = materials.Stone.val
                    # Coal. 1% between 5 and 60
                    distribute(chunk, 5, min(self.position.y, 60),
                               1, materials.CoalOre)
                    # Iron. .6% between 5 and 55
                    distribute(chunk, 5, min(self.position.y, 55),
                               .6, materials.IronOre)
                    # Redstone. .8% between 5 and 20
                    distribute(chunk, 5, min(self.position.y, 20),
                               .8, materials.RedstoneOre)
                    # Gold. .1% between 5 and 35
                    distribute(chunk, 5, min(self.position.y, 35),
                               .1, materials.GoldOre)
                    # Lapis. .1% between 5 and 35
                    distribute(chunk, 5, min(self.position.y, 35),
                               .1, materials.LapisLazuliOre)
                    # Diamond. .1% between 5 and 20
                    distribute(chunk, 5, min(self.position.y, 20),
                               .1, materials.DiamondOre)
                    # Bedrock. 60% between 0 and 4
                    distribute(chunk, 0, min(self.position.y, 4),
                               60, materials.Bedrock)
            pm.set_complete()
        # Blocks
        pm = pmeter.ProgressMeter()
        pm.init(num_blocks, label='Writing block buffer:')
        for block in self.blocks.values():
            # Progress
            pm.update_left(num_blocks)
            num_blocks -= 1
            # Mysteriously, this block contains no material.
            if block.material is None:
                continue
            # Translate block coords to world coords
            x = block.loc.x + self.position.x
            y = self.position.y - block.loc.y
            z = block.loc.z + self.position.z
            # Due to bad planning, sometimes we try to draw outside the bounds
            if (y < 0 or y >= world.Height):
                print 'WARN: Block outside height bounds. y =', y
                continue
            # Figure out the chunk and chunk offset
            chunk_z = z >> 4
            chunk_x = x >> 4
            xInChunk = x & 0xf
            zInChunk = z & 0xf
            # get the chunk
            if (world.containsChunk(chunk_x, chunk_z)):
                chunk = world.getChunk(chunk_x, chunk_z)
            else:
                if (block.material != materials._sandbar):
                    print 'Whoops! Block in nonexistent chunk!',
                    print 'crd: (%d, %d) chk: (%d, %d) mat: %s' % \
                        (x, z, chunk_x, chunk_z, block.material.name)
                continue
            # Don't render soft blocks if there is something there already
            if (block.soft is True and
                    chunk.Blocks[xInChunk, zInChunk, y] > 0):
                continue
            mat = block.material
            dat = block.data
            # Update meta materials
            if (mat._meta):
                mat.update(block.loc.x, block.loc.y, block.loc.z,
                           self.xsize * self.room_size,
                           self.levels * self.room_height,
                           self.zsize * self.room_size)
                dat = mat.data
            # Sandbars only render over water
            if (mat == materials._sandbar and
                    chunk.Blocks[xInChunk, zInChunk, y] != materials.Water.val and
                    chunk.Blocks[xInChunk, zInChunk, y] != materials.StillWater.val and
                    chunk.Blocks[xInChunk, zInChunk, y] != materials.Ice.val):
                continue
            # Natural just looks like the existing world block
            if (mat == materials._natural):
                continue

            val = mat.val
            # Silverfish egg pass
            # Look for cobblestone, stone (normal variant only) and all stone bricks
            if (cfg.silverfish > 0 and
                    ((val == 1 and dat == 0) or val == 4 or val == 98) and
                    random.randint(1, 100) <= cfg.silverfish):
                if (val == 4):
                    dat = 1  # Cobblestone
                elif (val == 1):
                    dat = 0  # Smooth Stone
                elif (val == 98):
                    if (dat == 0):
                        dat = 2  # Bricks
                    elif (dat == 1):
                        dat = 3  # Mossy Bricks
                    elif (dat == 2):
                        dat = 4  # Cracked Bricks
                    elif (dat == 3):
                        dat = 5  # Chiseled Bricks
                val = 97    # Switch to egg brick

            # Write the block.
            chunk.Blocks[xInChunk, zInChunk, y] = val
            chunk.Data[xInChunk, zInChunk, y] = dat
            # Add this to the list we want to relight later.
            changed_chunks.add(chunk)
            # Make sure we don't overwrite this chunk in the future.
            if ((chunk_x, chunk_z) in self.good_chunks and
                    mat != materials._sandbar):
                del(self.good_chunks[(chunk_x, chunk_z)])
        pm.set_complete()
        # Copy over tile entities
        print 'Creating tile entities...'
        num = len(self.tile_ents)
        for ent in self.tile_ents.values():
            spin(num)
            num -= 1
            # Calculate world coords.
            x = ent['x'].value + self.position.x
            y = self.position.y - ent['y'].value
            z = ent['z'].value + self.position.z
            # Move this tile ent to the world coords.
            ent['x'].value = x
            ent['y'].value = y
            ent['z'].value = z
            # Place the ent!
            world.addTileEntity(ent)
        # Copy over entities
        print 'Creating entities...'
        num = len(self.ents)
        for ent in self.ents:
            spin(num)
            num -= 1
            # Calculate world coords.
            x = ent['Pos'][0].value + float(self.position.x)
            y = float(self.position.y) - ent['Pos'][1].value
            z = ent['Pos'][2].value + float(self.position.z)
            # Move this ent to the world coords.
            ent['Pos'][0].value = x
            ent['Pos'][1].value = y
            ent['Pos'][2].value = z
            # Paintings and ItemFrames need special handling.
            if ent['id'].value in ('ItemFrame', 'Painting'):
                ent['TileX'].value += int(self.position.x)
                ent['TileY'].value = int(self.position.y) - ent['TileY'].value
                ent['TileZ'].value += int(self.position.z)
            # Place the ent!
            world.addEntity(ent)
        # Mark changed chunks so pymclevel knows to recompress/relight them.
        print 'Marking dirty chunks...'
        num = len(changed_chunks)
        for chunk in changed_chunks:
            spin(num)
            num -= 1
            chunk.chunkChanged()

    def keyName(self):
        ''' Generate a random name for a key 
        This is used by TreasureHunt and Dungeon classes where a new name 
        is required.  It includes colours codes to make it unduplicateable
        using an anvil '''
        _magic = u'\u00a7'
        _knamesA = (
            ('big', 1),
            ('small', 1),
            ('ornate', 1),
            ('long', 1),
            ('worn', 1),
            ('complex', 1),
            ('secret', 1),
            ('lost', 1),
            ('hidden', 1),
        )
        _kcolours = {
			#'black': '0',
			'blue': '1',
			'jade': '2',
			'red': '4',
			'purple': '5',
			'golden': '6',
			'silver': '7',
			'yellow': 'e',
			'aqua': '3',
			'steel': '8',
        }
        _knames = (
            (u'{M}r{owners} {A} {M}{CC}{C}{M}r key', 5),
            (u'{M}r{owners} {M}{CC}{C}{M}r key', 1),
            (u'{M}rThe {A} {M}{CC}{C}{M}r key of {owner}', 2),
        )
        if self.owner.endswith("s"):
            owners = self.owner + "'"
        else:
            owners = self.owner + "'s"
        A = weighted_choice(_knamesA)
        C = random.choice( _kcolours.keys() ) 
        CC = _kcolours[ C ]
        name = weighted_choice(_knames).format(A=A,C=C,CC=CC,M=_magic,
            owner=self.owner,owners=owners)
        return name

