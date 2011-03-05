from copy import *

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

class Material(object):
    def __init__(self, name, char, color):
        self.name = name
        self.val = 0
	self.c = '%s%s%s' % (color,char,ENDC)
    def updateMaterialValue(self, world):
        try:
            self.val = world.materials.materialNamed(self.name)
        except:
            raise Exception("couldn't find material: "+self.name)


Bedrock = Material('Bedrock', '#', DGREY)
Air = Material('Air', ' ','')
Stone = Material('Stone' ,'#',GREY)
Water = Material('Water (active)','~',BBLUE)
Sand = Material('Sand','"',BYELLOW)
Glass = Material('Glass', 'o',WHITE)
Grass = Material('Grass', '/',GREEN)
Dirt = Material('Dirt', '*',YELLOW)
Fire = Material('Fire', '!',BRED)
Chest = Material('Chest', 'C',YELLOW)
Lava = Material('Lava (active)', 'L',BRED)
TNT = Material('TNT', 'X',RED)
Wood = Material('Wood', 'W',RED)
WoodPlanks = Material('Wood Planks', '=',RED)
WoodenDoor = Material('Wooden Door', 'D',RED)
Torch = Material('Torch', 'T',BYELLOW)
Cobblestone = Material('Cobblestone', '%',DGREY)
MossStone = Material('Moss Stone', '%',GREEN)
Spawner = Material('Monster Spawner', 'S',DGREY)
Fence = Material('Fence', 'o',RED)
DoubleSlab = Material('Double Stone Slab', 'D',WHITE)

_wall = copy(Cobblestone)
_ceiling = copy(Glass)
_floor = copy(Stone)

