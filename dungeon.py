#!/usr/bin/python

import sys
import os
from random import *
from noise import pnoise3

import cfg
import items
import loottable
import materials
import rooms
import halls
import floors
import features
from utils import *
from pymclevel import mclevel, nbt

class Block(object):
    def __init__(self, loc):
        self.loc = loc
        self.material = None
        self.data = 0

class Dungeon (object):
    def __init__(self, xsize, zsize, levels):
        self.rooms = {}
        self.blocks = {}
        self.tile_ents = {}
        self.torches = {}
        self.doors = {}
        self.portcullises = {}
        self.entrance = None
        self.xsize = xsize
        self.zsize = zsize
        self.levels = levels
        self.room_size = 16
        self.room_height = 6
        self.position = Vec(0,0,0)


    def setblock(self, loc, material, data=0):
        if loc not in self.blocks:
            self.blocks[loc] = Block(loc)
        self.blocks[loc].material = material
        self.blocks[loc].data = data


    def findlocation(self, world):
        positions = {}
        final_positions = {}
        depths = {}
        bounds = world.bounds
        scx = world.playerSpawnPosition()[0]>>4
        scz = world.playerSpawnPosition()[2]>>4
        spawn_chunk = Vec(scx, 0, scz)
        min_depth = (self.levels+1)*self.room_height
        print 'World bounds:', bounds.getOrigin(), bounds.getSize()
        print 'Spawn position:', world.playerSpawnPosition()
        print 'Spawn chunk: (%d, %d)'%(scx, scz)
        print 'Minimum depth:', min_depth
        # List of blocks to ignore when checking depth
        ignore = (0,6,8,9,10,11,17,18,37,38,39,40,44,50,51,55,
                  59,63,64,65,66,68,70,71,72,75,76,
                  77,81,83,85,86,90,91,92,93,94)
        print 'Pass 1: Bounds check...'
        for chunk in bounds.chunkPositions:
            # First some basic distance from spawn checks...
            spin()
            chunk_box = Box(Vec(chunk[0], 0, chunk[1]-self.zsize+1),
                            self.xsize,
                            16,
                            self.zsize)
            dist_max = int(max(
                (spawn_chunk-chunk_box.loc).mag2d(),
                (spawn_chunk-(chunk_box.loc+Vec(self.xsize-1,0,0))).mag2d(),
                ((chunk_box.loc+Vec(0,0,self.zsize-1))-spawn_chunk).mag2d(),
                (spawn_chunk-(chunk_box.loc+
                 Vec(self.xsize-1,0,self.zsize-1))).mag2d()
            ))
            dist_min = int(min(
                (spawn_chunk-chunk_box.loc).mag2d(),
                (spawn_chunk-(chunk_box.loc+Vec(self.xsize-1,0,0))).mag2d(),
                ((chunk_box.loc+Vec(0,0,self.zsize-1))-spawn_chunk).mag2d(),
                (spawn_chunk-(chunk_box.loc+
                 Vec(self.xsize-1,0,self.zsize-1))).mag2d()
            ))
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
            positions[Vec(chunk[0], 0, chunk[1])] = True
        print 'Found',len(positions),'possible locations.'
        # Now we have to weed out the areas that are not deep enough
        print 'Pass 2: Depth and chunk check...'
        for chunk in positions:
            spin(chunk)
            # Fill in any missing depth info for this area
            depth = 128
            for p in iterate_cube(chunk, chunk+Vec(self.xsize-1,
                                                   0,
                                                   1-self.zsize)):
                try:
                    this_chunk = world.getChunk(p.x, p.z)
                except:
                    depths[p] = 0
                if (p in depths):
                    depth = min(depth, depths[p])
                    continue
                depths[p] = 128
                for x in xrange(16):
                    for z in xrange(16):
                        # Heightmap is a good starting place, but I need to
                        # look down 
                        y = this_chunk.HeightMap[z, x]-1
                        while (this_chunk.Blocks[x, z, y] in ignore):
                            y -= 1
                        depths[p] = min(y, depths[p])
                depth = min(depth, depths[p])
            if (depth >= min_depth):
                final_positions[Vec(chunk.x, 0, chunk.z)] = Vec(
                    chunk.x*self.room_size,
                    depth,
                    chunk.z*self.room_size)
        # The final list. Make a choice!
        print 'Found',len(final_positions),'possible locations.'
        try:
            self.position = random.choice(final_positions.values())
        except:
            sys.exit('Could not find any suitable locations!\n\
Try a smaller dungeon, or larger start area.')
        print 'Final location:',self.position

        spawnx = spawn_chunk.x
        spawnz = spawn_chunk.z
        for x in xrange(spawnx-cfg.max_dist, spawnx+cfg.max_dist):
            for z in xrange(spawnz+cfg.max_dist, spawnz-cfg.max_dist-2, -1):
                if (Vec(x,0,z) in final_positions):
                    if (Vec(x,0,z) == Vec(
                        self.position.x/self.room_size,
                        0,
                        self.position.z/self.room_size)):
                        sys.stdout.write('*')
                    else:
                        sys.stdout.write('+')
                else:
                    if (Vec(x,0,z) == spawn_chunk):
                        sys.stdout.write('S')
                    else:
                        sys.stdout.write('-')
            print

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


    def addspawner(self, loc):
        root_tag = nbt.TAG_Compound()
        root_tag['id'] = nbt.TAG_String('MobSpawner')
        root_tag['x'] = nbt.TAG_Int(loc.x)
        root_tag['y'] = nbt.TAG_Int(loc.y)
        root_tag['z'] = nbt.TAG_Int(loc.z)
        root_tag['EntityId'] = nbt.TAG_String(
                weighted_choice(cfg.master_mobs))
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
    def genrooms(self):
        # Place stairwells
        x = -1
        z = -1
        x1 = -1
        z1 = -1
        room = None
        roomup = None
        for y in xrange(0, self.levels):
            while (x == x1):
                x = randint(0, self.xsize-1)
            while (z == z1):
                z = randint(0, self.zsize-1)
            x1 = x
            z1 = z
            pos = Vec(x,y,z)
            posup = pos.up(1)
            if (pos.y < self.levels):
                while (room == None or
                       sum_points_inside_flat_poly(*room.canvas) < 24):
                    room = rooms.new(weighted_choice(cfg.master_rooms),
                                     self,
                                     pos)
                # Place an entrance at level zero
                if (pos.y == 0):
                    feature = features.new('entrance', room)
                    self.entrance = feature
                # All other levels are stairwells
                else:
                    feature = features.new('stairwell', room)
                room.features.append(feature)
                feature.placed()
                self.setroom(pos, room)
                room = None
            # If there is a level above, make room for the stairwell
            if (posup.y >= 0):
                while (roomup == None or
                       sum_points_inside_flat_poly(*roomup.canvas) < 24):
                    roomup = rooms.new(weighted_choice(cfg.master_rooms),
                                       self,
                                       posup)
                featureup = features.new('blank', roomup)
                roomup.features.append(featureup)
                self.setroom(posup, roomup)
                roomup = None
        # Place the portal
        if (cfg.mvportal is not ''):
            while (x == x1):
                x = randint(0, self.xsize-1)
            while (z == z1):
                z = randint(0, self.zsize-1)
            x1 = x
            z1 = z
            room = None
            pos = Vec(x,self.levels-1,z)
            while (room == None or
                   room.canvasWidth() < 8 or
                   room.canvasLength() < 8):
                room = rooms.new(weighted_choice(cfg.master_rooms), self, pos)
            feature = features.new('multiverseportal', room)
            feature.target = cfg.mvportal
            room.features.append(feature)
            feature.placed()
            self.setroom(pos, room)
        # Generate the rest of the map
        for y in xrange(self.levels):
            for x in xrange(self.xsize):
                for z in xrange(self.zsize):
                    loc = Vec(x*self.room_size,
                              y*self.room_height,
                              z*self.room_size)
                    pos = Vec(x,y,z)
                    self.setroom(pos,
                                 rooms.new(weighted_choice(cfg.master_rooms),
                                           self,
                                           pos)
                                )
    def genhalls(self):
        '''Step through all rooms and generate halls where possible'''
        for y in xrange(self.levels):
            for x in xrange(self.xsize):
                for z in xrange(self.zsize):
                    pos = Vec(x,y,z)
                    if (self.rooms[pos] is not None):
                        # Maximum halls this room could potentially handle
                        # Minimum hall size is 3, so we see if that side
                        # can handle the smallest possible hall
                        maxhalls = 0
                        for d in xrange(4):
                            if (self.rooms[pos].testHall(d,
                                             3,
                                             self.rooms[pos].hallSize[d][0],
                                             self.rooms[pos].hallSize[d][1]
                                            ) and
                                self.rooms[pos].halls[d] is None):
                                maxhalls += 1
                        # Each room is guaranteed to have 1 hall, and a
                        # max of 3
                        hallsremain = randint(min(1,maxhalls), min(2,maxhalls))
                        # Start on a random side
                        d = randint(0,3)
                        count = 4
                        while (hallsremain and count > 0):
                            # This is our list to try. We should (hopefully)
                            # never get to Blank as long as the rooms are
                            # structured well. (And nobody disables size
                            # 3 halls)
                            hall_list = weighted_shuffle(cfg.master_halls)
                            hall_list.insert(0, 'Blank')
                            if (self.rooms[pos].hallLength[d] > 0 and
                                self.rooms[pos].isOnEdge(d) is False):
                                if (self.rooms[pos].halls[d] is None):
                                    while (len(hall_list)):
                                        newhall = hall_list.pop()
                                        newsize = halls.sizeByName(newhall)
                                        nextpos = pos+pos.d(d)
                                        nextd = (d+2)%4
                                        # Get valid offsets for this room
                                        # and the ajoining room.
                                        # First test the current room.
                                        if (self.rooms[pos].isOnEdge(d) is False):
                                            result1 = self.rooms[pos].testHall(d, newsize, self.rooms[nextpos].hallSize[nextd][0], self.rooms[nextpos].hallSize[nextd][1])
                                            result2 = self.rooms[nextpos].testHall(nextd, newsize, self.rooms[pos].hallSize[d][0], self.rooms[pos].hallSize[d][1])
                                            if (result1 is not False and result2 is not False):
                                                offset = randint(min(result1[0], result2[0]), max(result1[1], result2[1]))
                                                self.rooms[pos].halls[d] = halls.new(newhall, self.rooms[pos], d, offset)
                                                self.rooms[nextpos].halls[nextd] = halls.new(newhall, self.rooms[nextpos], nextd, offset)
                                                hall_list = []
                                                hallsremain -= 1
                            d = (d+1)%4
                            count -= 1
                        # Close off any routes that didn't generate a hall
                        for d in xrange(4):
                            if (self.rooms[pos].halls[d] == None):
                                self.rooms[pos].halls[d] = halls.new('blank', self.rooms[pos], d, 0)
                                if (self.rooms[pos].isOnEdge(d) is False):
                                    nextpos = pos+pos.d(d)
                                    nextd = (d+2)%4
                                    self.rooms[nextpos].halls[nextd] = halls.new('blank', self.rooms[nextpos], nextd, 0)

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
        for pos, val in self.torches.items():
            if (count < maxcount and 
               pos in self.blocks and 
               self.blocks[pos].material == materials.Air and
               pos.up(1).y/self.room_height == level):
                self.blocks[pos].material = materials.Torch
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
                if (h.size == 0):
                    hcount += 1
            if (sum_points_inside_flat_poly(*self.rooms[room].canvas) < 6):
                hcount = 0
            # The weight is exponential. Base 10 seems to work well.
            candidates.append((room, 10**hcount-1))
        locations = weighted_shuffle(candidates)
        while (len(locations) > 0 and chests > 0):
            spin()
            room = self.rooms[locations.pop()]
            attempts = 0
            while(attempts < 10):
                point = random_point_inside_flat_poly(*room.canvas)
                point = point+room.loc
                if (self.blocks[point].material.val not in ignore and
                    self.blocks[point.up(1)].material.val == 0 and
                    self.blocks[point.up(2)].material.val == 0):
                    self.setblock(point.up(1), materials.Chest)
                    self.addchest(point.up(1))
                    chests -= 1
                    break
                attempts += 1
            if (attempts >= 10):
                print 'Failed place chest:', room.pos, point
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
                if (h.size == 0):
                    hcount += 1
            if (sum_points_inside_flat_poly(*self.rooms[room].canvas) < 6):
                hcount = 0
            # The weight is exponential. Base 10 seems to work well.
            candidates.append((room, 10**hcount-1))
        locations = weighted_shuffle(candidates)
        while (len(locations) > 0 and spawners > 0):
            spin()
            room = self.rooms[locations.pop()]
            attempts = 0
            while(attempts < 10):
                point = random_point_inside_flat_poly(*room.canvas)
                point = point+room.loc
                if (self.blocks[point].material.val not in ignore and
                    self.blocks[point.up(1)].material.val == 0):
                    self.setblock(point.up(1), materials.Spawner)
                    self.addspawner(point.up(1))
                    spawners -= 1
                    break
                attempts += 1
            if (attempts >= 10):
                print 'Failed place spawner:', room.pos, point
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
        count = len(self.rooms)*4
        for pos in self.rooms:
            for x in xrange(0,4):
                if (self.rooms[pos].halls[x]):
                    self.rooms[pos].halls[x].render()
                count -= 1
                if (count%10 == 0):
                    spin(count)

    def renderfloors(self):
        ''' Call render() on all floors'''
        count = len(self.rooms)
        for pos in self.rooms:
            for x in self.rooms[pos].floors:
                x.render()
                count -= 1
                if (count%10 == 0):
                    spin(count)

    def renderfeatures(self):
        ''' Call render() on all features'''
        count = len(self.rooms)
        for pos in self.rooms:
            for x in self.rooms[pos].features:
                x.render()
                count -= 1
                if (count%10 == 0):
                    spin(count)

    def outputterminal(self, floor):
        '''Print a slice (or layer) of the dungeon block buffer to the termial.
        We "look-through" any air blocks to blocks underneath'''
        layer = (floor-1)*self.room_height
        for x in xrange(self.xsize*self.room_size):
            for z in xrange(self.zsize*self.room_size):
                y = layer
                while (y < layer + self.room_height - 1 and
                       Vec(x,y,z) in self.blocks and
                         (self.blocks[Vec(x,y,z)].material == materials.Air or
                         self.blocks[Vec(x,y,z)].material == materials._ceiling)):
                    y += 1
                if Vec(x,y,z) in self.blocks:
                    mat = self.blocks[Vec(x,y,z)].material
                    # 3D perlin moss!
                    if (mat.name == 'cobblestone'):
                        if ((pnoise3(x / 3.0, y / 3.0, z / 3.0, 1) + 1.0) / 2.0 < 0.5):
                            mat = materials.MossStone
                        else:
                            mat = materials.Cobblestone
                    sys.stdout.write(mat.c)
                else:
                    sys.stdout.write('%s`%s' % (materials.DGREY, materials.ENDC))
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
            for x in xrange(self.xsize*self.room_size):
                f.write('<tr>')
                for z in xrange(self.zsize*self.room_size):
                    y = layer
                    while (y < layer + self.room_height - 1 and
                           Vec(x,y,z) in self.blocks and
                            (self.blocks[Vec(x,y,z)].material ==
                            materials.Air or
                            self.blocks[Vec(x,y,z)].material ==
                            materials._ceiling)):
                        y += 1
                    if Vec(x,y,z) in self.blocks:
                        mat = self.blocks[Vec(x,y,z)].material
                        # 3D perlin moss!
                        if (mat.name == 'cobblestone'):
                            if ((pnoise3(x / 3.0,
                                         y / 3.0,
                                         z / 3.0,
                                         1) + 1.0) / 2.0 < 0.5):
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
            self.position.z - self.entrance.parent.loc.z)
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
                chunk = world.getChunk(chunk_x, chunk_z)
                # Heightmap is a good starting place, but I need to look
                # down through foliage.
                y = chunk.HeightMap[zInChunk, xInChunk]-1
                while (chunk.Blocks[xInChunk, zInChunk, y] in ignore):
                    y -= 1
                if (chunk.Blocks[xInChunk, zInChunk, y] == 9):
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

    def applychanges(self, world):
        '''Write the block buffer to the specified world'''
        changed_chunks = set()
        for block in self.blocks.values():
            # Mysteriously, this block contains no material.
            if block.material is None:
                continue
            # Translate block coords to world coords
            x = block.loc.x + self.position.x
            y = self.position.y - block.loc.y
            z = self.position.z - block.loc.z
            # Figure out the chunk and chunk offset
            chunk_z = z>>4
            chunk_x = x>>4
            xInChunk = x & 0xf
            zInChunk = z & 0xf
            # get the chunk
            chunk = world.getChunk(chunk_x, chunk_z)
            # 3D perlin moss!
            mat = block.material
            dat = block.data
            if (mat.name == 'cobblestone'):
                if ((pnoise3(x / 3.0, y / 3.0, z / 3.0, 1) + 1.0) / 2.0 < 0.5):
                    mat = materials.MossStone
                else:
                    mat = materials.Cobblestone
            # Write the block.
            chunk.Blocks[xInChunk, zInChunk, y] = mat.val
            chunk.Data[xInChunk, zInChunk, y] = dat
            # Add this to the list we want to relight later.
            changed_chunks.add(chunk)
        # Copy over tile entities
        for ent in self.tile_ents.values():
            # Calculate world coords.
            x = ent['x'].value + self.position.x
            y = self.position.y - ent['y'].value
            z = self.position.z - ent['z'].value
            # Move this tile ent to the world coords.
            ent['x'].value = x
            ent['y'].value = y
            ent['z'].value = z
            # Load the chunk.
            chunk_z = z>>4
            chunk_x = x>>4
            xInChunk = x & 0xf
            zInChunk = z & 0xf
            chunk = world.getChunk(chunk_x, chunk_z)
            # copy rhe ent to the chunk
            chunk.TileEntities.append(ent)
            #print 'Copied entity:',ent['id'].value, ent['x'].value, ent['y'].value, ent['z'].value
            changed_chunks.add(chunk)
        # Mark changed chunkes so pymclevel knows to recompress/relight them.
        for chunk in changed_chunks:
            chunk.chunkChanged()
