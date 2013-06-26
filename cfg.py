import ConfigParser
import os
from pprint import pprint
import sys
import items

import materials
from utils import *

cache_dir = 'mcdungeon_cache'

loops = '0'
min_dist = '2'
max_dist = '10'
maximize_distance = 'True'
offset = ''
bury = 'True'
tower = '2.0'
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
exit_portal = 'False'
chests = '10'
double_treasure = 'False'
enchant_system = 'table+book'
spawners = '2'
hidden_spawners = 'False'
SpawnCount = 0
SpawnMaxNearbyEntities = 0
SpawnMinDelay = 0
SpawnMaxDelay = 0
SpawnRequiredPlayerRange = 0
treasure_SpawnCount = 0
treasure_SpawnMaxNearbyEntities = 0
treasure_SpawnMinDelay = 0
treasure_SpawnMaxDelay = 0
treasure_SpawnRequiredPlayerRange = 0
arrow_traps = '3'
chest_traps = '3'
sand_traps = '40'
arrow_trap_defects = '1'
skeleton_balconies = '25'
fill_caves = 'False'
torches_position = 3
hall_piston_traps = 75
resetting_hall_pistons = 'True'
secret_rooms = '75'
silverfish = '0'
maps = '0'
mapstore = ''
portal_exit = Vec(0,0,0)
dungeon_name = None

master_halls = []
master_rooms = []
master_srooms = []
master_features = []
master_stairwells = []
master_floors = []
master_ruins = [('blank',1)]
master_entrances = {}
master_treasure = [('pitwitharchers',1)]
master_dispensers = []
lookup_dispensers = {}
master_chest_traps = []
lookup_chest_traps = {}
master_mobs = {}
max_mob_tier = 0
structure_values = []
custom_spawners = {}
spawners_path = 'spawners'

file_extra_items = ''
file_dyes = 'dye_colors.txt'
file_potions = 'potions.txt'
file_magic_items = 'magic_items.txt'
file_fortunes = 'fortunes.txt'
dir_paintings = 'paintings'
dir_books = 'books'

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
    
def isDir(folder):
    if os.path.isdir(os.path.join(sys.path[0],folder)):
        return True
    elif os.path.isdir(folder):
        return True
    return False
    
def isFile(file):
    if os.path.isfile(os.path.join(sys.path[0],file)):
        return True
    elif os.path.isfile(file):
        return True
    return False

