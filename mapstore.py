# Generates map items from MCDungeon block arrays

# NBT Format for maps:
#
# TAG_Compound
#   TAG_Compound "data"
#       TAG_Byte "scale" (set to 0 for 1:1)
#       TAG_Int "xCenter" (center of map in world coords)
#       TAG_Int "zCenter" (center of map in world coords)
#       TAG_Short "height" (must be 128)
#       TAG_Short "width" (must be 128)
#       TAG_Byte "dimension" (0 == overworld)
#       TAG_Byte_Array "colors" (xoffset + zoffset * width) 0 == upper left

import os
import sys
import cPickle

from numpy import  array, uint8, zeros, fromstring

from pymclevel import nbt
from utils import Vec
import materials

class new:
    def __init__(self, mapstore):
        self.mapstore = os.path.join(mapstore, 'data')

        # Load the idcounts.dat NBT if it exists, otherwise make
        # a new one. Minecraft doesn't compress this file, and the nbt
        # library in pymclevel seems to have a bug loading non-zipped nbt
        # files, so we have to manually load the file into a string buffer
        # and call _load_buffer(). 
        #
        # To test this bug, try loading an idcounts.dat file with a map id of 3.
        # Something about this file seems to look like a gzip header and the
        # nbt buffer that gets passed to the parser turns out to be empty.
        # 
        if (os.path.isfile(os.path.join(self.mapstore, 'idcounts.dat'))):
            with file(os.path.join(self.mapstore, 'idcounts.dat'), "rb") as f:
                self.idcounts = nbt._load_buffer(f.read())
                print self.idcounts
        else:
            print 'No idcounts.dat file found. Creating a new one...'
            self.idcounts = nbt.TAG_Compound()
            self.idcounts['map'] = nbt.TAG_Short(-1)

        # Load the mcdungeon map ID usage cache
        if (os.path.isfile(os.path.join(self.mapstore, 'mcdungeon_maps'))):
            try:
                with open(os.path.join(self.mapstore, 'mcdungeon_maps'), 'rb') as FILE:
                    self.mapcache =  cPickle.load(FILE)
            except Exception as e:
                print e
                sys.exit('Failed to read the mcdungeon maps cache file.')
        else:
            print 'Mapstore cache not found. Creating new one...'
            self.mapcache = {'used': {}, 'available': set([])}

    def update_mapstore(self):
        '''Flushes the idcounts.dat and mcdungeon_maps cache to disk'''
        try:
            with open(os.path.join(self.mapstore, 'mcdungeon_maps'), 'wb') as FILE:
                cPickle.dump(self.mapcache, FILE, -1)
        except Exception as e:
            print e
            sys.exit('Failed to write mcdungeon_maps.')

        # Minecraft expects this one to be uncompressed. Compressed versions
        # cause java exceptions in Minecraft.
        try:
            self.idcounts.save(os.path.join(self.mapstore, 'idcounts.dat'),
                               compressed=False)
        except Exception as e:
            print e
            sys.exit('Failed to write idcounts.dat.')

    def delete_maps(self, loc):
        '''Delete maps for the given dungeon key and return those map IDs to the
        avilable pool.'''
        if loc in self.mapcache['used']:
            self.mapcache['available'].update(self.mapcache['used'][loc])
            for m in self.mapcache['used'][loc]:
                f = os.path.join(self.mapstore, 'map_%d.dat'%(m))
                try:
                    os.remove(f)
                except:
                    pass
            del(self.mapcache['used'][loc])
            self.update_mapstore()
        else:
            print 'No maps found for dungeon at ', loc

    def generate_map(self, dungeon, level):
        '''Generate a new map, save it to disk, flush the cache, and return a
        map item NBT with the appropriate map ID.'''

        dungeon_key = '%s,%s'%(dungeon.position.x, dungeon.position.z)
        if dungeon_key not in self.mapcache['used']:
            self.mapcache['used'][dungeon_key] = set([])

        # Find a map id. Look in the available list for old mcdungeon maps
        # that can be reused. If not, bump up the idcount and use that.
        if len(self.mapcache['available']) == 0:
            self.idcounts['map'].value += 1
            mapid = self.idcounts['map'].value
            self.mapcache['used'][dungeon_key].add(mapid)
        else:
            mapid = self.mapcache['available'].pop()
            self.mapcache['used'][dungeon_key].add(mapid)
        filename = os.path.join(self.mapstore, 'map_%d.dat'%(mapid))

        # Setup the defaults.
        # Offset will be way off somewhere were players are unlikely to go
        # to avoid the maps from being overwritten. Nothing else really matters. 
        tags = nbt.TAG_Compound()
        tags['data'] = nbt.TAG_Compound()
        tags['data']['scale'] = nbt.TAG_Byte(0)
        tags['data']['xCenter'] = nbt.TAG_Int(-12500000)
        tags['data']['zCenter'] = nbt.TAG_Int(-12500000)
        tags['data']['height'] = nbt.TAG_Short(128)
        tags['data']['width'] = nbt.TAG_Short(128)
        tags['data']['dimension'] = nbt.TAG_Byte(0)
        tags['data']['colors'] = nbt.TAG_Byte_Array(zeros(16384, uint8))

        # Generate the map. 
        blocks = dungeon.blocks
        colors = tags['data']['colors'].value
        y = level * dungeon.room_height - 3
        # Scale the map. We only scale up, not down since scaling
        # looks terrible. 
        max_dungeon = max(dungeon.xsize * dungeon.room_size,
                          dungeon.zsize * dungeon.room_size)
        max_dungeon = max(128, max_dungeon)

        # If the size is less than 8, try to center it. 
        xoffset = 0
        zoffset = 0
        if dungeon.xsize * dungeon.room_size < 128:
            xoffset = (128 - dungeon.xsize * dungeon.room_size) / 2
        if dungeon.zsize * dungeon.room_size < 128:
            zoffset = (128 - dungeon.zsize * dungeon.room_size) / 2

        # Draw pixels on the map corresponding to blocks just above
        # floor level. Color chests and spawners. Hide things that should be
        # hidden. 
        for x in xrange(128):
            for z in xrange(128):
                block = Vec(x*max_dungeon/128-xoffset,
                            y,
                            z*max_dungeon/128-zoffset)
                if block in blocks:
                    mat = blocks[block].material
                    if mat == materials.StonePressurePlate:
                        colors[x+z*128] = 10
                    elif blocks[block].hide is True:
                        colors[x+z*128] = 0
                    elif mat == materials.Air:
                        colors[x+z*128] = 10
                    elif mat == materials.Spawner:
                        colors[x+z*128] = 48
                    elif mat == materials.Chest:
                        colors[x+z*128] = 42
                    else:
                        colors[x+z*128] = 54
                else:
                    colors[x+z*128] = 0

        # Draw the level number in the corner
        digits = [
            [ 0, 1, 0,
              1, 0, 1,
              1, 0, 1,
              1, 0, 1,
              0, 1, 0 ],
            [ 0, 1, 0,
              1, 1, 0,
              0, 1, 0,
              0, 1, 0,
              1, 1, 1 ],
            [ 1, 1, 1,
              0, 0, 1,
              1, 1, 1,
              1, 0, 0,
              1, 1, 1 ],
            [ 1, 1, 0,
              0, 0, 1,
              0, 1, 0,
              0, 0, 1,
              1, 1, 0 ],
            [ 1, 0, 1,
              1, 0, 1,
              1, 1, 1,
              0, 0, 1,
              0, 0, 1 ],
            [ 1, 1, 1,
              1, 0, 0,
              1, 1, 1,
              0, 0, 1,
              1, 1, 1 ],
            [ 0, 1, 1,
              1, 0, 0,
              1, 1, 1,
              1, 0, 1,
              1, 1, 1 ],
            [ 1, 1, 1,
              0, 0, 1,
              0, 1, 0,
              0, 1, 0,
              0, 1, 0 ],
            [ 1, 1, 1,
              1, 0, 1,
              1, 1, 1,
              1, 0, 1,
              1, 1, 1 ],
            [ 1, 1, 1,
              1, 0, 1,
              1, 1, 1,
              0, 0, 1,
              1, 1, 1 ]
        ]
        sx = 120
        if level < 10:
            sx = 124
        sz = 123
        for d in str(level):
            for x in xrange(3):
                for z in xrange(5):
                    if digits[int(d)][x+z*3] == 1:
                        colors[x+sx+(z+sz)*128] = 16
            sx += 4

        # Save the map file, cache, and idcount.dat
        tags.save(filename)
        self.update_mapstore()

        # Return a map item
        item = nbt.TAG_Compound()
        item['id'] = nbt.TAG_Short(358)
        item['Damage'] = nbt.TAG_Short(mapid)
        item['Count'] = nbt.TAG_Byte(1)

        return item
