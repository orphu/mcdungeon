#!/usr/bin/python

import sys
import os
import argparse
import logging
import re
from pymclevel import mclevel, nbt

__version__ = '0.3.0-dev'
__version_info__ = tuple([ num for num in __version__.split('.')])
_vstring = '%%(prog)s %s' % (__version__)

parent_parser = argparse.ArgumentParser(add_help=False,
    description='Generate a tile-based dungeon in a Minecraft map.')
parent_parser.add_argument('-v', '--version',
                           action='version', version=_vstring,
                           help='Print version and exit')
parent_parser.add_argument('-c', '--config',
                    dest='config',
                    metavar='CFGFILE',
                    default='default.cfg',
                    help='Alternate config file. Default: default.cfg')
parent_parser.add_argument('--write',
                    action='store_true',
                    dest='write' ,
                    help='Write the dungeon to disk')
parent_parser.add_argument('--skip-relight',
                    action='store_true',
                    dest='skiprelight',
                    help='Skip relighting the level')
parent_parser.add_argument('-t','--term',
                    type=int,dest='term',
                    metavar='FLOOR',
                    help='Print a text version of a given floor to the \
                    terminal')
parent_parser.add_argument('--html',
                    dest='html',
                    metavar='BASENAME',
                    help='Output html versions of the dungeon. This \
                    produces one file per level of the form \
                    BASENAME-(level number).html')
parent_parser.add_argument('--force',
                    action='store_true',
                    dest='force',
                    help='Force overwriting of html output files')
parent_parser.add_argument('-s', '--seed',
                    dest='seed',
                    metavar='SEED',
                    help='Provide a seed for this dungeon. This can be \
                    anything')
parent_parser.add_argument('-o', '--offset',
                    dest='offset',
                    nargs=3,
                    type=int,
                    metavar=('X', 'Y', 'Z'),
                    help='Provide a location offset in blocks')
parent_parser.add_argument('-b', '--bury',
                    action='store_true',
                    dest='bury',
                    help='Attempt to calculate Y when using --offset')
parent_parser.add_argument('-e', '--entrance',
                    dest='entrance',
                    nargs=2,
                    type=int,
                    metavar=('Z', 'X'),
                    help='Provide an offset for the entrance in chunks')
parent_parser.add_argument('-n','--number',
                    type=int,dest='number',
                    metavar='NUM',
                    default=1,
                    help='Number of dungeons to generate. -1 will create as \
                    many as possible given X, Z, and LEVEL settings.')

i_parser = argparse.ArgumentParser(parents=[parent_parser], add_help=False)
i_parser.add_argument('-i', '--interactive',
                    action='store_true',
                    dest='interactive' ,
                    help='Start in interactive mode. Prompt for SAVEDIR, Z, X, \
                    CFGFILE, and LEVELS.')


noi_parser = argparse.ArgumentParser(parents=[i_parser])
noi_parser.add_argument('world',
                    metavar='SAVEDIR',
                    help='Target world (path to save directory)')
noi_parser.add_argument('z',
                    metavar='Z',
                    help='Number of rooms West -> East. Use -1 for random, or \
                        provide a range. (ie: 4-7)')
noi_parser.add_argument('x',
                    metavar='X',
                    help='Number of rooms North -> South. Use -1 for random, \
                        or provide a range.')
noi_parser.add_argument('levels',
                    metavar='LEVELS',
                    help='Number of levels. Enter a positive value, or provide a \
                        range.')

iargs = i_parser.parse_known_args()
if (iargs[0].interactive == False):
    args = noi_parser.parse_args()
else:
    args = iargs[0]

import cfg
import loottable
from dungeon import *
from utils import *

