#!/usr/bin/python

import sys
import os
import operator
import random
from random import *
import textwrap

import cfg
import loottable
import materials
import rooms
import halls
import floors
import features
import ruins
import pmeter
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
        # Hidden blocks are not drawn on maps
        self.hide = False
        # Locked blocks cannot be overwritten later
        self.lock = False
        # Soft blocks are only rendered in the world block is air
        self.soft = False

class MazeCell(object):
    states = enum('BLANK', 'USED', 'CONNECTED', 'RESTRICTED')
    def __init__(self, loc):
        self.loc = loc
        self.depth = 0
        self.state = 0

class Dungeon (object):
    def __init__(self, xsize, zsize, levels, good_chunks, args, world, oworld,
                 chunk_cache):
        self.caches = []
        self.caches.append(cache.LRUCache(size=100))

        self.world = world
        self.oworld = oworld
        self.chunk_cache = chunk_cache
        self.pm = pmeter.ProgressMeter()
        self.rooms = {}
        self.good_chunks = good_chunks
        self.blocks = {}
        self.tile_ents = {}
        self.ents = {}
        self.torches = {}
        self.doors = {}
        self.portcullises = {}
        self.signs = []
        self.entrance = None
        self.entrance_pos = Vec(0,0,0)
        self.xsize = xsize
        self.zsize = zsize
        self.levels = levels
        self.maze = {}
        self.stairwells = []
        for x in xrange(self.xsize):
            for y in xrange(self.levels):
                for z in xrange(self.zsize):
                    self.maze[Vec(x,y,z)] = MazeCell(Vec(x,y,z))
        self.halls = [ [ [ [None, None, None, None] for z in
                         xrange(self.zsize) ] for y in
                       xrange(self.levels) ] for x in
                     xrange(self.xsize) ]
        self.room_size = 16
        self.room_height = 6
        self.position = Vec(0,0,0)
        self.args = args
        self.heightmap = numpy.zeros((xsize*self.room_size,
                                      zsize*self.room_size))
        self.dinfo = {}
        self.dinfo['hard_mode'] = cfg.hard_mode
        self.dinfo['portal_exit'] = cfg.portal_exit

    def printmaze(self, y, cursor=None):
        for z in xrange(self.zsize):
            line = u''
            for x in xrange(self.xsize):
                p = Vec(x,y,z)
                if p in self.rooms:
                    if self.halls[x][y][z][0] == 1:
                        line += ( u'\u2554\u2569\u2557')
                    else:
                        line += ( u'\u2554\u2550\u2557')
                else:
                    line += ( u'\u2591\u2591\u2591')
            print line
            line = u''
            for x in xrange(self.xsize):
                p = Vec(x,y,z)
                if p in self.rooms:
                    if self.halls[x][y][z][3] == 1:
                        line += ( u'\u2563')
                    else:
                        line += ( u'\u2551')
                    if (cursor == p):
                        line += ( u'X')
                    elif self.maze[p].state == MazeCell.states.CONNECTED:
                        line += ( u' ')
                    elif self.maze[p].state == MazeCell.states.USED:
                        line += ( u'U')
                    else:
                        line += ( u'R')
                    if self.halls[x][y][z][1] == 1:
                        line += ( u'\u2560')
                    else:
                        line += ( u'\u2551')
                else:
                    line += ( u'\u2591\u2591\u2591')
            print line
            line = u''
            for x in xrange(self.xsize):
                p = Vec(x,y,z)
                if p in self.rooms:
                    if self.halls[x][y][z][2] == 1:
                        line += ( u'\u255a\u2566\u255d')
                    else:
                        line += ( u'\u255a\u2550\u255d')
                else:
                    line += ( u'\u2591\u2591\u2591')
            print line
            line = u''
        raw_input('continue...')


    def setblock(self, loc, material, data=0, hide=False, lock=False, soft=False):
        # If material is None, remove this block
        if material == None:
            if loc in self.blocks:
                del(self.blocks[loc])
            return

        # Build a block if we need to 
        if loc not in self.blocks:
            self.blocks[loc] = Block(loc)

        if (loc.x >= 0 and
            loc.z >= 0 and
            loc.x < self.xsize*self.room_size and
            loc.z < self.zsize*self.room_size):
            self.heightmap[loc.x][loc.z] = min(loc.y,
                                               self.heightmap[loc.x][loc.z])

        # If the existing block is locked, abort
        # Unless we are requesting a locked block
        if self.blocks[loc].lock == True and lock == False:
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

    def delblock(self, loc):
        if loc in self.blocks:
            del self.blocks[loc]

    def getblock(self, loc):
        if loc in self.blocks:
            return self.blocks[loc].material
        return False


    def findlocation(self, world, dungeon_locations):
        positions = {}
        sorted_p = []
        if self.args.debug: print 'Filtering for depth...'
        for key, value in self.good_chunks.iteritems():
            if value >= (self.levels+1)*self.room_height:
                positions[key] = value

        if (cfg.maximize_distance == True and len(dungeon_locations) > 0):
            if self.args.debug: print 'Marking distances...'
            for key in positions.keys():
                d = 2^64
                chunk = Vec(key[0], 0, key[1])
                for dungeon in dungeon_locations:
                    d = min(d, (dungeon - chunk).mag2d())
                positions[key] = d

            sorted_p = sorted(positions.iteritems(),
                          reverse=True,
                          key=operator.itemgetter(1))
        else:
            sorted_p = positions.items()
            random.shuffle(sorted_p)

        if self.args.debug: print 'Selecting a location...'
        all_chunks = set(positions.keys())
        # Offset is hard mode. Expand the size of the dungeon if hard_mode is
        # set. When recording the position, we'll center the dungeon in this
        # area.
        offset = 0
        if self.dinfo['hard_mode'] == True:
            offset = 10
        for p, d in sorted_p:
            #if self.args.debug: print 'Checking: ', p
            d_chunks = set()
            for x in xrange(self.xsize+offset):
                for z in xrange(self.zsize+offset):
                    d_chunks.add((p[0]+x, p[1]+z))
            if d_chunks.issubset(all_chunks):
                if self.args.debug: print 'Found: ', p
                self.position = Vec((p[0]+(offset/2))*self.room_size,
                                    0,
                                    (p[1]+(offset/2))*self.room_size)
                if self.args.debug: print 'Final: ', self.position
                self.worldmap(world, positions)
                return self.bury(world)
        return False

    def worldmap(self, world, positions):
        #rows, columns = os.popen('stty size', 'r').read().split()
        columns = 39
        bounds = world.bounds
        if self.args.spawn is None:
            scx = world.playerSpawnPosition()[0]>>4
            scz = world.playerSpawnPosition()[2]>>4
        else:
            scx = self.args.spawn[0]
            scz = self.args.spawn[1]
        spawn_chunk = Vec(scx, 0, scz)
        # Draw a nice little map of the dungeon location
        map_min_x = bounds.maxcx
        map_max_x = bounds.mincx
        map_min_z = bounds.maxcz
        map_max_z = bounds.mincz
        for p in self.good_chunks:
            map_min_x = min(map_min_x, p[0]+1)
            map_max_x = max(map_max_x, p[0]-1)
            map_min_z = min(map_min_z, p[1]+1)
            map_max_z = max(map_max_z, p[1]-1)

        # Include spawn
        map_min_x = min(map_min_x, spawn_chunk.x)
        map_max_x = max(map_max_x, spawn_chunk.x)
        map_min_z = min(map_min_z, spawn_chunk.z)
        map_max_z = max(map_max_z, spawn_chunk.z)

        if map_max_x-map_min_x+1 >= int(columns):
            print 'Map too wide for terminal:', map_max_x-map_min_x
            return

        sx = self.position.x/self.room_size
        sz = self.position.z/self.room_size
        if self.args.debug: print 'spos:', Vec(sx, 0, sz)
        d_box = Box(Vec(sx, 0, sz), self.xsize, world.Height, self.zsize)

        for z in xrange(map_min_z-1, map_max_z+2):
            for x in xrange(map_min_x-1, map_max_x+2):
                if (Vec(x,0,z) == spawn_chunk):
                    sys.stdout.write('SS')
                elif (x == 0 and z == 0):
                    sys.stdout.write('00')
                elif (Vec(x,0,z) == Vec(sx, 0, sz)):
                    sys.stdout.write('XX')
                elif (d_box.containsPoint(Vec(x,64,z))):
                    sys.stdout.write('##')
                elif ((x,z) in positions.keys()):
                    sys.stdout.write('++')
                elif ((x,z) in self.good_chunks.keys()):
                    sys.stdout.write('--')
                else:
                    sys.stdout.write('``')
            print


    def bury(self, world, manual=False):
        if self.args.debug: print 'Burying dungeon...'
        min_depth = (self.levels+1)*self.room_height

        d_chunks = set()
        p = (self.position.x/self.room_size,
             self.position.z/self.room_size)
        for x in xrange(self.xsize):
            for z in xrange(self.zsize):
                d_chunks.add((p[0]+x, p[1]+z))

        # Calaculate the biome
        biomes = {}
        rset = self.oworld.get_regionset(None)
        for chunk in d_chunks:
            cdata = rset.get_chunk(chunk[0],chunk[1])
            key = numpy.argmax(numpy.bincount((cdata['Biomes'].flatten())))
            if key in biomes:
                biomes[key] += 1
            else:
                biomes[key] = 1
            self.biome = max(biomes, key=lambda k: biomes[k])
        if self.args.debug: print 'Biome: ', self.biome

        depth = world.Height
        for chunk in d_chunks:
            if (chunk not in self.good_chunks):
                d1 = findChunkDepth(Vec(chunk[0], 0, chunk[1]), world)
                self.good_chunks[chunk] = d1
            else:
                d1 = self.good_chunks[chunk]
            if manual == False:
                if (d1 < min_depth):
                    print 'Selected area is too shallow to bury dungeon.'
                    return False
                elif (d1 > world.Height - 27):
                    print 'Selected area is too high to hold dungeon. ', d1
                    return False

            depth = min(depth, d1)

        if manual == False:
            self.position = Vec(self.position.x,
                                depth,
                                self.position.z)
        return True

    def snow(self, pos, limit=16):
        b = self.getblock(pos)
        if (b != False and b != materials.Air):
            return

        count = 1
        b = self.getblock(pos.down(count))
        while (count <= limit and (b == False or b == materials.Air)):
            count += 1
            b = self.getblock(pos.down(count))

        if count > limit:
            return

        if b == False:
            soft = True
        else:
            soft = False
        solids = [1, 2, 3, 4, 5, 12, 13, 17, 24, 43, 45, 48, 60, 89, 98, 99,
                  100, 112, 121, 123, 124, 125, 35]
        if self.getblock(pos.down(count)).val in solids:
            self.setblock(pos.down(count-1), materials.Snow, soft=soft)
            #print 'snow placed: ',pos.down(count-1), soft

    def vines(self, pos, grow=False):
        # Data values (1.9p5)
        # 1 - South
        # 2 - West
        # 4 - North
        # 8 - East
        b = self.getblock(pos)
        # Something here already
        if (b != False and b != materials.Air):
            return

        if b == False:
            soft = True
        else:
            soft = False

        # Look around for something to attach to
        noattach = [materials.Air, materials.Vines, materials.CobblestoneSlab,
                    materials.SandstoneSlab, materials.StoneBrickSlab,
                    materials.StoneSlab, materials.WoodenSlab, materials.Fence,
                    materials.IronBars, materials.Cobweb, materials.Torch,
                    materials.GlassPane, materials.StoneButton,
                    materials.StoneBrickStairs, materials.StoneStairs,
                    materials.WoodenStairs, materials.WallSign,
                    materials.NetherBrickFence, materials.CobblestoneWall,
                    materials.MossStoneWall, materials.StonePressurePlate,
                    materials.WoodenPressurePlate, materials.Chest]
        data = 0
        b = self.getblock(pos.s(1))
        if (b != False and b not in noattach):
            data += 1
        b = self.getblock(pos.w(1))
        if (b != False and b not in noattach):
            data += 2
        b = self.getblock(pos.n(1))
        if (b != False and b not in noattach):
            data += 4
        b = self.getblock(pos.e(1))
        if (b != False and b not in noattach):
            data += 8
        # Nothing to attach to
        if data == 0:
            return
        self.setblock(pos, materials.Vines, data, soft=soft)
        if grow == False:
            return
        pos = pos.down(1)
        b = self.getblock(pos)
        while ((b == False or b == materials.Air) and random.randint(1,100)<75):
            if b == False:
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
            for q in (Vec(1,0,0), Vec(-1,0,0),
                      Vec(0,1,0), Vec(0,-1,0),
                      Vec(0,0,1), Vec(0,0,-1)):
                if (p+q in self.blocks and
                    self.blocks[p+q].material != materials.Air and
                    random.randint(1,100) <= chance):
                    count += 1
            if count >= 3:
                webs[p] = True
        for p,q in webs.items():
            self.setblock(p, materials.Cobweb)

    def processBiomes(self):
        '''Add vines and snow according to biomes.'''
        rset = self.oworld.get_regionset(None)
        r = ov_world.CachedRegionSet(rset, self.caches)
        wp = Vec(self.position.x, 0, self.position.z)
        count = self.xsize*16*self.zsize*16
        self.pm.init(count, label='Processing biomes:')
        for p in iterate_cube(Vec(0,0,0),
                              Vec(self.xsize*16-1,0,self.zsize*16-1)):
            self.pm.update_left(count)
            count -= 1
            cx = (p.x+wp.x)//16
            cz = (p.z+wp.z)//16
            chunk = r.get_chunk(cx,cz)
            biome = chunk['Biomes'][p.x%16][p.z%16]
            # Vines in swamp, jungle, and jungle hills
            if biome in [6, 21, 22]:
                h = 0
                try:
                    h = min(self.heightmap[p.x-1][p.z], h)
                except IndexError:
                    pass
                try:
                    h = min(self.heightmap[p.x+1][p.z], h)
                except IndexError:
                    pass
                try:
                    h = min(self.heightmap[p.x][p.z-1], h)
                except IndexError:
                    pass
                try:
                    h = min(self.heightmap[p.x][p.z+1], h)
                except IndexError:
                    pass
                if h == 0:
                    continue
                for q in iterate_cube(Vec(p.x,h,p.z),
                                      Vec(p.x,0,p.z)):
                    if random.randint(1,100)<20:
                        self.vines(q, grow=True)
            # Snow in taiga, frozen ocean, frozen river, ice plains, ice
            # mountains, taiga hills
            if biome in [5, 10, 11, 12, 13, 19]:
                h = self.heightmap[p.x][p.z]
                if (h < 0):
                    self.snow(Vec(p.x, h-1, p.z), limit=abs(h-1))

        self.pm.set_complete()


    def getspawnertags(self, entity):
        # See if we have a custom spawner match
        if entity.lower() in cfg.custom_spawners.keys():
            entity = cfg.custom_spawners[entity.lower()]
            root_tag = nbt.load(filename=os.path.join(cfg.spawners_path,entity+'.nbt'))
            return root_tag
        else:
            root_tag = nbt.TAG_Compound()

        # Cases where the entity id doesn't match the config
        entity = entity.capitalize()
        if (entity == 'Pigzombie'):
            root_tag['EntityId'] = nbt.TAG_String('PigZombie')
        elif (entity == 'Cavespider'):
            root_tag['EntityId'] = nbt.TAG_String('CaveSpider')
        elif (entity == 'Lavaslime'):
            root_tag['EntityId'] = nbt.TAG_String('LavaSlime')
        elif (entity == 'Witherboss'):
            root_tag['EntityId'] = nbt.TAG_String('WitherBoss')
        # For everything else the input is the EntityId
        else:
            root_tag['EntityId'] = nbt.TAG_String(entity)

        return root_tag


    def addsign(self, loc, text1, text2, text3, text4):
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Sign')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        root_tag['Text1'] = nbt.TAG_String(text1)
        root_tag['Text2'] = nbt.TAG_String(text2)
        root_tag['Text3'] = nbt.TAG_String(text3)
        root_tag['Text4'] = nbt.TAG_String(text4)
        self.tile_ents[loc] = root_tag


    def addspawner(self, loc, entity='', tier=-1):
        if (entity == ''):
            level = loc.y/self.room_height
            if (cfg.max_mob_tier == 0 or level < 0):
                tier = 0
            elif tier == -1:
                if (self.levels > 1):
                    tier = (float(level) /
                            float(self.levels-1) *
                            float(cfg.max_mob_tier-2))+1.5
                    tier = int(min(cfg.max_mob_tier-1, tier))
                else:
                    tier = cfg.max_mob_tier-1
            entity = weighted_choice(cfg.master_mobs[tier])
            #print 'Spawner: lev=%d, tier=%d, ent=%s' % (level, tier, entity)
        root_tag = self.getspawnertags(entity)
        # Do generic spawner setup
        root_tag['id'] = nbt.TAG_String('MobSpawner')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        try: root_tag['Delay']
        except: root_tag['Delay'] = nbt.TAG_Short(0)
        # Boost Spawners - Only places the tags if they do not already exist
        # Doubles most default settings
        if (cfg.boost_spawners is True):
            try: root_tag['SpawnCount']
            except: root_tag['SpawnCount'] = nbt.TAG_Short(8)
            try: root_tag['MaxNearbyEntities']
            except: root_tag['MaxNearbyEntities'] = nbt.TAG_Short(16)
            try: root_tag['MinSpawnDelay']
            except: root_tag['MinSpawnDelay'] = nbt.TAG_Short(100)
            try: root_tag['MaxSpawnDelay']
            except: root_tag['MaxSpawnDelay'] = nbt.TAG_Short(400)
            try: root_tag['RequiredPlayerRange']
            except: root_tag['RequiredPlayerRange'] = nbt.TAG_Short(32)
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


    def loadrandbooktext(self):
        #This error should never trip. The loot generator shouldn't ask for books if the folder is empty
        if os.path.isdir(os.path.join(sys.path[0],'books')):
            book_path = os.path.join(sys.path[0],'books')
        elif os.path.isdir('books'):
            book_path = 'books'
        else:
            sys.exit("Error: Could not find the books folder!")
        #Make a list of all the txt files in the books directory
        booklist = []
        for file in os.listdir(book_path):
            if (str(file.lower()).endswith(".txt") and
                file.lower() is not "readme.txt"):
                booklist.append(file);
        #This error should also never trip.
        if (len(booklist) < 1):
            sys.exit("Error: There should be at least one book in the book folder")
        #Prevent unusual characters from being used
        valid_characters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ "
        #Open the book's text file
        bookfile = open(os.path.join(book_path, random.choice(booklist)))
        bookdata = bookfile.read().splitlines()
        bookfile.close()
        #Create NBT tag
        outtag = nbt.TAG_Compound()
        outtag['author'] = nbt.TAG_String(filter(lambda x: x in valid_characters, bookdata.pop(0)))
        outtag['title'] = nbt.TAG_String(filter(lambda x: x in valid_characters, bookdata.pop(0)))
        outtag["pages"] = nbt.TAG_List()
        #Slice the pages at 50 and the page text at 256 to match minecraft limits
        for p in bookdata[:50]:
            page = filter(lambda x: x in valid_characters, p)
            outtag["pages"].append(nbt.TAG_String(page[:256]))

        return outtag


    def loadrandfortune(self):
        fortune = '...in bed.'   #The default

        # Deal with missing fortune file with default
        if os.path.isfile(os.path.join(sys.path[0],'fortunes.txt')) == False:
            return fortune

        # Retrieve a random line from a file, reading through the file once
        # Prevents us from having to load the whole file in to memory
        forune_file = open(os.path.join(sys.path[0],'fortunes.txt'))
        lineNum = 0
        while 1:
            aLine = forune_file.readline()
            if not aLine:
                break
            if aLine[0] == '#' or aLine == '':
                continue
            lineNum = lineNum + 1
            # How likely is it that this is the last line of the file?
            if random.uniform(0,lineNum)<1:
                fortune = aLine.rstrip()
        forune_file.close()
        return fortune


    def buildItemTag(self, i):
        item_tag = nbt.TAG_Compound()
        # Standard stuff
        item_tag['id'] = nbt.TAG_Short(i.id)
        item_tag['Damage'] = nbt.TAG_Short(i.damage)
        # Enchantments
        if len(i.enchantments) > 0:
            item_tag['tag'] = nbt.TAG_Compound()
            if (i.flag == 'ENCH_BOOK'):
                item_tag['tag']['StoredEnchantments'] = nbt.TAG_List()
                elist = item_tag['tag']['StoredEnchantments']
            else:
                item_tag['tag']['ench'] = nbt.TAG_List()
                elist = item_tag['tag']['ench']
            for e in i.enchantments:
                e_tag = nbt.TAG_Compound()
                e_tag['id'] = nbt.TAG_Short(e['id'])
                e_tag['lvl'] = nbt.TAG_Short(e['lvl'])
                elist.append(e_tag)
        # Custom Potion Effects
        if i.p_effect != '':
            try: item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()
            item_tag['tag']['CustomPotionEffects'] = nbt.TAG_List()
            elist = item_tag['tag']['CustomPotionEffects']
            for e in i.p_effect.split(','):
                id, amp, dur = e.split('-')
                e_tag = nbt.TAG_Compound()
                e_tag['Id'] = nbt.TAG_Byte(id)
                e_tag['Amplifier'] = nbt.TAG_Byte(amp)
                e_tag['Duration'] = nbt.TAG_Int(dur)
                elist.append(e_tag)
        # Naming
        if i.customname != '':
            try: item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()
            item_tag['tag']['display'] = nbt.TAG_Compound()
            item_tag['tag']['display']['Name'] = nbt.TAG_String(i.customname)
        # Lore
        if i.lore != '':
            try: item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()
            try: item_tag['tag']['display']
            except:
                item_tag['tag']['display'] = nbt.TAG_Compound()
            item_tag['tag']['display']['Lore'] = nbt.TAG_List()
            loredata = i.lore.split(':')
            for loretext in loredata[:5]:
                item_tag['tag']['display']['Lore'].append(nbt.TAG_String(loretext[:50]))
        #Special flags
        # Dyed
        if (i.flag == 'DYED'):
            try: item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()
            try: item_tag['tag']['display']
            except:
                item_tag['tag']['display'] = nbt.TAG_Compound()
            if i.flagparam == '':
                item_tag['tag']['display']['color'] = nbt.TAG_Int(random.randint(0, 16777215))
            else:
                item_tag['tag']['display']['color'] = nbt.TAG_Int(i.flagparam)
        # special case for written books
        if (i.flag == 'WRITTEN'):
            item_tag['tag'] = self.loadrandbooktext()
        return item_tag


    def addchest(self, loc, tier=-1, loot=[]):
        level = loc.y/self.room_height
        if (tier < 0):
            if (self.levels > 1):
                tierf = (float(level) /
                         float(self.levels-1) *
                         float(loottable._maxtier-2))+1.5
                tierf = min(loottable._maxtier-1, tierf)
            else:
                tierf = loottable._maxtier-1
            tier = max(1, int(tierf))
            #print 'Adding chest: level',level+1,'tier',tier
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Chest')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        inv_tag = nbt.TAG_List()
        root_tag['Items'] = inv_tag
        if len(loot) == 0:
            loot = list(loottable.rollLoot(tier, level+1))
        for i in loot:
            if i.file != '':
                item_tag = item_tag = nbt.load(i.file)
            else:
                item_tag = self.buildItemTag(i)
            # Set the slot and count
            item_tag['Slot'] = nbt.TAG_Byte(i.slot)
            item_tag['Count'] = nbt.TAG_Byte(i.count)
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

    def addtrap(self, loc, name=None):
        if name == None:
            name = weighted_choice(cfg.master_dispensers)
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Trap')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        inv_tag = nbt.TAG_List()
        root_tag['Items'] = inv_tag
        item_tag = nbt.TAG_Compound()
        item_tag['Slot'] = nbt.TAG_Byte(0)
        item_tag['Count'] = nbt.TAG_Byte(int(cfg.lookup_dispensers[name][1]))
        item_tag['id'] = nbt.TAG_Short(loottable.items.byName(name).value)
        item_tag['Damage'] = nbt.TAG_Short(loottable.items.byName(name).data)
        inv_tag.append(item_tag)
        self.tile_ents[loc] = root_tag

    def addentity(self, root_tag):
        pos = Vec(
            root_tag['Pos'][0].value,
            root_tag['Pos'][1].value,
            root_tag['Pos'][2].value
        )
        self.ents[pos] = root_tag

    def setroom(self, coord, room):
        if coord not in self.rooms:
            self.rooms[coord] = room
            #print 'setroom:', coord
            return room.placed()
        print 'FATAL: Tried to place a room in a filled location!'
        print coord
        for p in self.rooms.keys():
            print p,
        print
        sys.exit()

    def genrooms(self, args_entrance):
        # Generate the maze used for room and hall placement.
        # stairwells contains the lower half of a stairwell. 
        self.stairwells = []
        entrance_pos = None
        exit_pos = None
        # The size of our dungeon. Note this is once less in the depth
        # dimension, because for most of the dungeon we don't want multilevel
        # rooms to extend to the last level. 
        dsize = Vec(self.xsize, self.levels-1, self.zsize)
        # Some convenient lookups.
        # dirs holds vectors for moving in a cardinal direction.
        dirs = {'N': Vec(0,0,-1),
                'E': Vec(1,0,0),
                'S': Vec(0,0,1),
                'W': Vec(-1,0,0)}
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
        if (args_entrance is not None):
            x = args_entrance[0]
            z = args_entrance[1]
        else:
            x = random.randint(0, self.xsize-1)
            z = random.randint(0, self.zsize-1)

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
            if (y == self.levels-1):
                dsize = dsize.down(1)
            # The level starts here.
            level_start = Vec(x,y,z)
            # The first cell contains an entrance. This is a tower if we are on
            # level 1, otherwise it's a stairwell. 
            if (y == 0):
                # Add the entrance cell to the stairwells list.
                self.stairwells.append(Vec(x,y,z))
                # For all levels except the last level, rooms can be as big as
                # they want. For the last level it has to be 1x1x1.
                maxsize = Vec(10,18,10)
                if (y == self.levels-1):
                    maxsize = Vec(1,1,1)
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
                #Any other start cell on a lower level is a stairwell
                self.stairwells.append(Vec(x,y,z))
                maxsize = Vec(10,18,10)
                if (y == self.levels-1):
                    maxsize = Vec(1,1,1)
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
            if (y == self.levels-1):
                # Try to find a location as far away from the level_start as
                # possible.
                pos = Vec(0,y,0)
                if (level_start.x < self.xsize/2):
                    pos.x = self.xsize-1
                if (level_start.z < self.zsize/2):
                    pos.z = self.zsize-1
                exit_pos = pos
                # Pick a treasure capable room
                room, pos = rooms.pickRoom(self, dsize, pos, treasure=True,
                                           room_list = cfg.master_treasure,
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
            while 1:
                # Walk the maze.
                if self.args.debug == True:
                    self.printmaze(y, cursor=Vec(x,y,z))
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
                        (self.maze[Vec(nx,y,nz)].state == state.BLANK or
                         self.maze[Vec(nx,y,nz)].state == state.USED)):
                        # For blank cells, we generate a new room
                        if self.maze[Vec(nx,y,nz)].state == state.BLANK:
                            room, pos = rooms.pickRoom(self, dsize, Vec(nx,y,nz))
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
                            root = ds.find(Vec(nx,y,nz))
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
                    #print 'Hunting...'
                    for p in iterate_plane(Vec(0,y,0),
                                           Vec(self.xsize-1,y,self.zsize-1)):
                        # Cell was connected, keep looking.
                        if (self.maze[Vec(p.x,y,p.z)].state ==
                            state.CONNECTED
                            or
                            self.maze[Vec(p.x,y,p.z)].state ==
                            state.RESTRICTED):
                            continue
                        # Cell is disconnected. Let's try to connect it to a
                        # neighbor. First, catalog which directions have a
                        # connected neighbor. 
                        neighbors = []
                        for d in dkeys:
                            key = Vec(p.x,y,p.z)+dirs[d]
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
                        if (self.maze[Vec(x,y,z)].state == state.BLANK):
                            room, pos = rooms.pickRoom(self, dsize, Vec(x,y,z))
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
                            root = ds.find(Vec(x,y,z))
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
                    for p in iterate_plane(Vec(0,y,0),
                                           Vec(self.xsize-1,y,self.zsize-1)):
                        for d in dirs.keys():
                            nx = p.x + dirs[d].x
                            nz = p.z + dirs[d].z
                            if (nx >= 0 and
                                nz >= 0 and
                                nx < self.xsize and
                                nz < self.zsize):
                                if (self.halls[p.x][y][p.z][sides[d]] is not 1 and
                                    self.halls[nx][y][nz][osides[d]] is not 1 and
                                    random.randint(1,100) <= cfg.loops):
                                    self.halls[p.x][y][p.z][sides[d]] = 1
                                    self.halls[nx][y][nz][osides[d]] = 1
                    if self.args.debug == True:
                        print 'Post loops:'
                        self.printmaze(y, cursor=Vec(x,y,z))
                    # Rebuild the depth tree.
                    # The first room on this level has a depth of 1
                    self.maze[level_start].depth = 1
                    recurse = True
                    while (recurse == True):
                        recurse = False
                        for p in iterate_plane(Vec(0,y,0),
                                           Vec(self.xsize-1,y,self.zsize-1)):
                            if (self.maze[Vec(p.x,y,p.z)].depth == maxdepth):
                                recurse = True
                                depth = maxdepth
                                for d in dirs.keys():
                                    if (self.halls[p.x][y][p.z][sides[d]]==1):
                                        depth = min(
                                self.maze[Vec(p.x,y,p.z)+dirs[d]].depth+1,
                                self.maze[Vec(p.x,y,p.z)].depth)
                                        self.maze[Vec(p.x,y,p.z)].depth = depth
                    # Find the deepest cell on this level that can contain a
                    # stairwell.
                    depth = 0
                    for p in iterate_plane(Vec(0,y,0),
                                           Vec(self.xsize-1,y,self.zsize-1)):
                        if (self.maze[Vec(p.x,y,p.z)].depth > depth and
                            self.rooms[Vec(p.x,y,p.z)]._is_stairwell == True):
                            depth = self.maze[Vec(p.x,y,p.z)].depth
                            x = p.x
                            z = p.z
                    break

        # Connect the treasure room. Find the deepest cell that has a neighbor
        # with a depth of zero and connect it. 
        depth = 0
        point = Vec(0,0,0)
        opoint = Vec(0,0,0)
        dr = 'N'
        for p in iterate_plane(Vec(0,y,0), Vec(self.xsize-1,y,self.zsize-1)):
            if (self.maze[Vec(p.x,y,p.z)].depth > depth):
                for d,v in dirs.items():
                    if (p+v in self.maze and self.maze[p+v].depth == 0):
                        point = p
                        opoint = p+v
                        depth = self.maze[Vec(p.x,y,p.z)].depth
                        dr = d
        self.halls[point.x][y][point.z][sides[dr]] = 1
        self.halls[opoint.x][y][opoint.z][osides[dr]] = 1
        if self.args.debug == True:
            print 'Post treasure:'
            self.printmaze(y, cursor=Vec(x,y,z))

        self.entrance_pos = entrance_pos
        if self.args.debug:
            print 'Entrance:', entrance_pos
            print 'Exit:', exit_pos


    def genhalls(self):
        '''Step through all rooms and generate halls where possible'''
        for y in xrange(self.levels):
            for x in xrange(self.xsize):
                for z in xrange(self.zsize):
                    pos = Vec(x,y,z)
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
                                   nextpos = pos+pos.d(d)
                                   nextd = (d+2)%4
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
                            self.rooms[pos].halls[d] = halls.new('blank',
                                                             self.rooms[pos],
                                                             d, 6)

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

    def genruins(self, world):
        for pos in self.rooms:
            if (pos.y == 0 and
                len(self.rooms[pos].ruins) == 0):
                if pos == self.entrance.parent.pos:
                    ruin = ruins.new(weighted_choice(cfg.master_entrances),
                                 self.rooms[pos])
                else:
                    ruin = ruins.new(weighted_choice(cfg.master_ruins),
                                 self.rooms[pos])
                self.rooms[pos].ruins.append(ruin)
                ruin.placed(world)

    def placetorches(self, level=0):
        '''Place a proportion of the torches where possible'''
        if (self.levels > 1):
            perc = int(float(level) / float(self.levels-1) *
                (cfg.torches_bottom-cfg.torches_top) +
                cfg.torches_top)
        else:
            perc = cfg.torches_top
        count = 0
        maxcount = 0
        for pos, val in self.torches.items():
            if (pos.up(1).y/self.room_height == level):
                maxcount += 1
        maxcount = perc * maxcount / 100
        offset = 3 - cfg.torches_position
        dirs = {
            '1': Vec(-1,0,0),
            '2': Vec(1,0,0),
            '3': Vec(0,0,-1),
            '4': Vec(0,0,1)
        }
        for pos, val in self.torches.items():
            attach_pos = pos.down(offset) + dirs[str(val)]
            if (count < maxcount and
                pos in self.blocks and
                self.blocks[pos.down(offset)].material == materials.Air and
                self.blocks[attach_pos].material == materials._wall and
                pos.up(1).y/self.room_height == level):
                #self.blocks[pos.down(offset)].material = materials.Torch
                self.setblock(pos.down(offset), materials.Torch, val)
                count += 1
        if (level < self.levels-1):
            self.placetorches(level+1)

    def placedoors(self, perc):
        '''Place a proportion of the doors where possible'''
        count = 0
        # in MC space, 0=W, 1=N, 2=E, 3=S
        # doors are populated N->S and W->E
        # This holds direction and starting hinge side
        #           N      E      S      W
        doordat = ((1,1), (2,1), (3,0), (0,0))
        maxcount = perc * len(self.doors) / 100
        for pos, door in self.doors.items():
            if (count < maxcount):
                x = doordat[door.direction][1]
                for dpos in door.doors:
                    if(dpos in self.blocks and  self.blocks[dpos].material == materials.Air):
                        self.setblock(dpos, materials._wall, hide=True)
                        self.blocks[dpos.down(1)].material = door.material
                        #self.blocks[dpos.down(1)].data = doordat[door.direction][x] | 8 # Top door
                        self.blocks[dpos.down(1)].data = 8+x # Top door & hinge
                        self.blocks[dpos.down(2)].material = door.material
                        self.blocks[dpos.down(2)].data = doordat[door.direction][0]
                    x = 1 - x
                count += 1

    def placechests(self, level=0):
        '''Place chests in the dungeon. This is called with no arguments,
        and iterates over itself to fill each level'''
        # First we build a weighted list of rooms. Rooms are more likely to
        # contain a chest if they have fewer halls.
        candidates = []
        chests = ceil(cfg.chests * float(self.xsize * self.zsize) / 10.0)
        # Blocks we are not allowed to place a chest upon
        ignore = (0, 6, 8, 9, 10, 11, 18, 20, 23, 25, 26, 37, 38, 39, 40,
                  44, 50, 51, 52, 53, 54, 55, 58, 59, 60, 61, 62, 63, 64, 65,
                  66, 67, 68, 69, 70, 71, 72, 75, 76, 77, 78, 81, 83, 84, 85,
                  86, 88, 90, 91, 92, 93, 94, 95, 96, 101, 102, 103, 104, 105,
                  106, 107, 108, 109, 111, 113, 114, 115, 116, 117, 118, 119,
                  120)
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
            candidates.append((room, 20**hcount-1))
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
                if(self.blocks[point].material.val not in ignore and
                   self.blocks[point.up(1)].material.val == 0 and 
                   self.blocks[point.up(2)].material.val == 0):
                    points.append(point)
                if (self.blocks[point.down(1)].material.val not in ignore and
                    self.blocks[point].material.val == 0 and
                    self.blocks[point.up(1)].material.val == 0):
                    points.append(point.down(1))
            # Pick a spot, if one exists.
            if (len(points) > 0):
                point = random.choice(points)
                self.setblock(point.up(1), materials.Chest)
                self.addchest(point.up(1))
                chests -= 1
        if (level < self.levels-1):
            self.placechests(level+1)


    def placespawners(self, level=0):
        '''Place spawners in the dungeon. This is called with no arguments,
        and iterates over itself to fill each level'''
        # First we build a weighted list of rooms. Rooms are more likely to
        # contain a spawners if they have fewer halls.
        candidates = []
        spawners = ceil(cfg.spawners * float(self.xsize * self.zsize) / 10.0)
        # Blocks we are not allowed to place a spawner upon
        ignore = (0, 6, 8, 9, 10, 11, 18, 20, 23, 25, 26, 37, 38, 39, 40,
                  44, 50, 51, 52, 53, 54, 55, 58, 59, 60, 61, 62, 63, 64, 65,
                  66, 67, 68, 69, 70, 71, 72, 75, 76, 77, 78, 81, 83, 84, 85,
                  86, 88, 90, 91, 92, 93, 94, 95, 96, 101, 102, 103, 104, 105,
                  106, 107, 108, 109, 111, 113, 114, 115, 116, 117, 118, 119,
                  120)
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
            candidates.append((room, 20**hcount-1))
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
                    if(self.blocks[point].material.val not in ignore and
                       self.blocks[point.up(1)].material.val == 0):
                        points.append(point)
            else:
                # Hidden spawners, just on the other side of walls.
                y = room.canvasHeight()
                for x in xrange(self.room_size):
                    for z in xrange(self.room_size):
                        p = room.loc+Vec(x,y,z)
                        adj = [Vec(1,0,0), Vec(0,0,1),
                               Vec(-1,0,0), Vec(0,0,-1)]
                        walls = 0
                        for q in adj:
                            if (p+q in self.blocks and
                                self.getblock(p+q) == materials._wall):
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
        if (level < self.levels-1):
            self.placespawners(level+1)


    def placeportcullises(self, perc):
        '''Place a proportion of the portcullises where possible'''
        count = 0
        maxcount = perc * len(self.portcullises) / 100
        for pos, portcullis in self.portcullises.items():
            if (count < maxcount):
                for dpos, val in portcullis.portcullises.items():
                    if(dpos in self.blocks and self.blocks[dpos].material == materials.Air):
                        for x in xrange(portcullis.size):
                            self.blocks[dpos.down(x)].material = portcullis.material
                count += 1

    def renderhallpistons(self):
        '''Locate hallway candidates for piston traps and draw them'''
        if cfg.hall_piston_traps <= 0:
            return
        # Some lookups
        # sides maps a dir to a room side for hall placement.
        # TODO: This is still backwards from the coordinate switch.
        # S == E, E == S, etc. 
        sides = {'N': 3,
                 'S': 1,
                 'E': 2,
                 'W': 0}
        # Materials lookup
        mat = {
            'CC': [materials._ceiling, 0],
            'SF': [materials._subfloor, 0],
            'ST': [materials.Stone, 0],
            'R0': [materials.RedStoneWire, 0],
            'R1': [materials.RedStoneWire, 15],
            'o-': [materials.RedStoneTorchOff, 4],
            '-*': [materials.RedStoneTorchOn, 3],
            '**': [materials.RedStoneTorchOn, 5],
            'AR': [materials.Air, 0],
            'P0': [materials.RedStoneRepeaterOff, 0],
            'P1': [materials.RedStoneRepeaterOn, 2],
            'PI': [materials.StickyPiston, 4+8],
            'PE': [materials.PistonExtension, 4+8],
            'TR': [materials.RedStoneRepeaterOff, 17],
            #'XX': [materials.Air, 0],
        }
        # Piston trap 
        # ptrap1[level][sw][sl]
        ptrap = [[
            ['CC', 'CC', 'CC', 'CC', 'CC', 'CC'],
            ['CC', 'CC', 'CC', 'CC', 'CC', 'CC'],
            ['CC', 'CC', 'CC', 'CC', 'CC', 'CC'],
            ['CC', 'CC', 'CC', 'CC', 'CC', 'CC'],
        ],[
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
            ['AR', 'AR', 'AR', 'AR', 'AR', 'AR'],
            ['AR', 'R1', '**', 'AR', 'AR', 'AR'],
            ['ST', 'ST', 'ST', 'ST', 'ST', 'ST'],
        ],[
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
            ['AR', 'AR', 'AR', 'R1', 'AR', 'AR'],
            ['o-', 'ST', 'ST', 'P0', 'R0', 'AR'],
            ['ST', 'ST', 'ST', 'ST', 'ST', 'ST'],
        ],[
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
            ['AR', 'AR', 'R1', 'ST', 'AR', 'AR'],
            ['R0', 'AR', 'AR', 'ST', 'ST', 'R0'],
            ['ST', 'ST', 'ST', 'ST', 'ST', 'ST'],
        ],[
            ['R0', 'R0', 'R0', 'PE', 'R0', 'R0'],
            ['R0', 'o-', 'ST', 'PI', 'ST', 'R0'],
            ['ST', '-*', 'R1', 'ST', 'ST', 'ST'],
            ['ST', 'ST', 'ST', 'ST', 'ST', 'ST'],
        ],[
            ['SF', 'SF', 'SF', 'SF', 'SF', 'SF'],
            ['SF', 'SF', 'SF', 'SF', 'SF', 'SF'],
            ['SF', 'SF', 'SF', 'SF', 'SF', 'SF'],
            ['SF', 'SF', 'SF', 'SF', 'SF', 'SF'],
        ]]
        traps = []
        # Make traps reset themselves
        if (cfg.resetting_hall_pistons == True):
            ptrap[4][1][0] = 'TR'
            ptrap[4][1][1] = 'AR'

        # Build a list of all the rooms and directions to check. We'll iterate
        # through them randomly, and remove cull out the overlaps as we go. 
        halls = {}
        # These are the West->East checks. 
        for y in xrange(0, self.levels):
            for z in xrange(0, self.zsize-1):
                for x in xrange(0, self.xsize):
                    halls[str(Vec(x,y,z))+'E'] = {'room': Vec(x,y,z),
                                                  'd': 'E'}
        # These are the North->South checks. 
        for y in xrange(0, self.levels):
            for z in xrange(0, self.zsize):
                for x in xrange(0, self.xsize-1):
                    halls[str(Vec(x,y,z))+'S'] = {'room': Vec(x,y,z),
                                                  'd': 'S'}
        # Randomize our search
        hallkeys = halls.keys()
        random.shuffle(hallkeys)

        # Now, go through all the keys and pick which traps to place.
        # To qualify, halls must be 1 or 2 blocks wide, at least 8 blocks
        # long. Single halls can be at any offset (just build on the inside
        # edge). Double halls must be between offset 3 and 9. 
        for key in hallkeys:
            if key not in halls:
                continue
            room = halls[key]['room']
            d = halls[key]['d']
            x = room.x
            y = room.y
            z = room.z

            if d == 'E':
                rpos1 = Vec(x,y,z)
                rpos2 = Vec(x,y,z+1)
                room1 = self.rooms[rpos1]
                room2 = self.rooms[rpos2]
                size = room1.halls[sides['E']].size - 2
                offset = room1.halls[sides['E']].offset
                length = room1.hallLength[sides['E']] + \
                         room2.hallLength[sides['W']]
                pos = Vec(0,0,0)
                if (size >= 1 and
                    size <= 2 and
                    length >= 8 and
                    #room1.features[0]._name != 'secretroom' and
                    #room2.features[0]._name != 'secretroom' and
                    room1._pistontrap == True and
                    room2._pistontrap == True and
                    random.randint(1,100) <= cfg.hall_piston_traps):
                    if (size == 1):
                        pos = room1.loc + Vec(offset,
                                          0,
                                          17-room1.hallLength[sides['E']])
                        sw = Vec(-1,0,0)
                        if offset < 8:
                            pos += Vec(2,0,0)
                            sw = Vec(1,0,0)
                        traps.append({'pos': pos,
                                      'length': length-7,
                                      'sw': sw,
                                      'sl': Vec(0,0,1)})
                    elif(size == 2 and offset >= 3 and offset <= 9):
                        pos = room1.loc + Vec(offset,
                                          0,
                                          17-room1.hallLength[sides['E']])
                        traps.append({'pos': pos,
                                      'length': length-7,
                                      'sw': Vec(-1,0,0),
                                      'sl': Vec(0,0,1)})
                        traps.append({'pos': pos+Vec(3,0,0),
                                  'length': length-7,
                                      'sw': Vec(1,0,0),
                                      'sl': Vec(0,0,1)})
                    else:
                        continue
                    # Remove any overlapping halls
                    k = str(Vec(x,y,z))+'S'
                    if k in halls:
                        del halls[k]
                    k = str(Vec(x-1,y,z))+'S'
                    if k in halls:
                        del halls[k]
                    k = str(Vec(x,y,z+1))+'S'
                    if k in halls:
                        del halls[k]
                    k = str(Vec(x-1,y,z+1))+'S'
                    if k in halls:
                        del halls[k]

            if d == 'S':
                rpos1 = Vec(x,y,z)
                rpos2 = Vec(x+1,y,z)
                room1 = self.rooms[rpos1]
                room2 = self.rooms[rpos2]
                size = room1.halls[sides['S']].size - 2
                offset = room1.halls[sides['S']].offset
                length = room1.hallLength[sides['S']] + \
                         room2.hallLength[sides['N']]
                pos = Vec(0,0,0)
                if (size >= 1 and
                    size <= 2 and
                    length >= 8 and
                    #room1.features[0]._name != 'secretroom' and
                    #room2.features[0]._name != 'secretroom' and
                    room1._pistontrap == True and
                    room2._pistontrap == True and
                    random.randint(1,100) <= cfg.hall_piston_traps):
                    if (size == 1):
                        pos = room1.loc + Vec(
                                          17-room1.hallLength[sides['S']],
                                          0,
                                          offset)
                        sw = Vec(0,0,-1)
                        if offset < 8:
                            pos += Vec(0,0,2)
                            sw = Vec(0,0,1)
                        traps.append({'pos': pos,
                                      'length': length-7,
                                      'sw': sw,
                                      'sl': Vec(1,0,0)})
                    elif(size == 2 and offset >= 3 and offset <= 9):
                        pos = room1.loc + Vec(
                                          17-room1.hallLength[sides['S']],
                                          0,
                                          offset)
                        traps.append({'pos': pos,
                                      'length': length-7,
                                      'sw': Vec(0,0,-1),
                                      'sl': Vec(1,0,0)})
                        traps.append({'pos': pos+Vec(0,0,3),
                                      'length': length-7,
                                      'sw': Vec(0,0,1),
                                      'sl': Vec(1,0,0)})
                    else:
                        continue
                    # Remove any overlapping halls
                    k = str(Vec(x,y,z))+'E'
                    if k in halls:
                        del halls[k]
                    k = str(Vec(x,y,z-1))+'E'
                    if k in halls:
                        del halls[k]
                    k = str(Vec(x+1,y,z))+'E'
                    if k in halls:
                        del halls[k]
                    k = str(Vec(x+1,y,z-1))+'E'
                    if k in halls:
                        del halls[k]

        # Render the traps
        for trap in traps:
            pos = trap['pos']
            length = trap['length']
            sw = trap['sw']
            sl = trap['sl']
            # x = width
            # z = length
            # y = depth
            # Rotate some materials according to the direction of the hall.
            # Hall runs East
            if sl == Vec(0,0,1):
                mat['o-'] = [materials.RedStoneTorchOff, 4]
                mat['-*'] = [materials.RedStoneTorchOn, 3]
                mat['P0'] = [materials.RedStoneRepeaterOff, 0]
                mat['P1'] = [materials.RedStoneRepeaterOn, 2]
                # South side
                if sw == Vec(1,0,0):
                    mat['PI'] = [materials.StickyPiston, 4+8]
                    mat['PE'] = [materials.PistonExtension, 4+8]
                    mat['TR'] = [materials.RedStoneRepeaterOff, 16+1]
                # North side
                else:
                    mat['PI'] = [materials.StickyPiston, 5+8]
                    mat['PE'] = [materials.PistonExtension, 5+8]
                    mat['TR'] = [materials.RedStoneRepeaterOff, 16+3]
            # Hall runs South
            else:
                mat['o-'] = [materials.RedStoneTorchOff, 2]
                mat['-*'] = [materials.RedStoneTorchOn, 1]
                mat['P0'] = [materials.RedStoneRepeaterOff, 3]
                mat['P1'] = [materials.RedStoneRepeaterOn, 1]
                # East side
                if sw == Vec(0,0,1):
                    mat['PI'] = [materials.StickyPiston, 2+8]
                    mat['PE'] = [materials.PistonExtension, 2+8]
                    mat['TR'] = [materials.RedStoneRepeaterOff, 16+2]
                # West side
                else:
                    mat['PI'] = [materials.StickyPiston, 3+8]
                    mat['PE'] = [materials.PistonExtension, 3+8]
                    mat['TR'] = [materials.RedStoneRepeaterOff, 16+0]
            # This is the first trigger mechanism. 
            for p in iterate_cube(Vec(0,0,0), Vec(3,5,2)):
                q = pos + sw*p.x + sl*p.z + Vec(0,1,0)*p.y
                block = ptrap[p.y][p.x][p.z]
                if block is not 'XX':
                    m = mat[block]
                    self.setblock(q, m[0], m[1], hide=True)
            # First pressure plate
            p1 = pos + sw*-1 + sl*2 + Vec(0,1,0)*3
            self.setblock(p1, materials.StonePressurePlate)
            #c = 0
            # The piston section. Repeat this, alternating configurations for
            # the length of the hall minus some space at the end. 
            for i in xrange(0,length):
                # In 1.5 snapshots, repeaters don't power the block they sit on.
                #if c == 0:
                #    ptrap[2][1][3] = 'R1'
                #else:
                #    ptrap[2][1][3] = 'P1'
                #c  = (c+1)%2
                for p in iterate_cube(Vec(0,0,3), Vec(3,5,3)):
                    q = pos + sw*p.x + sl*(p.z+i) + Vec(0,1,0)*p.y
                    block = ptrap[p.y][p.x][p.z]
                    if block is not 'XX':
                        m = mat[block]
                        self.setblock(q, m[0], m[1], hide=True)
            # The return trigger mechanism.
            for p in iterate_cube(Vec(0,0,4), Vec(3,5,5)):
                q = pos + sw*p.x + sl*p.z  + sl*(length-1) + Vec(0,1,0)*p.y
                block = ptrap[p.y][p.x][p.z]
                if block is not 'XX':
                    m = mat[block]
                    self.setblock(q, m[0], m[1], hide=True)
            # Return pressure plate
            p2 = pos + sw*-1 + sl*4  + sl*(length-1) + Vec(0,1,0)*3
            self.setblock(p2, materials.StonePressurePlate)
            # Lava
            for p in iterate_cube(p1.down(2), p2.down(2)):
                self.setblock(p, materials.Lava)


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
        count = len(self.rooms)*4
        self.pm.init(count, label='Rendering halls:')
        for pos in self.rooms:
            self.pm.update_left(count)
            count -= 4
            for x in xrange(0,4):
                if (self.rooms[pos].halls[x]):
                    self.rooms[pos].halls[x].render()
        self.pm.set_complete()

    def renderfloors(self):
        ''' Call render() on all floors'''
        count = len(self.rooms)
        self.pm.init(count,label='Rendering floors:')
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

    def outputterminal(self, floor):
        '''Print a slice (or layer) of the dungeon block buffer to the termial.
        We "look-through" any air blocks to blocks underneath'''
        layer = (floor-1)*self.room_height
        for z in xrange(self.zsize*self.room_size):
            for x in xrange(self.xsize*self.room_size):
                y = layer
                while (y < layer + self.room_height - 1 and
                       Vec(x,y,z) in self.blocks and
                         (self.blocks[Vec(x,y,z)].hide == True or
                          self.blocks[Vec(x,y,z)].material == materials.Air or
                          self.blocks[Vec(x,y,z)].material == materials._ceiling)):
                    y += 1
                if (Vec(x,y,z) in self.blocks and
                    self.blocks[Vec(x,y,z)].hide == False):
                    mat = self.blocks[Vec(x,y,z)].material
                    if (mat._meta == True):
                        mat.update(x,y,z,
                                   self.xsize*self.room_size,
                                   self.levels*self.room_height,
                                   self.zsize*self.room_size)
                    sys.stdout.write(mat.c)
                else:
                    sys.stdout.write(materials.NOBLOCK)
            print


    def outputhtml(self, basename, force):
        '''Print all levels of the dungeon block buffer to html.
        We "look-through" any air blocks to blocks underneath'''
        # First search for existing files
        if (force == False):
            for floor in xrange(self.levels):
                filename = basename+'-'+str(floor+1)+'.html'
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
            layer = floor*self.room_height
            # Build the form.
            form = '''
            <form action="foo">
            <select name="newurl" onchange="menu_goto(this.form)">
            '''
            for menufloor in xrange(self.levels):
                path = basename+'-'+str(menufloor+1)+'.html'
                (head, tail) = os.path.split(path)
                selected = ''
                if (floor == menufloor):
                    selected = ' selected="selected"'
                form += '<option value="%s"%s>Level %d</option>' % (
                    tail, selected, menufloor+1)
            form += '</select></form><br>'
            # Write the floor file.
            filename = basename+'-'+str(floor+1)+'.html'
            print 'Writing:',filename
            f = open(filename, 'w')
            f.write(header+form)
            f.write('<table border=0 cellpadding=0 cellspacing=0>')
            for z in xrange(self.zsize*self.room_size):
                f.write('<tr>')
                for x in xrange(self.xsize*self.room_size):
                    y = layer
                    while (Vec(x,y,z) in self.blocks and
                            (self.blocks[Vec(x,y,z)].hide == True or
                             self.blocks[Vec(x,y,z)].material ==
                             materials.Air or
                             self.blocks[Vec(x,y,z)].material ==
                             materials._ceiling)):
                        y += 1
                    if (Vec(x,y,z) in self.blocks):
                        mat = self.blocks[Vec(x,y,z)].material
                        if (mat._meta == True):
                            mat.update(x,y,z,
                                       self.xsize*self.room_size,
                                       self.levels*self.room_height,
                                       self.zsize*self.room_size)
                            self.blocks[Vec(x,y,z)].data = mat.data
                        dat = self.blocks[Vec(x,y,z)].data

                        # Doors are ... different
                        if (mat == materials.WoodenDoor or
                            mat == materials.IronDoor):
                            dat2 = self.blocks[Vec(x,y+1,z)].data
                            dat = ((dat & 1) << 3) + dat2

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
        dirs = {3: Vec(-1,0,0),
                1: Vec(1,0,0),
                2: Vec(0,0,1),
                0: Vec(0,0,-1)}

        # Find them
        for p in self.rooms:
            room = self.rooms[p]
            if room.features[0]._name == 'entrance':
                continue
            if room.features[0]._is_stairwell:
                continue
            if p.y < self.levels-1:
                droom = self.rooms[p.down(1)]
                if droom.features[0]._is_stairwell:
                    continue
            if room.size != Vec(1,1,1):
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
            room2 = self.rooms[p+dirs[d]]
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
            if random.randint(1,100) > cfg.secret_rooms:
                continue

            if self.args.debug == True:
                print 'Secret room from',room._name, 'to', room2._name
            # Override this room's feature
            room.features = []
            room.features.append(features.new(weighted_choice(cfg.master_srooms), room))
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
            od = (d+2)%4
            offset = room2.halls[od].offset
            if offset < 4:
                offset = 4
            if offset > 9:
                offset = 9
            room2.halls[od] = halls.new('single', room2, od, offset)


    def setentrance(self, world):
        if self.args.debug: print 'Extending entrance to the surface...'
        wcoord=Vec(self.entrance.parent.loc.x + self.position.x,
                   self.position.y - self.entrance.parent.loc.y,
                   self.entrance.parent.loc.z + self.position.z)
        if self.args.debug: print '   World coord:',wcoord
        baseheight = wcoord.y + 2 # plenum + floor
        #newheight = baseheight
        low_height = world.Height
        high_height = baseheight
        if self.args.debug: print '   Base height:',baseheight
        # List of blocks to ignore.
        # Leaves, trees, flowers, etc.
        ignore = (0,6,17,18,31,37,38,39,40,44,50,51,55,
                  59,63,64,65,66,68,70,71,72,75,76,
                  77,81,83,85,86,90,91,92,93,94, 99, 100, 103, 104, 105, 106,
                  111, 127)
        chunk = world.getChunk(wcoord.x>>4, wcoord.z>>4)
        for x in xrange(wcoord.x+4, wcoord.x+12):
            for z in xrange(wcoord.z+4, wcoord.z+12):
                xInChunk = x & 0xf
                zInChunk = z & 0xf
                # Heightmap is a good starting place, but I need to look
                # down through foliage.
                y = chunk.HeightMap[zInChunk, xInChunk]-1
                while (chunk.Blocks[xInChunk, zInChunk, y] in ignore):
                    y -= 1
                if (chunk.Blocks[xInChunk, zInChunk, y] == 9 or
                    chunk.Blocks[xInChunk, zInChunk, y] == 79):
                    self.entrance.inwater = True
                high_height = max(y, high_height)
                low_height = min(y, low_height)
        if self.args.debug:
            print "    Low height:",low_height
            print "   High height:",high_height
            if (self.entrance.inwater == True):
                print "   Entrance is in water."
        if (low_height - baseheight > 0):
            self.entrance.height += low_height - baseheight
            self.entrance.low_height += low_height - baseheight
        if (high_height - baseheight > 0):
            self.entrance.high_height += high_height - baseheight
        self.entrance.u = int(cfg.tower*self.entrance.u)
        # Check the upper bounds of the tower
        if (high_height + self.entrance.u >= world.Height):
            self.entrance.u = world.Height - 3 - high_height


    def applychanges(self, world):
        '''Write the block buffer to the specified world'''
        changed_chunks = set()
        num_blocks = len(self.blocks)
        # Hard mode
        if (self.dinfo['hard_mode'] is True):
            num = (self.zsize+10) * (self.xsize+10)
            pm = pmeter.ProgressMeter()
            pm.init(num, label='Filling in caves:')
            for z in xrange((self.position.z>>4)-5,
                            (self.position.z>>4)+self.zsize+5):
                for x in xrange((self.position.x>>4)-5,
                                (self.position.x>>4)+self.xsize+5):
                    pm.update_left(num)
                    num -= 1
                    if ((x,z) in self.good_chunks):
                        p = Vec(x,0,z)
                        chunk = world.getChunk(x, z)
                        miny = self.good_chunks[(x,z)]
                        air = ( chunk.Blocks[:,:,0:miny] == 0)
                        chunk.Blocks[air] = materials._floor.val
                        changed_chunks.add(chunk)
                        del(self.good_chunks[(x,z)])
            pm.set_complete()
        # Regeneration
        if self.args.command == 'regenerate':
            num = (self.zsize) * (self.xsize)
            pm = pmeter.ProgressMeter()
            pm.init(num, label='Regenerating resources/chests:')
            for z in xrange((self.position.z>>4),
                             (self.position.z>>4)+self.zsize):
                for x in xrange(self.position.x>>4,
                                 (self.position.x>>4)+self.xsize):
                    pm.update_left(num)
                    num -= 1
                    p = Vec(x,0,z)
                    chunk = world.getChunk(x, z)
                    # Repopulate any above ground chests
                    for tileEntity in chunk.TileEntities:
                        if (tileEntity["id"].value == "Chest"):
                            p = Vec(0,0,0)
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
                    chunk.Blocks[:,:,0:self.position.y] = materials.Stone.val
                    # Coal. 1% between 5 and 60
                    distribute(chunk, 5, min(self.position.y, 60),
                               1, materials.CoalOre)
                    ## Iron. .6% between 5 and 55
                    distribute(chunk, 5, min(self.position.y, 55),
                               .6, materials.IronOre)
                    ## Redstone. .8% between 5 and 20
                    distribute(chunk, 5, min(self.position.y, 20),
                               .8, materials.RedStoneOre)
                    ## Gold. .1% between 5 and 35
                    distribute(chunk, 5, min(self.position.y, 35),
                               .1, materials.GoldOre)
                    ## Lapis. .1% between 5 and 35
                    distribute(chunk, 5, min(self.position.y, 35),
                               .1, materials.LapisOre)
                    ## Diamond. .1% between 5 and 20
                    distribute(chunk, 5, min(self.position.y, 20),
                               .1, materials.DiamondOre)
                    ## Bedrock. 60% between 0 and 4
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
            chunk_z = z>>4
            chunk_x = x>>4
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
            if (mat._meta == True):
                mat.update(block.loc.x,block.loc.y,block.loc.z,
                           self.xsize*self.room_size,
                           self.levels*self.room_height,
                           self.zsize*self.room_size)
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
            if (cfg.silverfish > 0 and
                (val == 1 or val == 4 or val == 98) and
                random.randint(1,100) <= cfg.silverfish):
                if (val == 4):
                    val = 97
                    dat = 1
                elif (val == 1):
                    val = 97
                    dat = 0
                elif (val == 98 and dat == 0):
                    val = 97
                    dat = 2
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
        for ent in self.ents.values():
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
