import ConfigParser
from copy import copy
import os
import platform
import random
import re
import sys

import perlin

BLACK = '\033[0;30m'
DGREY = '\033[1;30m'
RED = '\033[0;31m'
BRED = '\033[1;31m'
GREEN = '\033[0;32m'
BGREEN = '\033[1;32m'
YELLOW = '\033[0;33m'
BYELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
BBLUE = '\033[1;34m'
PURPLE = '\033[0;35m'
BPURPLE = '\033[1;35m'
CYAN = '\033[0;36m'
BCYAN = '\033[1;36m'
GREY = '\033[0;37m'
WHITE = '\033[1;37m'
ENDC = '\033[0m'

NOBLOCK = '%s`%s' % (DGREY, ENDC)

# Windows terminal can't handle ANSI color.
if (platform.system() == 'Windows'):
    NOBLOCK = '`'


def valByName(name):
    '''Return a material block value given a name string.'''
    for oname, obj in sys.modules[__name__].__dict__.items():
        if isinstance(obj, Material):
            if (obj.name.lower() == name):
                return obj.val
    return -1

def materialById(id):
    ''' return a Material object given an object identifier '''
    for oname, obj in sys.modules[__name__].__dict__.items():
        if isinstance(obj, Material):
            if obj.val == id or obj.name == id:
                return obj
    return None

# Material class
class Material(object):
    _meta = False
    name = ''
    val = 0
    data = 0
    stack = 0
    id = ''
    heightmap = False
    attach_vines = True
    c = ''
    color = WHITE

    def __init__(self,
                 name='Air',
                 val=0,
                 data=0,
                 stack=64,
                 id='minecraft:air',
                 heightmap=False,
                 attach_vines=True,
                 c=' ',
                 color='WHITE'):
        self.name = name.lower()
        self.val = val
        self.data = data
        self.stack = stack
        self.id = id
        self.heightmap = heightmap
        self.attach_vines = attach_vines
        self.c = c
        color = color.upper()
        if color in globals():
            self.color = globals()[color]
        else:
            print 'WARNING: Invalid color in materials.cfg "{0}"'.format(color)
            self.color = WHITE

        # Windows terminal can't handle ANSI color.
        if (platform.system() == 'Windows'):
            self.c = '%s' % (self.c)
        else:
            self.c = '%s%s%s' % (self.color, self.c, ENDC)

    def __str__(self):
        return 'name: ' + str(self.name) + \
               '\nblock id: ' + str(self.val) + \
               '\ndata value: ' + str(self.data) + \
               '\nstack size: ' + str(self.stack) + \
               '\nstring id: ' + str(self.id) + \
               '\nmap character: ' + str(self.c) + \
               '\nused in heightmap: ' + str(self.heightmap) + \
               '\ncan attach to vines: ' + str(self.attach_vines)


# MetaMaterial class.
class MetaMaterial(Material):
    _meta = True

    def __init__(self):
        return

    def update(self, x, y, z, maxx, maxy, maxz):
        return


# Config parser with default values.
parser = ConfigParser.SafeConfigParser({
    'blockid': '0',
    'datavalue': '0',
    'maxstack': '64',
    'heightmap': 'False',
    'attach_vines': 'True',
    'char': ' ',
    'color': 'WHITE'
})

# Find and parse materials.cfg.
temp = os.path.join(sys.path[0], 'materials.cfg')
try:
    fh = open(temp)
    fh.close
    filename = temp
except:
    filename = os.path.join('materials.cfg')

try:
    parser.readfp(open(filename))
except Exception as e:
    print "Failed to read materials config file!"
    sys.exit(e.message)

