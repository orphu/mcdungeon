from copy import *
import platform

import items

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

class Material(object):
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

Air = Material('Air', ' ','')
Bedrock = Material('Bedrock', '#', DGREY)
Cactus = Material('Cactus', "*", BGREEN)
Chest = Material('Chest', 'C',BPURPLE)
CoalOre = Material('Coal Ore', 'o',DGREY)
Cobblestone = Material('Cobblestone', '%',DGREY)
CobblestoneSlab = Material('Cobblestone Slab', '%',GREY)
DiamondOre = Material('Diamond Ore', 'o',WHITE)
Dirt = Material('Dirt', '*',YELLOW)
Dispenser = Material('Dispenser', 'D', PURPLE)
DoubleSlab = Material('Stone Double Slab', 'D',WHITE)
Farmland = Material('Farmland', "=", YELLOW)
Fence = Material('Fence', 'o',RED)
Fire = Material('Fire', '!',BRED)
Glass = Material('Glass', 'o',WHITE)
Glowstone = Material('Glowstone Block', "%", YELLOW)
GoldOre = Material('Gold Ore', 'o',YELLOW)
Grass = Material('Grass', '/',GREEN)
Gravel = Material('Gravel', '~',GREY)
IronOre = Material('Iron Ore', 'o',PURPLE)
LapisBlock = Material('Lapis Lazuli Block', 'L',BBLUE)
LapisOre = Material('Lapis Lazuli Ore', 'o',BBLUE)
Lava = Material('Lava', 'L',BRED)
MossStone = Material('Moss Stone', '%',GREEN)
NetherPortal = Material('Portal', '@',BPURPLE)
Obsidian = Material('Obsidian', "@", DGREY)
RedStoneOre = Material('Redstone Ore', 'o',RED)
RedStoneTorchOff = Material('Redstone Torch off', '|', RED)
RedStoneTorchOn = Material('Redstone Torch', '|', BRED)
RedStoneWire = Material('Redstone Wire', '+', RED)
Sand = Material('Sand','"',BYELLOW)
Sandstone = Material('Sandstone', '~',BYELLOW)
SoulSand = Material('Soul Sand', 'S',PURPLE)
Spawner = Material('Monster Spawner', 'S',DGREY)
Stone = Material('Stone' ,'#',GREY)
StonePressurePlate = Material('Stone Pressure Plate' ,'O',GREY)
StoneSlab = Material('Stone Slab', 'd',WHITE)
StoneStairs = Material('Cobblestone Stairs', 'L',DGREY)
Torch = Material('Torch', 'T',BYELLOW)
TNT = Material('TNT', 'X',RED)
WallSign = Material('Wall Sign','[',RED)
Water = Material('Water','~',BBLUE)
Wood = Material('Wood', 'W',RED)
WoodPlanks = Material('Wooden Plank', '=',RED)
WoodenDoor = Material('Wooden Door Block', 'D',RED)
Wool = Material('Wool', 'W',GREY)

_wall = copy(Cobblestone)
_ceiling = copy(Cobblestone)
_floor = copy(Stone)
_subfloor = copy(Bedrock)
