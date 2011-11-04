import sys
import os
import materials
import ConfigParser

from utils import *

loops = '0'
min_dist = '2'
max_dist = '10'
maximize_distance = 'True'
offset = ''
tower = '2.0'
tower_ruin = '80'
ruin_ruins = 'True'
doors = '25'
portcullises = '25'
portcullis_closed = '10'
portcullis_web = '5'
torches_top = '50'
torches_bottom = '50'
wall = 'Cobblestone'
secret_door = 'Cobblestone'
floor = 'Stone'
ceiling = 'Cobblestone'
subfloor = 'Bedrock'
mvportal = ''
chests = '10'
spawners = '2'
arrow_traps = '3'
sand_traps = '40'
arrow_trap_defects = '1'
skeleton_balconies = '25'
hard_mode = 'False'
torches_position = 3
hall_piston_traps = 75
resetting_hall_pistons = 'True'
secret_rooms = '75'
silverfish = '0'

master_halls = []
master_rooms = []
master_features = []
master_floors = []
master_ruins = [('blank',1)]
master_entrances = [('squaretowerentrance',1)]
master_treasure = [('pitwitharchers',1)]
master_mobs = []
structure_values = []

parser = ConfigParser.SafeConfigParser()

def get(section, var, default):
    global parser
    try:
        temp = parser.get(section, var)
    except:
        return default
    return temp

def str2bool(string):
    if (string.lower() is False or
        string.lower() == 'false' or
        string.lower() == 'no' or
        string == '0'):
        return False
    return True

def Load(filename = 'default.cfg'):
    global parser, offset, tower, doors, portcullises, torches_top, wall, \
    floor, ceiling, mvportal, master_halls, master_rooms, master_features, \
    master_floors, chests, spawners, master_mobs, torches_bottom, min_dist, \
    max_dist, arrow_traps, loops, portcullis_closed, hard_mode, \
    portcullis_web, subfloor, torches_position, skeleton_balconies, \
    arrow_trap_defects, sand_traps, master_ruins, tower_ruin, ruin_ruins, \
    maximize_distance, hall_piston_traps, resetting_hall_pistons, \
    structure_values, master_entrances, master_treasure, secret_rooms, \
    secret_door, silverfish

    temp = os.path.join(sys.path[0], 'configs', filename)
    try:
        fh = open(temp)
        fh.close
        filename = temp
    except:
        filename = os.path.join('configs', filename)

    print 'Reading config from', filename, '...'
    try:
        parser.readfp(open(filename))
    except Exception, e:
        print "Failed to read config file!"
        sys.exit(e.message)

    # Load master tables from .cfg.
    master_halls = parser.items('halls')
    master_rooms = parser.items('rooms')
    master_features = parser.items('features')
    master_floors = parser.items('floors')
    temp_mobs = parser.items('mobs')
    try:
        master_ruins = parser.items('ruins')
    except:
        print 'WARNING: No ruins section found in config. Using default.'
    try:
        master_entrances = parser.items('entrances')
    except:
        print 'WARNING: No entrances section found in config. Using default.'
    try:
        master_treasure = parser.items('treasure rooms')
    except:
        print 'WARNING: No treasure rooms section found in config. Using default.'

    # Fix the mob names...
    for mob in temp_mobs:
        mob2 = mob[0].capitalize()
        if (mob2 == 'Pigzombie'):
            mob2 = 'PigZombie'
        elif (mob2 == 'Cavespider'):
            mob2 = 'CaveSpider'
        master_mobs.append((mob2, mob[1]))

    # Load other config options
    offset = get('dungeon', 'offset', offset)

    tower = float(get('dungeon', 'tower', tower))
    tower_ruin = int(get('dungeon', 'tower_ruin', tower_ruin))
    ruin_ruins = str2bool(get('dungeon', 'ruin_ruins', ruin_ruins))
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
    torches_position = int(get('dungeon',
                             'torches_position',
                             torches_position))

    wall = get('dungeon', 'wall', wall).lower()
    ceiling = get('dungeon', 'ceiling', ceiling).lower()
    floor = get('dungeon', 'floor', floor).lower()
    subfloor = get('dungeon', 'subfloor', subfloor).lower()
    secret_door = get('dungeon', 'secret_door', secret_door).lower()

    mvportal = get('dungeon', 'mvportal', mvportal)

    chests = float(get('dungeon', 'chests', chests))
    spawners = float(get('dungeon', 'spawners', spawners))
    min_dist = int(get('dungeon', 'min_dist', min_dist))
    max_dist = int(get('dungeon', 'max_dist', max_dist))
    maximize_distance = str2bool(get('dungeon', 'maximize_distance',
                                     maximize_distance))
    arrow_traps = int(get('dungeon', 'arrow_traps', arrow_traps))
    arrow_trap_defects = int(get('dungeon', 'arrow_trap_defects',
                                 arrow_trap_defects))
    hall_piston_traps = int(get('dungeon', 'hall_piston_traps',
                                hall_piston_traps))
    resetting_hall_pistons = str2bool(get('dungeon', 'resetting_hall_pistons',
                                resetting_hall_pistons))
    skeleton_balconies = int(get('dungeon', 'skeleton_balconies',
                                 skeleton_balconies))
    sand_traps = int(get('dungeon', 'sand_traps', sand_traps))
    loops = int(get('dungeon', 'loops', loops))

    hard_mode = str2bool(get('dungeon', 'hard_mode', hard_mode))
    secret_rooms = int(get('dungeon', 'secret_rooms', secret_rooms))
    silverfish = int(get('dungeon', 'silverfish', silverfish))

    if (tower < 1.0):
        sys.exit('The tower height parameter is too small. This should be >= 1.0. Check the cfg file.')

    if (chests < 0.0 or chests > 10.0):
        sys.exit('Chests should be between 0 and 10. Check the cfg file.')

    if (spawners < 0.0 or spawners > 10.0):
        sys.ext('Spawners should be between 0 and 10. Check the cfg file.')

    if (torches_position < 1 or torches_position > 3):
        sys.ext('torches_position should be between 1-3. Check the cfg file.')

    # Set the wall, ceiling, and floor materials
    for name, val in materials.__dict__.items():
        if (isinstance(val, materials.Material) == True):
            if (val.name == wall):
                materials._wall = copy(val)
            if (val.name == ceiling):
                materials._ceiling = copy(val)
            if (val.name == floor):
                materials._floor = copy(val)
            if (val.name == subfloor):
                materials._subfloor = copy(val)
            if (val.name == secret_door):
                materials._secret_door = copy(val)

    # Load structure list
    s = [x.strip() for x in str(get('dungeon', 'structures', '')).split(',')]
    s = [x.lower() for x in s]
    if (len(s) > 0 and s[0] is not ''):
        for a in s:
            v = materials.valByName(a)
            if (v >= 0):
                structure_values.append(v)
            else:
                sys.exit('Unable to find structure material: '+str(a))