if (args.interactive == True):
    print 'Starting interactive mode!'

    configDir = os.path.join(sys.path[0], 'configs')
    if (os.path.isdir(configDir) == False):
        configDir = 'configs'
    if (os.path.isdir(configDir) == False):
        sys.exit('\nI cannot find your configs directory! Aborting!')
    print '\nConfigurations in your configs directory:\n'
    for file in os.listdir(configDir):
        file_path = os.path.join(configDir, file)
        file = file.replace('.cfg', '')
        if (os.path.isfile(file_path) and
           file_path.endswith('.cfg')):
            print '   ',file
    print '\nEnter the name of the configuration you wish to use.'
    config = raw_input('(leave blank for default): ')
    if (config == ''):
        config = 'default'
    #args.config = str(os.path.join(configDir, config))+'.cfg'
    args.config = str(config)+'.cfg'
    cfg.Load(args.config)

    saveFileDir = mclevel.saveFileDir
    print '\nYour save directory is:\n', saveFileDir
    if (os.path.isdir(saveFileDir) == False):
        sys.exit('\nI cannot find your save directory! Aborting!')
    print '\nWorlds in your save directory:\n'
    for file in os.listdir(saveFileDir):
        file_path = os.path.join(saveFileDir, file)
        if os.path.isdir(file_path):
            print '   ',file
    world = raw_input('\nEnter the name of the world you wish to modify: ')
    args.world = os.path.join(saveFileDir, world)

    m = cfg.max_dist - cfg.min_dist
    print '\nEnter the size of the dungeon(s) from East to West. (Z size)'
    print 'You can enter a fixed value >= 4, or a range (ie: 4-7)'
    print 'Enter -1 to pick random values between 4 and %d. (based on your config)'%(m)
    args.z = raw_input('Z size: ')

    print '\nEnter the size of the dungeon(s) from North to South. (X size)'
    print 'You can enter a fixed value >= 4, or a range (ie: 4-7)'
    print 'Enter -1 to pick random values between 4 and %d. (based on your config)'%(m)
    args.x = raw_input('X size: ')

    print '\nEnter a number of levels.'
    print 'You can enter a fixed value >= 1, or a range (ie: 3-5)'
    print 'Enter -1 to pick random values between 1 and 8.'
    args.levels = raw_input('Levels: ')

    print '\nEnter the maximum number of dungeons to add.'
    print 'Depending on the characteristics of your world, and size of your'
    print 'dungeons, the actual number placed may be less.'
    print 'Enter -1 to add as many dungeons as possible.'
    args.number = raw_input('Number of dungeons (leave blank for 1): ')
    if (args.number == ''):
        args.number = 1
    try:
        args.number  = int(args.number)
    except ValueError:
        sys.exit('You must enter an integer.')

    #html = raw_input('\nWould you like to create an HTML map? (y/n): ')
    #if (html.lower() == 'y'):
    #    args.html = world
    #    args.force = True
    args.write = True
else:
    cfg.Load(args.config)

# Load lewts
loottable.Load()

# Parse out the sizes
min_x = 4
max_x = cfg.max_dist - cfg.min_dist
min_z = 4
max_z = cfg.max_dist - cfg.min_dist
min_levels = 1
max_levels = 8

# Range for Z
result = re.search('(\d+)-(\d+)', args.z)
if (result):
    min_z = int(result.group(1))
    max_z = int(result.group(2))
    args.z = -1
    if (min_z > max_z):
        sys.exit('Minimum Z must be equal or less than maximum Z.')
    if (min_z < 4):
        sys.exit('Minimum Z must be equal or greater than 4.')
# Range for X
result = re.search('(\d+)-(\d+)', args.x)
if (result):
    min_x = int(result.group(1))
    max_x = int(result.group(2))
    args.x = -1
    if (min_x > max_x):
        sys.exit('Minimum X must be equal or less than maximum X.')
    if (min_x < 4):
        sys.exit('Minimum X must be equal or greater than 4.')
# Range for Levels
result = re.search('(\d+)-(\d+)', args.levels)
if (result):
    min_levels = int(result.group(1))
    max_levels = int(result.group(2))
    args.levels = -1
    if (min_levels > max_levels):
        sys.exit('Minimum levels must be equal or less than maximum levels.')
    if (min_levels < 1):
        sys.exit('Minimum levels must be equal or greater than 1.')
    if (max_levels > 18):
        sys.exit('Maximum levels must be equal or less than 18.')

try:
    args.z = int(args.z)
except ValueError:
    sys.exit('Z doesn\'t appear to be an integer!')
try:
    args.x = int(args.x)
except ValueError:
    sys.exit('X doesn\'t appear to be an integer!')
try:
    args.levels = int(args.levels)
except ValueError:
    sys.exit('Levels doesn\'t appear to be an integer!')

if (args.z < 4 and args.z >= 0):
    sys.exit('Too few rooms in Z direction. (%d) Try >= 4.'%(args.z))
if (args.x < 4 and args.x >= 0):
    sys.exit('Too few rooms in X direction. (%d) Try >= 4.'%(args.x))
if (args.levels == 0 or args.levels > 18):
    sys.exit('Invalid number of levels. (%d) Try between 1 and 18.'%(args.levels))

if (args.offset is not None):
    cfg.offset = '%d, %d, %d' % (args.offset[0],
                                 args.offset[1],
                                 args.offset[2])

if (args.entrance is not None and (
    args.entrance[0] >= args.z or
    args.entrance[0] < 0 or
    args.entrance[1] >= args.x or
    args.entrance[1] < 0)):
    print 'Entrance offset values out of range.'
    print 'These should be >= 0 and < the maximum width or length of the dungeon.'
    sys.exit(1)

# Some options don't work with multidungeons
if (args.number is not 1):
    if (args.offset is not None):
        print 'WARN: Offset option is ignored when generating multiple dungeons.'
        cfg.offset = None
    if (args.entrance is not None):
        print 'WARN: Entrance option is ignored when generating multiple dungeons.'
        cfg.entrance = None
    if  (args.html is not None):
        print 'WARN: HTML option is ignored when generating multiple dungeons.'
        args.html = None
    if  (args.seed is not None):
        print 'WARN: Seed option is ignored when generating multiple dungeons.'
        args.seed = None


# Attempt to open the world. Look in cwd first, then try to search the user's
# save directory. 
try:
    print "Trying to open:", args.world
    world = mclevel.fromFile(args.world)
