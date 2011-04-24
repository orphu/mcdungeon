import sys
import materials
import ConfigParser

from utils import *

offset = ''
min_dist = '1'
max_dist = '16'
tower = '1.0'
doors = '50'
portcullises = '50'
portcullis_closed = '10'
portcullis_web = '50'
torches_top = '50'
torches_bottom = '50'
wall = 'Cobblestone'
floor = 'Stone'
ceiling = 'Cobblestone'
subfloor = 'Bedrock'
mvportal = ''
chests = '1'
spawners = '2'
arrow_traps = '5'
loops = '0'
hard_mode = '0'

master_halls = []
master_rooms = []
master_features = []
master_floors = []
master_mobs = []

defaults = {
    'offset': offset,
    'min_dist': min_dist,
    'max_dist': max_dist,
    'tower': tower,
    'doors': doors,
    'portcullises': portcullises,
    'portcullis_closed': portcullis_closed,
    'portcullis_web': portcullis_web,
    'torches_top': torches_top,
    'torches_bottom': torches_bottom,
    'wall': wall,
    'floor': floor,
    'ceiling': ceiling,
    'subfloor': subfloor,
    'mvportal': mvportal,
    'chests': chests,
    'spawners': spawners,
    'arrow_traps': arrow_traps,
    'loops': loops,
    'hard_mode': hard_mode,
}

parser = ConfigParser.SafeConfigParser()

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
    offset = parser.get('dungeon',
                        'offset',
                        True,
                        defaults)

    tower = float(parser.get('dungeon',
                             'tower',
                             True,
                             defaults))

    doors = int(parser.get('dungeon',
                           'doors',
                           True,
                           defaults))

    portcullises = int(parser.get('dungeon',
                                  'portcullises',
                                  True,
                                  defaults))

    portcullis_closed = int(parser.get('dungeon',
                                       'portcullis_closed',
                                       True,
                                       defaults))

    portcullis_web = int(parser.get('dungeon',
                                       'portcullis_web',
                                       True,
                                       defaults))

    torches_top = int(parser.get('dungeon',
                                    'torches_top',
                                       True,
                                       defaults))

    torches_bottom = int(parser.get('dungeon',
                                       'torches_bottom',
                                       True,
                                       defaults))


    wall = parser.get('dungeon', 'wall', True, defaults).lower()
    ceiling = parser.get('dungeon', 'ceiling', True, defaults).lower()
    floor = parser.get('dungeon', 'floor', True, defaults).lower()
    subfloor = parser.get('dungeon', 'subfloor', True, defaults).lower()
    mvportal = parser.get('dungeon', 'mvportal', True, defaults)

    chests = float(parser.get('dungeon', 'chests', True, defaults))
    spawners = float(parser.get('dungeon', 'spawners', True, defaults))
    min_dist = int(parser.get('dungeon', 'min_dist', True, defaults))
    max_dist = int(parser.get('dungeon', 'max_dist', True, defaults))
    arrow_traps = int(parser.get('dungeon', 'arrow_traps', True, defaults))
    loops = int(parser.get('dungeon', 'loops', True, defaults))

    hard_mode = bool(parser.get('dungeon', 'hard_mode', True, defaults))

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

    print 'halls:', master_halls
