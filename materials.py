import sys

from copy import *
import platform
import random

import items
import perlin

BLACK  = '\033[0;30m'
DGREY  = '\033[1;30m'
RED    = '\033[0;31m'
BRED   = '\033[1;31m'
GREEN  = '\033[0;32m'
BGREEN = '\033[1;32m'
YELLOW = '\033[0;33m'
BYELLOW= '\033[1;33m'
BLUE   = '\033[0;34m'
BBLUE  = '\033[1;34m'
PURPLE = '\033[0;35m'
BPURPLE= '\033[1;35m'
CYAN   = '\033[0;36m'
BCYAN  = '\033[1;36m'
GREY   = '\033[0;37m'
WHITE  = '\033[1;37m'
ENDC   = '\033[0m'

NOBLOCK = '%s`%s' % (DGREY, ENDC)

if (platform.system() == 'Windows'):
    NOBLOCK = '`'

def valByName(name):
    '''Return a material block value given a name string.'''
    for oname, obj in sys.modules[__name__].__dict__.items():
        if type(obj) == Material:
            if (obj.name.lower() == name):
                return obj.val
    return -1

class Material(object):
    _meta = False
    name = 'Air'
    val = 0
    data = 0
    def __init__(self, name, char, color):
        self.name = name.lower()
        self.updateData()
        if (platform.system() == 'Windows'):
            self.c = '%s' % (char)
        else:
            self.c = '%s%s%s' % (color,char,ENDC)

    def updateData(self):
        self.val = items.byName(self.name).value
        self.data = items.byName(self.name).data

class MetaMaterial(Material):
    _meta = True
    name = 'Air'
    val = 0
    data = 0
    def __init__(self):
        return
    def update(self, x,y,z, maxx, maxy, maxz):
        return


Air = Material('Air', ' ',BLACK)
Bedrock = Material('Bedrock', '#', DGREY)
Birch = Material('Birch', 'W', DGREY)
Bookshelf = Material('Bookshelf', '#', RED)
BrickBlock = Material('Brick Block', '#', RED)
BrownMushroom = Material('Brown Mushroom', 'p',RED)
Cactus = Material('Cactus', "*", BGREEN)
Chest = Material('Chest', 'C',BPURPLE)
CoalOre = Material('Coal Ore', 'o',DGREY)
Cobblestone = Material('Cobblestone', '%',DGREY)
CobblestoneSlab = Material('Cobblestone Slab', '%',GREY)
Cobweb = Material('Cobweb','*',WHITE)
CrackedStoneBrick = Material('Cracked Stone Brick' ,'P',GREY)
CraftingTable = Material('Crafting Table', 'C', YELLOW)
DiamondOre = Material('Diamond Ore', 'o',WHITE)
Dirt = Material('Dirt', '*',YELLOW)
Dispenser = Material('Dispenser', 'D', PURPLE)
DoubleSlab = Material('Stone Double Slab', 'D',WHITE)
EndPortalFrame = Material('End Portal Frame', 'E',CYAN)
EndStone = Material('End Stone', 'E',WHITE)
Farmland = Material('Farmland', "=", YELLOW)
Fence = Material('Fence', 'o',RED)
Fire = Material('Fire', '!',BRED)
Furnace = Material('Furnace', 'F', DGREY)
Glass = Material('Glass', 'o',CYAN)
GlassPane = Material('Glass Pane', 'o',CYAN)
Glowstone = Material('Glowstone Block', "%", YELLOW)
GoldOre = Material('Gold Ore', 'o',YELLOW)
Grass = Material('Grass', '/',GREEN)
Gravel = Material('Gravel', '~',GREY)
Ice = Material('Ice', '~',CYAN)
IronBars = Material('Iron Bars', 'o',CYAN)
IronDoor = Material('Iron Door Block', 'D',CYAN)
IronOre = Material('Iron Ore', 'o',PURPLE)
LapisBlock = Material('Lapis Lazuli Block', 'L',BBLUE)
LapisOre = Material('Lapis Lazuli Ore', 'o',BBLUE)
Lava = Material('Lava', 'L',BRED)
MossStone = Material('Moss Stone', '%',GREEN)
MossyStoneBrick = Material('Mossy Stone Brick' ,'B',GREEN)
NetherBrick = Material('Nether Brick', 'B',BPURPLE)
NetherBrickFence = Material('Nether Brick Fence', 'o',BPURPLE)
NetherPortal = Material('Portal', '@',BPURPLE)
Netherrack = Material('Netherrack', '%',BPURPLE)
NoteBlock = Material('Note Block', 'N',CYAN)
Obsidian = Material('Obsidian', "@", DGREY)
Piston = Material('Piston', "P", GREY)
PistonExtension = Material('Piston Extension', "T", YELLOW)
Rails = Material('Rails', 'H',GREY)
RedMushroom = Material('Red Mushroom', 'p',BRED)
RedStoneOre = Material('Redstone Ore', 'o',RED)
RedStoneTorchOff = Material('Redstone Torch off', '|', RED)
RedStoneTorchOn = Material('Redstone Torch', '|', BRED)
RedStoneWire = Material('Redstone Wire', '+', RED)
RedStoneRepeaterOff = Material('Redstone Repeater Off', '>', RED)
RedStoneRepeaterOn = Material('Redstone Repeater On', '>', BRED)
Redwood = Material('Redwood', 'W', RED)
Sand = Material('Sand','"',BYELLOW)
Sandstone = Material('Sandstone', '~',BYELLOW)
SandstoneSlab = Material('Sandstone Slab', '~',BYELLOW)
SoulSand = Material('Soul Sand', 'S',PURPLE)
Spawner = Material('Monster Spawner', 'S',DGREY)
StickyPiston = Material('Sticky Piston', "P", GREEN)
StillWater = Material('StillWater','~',BBLUE)
Stone = Material('Stone' ,'#',GREY)
StoneBrick = Material('Stone Brick' ,'B',GREY)
StoneBrickSlab = Material('Stone Brick Slab' ,'b',GREY)
StoneBrickStairs = Material('Stone Brick Stairs' ,'L',DGREY)
StoneButton = Material('Stone Button' ,'.',GREY)
StonePressurePlate = Material('Stone Pressure Plate' ,'O',GREY)
StoneSlab = Material('Stone Slab', 'd',WHITE)
StoneStairs = Material('Cobblestone Stairs', 'L',DGREY)
Torch = Material('Torch', 'T',BYELLOW)
TNT = Material('TNT', 'X',RED)
Vines = Material('Vines', 'V',GREEN)
WallSign = Material('Wall Sign','[',RED)
Water = Material('Water','~',BBLUE)
Wood = Material('Wood', 'W',RED)
WoodPlanks = Material('Wooden Plank', '=',RED)
WoodenDoor = Material('Wooden Door Block', 'D',RED)
WoodenPressurePlate = Material('Wooden Pressure Plate' ,'O',RED)
WoodenSlab = Material('Wooden Slab', 'd',RED)
WoodenStairs = Material('Wooden Stairs', 'L',RED)
Wool = Material('Wool', 'W',GREY)