def Load(filename = 'default.cfg'):
    global parser, offset, tower, doors, portcullises, torches_top, wall, \
    floor, ceiling, exit_portal, master_halls, master_rooms, master_features, \
    master_floors, chests, double_treasure, enchant_system, spawners, \
    master_mobs, torches_bottom, min_dist, max_dist, arrow_traps, loops, \
    portcullis_closed, fill_caves, portcullis_web, subfloor, torches_position, \
    skeleton_balconies, arrow_trap_defects, sand_traps, master_ruins, ruin_ruins, \
    maximize_distance, hall_piston_traps, resetting_hall_pistons, \
    structure_values, master_entrances, master_treasure, secret_rooms, \
    secret_door, silverfish, bury, master_dispensers, maps, mapstore, \
    max_mob_tier, custom_spawners, spawners_path, master_stairwells, \
    hidden_spawners, master_srooms, SpawnCount, SpawnMaxNearbyEntities, \
    SpawnMinDelay, SpawnMaxDelay, SpawnRequiredPlayerRange, chest_traps, \
    master_chest_traps, treasure_SpawnCount, treasure_SpawnMaxNearbyEntities, \
    treasure_SpawnMinDelay, treasure_SpawnMaxDelay, treasure_SpawnRequiredPlayerRange, \
    file_extra_items, file_dyes, file_potions, file_magic_items, file_fortunes, \
    dir_paintings, dir_books

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
        
    # Load the various extra file locations
    file_extra_items = get('locations', 'file_extra_items', file_extra_items)
    file_dyes = get('locations', 'file_dyes', file_dyes)
    file_potions = get('locations', 'file_potions', file_potions)
    file_magic_items = get('locations', 'file_magic_items', file_magic_items)
    file_fortunes = get('locations', 'file_fortunes', file_fortunes)
    dir_paintings = get('locations', 'dir_paintings', dir_paintings)
    dir_books = get('locations', 'dir_books', dir_books)
    
    # These are not used until actual generation begins, so check they are
    # good now. Just shows warnings.
    if isFile(file_fortunes) == False:
            print "Warning: fortune file '"+file_fortunes+"' not found."
    if isDir(dir_paintings) == False:
            print "Warning: paintings directory '"+dir_paintings+"' not found."
    if isDir(dir_books) == False:
            print "Warning: books directory '"+dir_books+"' not found."

    # Only vanilla items have been loaded so far, we can now load the rest
    if file_extra_items != '':
        items.LoadItems(file_extra_items)
    items.LoadDyedArmour(file_dyes)
    items.LoadPotions(file_potions)
    items.LoadMagicItems(file_magic_items)

    # Load master tables from .cfg.
    master_halls = parser.items('halls')
    master_rooms = parser.items('rooms')
    master_srooms = parser.items('secret rooms')
    master_features = parser.items('features')
    master_stairwells = parser.items('stairwells')
    master_floors = parser.items('floors')
    temp_dispensers = parser.items('dispensers')
    temp_chest_traps = parser.items('chest_traps')
    try:
        master_ruins = parser.items('ruins')
    except:
        print 'WARNING: No ruins section found in config. Using default.'
    try:
        master_treasure = parser.items('treasure rooms')
    except:
        print 'WARNING: No treasure rooms section found in config. Using default.'

    # Load per-biome entrances.
    # First, the default
    try:
        default_entrances = parser.items('entrances')
    except:
        default_entrances = [('SquareTowerEntrance', 10)]
    # 23 biomes as of Minecraft 1.5
    for d in xrange(0,23):
        section = 'entrances.{0}'.format(d)
        try:
            master_entrances[d] = parser.items(section)
        except:
            master_entrances[d] = default_entrances

    # Load the mob spawner tables
    max_mob_tier = 0
    if parser.has_section('mobs'):
        print 'WARNING: This config file contains old-stye mob definitions.'
        print 'You should update your config file with the new mob features.'
        temp_mobs = parser.items('mobs')
    elif parser.has_section('mobs.0'):
        temp_mobs = parser.items('mobs.0')
    else:
        sys.exit('Failed to read mob config from config file.')
    while len(temp_mobs) is not 0:
        for mob in temp_mobs:
            mob_name = mob[0]
            if max_mob_tier not in master_mobs:
                master_mobs[max_mob_tier] = []
            master_mobs[max_mob_tier].append((mob_name, mob[1]))
        max_mob_tier += 1
        try:
            temp_mobs = parser.items('mobs.'+str(max_mob_tier))
        except:
            temp_mobs = []
            max_mob_tier -= 1

    # Load custom spawners
    try:
        if os.path.isdir(os.path.join(sys.path[0],'spawners')):
            spawners_path = os.path.join(sys.path[0],'spawners')
        else:
            spawners_path = 'spawners'
        for file in os.listdir(spawners_path):
            if file.endswith(".nbt"):
                custom_spawners[file[:-4].lower()] = file[:-4]
        print 'Loaded', len(custom_spawners), 'custom spawners.'
    except:
        print 'Could not find spawners directory!'

    # Process dispensers config
    for d in temp_dispensers:
        (prob, number) = d[1].split(',')
        name = d[0].lower()
        lookup_dispensers[name]= (prob, number)
        master_dispensers.append((name, prob))

    # Process chest_traps config
    for d in temp_chest_traps:
        (prob, number) = d[1].split(',')
        name = d[0].lower()
        lookup_chest_traps[name]= (prob, number)
        master_chest_traps.append((name, prob))

    # Load other config options
    offset = get('dungeon', 'offset', offset)
    bury = str2bool(get('dungeon', 'force_bury', bury))

    tower = float(get('dungeon', 'tower', tower))
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

    exit_portal = str2bool(get('dungeon', 'exit_portal', exit_portal))

    chests = float(get('dungeon', 'chests', chests))
    double_treasure = str2bool(get('dungeon', 'double_treasure', double_treasure))
    enchant_system = get('dungeon', 'enchant_system', enchant_system).lower()
    spawners = float(get('dungeon', 'spawners', spawners))
    hidden_spawners = str2bool(get('dungeon', 'hidden_spawners', hidden_spawners))
    SpawnCount = int(get('dungeon', 'SpawnCount', SpawnCount))
    SpawnMaxNearbyEntities = int(get('dungeon', 'SpawnMaxNearbyEntities',
                                                 SpawnMaxNearbyEntities))
    SpawnMinDelay = int(get('dungeon', 'SpawnMinDelay', SpawnMinDelay))
    SpawnMaxDelay = int(get('dungeon', 'SpawnMaxDelay', SpawnMaxDelay))
    SpawnRequiredPlayerRange = int(get('dungeon', 'SpawnRequiredPlayerRange',
                                                   SpawnRequiredPlayerRange))
    # These fall back to the above when not set
    treasure_SpawnCount = int(get('dungeon', 'treasure_SpawnCount', SpawnCount))
    treasure_SpawnMaxNearbyEntities = int(get('dungeon', 'treasure_SpawnMaxNearbyEntities',
                                                          SpawnMaxNearbyEntities))
    treasure_SpawnMinDelay = int(get('dungeon', 'treasure_SpawnMinDelay',
                                                 SpawnMinDelay))
    treasure_SpawnMaxDelay = int(get('dungeon', 'treasure_SpawnMaxDelay',
                                                 SpawnMaxDelay))
    treasure_SpawnRequiredPlayerRange = int(get('dungeon', 'treasure_SpawnRequiredPlayerRange',
                                                SpawnRequiredPlayerRange))
    min_dist = int(get('dungeon', 'min_dist', min_dist))
    max_dist = int(get('dungeon', 'max_dist', max_dist))
    maximize_distance = str2bool(get('dungeon', 'maximize_distance',
                                     maximize_distance))
    arrow_traps = int(get('dungeon', 'arrow_traps', arrow_traps))
    chest_traps = int(get('dungeon', 'chest_traps', chest_traps))
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

    fill_caves = str2bool(get('dungeon', 'fill_caves', fill_caves))
    secret_rooms = int(get('dungeon', 'secret_rooms', secret_rooms))
    silverfish = int(get('dungeon', 'silverfish', silverfish))
    maps = int(get('dungeon', 'maps', maps))
    mapstore = get('dungeon', 'mapstore', mapstore)

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
