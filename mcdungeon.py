#!/usr/bin/python

import sys
import argparse
import ConfigParser
import inspect
from random import *
from copy import * 

import materials
import rooms
import halls
import floors
import features
from mymath import * 
from pymclevel import mclevel
from noise import pnoise3

parser = argparse.ArgumentParser(description='Generate some DungeonQuest-like dungeons in a Minecraft map.')
parser.add_argument('z', type=int, help='Number of rooms West -> East')
parser.add_argument('x', type=int, help='Number of rooms North -> South')
parser.add_argument('levels', type=int, help='Number of levels')
parser.add_argument('--config', dest='config', metavar='CFGFILE', default='mcdungeon.cfg', help='Alternate config file. Default: mcdungeon.cfg')
parser.add_argument('--write', action='store_true', dest='write' , help='Write the dungeon to disk')
parser.add_argument('--skip-relight', action='store_true', dest='skiprelight', help='Skip relighting the level')
parser.add_argument('--term', type=int,dest='term', metavar='FLOOR', help='Print a text version of a given floor to the terminal')
parser.add_argument('--html', type=int,dest='html', metavar='FLOOR', help='Print an html version of a given floor to the terminal')
parser.add_argument('--seed', dest='seed', metavar='SEED', help='Provide a seed for this dungeon. This can be anything.')
parser.add_argument('--world', dest='world', metavar='SAVEDIR', help='Target world (path to save directory)', required=True)
args = parser.parse_args()

# Do some initial error checking
if (args.z < 2):
	sys.exit('Too few rooms in Z direction. Try >= 2.')
if (args.x < 2):
	sys.exit('Too few rooms in X direction. Try >= 2.')
if (args.levels < 1 or args.levels > 18):
	sys.exit('Invalid number of levels.')

config = ConfigParser.SafeConfigParser()
try: 
	config.readfp(open(args.config))
except:
	print "Failed to read config file:", args.config
	sys.exit(1)

master_halls = config.items('halls')
master_rooms = config.items('rooms')
master_features = config.items('features')
master_floors = config.items('floors')
cfg_offset = str2Vec(config.get('dungeon', 'offset'))
cfg_tower = config.getfloat('dungeon','tower')
cfg_doors = config.getint('dungeon','doors')
cfg_portcullises = config.getint('dungeon', 'portcullises')
cfg_torches = config.getint('dungeon', 'torches')
cfg_wall = config.get('dungeon', 'wall')
cfg_ceiling = config.get('dungeon', 'ceiling')
cfg_floor = config.get('dungeon', 'floor')

if (cfg_tower < 1.0):
	sys.exit('The tower height parameter is too small. This should be >= 1.0. Check the cfg file.')

if (args.seed is not None):
	seed(args.seed)

class Block(object):
    def __init__(self, loc):
        self.loc = loc
        self.material = None
        self.data = 0

