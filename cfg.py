import sys
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

master_halls = {}
master_rooms = {}
master_features = {}
master_floors = {}

def Load(filename = 'mcdungeon.cfg'):
    global parser, offset, tower, doors, portcullises, torches, wall, floor, \
    ceiling, mvportal, master_halls, master_rooms, master_features, \
    master_floors

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

    if (tower < 1.0):
        sys.exit('The tower height parameter is too small. This should be \
                 >= 1.0. Check the cfg file.')