# Wools
OrangeWool = Material('Orange Wool', 'W', YELLOW)
MagentaWool = Material('Magenta Wool', 'W', BPURPLE)
LightBlueWool = Material('Light Blue Wool', 'W', CYAN)
YellowWool = Material('Yellow Wool', 'W', BYELLOW)
LightGreenWool = Material('Light Green Wool', 'W', BGREEN)
PinkWool = Material('Pink Wool', 'W', RED)
GrayWool = Material('Gray Wool', 'W', DGREY)
LightGrayWool = Material('Light Gray Wool', 'W', GREY)
CyanWool = Material('Cyan Wool', 'W', BCYAN)
PurpleWool = Material('Purple Wool', 'W', PURPLE)
BlueWool = Material('Blue Wool', 'W', BLUE)
BrownWool = Material('Brown Wool', 'W', RED)
DarkGreenWool = Material('Dark Green Wool', 'W', GREEN)
RedWool = Material('Red Wool', 'W', RED)
BlackWool = Material('Black Wool', 'W', DGREY)


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


class meta_class_mossystonebrick(MetaMaterial):
    name = 'meta_mossystonebrick'
    val = StoneBrick.val
    data = StoneBrick.data
    c = StoneBrick.c
    pn = perlin.SimplexNoise(256)
    def update(self, x, y, z, maxx, maxy, maxz):
        if random.randint(1,100) < 7:
            self.val = CrackedStoneBrick.val
            self.data = CrackedStoneBrick.data
            self.c = CrackedStoneBrick.c
            return

        if self.pn.noise3(x / 4.0, y / 4.0, z / 4.0) < 0:
            self.val = MossyStoneBrick.val
            self.data = MossyStoneBrick.data
            self.c = MossyStoneBrick.c
        else:
            self.val = StoneBrick.val
            self.data = StoneBrick.data
            self.c = StoneBrick.c


class meta_class_stonedungeon(MetaMaterial):
    name = 'meta_stonedungeon'
    val = StoneBrick.val
    data = StoneBrick.data
    c = StoneBrick.c
    pn = perlin.SimplexNoise(256)
    def update(self, x, y, z, maxx, maxy, maxz):
        n = self.pn.noise3(x / 100.0, y / 100.0, z / 100.0)
        n = n + (float(y)/float(maxy))*2

        if n <= 1.5:
            broken = .1+(float(y)/float(maxy))*.5
            if random.randint(1,100) < broken*10+5:
                self.val = CrackedStoneBrick.val
                self.data = CrackedStoneBrick.data
                self.c = CrackedStoneBrick.c
                return

        if (n > 1.5):
            #self.val = MossStone.val
            #self.data = MossStone.data
            #self.c = MossStone.c
            if self.pn.noise3(x / 4.0, y / 4.0, z / 4.0) < 0:
                self.val = MossStone.val
                self.data = MossStone.data
                self.c = MossStone.c
            else:
                self.val = Cobblestone.val
                self.data = Cobblestone.data
                self.c = Cobblestone.c
        elif (n > 1.0):
            self.val = Cobblestone.val
            self.data = Cobblestone.data
            self.c = Cobblestone.c
        elif (n > 0.5):
            #self.val = MossyStoneBrick.val
            #self.data = MossyStoneBrick.data
            #self.c = MossyStoneBrick.c
            if self.pn.noise3(x / 4.0, y / 4.0, z / 4.0) < 0:
                self.val = MossyStoneBrick.val
                self.data = MossyStoneBrick.data
                self.c = MossyStoneBrick.c
            else:
                self.val = StoneBrick.val
                self.data = StoneBrick.data
                self.c = StoneBrick.c
        else:
            self.val = StoneBrick.val
            self.data = StoneBrick.data
            self.c = StoneBrick.c

meta_mossycobble = meta_class_mossycobble()
meta_mossystonebrick = meta_class_mossystonebrick()
meta_stonedungeon = meta_class_stonedungeon()

_wall = copy(Cobblestone)
_secret_door = copy(Cobblestone)
_ceiling = copy(Cobblestone)
_floor = copy(Stone)
_subfloor = copy(Bedrock)
_sandbar = copy(Sand)
_natural = copy(Air)