class Dungeon (object):
	def __init__(self, pos, xsize, zsize, levels):
		self.rooms = {}
		self.blocks = {}
		self.torches = {}
		self.doors = {}
		self.portcullises = {}
		self.entrance = None
		self.xsize = xsize
		self.zsize = zsize
		self.levels = levels
		self.room_size = 16
		self.room_height = 6
		self.position = pos
	def setblock(self, loc, material):
		if loc not in self.blocks:
			self.blocks[loc] = Block(loc)
		self.blocks[loc].material = material
		self.blocks[loc].data = 0
	def setroom(self, coord, room):
		if coord not in self.rooms:
			self.rooms[coord] = room
			room.placed()
			#print "New room: ",coord
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
				while (room == None or sum_points_inside_flat_poly(*room.canvas) < 24):
					room = rooms.new(weighted_choice(master_rooms), self, pos)
				# Place an entrance at level zero
				if (pos.y == 0):
					feature = features.new('entrance', room)
					self.entrance = feature
				# All other levels are stairwells
				else:
					feature = features.new('stairwell', room)
				room.features.append(feature)
				self.setroom(pos, room)
				room = None
			# If there is a level above, make room for the stairwell
			if (posup.y >= 0):
				while (roomup == None or sum_points_inside_flat_poly(*roomup.canvas) < 24):
					roomup = rooms.new(weighted_choice(master_rooms), self, posup)
				featureup = features.new('blank', roomup)
				roomup.features.append(featureup)
				self.setroom(posup, roomup)
				roomup = None
				
		# Generate the rest of the map
		for y in xrange(self.levels):
			for x in xrange(self.xsize):
				for z in xrange(self.zsize):
					loc = Vec(x*self.room_size,y*self.room_height,z*self.room_size)
					pos = Vec(x,y,z)
					self.setroom(pos, rooms.new(weighted_choice(master_rooms), self, pos))
	def genhalls(self):
		'''Step through all rooms and generate halls where possible'''
		for y in xrange(self.levels):
			for x in xrange(self.xsize):
				for z in xrange(self.zsize):
					pos = Vec(x,y,z)
					if (self.rooms[pos] is not None):
						# Maximum halls this room could potentially handle
						maxhalls = 0
						for d in xrange(4):
							if (self.rooms[pos].testHall(d, 3, self.rooms[pos].hallSize[d][0], self.rooms[pos].hallSize[d][1]) and self.rooms[pos].halls[d] is None):
								maxhalls += 1
						#if (maxhalls < 1):
							#print "This room can't have halls!",pos
						# Each room is guaranteed to have 1 hall, and a max of 3
						hallsremain = randint(min(1,maxhalls), min(2,maxhalls))
						# Start on a random side
						d = randint(0,3)
						count = 4
						while (hallsremain and count > 0):
							# This is our list to try. We should (hopefully) never get to Blank
							# as long as the rooms are structured well
							hall_list = weighted_shuffle(master_halls)
							hall_list.insert(0, 'Blank')
							if (self.rooms[pos].hallLength[d] > 0 and self.rooms[pos].isOnEdge(d) is False):
								if (self.rooms[pos].halls[d] is None):
									while (len(hall_list)):
										newhall = hall_list.pop()
										newsize = halls.sizeByName(newhall)
										nextpos = pos+pos.d(d)
										nextd = (d+2)%4
										# get valid offsets for this room and the ajoining room
										# first test the current room
										#print pos,d,newhall
										if (self.rooms[pos].isOnEdge(d) is False):
											result1 = self.rooms[pos].testHall(d, newsize, self.rooms[nextpos].hallSize[nextd][0], self.rooms[nextpos].hallSize[nextd][1])
											result2 = self.rooms[nextpos].testHall(nextd, newsize, self.rooms[pos].hallSize[d][0], self.rooms[pos].hallSize[d][1])
											#print pos,d,"Tried:",newhall,"Result 1:",result1,"Result 2:",result2
											if (result1 is not False and result2 is not False):
												#print "Winner!"
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
			floor = floors.new(weighted_choice(master_floors), self.rooms[pos])
			self.rooms[pos].floors.append(floor)

	def genfeatures(self):
		for pos in self.rooms:
			if (len(self.rooms[pos].features) == 0):
				feature = features.new(weighted_choice(master_features), self.rooms[pos])
				self.rooms[pos].features.append(feature)
				feature.placed()

	def placetorches(self, perc):
		'''Place a proportion of the torches where possible'''
		count = 0
		maxcount = perc * len(self.torches) / 100
		for pos, val in self.torches.items():
			if (count < maxcount and pos in self.blocks and self.blocks[pos].material == materials.Air):
				self.blocks[pos].material = materials.Torch
				count += 1

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
	def placeportcullises(self, perc):
		'''Place a proportion of the portcullises where possible'''
		count = 0
		maxcount = perc * len(self.portcullises) / 100
		for pos, portcullis in self.portcullises.items():
			if (count < maxcount):
				for dpos, val in portcullis.portcullises.items():
					if(dpos in self.blocks and  self.blocks[dpos].material == materials.Air):
						for x in xrange(portcullis.size):
							self.blocks[dpos.down(x)].material = portcullis.material
				count += 1


	def renderrooms(self):
		'''Call render() on all rooms to populate the block buffer'''
		for pos in self.rooms:
			#sys.stdout.write(".")
			#sys.stdout.flush()
			self.rooms[pos].render()

	def renderhalls(self):
		''' Call render() on all halls'''
		for pos in self.rooms:
			for x in xrange(0,4):
				if (self.rooms[pos].halls[x]):
					self.rooms[pos].halls[x].render()
	def renderfloors(self):
		''' Call render() on all floors'''
		for pos in self.rooms:
			for x in self.rooms[pos].floors:
				x.render()

	def renderfeatures(self):
		''' Call render() on all features'''
		for pos in self.rooms:
			for x in self.rooms[pos].features:
				x.render()

	def outputterminal(self, floor):
		'''Print a slice (or layer) of the dungeon block buffer to the termial.
		We "look-through" any air blocks to blocks underneath'''
		layer = (floor-1)*self.room_height
		for x in xrange(self.xsize*self.room_size):
			for z in xrange(self.zsize*self.room_size):
				y = layer
				while (y < layer + self.room_height - 1 and 
						(Vec(x,y,z) not in self.blocks 
						or self.blocks[Vec(x,y,z)].material == materials.Air 
						or self.blocks[Vec(x,y,z)].material == materials._ceiling)):
					y += 1
				if Vec(x,y,z) in self.blocks:
					mat = self.blocks[Vec(x,y,z)].material
					# 3D perlin moss!
					if (mat.name == 'Cobblestone'):
						if ((pnoise3(x / 3.0, y / 3.0, z / 3.0, 1) + 1.0) / 2.0 < 0.5):
							mat = materials.MossStone
						else:
							mat = materials.Cobblestone
					sys.stdout.write(mat.c)
				else:
					sys.stdout.write('%s`%s' % (materials.DGREY, materials.ENDC))
			print
        def outputhtml(self, floor):
                '''Print a slice (or layer) of the dungeon block buffer to an html table.
                We "look-through" any air blocks to blocks underneath'''
		layer = (floor-1)*self.room_height
		sys.stdout.write('<table border=0 cellpadding=0 cellspacing=0>')
		for x in xrange(self.xsize*self.room_size):
			sys.stdout.write('<tr>')
			for z in xrange(self.zsize*self.room_size):
                                y = layer
				while (y < layer + self.room_height - 1 and 
						(Vec(x,y,z) not in self.blocks 
						or self.blocks[Vec(x,y,z)].material == materials.Air 
						or self.blocks[Vec(x,y,z)].material == materials._ceiling)):
					y += 1
                                if Vec(x,y,z) in self.blocks:
					mat = self.blocks[Vec(x,y,z)].material
					# 3D perlin moss!
                                        if (mat.name == 'Cobblestone'):
                                                if ((pnoise3(x / 3.0, y / 3.0, z / 3.0, 1) + 1.0) / 2.0 < 0.5):
							mat = materials.MossStone
						else:
							mat = materials.Cobblestone
                                        sys.stdout.write('<td><img src=d/%d-%d.png>' % (mat.val,self.blocks[Vec(x,y,z)].data))
                                else:
                                        sys.stdout.write('<td><img src=d/0.png>')
		sys.stdout.write('</table>')
	def setentrance(self, world):
		wcoord=Vec(self.entrance.parent.loc.x + self.position.x,
			self.position.y - self.entrance.parent.loc.y,
			self.position.z - self.entrance.parent.loc.z)
		print "   World coord:",wcoord
		baseheight = wcoord.y + 2 # plenum + floor
		newheight = baseheight
		print "   Base height:",baseheight 
		# List of blocks to ignore
		# leaves, trees, flowers, etc.
		ignore = (0,6,17,18,37,38,39,40,44,50,51,55,59,63,64,65,66,68,70,71,72,75,76,77,81,83,85,86,90,91,92,93,94)
		for x in xrange(wcoord.x+4, wcoord.x+12):
			for z in xrange(wcoord.z-11, wcoord.z-3):
				chunk_z = z>>4
				chunk_x = x>>4
				xInChunk = x & 0xf;
				zInChunk = z & 0xf;
				chunk = world.getChunk(chunk_x, chunk_z)
				# Heightmap is a good starting place, but I need to look down through
				# foliage. 
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
		self.entrance.u = int(cfg_tower*self.entrance.u)
	def applychanges(self, world):
		'''Write the block buffer to the specified world'''
		changed_chunks = set()
		for block in self.blocks.values():
			# We have no changes for this block
			if block.material is None:
				continue
			# Translate block coords to world coords
			x = block.loc.x + self.position.x
			y = self.position.y - block.loc.y
			z = self.position.z - block.loc.z
			# Figure out the chunk and chunk offset
			chunk_z = z>>4
			chunk_x = x>>4
			xInChunk = x & 0xf;
			zInChunk = z & 0xf;
			# get the chunk
			chunk = world.getChunk(chunk_x, chunk_z)
			# 3D perlin moss!
			mat = block.material
			dat = block.data
			if (mat.name == 'Cobblestone'):
				if ((pnoise3(x / 3.0, y / 3.0, z / 3.0, 1) + 1.0) / 2.0 < 0.5):
					mat = materials.MossStone
				else:
					mat = materials.Cobblestone
			# Write the block
			chunk.Blocks[xInChunk, zInChunk, y] = mat.val
			chunk.Data[xInChunk, zInChunk, y] = dat
			# Write data
			# Add this to the list we want to relight later
			changed_chunks.add(chunk)
		# Mark changed chunkes so pymclevel knows to recompress/relight them
		for chunk in changed_chunks:
			chunk.chunkChanged()

