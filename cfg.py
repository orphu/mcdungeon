import sys
import materials
import ConfigParser

from utils import *

parser = ConfigParser.SafeConfigParser()

offset = Vec(0,0,0)
tower = 1.0
doors = 50
portcullises = 50
torches = 50
wall = 'Cobblestone'
floor = 'Stone'
ceiling = 'Cobblestone'
mvportal = ''
chests = 1
spawners = 2

master_halls = {}
master_rooms = {}
master_features = {}
master_floors = {}
master_mobs = []

def Load(filename = 'mcdungeon.cfg'):
    global parser, offset, tower, doors, portcullises, torches, wall, floor, \
    ceiling, mvportal, master_halls, master_rooms, master_features, \
    master_floors, chests, spawners, master_mobs

    print 'Reading config from', filename, '...'
    try:
        parser.readfp(open(filename))
    except:
        print "Failed to read config file:", filename
        sys.exit(1)

    # Load master tables from .cfg.
    master_halls = parser.items('halls')
    master_rooms = parser.items('rooms')
    master_features = parser.items('features')
    master_floors = parser.items('floors')
    temp_mobs = parser.items('mobs')

    # Fix the mob names...
    for mob in temp_mobs:
        mob2 = mob[0].capitalize()
        if (mob2 == 'Pigzombie'):
            mob2 = 'PigZombie'
        master_mobs.append((mob2, mob[1]))

    # Load other config options
    offset = str2Vec(parser.get('dungeon', 'offset'))
    tower = parser.getfloat('dungeon','tower')
    doors = parser.getint('dungeon','doors')
    portcullises = parser.getint('dungeon', 'portcullises')
    torches = parser.getint('dungeon', 'torches')
    wall = parser.get('dungeon', 'wall')
    ceiling = parser.get('dungeon', 'ceiling')
    floor = parser.get('dungeon', 'floor')
    mvportal = parser.get('dungeon', 'mvportal')
    chests = parser.getfloat('dungeon', 'chests')
    spawners = parser.getfloat('dungeon', 'spawners')

    if (tower < 1.0):
        sys.exit('The tower height parameter is too small. This should be \
                 >= 1.0. Check the cfg file.')

    if (chests < 0.0 or chests > 10.0):
        sys.ext('Chests should be between 0 and 10. Check the cfg file.')

    if (spawners < 0.0 or spawners > 10.0):
        sys.ext('Spawners should be between 0 and 10. Check the cfg file.')

    # Set the wall, ceiling, and floor materials
    for name, val in materials.__dict__.items():
        if type(val) == materials.Material:
            if (val.name == wall):
                materials._wall = copy(val)
            if (val.name == ceiling):
                materials._ceiling = copy(val)
            if (val.name == floor):
                materials._floor = copy(val)


