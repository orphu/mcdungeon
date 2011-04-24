import sys
import materials
import ConfigParser

from utils import *

loops = '0'
min_dist = '2'
max_dist = '10'
offset = ''
tower = '2.0'
doors = '25'
portcullises = '25'
portcullis_closed = '10'
portcullis_web = '5'
torches_top = '50'
torches_bottom = '50'
wall = 'Cobblestone'
floor = 'Stone'
ceiling = 'Cobblestone'
subfloor = 'Bedrock'
mvportal = ''
chests = '10'
spawners = '2'
arrow_traps = '5'
hard_mode = 'False'

master_halls = []
master_rooms = []
master_features = []
master_floors = []
master_mobs = []

parser = ConfigParser.SafeConfigParser()

def get(section, var, default):
    global parser
    try:
        temp = parser.get(section, var)
    except:
        return default
    return temp

def Load(filename = 'configs/default.cfg'):
    global parser, offset, tower, doors, portcullises, torches_top, wall, \
    floor, ceiling, mvportal, master_halls, master_rooms, master_features, \
    master_floors, chests, spawners, master_mobs, torches_bottom, min_dist, \
    max_dist, arrow_traps, loops, portcullis_closed, hard_mode, \
    portcullis_web, subfloor

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
    offset = get('dungeon', 'offset', offset)

    tower = float(get('dungeon', 'tower', tower))
    doors = int(get('dungeon', 'doors', doors))
    portcullises = int(get('dungeon', 'portcullises', portcullises))
    portcullis_closed = int(get('dungeon',
                                'portcullis_closed',
                                portcullis_closed))
    portcullis_web = int(get('dungeon',
                             'portcullis_web',
                             portcullis_web))
    torches_top = int(get('dungeon',
                          'torches_top',
                          torches_top))
    torches_bottom = int(get('dungeon',
                             'torches_bottom',
                             torches_bottom))

    wall = get('dungeon', 'wall', wall).lower()
    ceiling = get('dungeon', 'ceiling', ceiling).lower()
    floor = get('dungeon', 'floor', floor).lower()
    subfloor = get('dungeon', 'subfloor', subfloor).lower()

    mvportal = get('dungeon', 'mvportal', mvportal)

    chests = float(get('dungeon', 'chests', chests))
    spawners = float(get('dungeon', 'spawners', spawners))
    min_dist = int(get('dungeon', 'min_dist', min_dist))
    max_dist = int(get('dungeon', 'max_dist', max_dist))
    arrow_traps = int(get('dungeon', 'arrow_traps', arrow_traps))
    loops = int(get('dungeon', 'loops', loops))

    hard_mode = bool(get('dungeon', 'hard_mode', hard_mode))

    if (tower < 1.0):
        sys.exit('The tower height parameter is too small. This should be \
                 >= 1.0. Check the cfg file.')

    if (chests < 0.0 or chests > 10.0):
        sys.exit('Chests should be between 0 and 10. Check the cfg file.')

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
            if (val.name == subfloor):
                materials._subfloor = copy(val)