# Convert materials.cfg into Materials objects.
# Object names will be the section name with whitespace removed.
# This is a really bad way to do this. I'm a terrible person.
# But is sure is convenient.
num_materials = 0
for material in parser.sections():
    material_id = re.sub('\s+', '', material)
    if material_id not in globals():
        globals()[material_id] = Material(
            name=material,
            val=int(parser.get(material, 'blockid')),
            data=int(parser.get(material, 'datavalue')),
            stack=int(parser.get(material, 'maxstack')),
            id=parser.get(material, 'id'),
            heightmap=(parser.get(material, 'heightmap').lower() == 'true'),
            attach_vines=(parser.get(material,
                                     'attach_vines').lower() == 'true'),
            c=parser.get(material, 'char'),
            color=parser.get(material, 'color')
        )
        num_materials += 1
    else:
        print 'WARNING: Duplicate material:', material
print 'Loaded', num_materials, 'materials.'

# Create a convenience set of blockids for heightmap blocks.
heightmap_solids = set()
for oname, obj in sys.modules[__name__].__dict__.items():
    if isinstance(obj, Material):
        if obj.heightmap is True:
            heightmap_solids.add(obj.val)

# Create a convenience set of blockids for vine blocks.
vine_solids = set()
for oname, obj in sys.modules[__name__].__dict__.items():
    if isinstance(obj, Material):
        if obj.attach_vines is True:
            vine_solids.add(obj.val)


# Meta materials
class meta_class_mossycobble(MetaMaterial):
    name = 'meta_mossycobble'
    val = Cobblestone.val
    data = Cobblestone.data
    c = Cobblestone.c
    pn = perlin.SimplexNoise(256)

    def update(self, x, y, z, maxx, maxy, maxz):
        if self.pn.noise3(x / 4.0, y / 4.0, z / 4.0) < 0:
            self.val = MossStone.val
            self.data = MossStone.data
            self.c = MossStone.c
        else:
            self.val = Cobblestone.val
            self.data = Cobblestone.data
            self.c = Cobblestone.c


class meta_class_mossycobblewall(MetaMaterial):
    name = 'meta_mossycobblewall'
    val = CobblestoneWall.val
    data = CobblestoneWall.data
    c = CobblestoneWall.c
    pn = perlin.SimplexNoise(256)

    def update(self, x, y, z, maxx, maxy, maxz):
        if self.pn.noise3(x / 4.0, y / 4.0, z / 4.0) < 0:
            self.val = MossStoneWall.val
            self.data = MossStoneWall.data
            self.c = MossStoneWall.c
        else:
            self.val = CobblestoneWall.val
            self.data = CobblestoneWall.data
            self.c = CobblestoneWall.c


class meta_class_mossystonebrick(MetaMaterial):
    name = 'meta_mossystonebrick'
    val = StoneBrick.val
    data = StoneBrick.data
    c = StoneBrick.c
    pn = perlin.SimplexNoise(256)

    def update(self, x, y, z, maxx, maxy, maxz):
        if random.randint(1, 100) < 7:
            self.val = CrackedStoneBrick.val
            self.data = CrackedStoneBrick.data
            self.c = CrackedStoneBrick.c
            return

        if random.randint(0, 100) < 2:
            self.val = ChiseledStoneBrick.val
            self.data = ChiseledStoneBrick.data
            self.c = ChiseledStoneBrick.c
            return

        if self.pn.noise3(x / 4.0, y / 4.0, z / 4.0) < 0:
            self.val = MossyStoneBrick.val
            self.data = MossyStoneBrick.data
            self.c = MossyStoneBrick.c
        else:
            self.val = StoneBrick.val
            self.data = StoneBrick.data
            self.c = StoneBrick.c


class meta_class_decoratedsandstone(MetaMaterial):
    name = 'meta_decoratedsandstone'
    val = Sandstone.val
    data = Sandstone.data
    c = Sandstone.c

    def update(self, x, y, z, maxx, maxy, maxz):
        if random.randint(1, 100) < 10:
            self.val = Sandstone.val
            self.data = Sandstone.data
            self.c = Sandstone.c
            return

        if random.randint(1, 100) < 10:
            self.val = SmoothSandstone.val
            self.data = SmoothSandstone.data
            self.c = SmoothSandstone.c
            return

        if y % 5 == 0:
            self.val = ChiseledSandstone.val
            self.data = ChiseledSandstone.data
            self.c = ChiseledSandstone.c
        else:
            self.val = Sandstone.val
            self.data = Sandstone.data
            self.c = Sandstone.c


