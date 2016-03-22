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
import shutil
import hashlib

from numpy import uint8, zeros

from pymclevel import nbt
from utils import Vec
import materials
import items


class new:

    def __init__(self, mapstore, dir_paintings='paintings'):
        self.mapstore = os.path.join(mapstore, 'data')

        # Load the idcounts.dat NBT if it exists, otherwise make
        # a new one.
        try:
            self.idcounts = nbt.load(
                os.path.join(
                    self.mapstore,
                    'idcounts.dat'))
        except:
            print 'No idcounts.dat file found. Creating a new one...'
            self.idcounts = nbt.TAG_Compound()

        # Load the mcdungeon map ID usage cache
        if (os.path.isfile(os.path.join(self.mapstore, 'mcdungeon_maps'))):
            try:
                with open(os.path.join(self.mapstore, 'mcdungeon_maps'), 'rb') as FILE:
                    self.mapcache = cPickle.load(FILE)
            except Exception as e:
                print e
                print "Failed to read the mcdungeon maps cache file."
                print "The file tracking MCDungeon map usage may be corrupt."
                print "You can try deleting or moving this file to recover:"
                print os.path.join(self.mapstore, 'mcdungeon_maps')
                sys.exit(1)
        else:
            print 'Mapstore cache not found. Creating new one...'
            self.mapcache = {'used': {}, 'available': set([])}

        # Generate map hash table
        self.maphash = {}
        for file in os.listdir(self.mapstore):
            if (str(file.lower()).endswith(".dat") and
                    str(file.lower()).startswith("map_")):
                # Gen hash and extract map ID
                hash = hashlib.md5(
                    open(
                        os.path.join(
                            self.mapstore,
                            file),
                        'r').read()).digest()
                self.maphash[hash] = int(file[4:-4])

        # Store paintings path
        if os.path.isdir(os.path.join(sys.path[0], dir_paintings)):
            self.painting_path = os.path.join(sys.path[0], dir_paintings)
        elif os.path.isdir(dir_paintings):
            self.painting_path = dir_paintings
        else:
            sys.exit("Error: Could not find the paintings folder!")

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
                f = os.path.join(self.mapstore, 'map_%d.dat' % (m))
                try:
                    os.remove(f)
                except:
                    pass
            del(self.mapcache['used'][loc])
            self.update_mapstore()
        else:
            print 'No maps found for dungeon at ', loc

    def add_painting(self, painting_file):
        src = os.path.join(self.painting_path, painting_file + '.dat')
        painting_file_hash = hashlib.md5(open(src, 'r').read()).digest()
        # Look up file in hashtable
        if painting_file_hash in self.maphash:
            mapid = self.maphash[painting_file_hash]
        else:
            # Initialize the map count if it doesn't exist.
            if 'map' not in self.idcounts:
                self.idcounts['map'] = nbt.TAG_Short(-1)
            # Increment and return id
            self.idcounts['map'].value += 1
            mapid = self.idcounts['map'].value
            # Copy the map to the data dir
            dest = os.path.join(self.mapstore, 'map_%d.dat' % (mapid))
            try:
                shutil.copy(src, dest)
            except:
                sys.exit('Error when placing painting in map directory.')
            self.maphash[painting_file_hash] = mapid   # Update hashtable
            self.update_mapstore()

        # Create map item tag
        item = nbt.TAG_Compound()
        item['id'] = nbt.TAG_String(items.byName('map').id)
        item['Damage'] = nbt.TAG_Short(mapid)
        item['Count'] = nbt.TAG_Byte(1)

        # Fetch the lore text for this map
        lorefile = open(
            os.path.join(
                self.painting_path,
                painting_file +
                '.txt'))
        loredata = lorefile.read().splitlines()
        lorefile.close()
        # Create NBT tag
        valid_characters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ "
        item['tag'] = nbt.TAG_Compound()
        item['tag']['display'] = nbt.TAG_Compound()
        item['tag']['display']['Name'] = nbt.TAG_String(
            filter(
                lambda x: x in valid_characters,
                loredata.pop(0)))
        item['tag']['display']['Lore'] = nbt.TAG_List()
        # Slice at 5 lines of 50 chars each
        for p in loredata[:5]:
            line = filter(lambda x: x in valid_characters, p)
            item['tag']['display']['Lore'].append(nbt.TAG_String(line[:50]))

        return item

    def generate_map(self, dungeon, level):
        '''Generate a new map, save it to disk, flush the cache, and return a
        map item NBT with the appropriate map ID.'''

        dungeon_key = '%s,%s' % (dungeon.position.x, dungeon.position.z)
        if dungeon_key not in self.mapcache['used']:
            self.mapcache['used'][dungeon_key] = set([])

        # Find a map id. Look in the available list for old mcdungeon maps
        # that can be reused. If not, bump up the idcount and use that.
        if len(self.mapcache['available']) == 0:
            # Initialize the map count if it doesn't exist.
            if 'map' not in self.idcounts:
                self.idcounts['map'] = nbt.TAG_Short(-1)

            self.idcounts['map'].value += 1
            mapid = self.idcounts['map'].value
            self.mapcache['used'][dungeon_key].add(mapid)
        else:
            mapid = self.mapcache['available'].pop()
            self.mapcache['used'][dungeon_key].add(mapid)
        filename = os.path.join(self.mapstore, 'map_%d.dat' % (mapid))

        # Setup the defaults.
        # Offset will be way off somewhere were players are unlikely to go
        # to avoid the maps from being overwritten. Nothing else really
        # matters.
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
                block = Vec(x * max_dungeon / 128 - xoffset,
                            y,
                            z * max_dungeon / 128 - zoffset)
                if block in blocks:
                    mat = blocks[block].material
                    if mat == materials.StonePressurePlate:
                        colors[x + z * 128] = 10
                    elif blocks[block].hide is True:
                        colors[x + z * 128] = 0
                    elif blocks[block].blank is True:
                        colors[x + z * 128] = 0
                    elif mat == materials.Air:
                        colors[x + z * 128] = 10
                    elif mat == materials.Spawner:
                        colors[x + z * 128] = 48
                    elif (mat == materials.Chest or
                          mat == materials.TrappedChest):
                        colors[x + z * 128] = 42
                    else:
                        colors[x + z * 128] = 54
                else:
                    colors[x + z * 128] = 0

        # Draw the level number in the corner
        digits = [
            [0, 1, 0,
             1, 0, 1,
             1, 0, 1,
             1, 0, 1,
             0, 1, 0],
            [0, 1, 0,
             1, 1, 0,
             0, 1, 0,
             0, 1, 0,
             1, 1, 1],
            [1, 1, 1,
             0, 0, 1,
             1, 1, 1,
             1, 0, 0,
             1, 1, 1],
            [1, 1, 0,
             0, 0, 1,
             0, 1, 0,
             0, 0, 1,
             1, 1, 0],
            [1, 0, 1,
             1, 0, 1,
             1, 1, 1,
             0, 0, 1,
             0, 0, 1],
            [1, 1, 1,
             1, 0, 0,
             1, 1, 1,
             0, 0, 1,
             1, 1, 1],
            [0, 1, 1,
             1, 0, 0,
             1, 1, 1,
             1, 0, 1,
             1, 1, 1],
            [1, 1, 1,
             0, 0, 1,
             0, 1, 0,
             0, 1, 0,
             0, 1, 0],
            [1, 1, 1,
             1, 0, 1,
             1, 1, 1,
             1, 0, 1,
             1, 1, 1],
            [1, 1, 1,
             1, 0, 1,
             1, 1, 1,
             0, 0, 1,
             1, 1, 1]
        ]
        sx = 120
        if level < 10:
            sx = 124
        sz = 123
        for d in str(level):
            for x in xrange(3):
                for z in xrange(5):
                    if digits[int(d)][x + z * 3] == 1:
                        colors[x + sx + (z + sz) * 128] = 16
            sx += 4

        # Save the map file, cache, and idcount.dat
        tags.save(filename)
        self.update_mapstore()

        # Return a map item
        item = nbt.TAG_Compound()
        item['id'] = nbt.TAG_String(items.byName('map').id)
        item['Damage'] = nbt.TAG_Short(mapid)
        item['Count'] = nbt.TAG_Byte(1)
        item['tag'] = nbt.TAG_Compound()
        item['tag']['display'] = nbt.TAG_Compound()
        name = dungeon.dungeon_name + ' Lv {l}'
        item['tag']['display']['Name'] = nbt.TAG_String(name.format(l=level))
        print item['tag']['display']['Name'].value

        return item
