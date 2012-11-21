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
# Annoyingly, the anvil data values are different when in the inventory
# and placed as a block. The values must be set in each setblock call
Anvil = Material('Anvil', 'T',DGREY)
AnvilSlightlyDmg = Material('Slightly Damaged Anvil', 'T',DGREY)
AnvilVeryDmg = Material('Very Damaged Anvil', 'T',DGREY)
Bedrock = Material('Bedrock', '#', DGREY)
Birch = Material('Birch', 'W', DGREY)
Bookshelf = Material('Bookshelf', '#', RED)
BrewingStand = Material('Brewing Stand Block', '#', DGREY)
BrickBlock = Material('Brick Block', '#', RED)
BrownMushroom = Material('Brown Mushroom', 'p',RED)
Cactus = Material('Cactus', "*", BGREEN)
Cauldron = Material('Cauldron Block', "C", DGREY)
Chest = Material('Chest', 'C',BPURPLE)
CircleStoneBrick = Material('Circle Stone Brick' ,'0',GREY)
CoalOre = Material('Coal Ore', 'o',DGREY)
Cobblestone = Material('Cobblestone', '%',DGREY)
CobblestoneSlab = Material('Cobblestone Slab', '%',GREY)
CobblestoneWall = Material('Cobblestone Wall' ,'o',DGREY)
Cobweb = Material('Cobweb','*',WHITE)
CrackedStoneBrick = Material('Cracked Stone Brick' ,'P',GREY)
CraftingTable = Material('Crafting Table', 'C', YELLOW)
DiamondOre = Material('Diamond Ore', 'o',WHITE)
Dirt = Material('Dirt', '*',YELLOW)
Dispenser = Material('Dispenser', 'D', PURPLE)
DoubleSlab = Material('Stone Double Slab', 'D',WHITE)
EndPortalFrame = Material('End Portal Frame', 'E',CYAN)
EndStone = Material('End Stone', 'E',WHITE)
EmeraldOre = Material('Emerald Ore', 'o',GREEN)
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
Head = Material('Head Block', 'o',CYAN)
Ice = Material('Ice', '~',CYAN)
IronBars = Material('Iron Bars', 'o',CYAN)
IronDoor = Material('Iron Door Block', 'D',CYAN)
IronOre = Material('Iron Ore', 'o',PURPLE)
Jungle = Material('Jungle', 'W',RED)
LapisBlock = Material('Lapis Lazuli Block', 'L',BBLUE)
LapisOre = Material('Lapis Lazuli Ore', 'o',BBLUE)
Lava = Material('Lava', 'L',BRED)
MossStone = Material('Moss Stone', '%',GREEN)
MossyStoneBrick = Material('Mossy Stone Brick' ,'B',GREEN)
MossStoneWall = Material('Moss Stone Wall' ,'o',GREEN)
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
Spruce = Material('Spruce', 'W', RED)
Sand = Material('Sand','"',BYELLOW)
Sandstone = Material('Sandstone', '~',BYELLOW)
SandstoneStairs = Material('Sandstone Stairs', 'L',BYELLOW)
ChiseledSandstone = Material('ChiseledSandstone', '#',BYELLOW)
SmoothSandstone = Material('SmoothSandstone', '-',BYELLOW)
SandstoneSlab = Material('Sandstone Slab', '~',BYELLOW)
Snow = Material('Snow', 'S',WHITE)
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
Trapdoor = Material('Trapdoor', '-',RED)
Tripwire = Material('Tripwire', '-',DGREY)
TripwireHook = Material('Tripwire Hook', '^',PURPLE)
Vines = Material('Vines', 'V',GREEN)
WallSign = Material('Wall Sign','[',RED)
Water = Material('Water','~',BBLUE)
Wood = Material('Wood', 'W',RED)
WoodPlanks = Material('Wooden Plank', '=',RED)
SprucePlanks = Material('Spruce Plank', '=',RED)
BirchPlanks = Material('Birch Plank', '=',RED)
JunglePlanks = Material('Jungle Plank', '=',RED)
WoodenDoor = Material('Wooden Door Block', 'D',RED)
WoodenPressurePlate = Material('Wooden Pressure Plate' ,'O',RED)
WoodenSlab = Material('Wooden Slab', 'd',RED)
SpruceSlab = Material('Spruce Slab', 'd',RED)
BirchSlab = Material('Birch Slab', 'd',RED)
JungleSlab = Material('Jungle Slab', 'd',RED)
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
        if random.randint(1,100) < 7:
            self.val = CrackedStoneBrick.val
            self.data = CrackedStoneBrick.data
            self.c = CrackedStoneBrick.c
            return

        if random.randint(0,100) < 2:
            self.val = CircleStoneBrick.val
            self.data = CircleStoneBrick.data
            self.c = CircleStoneBrick.c
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
        if random.randint(1,100) < 10:
            self.val = Sandstone.val
            self.data = Sandstone.data
            self.c = Sandstone.c
            return

        if random.randint(1,100) < 10:
            self.val = SmoothSandstone.val
            self.data = SmoothSandstone.data
            self.c = SmoothSandstone.c
            return

        if  y % 5 == 0:
            self.val = ChiseledSandstone.val
            self.data = ChiseledSandstone.data
            self.c = ChiseledSandstone.c
        else:
            self.val = Sandstone.val
            self.data = Sandstone.data
            self.c = Sandstone.c


class meta_class_stonedungeon(MetaMaterial):
    name = 'meta_stonedungeon'
    val = StoneBrick.val
    data = StoneBrick.data
    c = StoneBrick.c
    pn = perlin.SimplexNoise(256)
    def update(self, x, y, z, maxx, maxy, maxz):
        n = self.pn.noise3(x / 100.0, y / 100.0, z / 100.0)
        n = n + (float(y)/float(maxy))*2

        # Random broken stone brick in stone brick and cobble zones.
        if n <= 1.5:
            broken = .1+(float(y)/float(maxy))*.5
            if random.randint(1,100) < broken*10+5:
                self.val = CrackedStoneBrick.val
                self.data = CrackedStoneBrick.data
                self.c = CrackedStoneBrick.c
                return

        # Random circle stone in stone brick zones
        if n <= 1.0:
            if random.randint(0,100) < 2:
                self.val = CircleStoneBrick.val
                self.data = CircleStoneBrick.data
                self.c = CircleStoneBrick.c
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

_wall = copy(Cobblestone)
_secret_door = copy(Cobblestone)
_ceiling = copy(Cobblestone)
_floor = copy(Stone)
_subfloor = copy(Bedrock)
_sandbar = copy(Sand)
_natural = copy(Air)