except:
    saveFileDir = mclevel.saveFileDir
    args.world = os.path.join(saveFileDir, args.world)
    print "Trying to open:", args.world
    try:
        world = mclevel.fromFile(args.world)
    except:
        print "Failed to open world:",args.world
        sys.exit(1)
print 'Loaded world: %s (%d chunks)' % (args.world, world.chunkCount)

#dumpEnts(world)
#sys.exit()

print "MCDungeon",__version__,"startup complete. "

depths = {}
dungeons = []
dungeon_positions = {}
total_rooms = 0

while args.number is not 0:

    # Define our dungeon.
    x = args.x
    z = args.z
    levels = args.levels
    if (args.z < 0):
        z = randint(min_z, max_z)
    if (args.x < 0):
        x = randint(min_x, max_x)
    if (args.levels < 0):
        levels = randint(min_levels, max_levels)

    dungeon = None
    located = False

    if (cfg.offset is not None and cfg.offset is not ''):
        pos = str2Vec(cfg.offset)
        pos.x = pos.x &~15
        pos.z = pos.z &~15
        dungeon = Dungeon(x, z, levels, depths)
        print 'Dungeon size: %d x %d x %d' % (z, x, levels)
        if (args.bury is False):
            dungeon.position = pos
            print "location set to", dungeon.position
            located = True
        else:
            located = dungeon.bury(world,
                                   {Vec(pos.x>>4,
                                        0,
                                        pos.z>>4): True},
                                  dungeon_positions)
            if (located == False):
                print 'Unable to bury a dungeon of requested depth at', pos
                print 'Try fewer levels, or a smaller size.'
                sys.exit(1)

    else:
        print "Searching for a suitable location..."
        while (located is False):
            dungeon = Dungeon(x, z, levels, depths)
            print 'Dungeon size: %d x %d x %d' % (z, x, levels)
            located = dungeon.findlocation(world, dungeon_positions)
            if (located is False):
                adjusted = False
                if (args.x < 0 and x > min_x):
                    x -= 1
                    adjusted = True
                if (args.z < 0 and z > min_z):
                    z -= 1
                    adjusted = True
                if (adjusted is False and
                    args.levels < 0 and
                    levels > min_levels):
                    levels -= 1
                    adjusted = True
                if (adjusted is False):
                    print 'Unable to place any more dungeons.'
                    break
    if (located is True):
        if (args.seed is not None):
            seed(args.seed)
            print 'Seed:',args.seed

        print "Generating rooms..."
        dungeon.genrooms(args.entrance)

        print "Generating halls..."
        dungeon.genhalls()

        print "Generating floors..."
        dungeon.genfloors()

        print "Generating features..."
        dungeon.genfeatures()

        print "Generating ruins..."
        dungeon.genruins(world)

        print "Extending the entrance to the surface..."
        dungeon.setentrance(world)

        print "Rendering rooms..."
        dungeon.renderrooms()

        print "Rendering halls..."
        dungeon.renderhalls()

        print "Rendering floors..."
        dungeon.renderfloors()

        print "Rendering features..."
        dungeon.renderfeatures()

        print "Rendering ruins..."
        dungeon.renderruins()

        print "Placing doors..."
        dungeon.placedoors(cfg.doors)

        print "Placing portcullises..."
        dungeon.placeportcullises(cfg.portcullises)

        print "Placing torches..."
        dungeon.placetorches()

        print "Placing chests..."
        dungeon.placechests()

        print "Placing spawners..."
        dungeon.placespawners()

        # Write the changes to the world.
        print "Writing blocks..."
        dungeon.applychanges(world)

        # Output an html version.
        if (args.html is not None):
            dungeon.outputhtml(args.html, args.force)

        # Output a slice of the dungeon to the terminal if requested.
        if (args.term is not None):
            dungeon.outputterminal(args.term)

        start = dungeon.position
        end = Vec(start.x + dungeon.xsize * dungeon.room_size - 1,
          start.y - dungeon.levels * dungeon.room_height + 1,
          start.z - dungeon.zsize * dungeon.room_size + 1)
        dungeon_positions[Vec(start.x>>4,
                             0,
                             start.z>>4)] = start
        dungeons.append('Dungeon %d (%d x %d x %d): %s to %s' %
                        (len(dungeons)+1,
                         z,
                         x,
                         levels,
                         start.__str__(),
                         end.__str__()))
        total_rooms += (x * z * levels)

    args.number -= 1
    if (located is False):
        args.number = 0

if (len(dungeons) == 0):
    print 'No dungeons were generated!'
    print 'You may have requested too deep or too large a dungeon, or'
    print 'your allowed spawn region is too small.'
    print 'Check your settings in the config file.'
    sys.exit(1)

# Relight
if (args.write is True and args.skiprelight is False):
    print "Relighting chunks..."
    logging.getLogger().level = logging.INFO
    world.generateLights()

print 'Placed', len(dungeons), 'dungeons!'
for d in dungeons:
    print d
print 'Total rooms:', total_rooms

# Save the world.
if (args.write is True):
    print "Saving..."
    world.saveInPlace()
else:
    print "Map NOT saved! This was a dry run. Use --write to enable saving."

print 'Done!                   '