# Attempt to open the world
try: 
	world = mclevel.fromFile(args.world)
except:
	print "Failed to open world:",args.world
	sys.exit(1)

#print "materials = ", world.materials.names
# Gather the actual block IDs for all the materials
for name,val in materials.__dict__.items():
    if type(val) == materials.Material:
        val.updateMaterialValue(world)
	if (val.name == cfg_wall):
		materials._wall = copy(val)
	if (val.name == cfg_ceiling):
		materials._ceiling = copy(val)
	if (val.name == cfg_floor):
		materials._floor = copy(val)

print "Startup compete. "

# Define our dungeon
dungeon = Dungeon(cfg_offset, args.x, args.z, args.levels)

print "Generating rooms..."
dungeon.genrooms()

print "Generating floors..."
dungeon.genfloors()

print "Generating features..."
dungeon.genfeatures()

print "Generating halls..."
dungeon.genhalls()

print "Extending the entrance to the surface..."
dungeon.setentrance(world)

print "Rendering rooms..."
dungeon.renderrooms()

print "Rendering halls..."
dungeon.renderhalls()

print "Rendering floors..."
dungeon.renderfloors()

print "Rendering features..."
dungeon.renderfeatures()

print "Placing doors..."
dungeon.placedoors(cfg_doors)

print "Placing portcullises..."
dungeon.placeportcullises(cfg_portcullises)

print "Placing torches..."
dungeon.placetorches(cfg_torches)

# Output a slice of the dungoen to the terminal if requested
if (args.term is not None):
	dungeon.outputterminal(args.term)

# Output an html version
if (args.html is not None):
	dungeon.outputhtml(args.html)

# Write the changes to teh world
if (args.write):
	print "Writing blocks..."
	dungeon.applychanges(world)
	if (args.skiprelight is False):
		print "Relighting chunks..."
		world.generateLights()

# Save the world
if (args.write):
	print "Saving..."
	world.saveInPlace()

print "Done!"