class meta_class_decoratedredsandstone(MetaMaterial):
    name = 'meta_decoratedredsandstone'
    val = RedSandstone.val
    data = RedSandstone.data
    c = RedSandstone.c

    def update(self, x, y, z, maxx, maxy, maxz):
        if random.randint(1, 100) < 10:
            self.val = RedSandstone.val
            self.data = RedSandstone.data
            self.c = RedSandstone.c
            return

        if random.randint(1, 100) < 10:
            self.val = SmoothRedSandstone.val
            self.data = SmoothRedSandstone.data
            self.c = SmoothRedSandstone.c
            return

        if y % 5 == 0:
            self.val = ChiseledRedSandstone.val
            self.data = ChiseledRedSandstone.data
            self.c = ChiseledRedSandstone.c
        else:
            self.val = RedSandstone.val
            self.data = RedSandstone.data
            self.c = RedSandstone.c


class meta_class_stonedungeon(MetaMaterial):
    name = 'meta_stonedungeon'
    val = StoneBrick.val
    data = StoneBrick.data
    c = StoneBrick.c
    pn = perlin.SimplexNoise(256)

    def update(self, x, y, z, maxx, maxy, maxz):
        n = self.pn.noise3(x / 100.0, y / 100.0, z / 100.0)
        n = n + (float(y) / float(maxy)) * 2

        # Random broken stone brick in stone brick and cobble zones.
        if n <= 1.5:
            broken = .1 + (float(y) / float(maxy)) * .5
            if random.randint(1, 100) < broken * 10 + 5:
                self.val = CrackedStoneBrick.val
                self.data = CrackedStoneBrick.data
                self.c = CrackedStoneBrick.c
                return

        # Random circle stone in stone brick zones
        if n <= 1.0:
            if random.randint(0, 100) < 2:
                self.val = ChiseledStoneBrick.val
                self.data = ChiseledStoneBrick.data
                self.c = ChiseledStoneBrick.c
                return

        # Deepest areas are mossy cobble
        if (n > 1.5):
            if self.pn.noise3(x / 4.0, y / 4.0, z / 4.0) < 0:
                self.val = MossStone.val
                self.data = MossStone.data
                self.c = MossStone.c
            else:
                self.val = Cobblestone.val
                self.data = Cobblestone.data
                self.c = Cobblestone.c
        # Deep areas are cobble
        elif (n > 1.0):
            self.val = Cobblestone.val
            self.data = Cobblestone.data
            self.c = Cobblestone.c
        # lower areas as mossy brick
        elif (n > 0.5):
            if self.pn.noise3(x / 4.0, y / 4.0, z / 4.0) < 0:
                self.val = MossyStoneBrick.val
                self.data = MossyStoneBrick.data
                self.c = MossyStoneBrick.c
            else:
                self.val = StoneBrick.val
                self.data = StoneBrick.data
                self.c = StoneBrick.c
        # High areas are stone brick
        else:
            self.val = StoneBrick.val
            self.data = StoneBrick.data
            self.c = StoneBrick.c


meta_mossycobble = meta_class_mossycobble()
meta_mossycobblewall = meta_class_mossycobblewall()
meta_mossystonebrick = meta_class_mossystonebrick()
meta_stonedungeon = meta_class_stonedungeon()
meta_decoratedsandstone = meta_class_decoratedsandstone()
meta_decoratedredsandstone = meta_class_decoratedredsandstone()

_wall = copy(Cobblestone)
_secret_door = copy(Cobblestone)
_ceiling = copy(Cobblestone)
_floor = copy(Stone)
_subfloor = copy(Bedrock)
_sandbar = copy(Sand)
_natural = copy(Air)
