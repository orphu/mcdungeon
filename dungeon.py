#!/usr/bin/python

import sys
import os
import platform
from random import *
import perlin

import cfg
import items
import loottable
import materials
import rooms
import halls
import floors
import features
import ruins
from utils import *
from pymclevel import mclevel, nbt

class Block(object):
    def __init__(self, loc):
        self.loc = loc
        self.material = None
        self.data = 0
        self.hide = False

class MazeCell(object):
    states = enum('BLANK', 'USED', 'CONNECTED')
    def __init__(self, loc):
        self.loc = loc
        self.depth = 0
        self.state = 0

class Dungeon (object):
    def __init__(self, xsize, zsize, levels, depths):
        self.rooms = {}
        self.depths = depths
        self.blocks = {}
        self.tile_ents = {}
        self.torches = {}
        self.doors = {}
        self.portcullises = {}
        self.entrance = None
        self.xsize = xsize
        self.zsize = zsize
        self.levels = levels
        self.maze = {}
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


    def setblock(self, loc, material, data=0, hide=False):
        # If material is None, remove this block
        if material == None:
            if loc in self.blocks:
                del(self.blocks[loc])
            return

        # Build a block if we need to 
        if loc not in self.blocks:
            self.blocks[loc] = Block(loc)

        # Setup the material
        self.blocks[loc].material = material

        # Set the data value
        if (data == 0):
            self.blocks[loc].data = material.data
        else:
            self.blocks[loc].data = data

        # Hide this from the map generator if requested
        self.blocks[loc].hide = hide

    def delblock(self, loc):
        if loc in self.blocks:
            del self.blocks[loc]

    def getblock(self, loc):
        if loc in self.blocks:
            return self.blocks[loc].material
        return False


    def findlocation(self, world, dungeon_locations):
        positions = {}
        bounds = world.bounds
        scx = world.playerSpawnPosition()[0]>>4
        scz = world.playerSpawnPosition()[2]>>4
        spawn_chunk = Vec(scx, 0, scz)
        print 'World bounds: (%d, %d) to (%d, %d)' % (bounds.getMinx(),
                                                      bounds.getMinz(),
                                                      bounds.getMaxx(),
                                                      bounds.getMaxz())
        print 'World chunks: (%d, %d) to (%d, %d)' % (bounds.getMincx(),
                                                      bounds.getMincz(),
                                                      bounds.getMaxcx(),
                                                      bounds.getMaxcz())
        print 'Spawn point: (%d, %d, %d)'%(world.playerSpawnPosition()[0],
                                           world.playerSpawnPosition()[1],
                                           world.playerSpawnPosition()[2])
        print 'Spawn chunk: (%d, %d)'%(scx, scz)
        print 'Minimum distance from spawn:', cfg.min_dist, 'chunks'
        print 'Maximum distance from spawn:', cfg.max_dist, 'chunks'
        # List of blocks to ignore when checking depth
        ignore = (0,6,8,9,10,11,17,18,37,38,39,40,44,50,51,55,
                  59,63,64,65,66,68,70,71,72,75,76,
                  77,81,83,85,86,90,91,92,93,94)
        print 'Bounds and chunk check...'
        for chunk in bounds.chunkPositions:
            # Does this chunk even exist?
            if (world.containsChunk(chunk[0], chunk[1]) == False):
                continue
            # First some basic distance from spawn checks...
            spin()
            chunk_box = Box(Vec(chunk[0], 0, chunk[1]-self.zsize+1),
                            self.xsize,
                            16,
                            self.zsize)
            dist_max = max(
                (spawn_chunk-chunk_box.loc).mag2d(),
                (spawn_chunk-(chunk_box.loc+Vec(self.xsize-1,0,0))).mag2d(),
                ((chunk_box.loc+Vec(0,0,self.zsize-1))-spawn_chunk).mag2d(),
                (spawn_chunk-(chunk_box.loc+
                 Vec(self.xsize-1,0,self.zsize-1))).mag2d()
            )
            dist_min = (spawn_chunk-Vec(clamp(spawn_chunk.x,
                                             chunk_box.loc.x,
                                             chunk_box.loc.x+self.xsize-1),
                                       0,
                                       clamp(spawn_chunk.z,
                                             chunk_box.loc.z,
                                             chunk_box.loc.z+self.zsize-1))).mag2d()
            # Don't overlap with spawn...
            if (chunk_box.containsPoint(spawn_chunk) == True):
                continue
            # Not too far away...
            if (dist_max > cfg.max_dist):
                continue
            # Not too close...
            if (dist_min < cfg.min_dist):
                continue
            # Looks good so far
            positions[Vec(chunk[0], 0, chunk[1])] = 1
        print 'Found',len(positions),'possible locations.'
        return self.bury(world, positions, dungeon_locations)

    def bury(self, world, positions, dungeon_locations):
        # Filter for the maximum distance.
        maxd = 1
        if (cfg.maximize_distance == True and
            len(dungeon_locations) > 0):
            print 'Marking distances...'
            for chunk in positions:
                spin()
                d = 2^64
                for dungeon in dungeon_locations:
                    d = min(d, (dungeon - chunk).mag2d())
                positions[chunk] = d
        depth_positions = {}
        final_positions = {}
        min_depth = (self.levels+1)*self.room_height
        bounds = world.bounds
        scx = world.playerSpawnPosition()[0]>>4
        scz = world.playerSpawnPosition()[2]>>4
        spawn_chunk = Vec(scx, 0, scz)
        # Now we have to weed out the areas that are not deep enough
        print 'Depth check...'
        print 'Minimum depth:', min_depth, 'blocks'
        for chunk in positions:
            spin(chunk)
            # Fill in any missing depth info for this area
            depth = 128
            for p in iterate_cube(chunk, chunk+Vec(self.xsize-1,
                                                   0,
                                                   1-self.zsize)):
                if (p not in self.depths):
                    self.depths[p] = findChunkDepth(p, world)
                depth = min(depth, self.depths[p])
            if (depth >= min_depth):
                maxd = max(maxd, positions[chunk])
                depth_positions[chunk] = Vec(
                    chunk.x*self.room_size,
                    depth,
                    chunk.z*self.room_size)
        print 'Found',len(depth_positions),'possible locations.'
        # Filter out all but the furthest positions
        print 'Distance check...'
        for chunk, pos in depth_positions.iteritems():
            if (positions[chunk] >= maxd):
                final_positions[chunk] = depth_positions[chunk]
        # The final list. Make a choice!
        print 'Found',len(final_positions),'possible locations.'
        try:
            self.position = random.choice(final_positions.values()) + Vec(0,
                                                                          -1,
                                                                          0)
        except:
            return False
        print 'Final location: (%d, %d, %d)'% (self.position.x,
                                               self.position.y,
                                               self.position.z)

        # Draw a nice little map of the dungeon location
        map_min_x = bounds.getMaxcx()
        map_max_x = bounds.getMincx()
        map_min_z = bounds.getMaxcz()
        map_max_z = bounds.getMincz()
        for p in final_positions:
            map_min_x = min(map_min_x, p.x)
            map_max_x = max(map_max_x, p.x+self.xsize-1)
            map_min_z = min(map_min_z, p.z-self.zsize+1)
            map_max_z = max(map_max_z, p.z)

        # Include spawn
        map_min_x = min(map_min_x, spawn_chunk.x)
        map_max_x = max(map_max_x, spawn_chunk.x)
        map_min_z = min(map_min_z, spawn_chunk.z)
        map_max_z = max(map_max_z, spawn_chunk.z)

        sx = self.position.x/self.room_size
        sz = self.position.z/self.room_size
        d_box = Box(Vec(sx, 0, sz-self.zsize+1), self.xsize, 128, self.zsize)

        for x in xrange(map_min_x-1, map_max_x+2):
            for z in xrange(map_max_z+1, map_min_z-2, -1):
                if (Vec(x,0,z) == spawn_chunk):
                    sys.stdout.write('S')
                elif (Vec(x,0,z) == Vec(sx, 0, sz)):
                    sys.stdout.write('X')
                elif (d_box.containsPoint(Vec(x,64,z))):
                    sys.stdout.write('#')
                elif (Vec(x,0,z) in final_positions):
                    sys.stdout.write('+')
                else:
                    sys.stdout.write('`')
            print
        return True

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


    def addspawner(self, loc, entity=''):
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('MobSpawner')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        if (entity == ''):
            entity = weighted_choice(cfg.master_mobs)
        root_tag['EntityId'] = nbt.TAG_String(entity)
        root_tag['Delay'] = nbt.TAG_Short(0)
        self.tile_ents[loc] = root_tag
    def addchest(self, loc, tier=-1):
        if (tier < 0):
            level = loc.y/self.room_height
            if (self.levels > 1):
                tierf = (float(level) /
                         float(self.levels-1) *
                         float(loottable._maxtier-2))+1.5
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
        for i in loottable.rollLoot(tier):
            item_tag = nbt.TAG_Compound()
            item_tag['Slot'] = nbt.TAG_Byte(i.slot)
            item_tag['Count'] = nbt.TAG_Byte(i.count)
            item_tag['id'] = nbt.TAG_Short(i.id)
            item_tag['Damage'] = nbt.TAG_Short(i.damage)
            inv_tag.append(item_tag)
        self.tile_ents[loc] = root_tag
    def addtrap(self, loc):
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('Trap')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        inv_tag = nbt.TAG_List()
        root_tag['Items'] = inv_tag
        item_tag = nbt.TAG_Compound()
        item_tag['Slot'] = nbt.TAG_Byte(0)
        item_tag['Count'] = nbt.TAG_Byte(3)
        item_tag['id'] = nbt.TAG_Short(262)
        item_tag['Damage'] = nbt.TAG_Short(0)
        inv_tag.append(item_tag)
        self.tile_ents[loc] = root_tag

    def setroom(self, coord, room):
        if coord not in self.rooms:
            self.rooms[coord] = room
            room.placed()

    def genrooms(self, args_entrance):
        # Generate the maze used for room and hall placement.
        # Stairwells contains the lower half of a stairwell. 
        stairwells = []
        entrance_pos = None
        exit_pos = None
        # The size of our dungeon
        dsize = Vec(self.xsize, self.levels-1, self.zsize)
        # Some convenient lookups.
        # dirs holds vectors for moving in a cardinal direction.
        dirs = {'N': Vec(-1,0,0),
                'S': Vec(1,0,0),
                'E': Vec(0,0,1),
                'W': Vec(0,0,-1)}
        # sides maps a dir to a room side for hall placement.
        sides = {'N': 3,
                 'S': 1,
                 'E': 2,
                 'W': 0}
        # opposite sides for setting the matching hall in the adjacent room. 
        osides = {'N': 1,
                  'S': 3,
                  'E': 0,
                  'W': 2}
        # dkeys holds our valid directions.
        dkeys = dirs.keys()
        # Our maze state flags
        state = MazeCell.states

        # Start in a random location on level 1, unless the -e
        # options was used. 
        if (args_entrance is not None):
            x = args_entrance[1]
            z = args_entrance[0]
        else:
            x = random.randint(0, self.xsize-1)
            z = random.randint(0, self.zsize-1)

        # A maximum depth value. No one room can be this deep on a single
        # level. 
        maxdepth = self.xsize * self.zsize * self.levels + 1

        # Generate a maze for each level. 
        for y in xrange(self.levels):
            # The first cell is "connected" has a depth of 1.
            self.maze[Vec(x,y,z)].state = state.CONNECTED
            self.maze[Vec(x,y,z)].depth = 1
            #print 'Set:', Vec(x,y,z)
            # The first cell contains an entrance. This is a tower if we are on
            # level 1, otherwise it's a stairwell. 
            if (y == 0):
                entrance_pos = Vec(x,y,z)
            else:
                stairwells.append(Vec(x,y,z))
            # If we are on the last level, allow rooms on the last level.
            if (y == self.levels-1):
                dsize = dsize.down(1)
            while 1:
                # Walk the maze.
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
                        self.maze[Vec(nx,y,nz)].state != state.CONNECTED):
                        # Set the status to maxdepth. Later we will calculate
                        # this. 
                        self.maze[Vec(nx,y,nz)].depth = maxdepth
                        # Connect the new cell
                        self.maze[Vec(nx,y,nz)].state = state.CONNECTED
                        # Mark the halls leaving the current cell and the
                        # next cell as connected. We'll set the hall class
                        # later. 
                        self.halls[x][y][z][sides[d]] = 1
                        self.halls[nx][y][nz][osides[d]] = 1
                        # Set the current cell. 
                        x = nx
                        z = nz
                        # We found a good cell, no need to look further.
                        #print 'Moved:', d, dirs[d]
                        #print 'Set:', Vec(x,y,z)
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
                        if (self.maze[Vec(p.x,y,p.z)].state == state.CONNECTED):
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
                        #print 'Set:', Vec(x,y,z), 'connect to', Vec(ox,y,oz)
                        self.maze[Vec(x,y,z)].depth = maxdepth
                        self.maze[Vec(x,y,z)].state = state.CONNECTED
                        self.halls[x][y][z][sides[d]] = 1
                        self.halls[ox][y][oz][osides[d]] = 1
                        break

                # If the last cell and current cell are still the same (we could
                # not move, and the hunt failed) then we've filled the level. 
                # Recalculate the depth tree, find the deepest cell on
                # this level, and use it for the stairwell (starting point)
                # on the next.
                if (lx == x and lz == z):
                    #print 'Finished level'
                    # Sprinkle some extra hallways into the dungeon using the
                    # loops config parameter. 
                    for p in iterate_plane(Vec(0,y,0),
                                           Vec(self.xsize-1,y,self.zsize-1)):
                        for d in dirs.keys():
                            if (self.halls[p.x][y][p.z][sides[d]] is not 1 and
                                random.randint(1,100) <= cfg.loops):
                                nx = p.x + dirs[d].x
                                nz = p.z + dirs[d].z
                                if (nx >= 0 and
                                    nz >= 0 and
                                    nx < self.xsize and
                                    nz < self.zsize):
                                    self.halls[p.x][y][p.z][sides[d]] = 1
                                    self.halls[nx][y][nz][osides[d]] = 1
                    # Rebuild the depth tree.
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
                    # Find the deepest cell on this level.
                    depth = 0
                    for p in iterate_plane(Vec(0,y,0),
                                           Vec(self.xsize-1,y,self.zsize-1)):
                        if (self.maze[Vec(p.x,y,p.z)].depth > depth):
                            depth = self.maze[Vec(p.x,y,p.z)].depth
                            x = p.x
                            z = p.z
                    break

        # The exit is the deepest cell on the last level. Treasure rooms are now
        # 2x2, so we have a few possibilities. First grab a weighted random list
        # of positions based on depth from the stairwell on this level. 
        # We'll pop through them looking for a good location. 
        tchoices = []
        for p in iterate_plane(Vec(0,y,0),
                               Vec(self.xsize-1,y,self.zsize-1)):
            tchoices.append((self.maze[p].depth, p))
        tchoices.sort()
        # 1) Rooms extending East and South are available. We're good!
        while len(tchoices) > 0:
            d, p = tchoices.pop()
        #    if (p != entrance_pos and
        #        p.x < self.xsize-1 and
        #        p.z < self.zsize-1 and
        #        p+Vec(1,0,0) not in stairwells and
        #        p+Vec(0,0,1) not in stairwells and
        #        p+Vec(1,0,1) not in stairwells and
        #        p+Vec(1,0,0) != entrance_pos and
        #        p+Vec(0,0,1) != entrance_pos and
        #        p+Vec(1,0,1) != entrance_pos):
            exit_pos = p
            break

        if exit_pos == None:
            sys.exit('Unable to find treasure room location. :(')

        print 'Entrance:', entrance_pos
        print 'Exit:', exit_pos

        # Fill-in all the special rooms.
        # This is the entrance
        room = None
        pos = entrance_pos
        while (room == None or
               room.canvasWidth() < 8 or
               room.canvasLength() < 8 or
               len(room.features) > 0):
            room = rooms.new(rooms.pickRoom(self.rooms,
                                            dsize,
                                            pos,
                                            Vec(1,1,1)),
                             self,
                             pos)
        feature = features.new('entrance', room)
        self.entrance = feature
        room.features.append(feature)
        feature.placed()
        self.setroom(pos, room)

        # This is the exit. MultiVerse Portal or treasure room.
        room = None
        pos = exit_pos
        room = rooms.new('circular', self, pos)
        if (cfg.mvportal is not ''):
            feature = features.new('multiverseportal', room)
            feature.target = cfg.mvportal
        else:
            feature = features.new('treasureroom', room)
        room.features.append(feature)
        feature.placed()
        self.setroom(pos, room)

        # These are the stairwells
        room = None
        for pos in stairwells:
            while (room == None or
                   room.canvasWidth() < 6 or
                   room.canvasLength() < 8 or
                   len(room.features) > 0):
                room = rooms.new(rooms.pickRoom(self.rooms,
                                                dsize,
                                                pos,
                                                Vec(1,1,1)),
                                 self,
                                 pos)
            feature = features.new('stairwell', room)
            room.features.append(feature)
            feature.placed()
            self.setroom(pos, room)
            # This is the upper half of a stairwell.
            posup = pos.up(1)
            while (room == None or
                   room.canvasWidth() < 6 or
                   room.canvasLength() < 8 or
                   len(room.features) > 0):
                room = rooms.new(rooms.pickRoom(self.rooms,
                                                dsize,
                                                pos,
                                                Vec(1,1,1)),
                                 self,
                                 posup)
            feature = features.new('blank', room)
            room.features.append(feature)
            feature.placed()
            self.setroom(posup, room)

        # Fill-in the rest of the rooms.
        # Iterate through random cells in the maze filling it in with rooms as
        # we go. 
        keys = self.maze.keys()
        shuffle(keys)
        for pos in keys:
            if (self.maze[pos].state == state.BLANK):
                print "WARNING: Blank room at", pos
                continue
            if pos not in self.rooms:
                room = rooms.new(rooms.pickRoom(self.rooms,
                                                dsize,
                                                pos),
                                 self,
                                 pos)
                self.setroom(pos, room)


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
                                   # and the ajoining room.
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
                pos != self.entrance.parent.pos and
                len(self.rooms[pos].ruins) == 0):
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
        for pos, val in self.torches.items():
            if (count < maxcount and
               pos in self.blocks and
               self.blocks[pos.down(offset)].material == materials.Air and
               pos.up(1).y/self.room_height == level):
                self.blocks[pos.down(offset)].material = materials.Torch
                count += 1
        if (level < self.levels-1):
            self.placetorches(level+1)

    def placedoors(self, perc):
        '''Place a proportion of the doors where possible'''
        count = 0
        # in MC space, 0=E, 1=N, 2=W, 3=S
        # doors are populated N->S and W->E
        doordat = ((3,6),(2,5),(4,1),(7,0))
        maxcount = perc * len(self.doors) / 100
        for pos, door in self.doors.items():
            if (count < maxcount):
                x = 0
                for dpos in door.doors:
                    if(dpos in self.blocks and  self.blocks[dpos].material == materials.Air):
                        self.blocks[dpos].material = materials._ceiling
                        self.blocks[dpos.down(1)].material = door.material
                        self.blocks[dpos.down(1)].data = doordat[door.direction][x] | 8 # Top door
                        self.blocks[dpos.down(2)].material = door.material
                        self.blocks[dpos.down(2)].data = doordat[door.direction][x]
                    x += 1
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
                 86, 88, 90, 91, 92, 93, 94)
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
        # Blocks we are not allowed to place a chest upon
        ignore = (0, 6, 8, 9, 10, 11, 18, 20, 23, 25, 26, 37, 38, 39, 40,
                 44, 50, 51, 52, 53, 54, 55, 58, 59, 60, 61, 62, 63, 64, 65,
                 66, 67, 68, 69, 70, 71, 72, 75, 76, 77, 78, 81, 83, 84, 85,
                 86, 88, 90, 91, 92, 93, 94)
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
            # Pick a spot, if one exists.
            if (len(points) > 0):
                point = random.choice(points)
                self.setblock(point.up(1), materials.Spawner)
                self.addspawner(point.up(1))
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

    def renderrooms(self):
        '''Call render() on all rooms to populate the block buffer'''
        count = len(self.rooms)
        for pos in self.rooms:
            self.rooms[pos].render()
            count -= 1
            if (count%10 == 0):
                spin(count)

    def renderhalls(self):
        ''' Call render() on all halls'''
        for pos in self.rooms:
            for x in xrange(0,4):
                if (self.rooms[pos].halls[x]):
                    self.rooms[pos].halls[x].render()
                    spin()

    def renderfloors(self):
        ''' Call render() on all floors'''
        for pos in self.rooms:
            for x in self.rooms[pos].floors:
                x.render()
                spin()

    def renderfeatures(self):
        ''' Call render() on all features'''
        for pos in self.rooms:
            for x in self.rooms[pos].features:
                x.render()
                spin()

    def renderruins(self):
        ''' Call render() on all ruins'''
        for pos in self.rooms:
            for x in self.rooms[pos].ruins:
                x.render()
                spin()

    def outputterminal(self, floor):
        '''Print a slice (or layer) of the dungeon block buffer to the termial.
        We "look-through" any air blocks to blocks underneath'''
        pn = perlin.SimplexNoise(256)
        layer = (floor-1)*self.room_height
        for x in xrange(self.xsize*self.room_size):
            for z in xrange(self.zsize*self.room_size):
                y = layer
                while (y < layer + self.room_height - 1 and
                       Vec(x,y,z) in self.blocks and
                         (self.blocks[Vec(x,y,z)].hide == True or
                          self.blocks[Vec(x,y,z)].material == materials.Air or
                          self.blocks[Vec(x,y,z)].material == materials._ceiling)):
                    y += 1
                if Vec(x,y,z) in self.blocks:
                    mat = self.blocks[Vec(x,y,z)].material
                    # 3D perlin moss!
                    if (mat.name == 'cobblestone'):
                        if ((pn.noise3(x / 4.0, y / 4.0, z / 4.0) + 1.0) / 2.0 < 0.5):
                            mat = materials.MossStone
                        else:
                            mat = materials.Cobblestone
                    sys.stdout.write(mat.c)
                else:
                    sys.stdout.write(materials.NOBLOCK)
            print


    def outputhtml(self, basename, force):
        '''Print all levels of the dungeon block buffer to html.
        We "look-through" any air blocks to blocks underneath'''
        pn = perlin.SimplexNoise(256)
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
            for x in xrange(self.xsize*self.room_size):
                f.write('<tr>')
                for z in xrange(self.zsize*self.room_size):
                    y = layer 
                    while (y < layer + self.room_height - 1 and
                           Vec(x,y,z) in self.blocks and
                            (self.blocks[Vec(x,y,z)].hide == True or
                             self.blocks[Vec(x,y,z)].material ==
                             materials.Air or
                             self.blocks[Vec(x,y,z)].material ==
                             materials._ceiling)):
                        y += 1
                    if Vec(x,y,z) in self.blocks:
                        mat = self.blocks[Vec(x,y,z)].material
                        # 3D perlin moss!
                        if (mat.name == 'cobblestone'):
                            if ((pn.noise3(x / 4.0,
                                         y / 4.0,
                                         z / 4.0,
                                         ) + 1.0) / 2.0 < 0.5):
                                mat = materials.MossStone
                            else:
                                mat = materials.Cobblestone
                        f.write('<td><img src=d/%d-%d.png>' %
                                (mat.val,
                                 self.blocks[Vec(x,y,z)].data))
                    else:
                        f.write('<td><img src=d/0.png>')
            f.write('</table>')
            f.write(footer)
            f.close()


    def setentrance(self, world):
        wcoord=Vec(self.entrance.parent.loc.x + self.position.x,
            self.position.y - self.entrance.parent.loc.y,
            self.position.z - self.entrance.parent.loc.z + 15)
        print '   World coord:',wcoord
        baseheight = wcoord.y + 2 # plenum + floor
        newheight = baseheight
        print '   Base height:',baseheight
        # List of blocks to ignore.
        # Leaves, trees, flowers, etc.
        ignore = (0,6,17,18,37,38,39,40,44,50,51,55,
                  59,63,64,65,66,68,70,71,72,75,76,
                  77,81,83,85,86,90,91,92,93,94)
        for x in xrange(wcoord.x+4, wcoord.x+12):
            for z in xrange(wcoord.z-11, wcoord.z-3):
                chunk_z = z>>4
                chunk_x = x>>4
                xInChunk = x & 0xf
                zInChunk = z & 0xf
                if (world.containsChunk(chunk_x, chunk_z)):
                    chunk = world.getChunk(chunk_x, chunk_z)
                else:
                    print 'Entrance in nonexistent chunk!',
                    print 'crd: (%d, %d) chk: (%d, %d)'%(x, z, chunk_x, chunk_z)
                    continue
                # Heightmap is a good starting place, but I need to look
                # down through foliage.
                y = chunk.HeightMap[zInChunk, xInChunk]-1
                while (chunk.Blocks[xInChunk, zInChunk, y] in ignore):
                    y -= 1
                if (chunk.Blocks[xInChunk, zInChunk, y] == 9 or
                    chunk.Blocks[xInChunk, zInChunk, y] == 79):
                    self.entrance.inwater = True
                #chunk.Blocks[xInChunk, zInChunk, y] = 1
                newheight = max(y, newheight)
                # Check for water here?
        print "   New height:",newheight
        if (self.entrance.inwater == True):
            print "   Entrance is in water."
        if (newheight - baseheight > 0):
            self.entrance.height += newheight - baseheight
        self.entrance.u = int(cfg.tower*self.entrance.u)
        # Check the upper bounds of the tower
        if (newheight + self.entrance.u >= 128):
            self.entrance.u = 124 - newheight

    def applychanges(self, world):
        '''Write the block buffer to the specified world'''
        changed_chunks = set()
        num_blocks = len(self.blocks)
        pn = perlin.SimplexNoise(256)
        # Hard mode
        if (cfg.hard_mode is True):
            print 'Filling in caves (hard mode)...'
            num = (self.zsize+10) * (self.xsize+10)
            for z in xrange((self.position.z>>4)-self.zsize-5,
                            (self.position.z>>4)+5):
                for x in xrange((self.position.x>>4)-5,
                                (self.position.x>>4)+self.xsize+5):
                    spin(num)
                    num -= 1
                    if (world.containsChunk(x, z)):
                        p = Vec(x,0,z)
                        chunk = world.getChunk(x, z)
                        if (p not in self.depths):
                            self.depths[p] = findChunkDepth(p, world)
                        miny = self.depths[p]
                        air = ( chunk.Blocks[:,:,0:miny] == 0)
                        chunk.Blocks[air] = materials._floor.val
                        changed_chunks.add(chunk)
        # Blocks
        print 'Writing block buffer...'
        for block in self.blocks.values():
            # Progress
            num_blocks -= 1
            if (num_blocks % 10000 == 0):
                spin(num_blocks/10000)
            # Mysteriously, this block contains no material.
            if block.material is None:
                continue
            # Translate block coords to world coords
            x = block.loc.x + self.position.x
            y = self.position.y - block.loc.y
            z = self.position.z - block.loc.z + 15
            # Due to bad planning, sometimes we try to draw outside the bounds
            if (y < 0 or y > 127):
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
            # 3D perlin moss!
            mat = block.material
            dat = block.data
            if (mat.name == 'cobblestone'):
                if ((pn.noise3(x / 4.0, y / 4.0, z / 4.0) + 1.0) / 2.0 < 0.5):
                    mat = materials.MossStone
                else:
                    mat = materials.Cobblestone
            if (mat == materials._sandbar and
                chunk.Blocks[xInChunk, zInChunk, y] != materials.Water.val and
                chunk.Blocks[xInChunk, zInChunk, y] != materials.StillWater.val and
                chunk.Blocks[xInChunk, zInChunk, y] != materials.Ice.val):
                continue
            if (mat == materials._natural):
                continue
            # Write the block.
            chunk.Blocks[xInChunk, zInChunk, y] = mat.val
            chunk.Data[xInChunk, zInChunk, y] = dat
            # Add this to the list we want to relight later.
            changed_chunks.add(chunk)
            # Make sure we don't overwrite this chunk in the future. 
            self.depths[Vec(chunk_x, 0, chunk_z)] = 0
        # Copy over tile entities
        print 'Creating tile entities...'
        num = len(self.tile_ents)
        for ent in self.tile_ents.values():
            spin(num)
            num -= 1
            # Calculate world coords.
            x = ent['x'].value + self.position.x
            y = self.position.y - ent['y'].value
            z = self.position.z - ent['z'].value + 15
            # Move this tile ent to the world coords.
            ent['x'].value = x
            ent['y'].value = y
            ent['z'].value = z
            # Load the chunk.
            chunk_z = z>>4
            chunk_x = x>>4
            xInChunk = x & 0xf
            zInChunk = z & 0xf
            # get the chunk
            if (world.containsChunk(chunk_x, chunk_z)):
                chunk = world.getChunk(chunk_x, chunk_z)
            else:
                print 'Whoops! Tile entity in nonexistent chunk!',
                print 'crd: (%d, %d) chk: (%d, %d)'%(x, z, chunk_x, chunk_z)
                continue
            # copy rhe ent to the chunk
            chunk.TileEntities.append(ent)
            #print 'Copied entity:',ent['id'].value, ent['x'].value, ent['y'].value, ent['z'].value
            changed_chunks.add(chunk)
        # Mark changed chunks so pymclevel knows to recompress/relight them.
        print 'Marking dirty chunks...'
        num = len(changed_chunks)
        for chunk in changed_chunks:
            spin(num)
            num -= 1
            chunk.chunkChanged()
