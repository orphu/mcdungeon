#!/usr/bin/python

import sys
import argparse

__version__ = '0.0.2'
__version_info__ = tuple([ int(num) for num in __version__.split('.')])
_vstring = '%%(prog)s %s' % (__version__)

parser = argparse.ArgumentParser(
    description='Generate a tile-based dungeon in a Minecraft map.')
parser.add_argument('--version', action='version', version=_vstring, 
                    help='Print version and exit')
parser.add_argument('z',
                    type=int,
                    help='Number of rooms West -> East')
parser.add_argument('x',
                    type=int,
                    help='Number of rooms North -> South')
parser.add_argument('levels',
                    type=int,
                    help='Number of levels')
parser.add_argument('--config',
                    dest='config',
                    metavar='CFGFILE',
                    default='mcdungeon.cfg',
                    help='Alternate config file. Default: mcdungeon.cfg')
parser.add_argument('--write',
                    action='store_true',
                    dest='write' ,
                    help='Write the dungeon to disk')
parser.add_argument('--skip-relight',
                    action='store_true',
                    dest='skiprelight',
                    help='Skip relighting the level')
parser.add_argument('-t','--term',
                    type=int,dest='term',
                    metavar='FLOOR',
                    help='Print a text version of a given floor to the \
                    terminal')
parser.add_argument('--html',
                    dest='html',
                    metavar='BASENAME',
                    help='Output html versions of the dungeon. This \
                    produces one file per level of the form \
                    BASENAME-(level number).html')
parser.add_argument('--force',
                    action='store_true',
                    dest='force',
                    help='Force overwriting of html output files')
parser.add_argument('-s', '--seed',
                    dest='seed',
                    metavar='SEED',
                    help='Provide a seed for this dungeon. This can be \
                    anything')
parser.add_argument('-o', '--offset',
                    dest='offset',
                    nargs=3,
                    type=int,
                    metavar='x y z',
                    help='Provide a location offset. (overrides .cfg file)')
parser.add_argument('-w', '--world',
                    dest='world',
                    metavar='SAVEDIR',
                    required=True,
                    help='Target world (path to save directory)')
args = parser.parse_args()

import cfg
import loottable
from dungeon import *
from utils import *
from pymclevel import mclevel, nbt

# Load configs
cfg.Load(args.config)
loottable.Load()

# Random level sizes
if (args.z < 0):
    args.z = randint(2, cfg.max_dist - cfg.min_dist)
if (args.x < 0):
    args.x = randint(2, cfg.max_dist - cfg.min_dist)
if (args.levels < 0):
    args.levels = randint(2, 8)

# Do some initial error checking
if (args.z < 2):
    sys.exit('Too few rooms in Z direction. Try >= 2.')
if (args.x < 2):
    sys.exit('Too few rooms in X direction. Try >= 2.')
if (args.levels < 1 or args.levels > 18):
    sys.exit('Invalid number of levels.')

print 'Dungeon size: %d x %d x %d' % (args.z, args.x, args.levels)

if (args.seed is not None):
    seed(args.seed)
    print 'Seed:',args.seed

if (args.offset is not None):
    cfg.offset = '%d, %d, %d' % (args.offset[0],
                                 args.offset[1],
                                 args.offset[2])

# Attempt to open the world.
try:
    world = mclevel.fromFile(args.world)
except:
    print "Failed to open world:",args.world
    sys.exit(1)
print 'Loaded world: %s (%d chunks)' % (args.world, world.chunkCount)

#dumpEnts(world)
#sys.exit()

print "Startup compete. "

# Define our dungeon.
dungeon = Dungeon(args.x, args.z, args.levels)

try:
    dungeon.position = str2Vec(cfg.offset)
    print "location set to",cfg.offset
except:
    print "Searching for a good location..."
    dungeon.findlocation(world)

print "Generating rooms..."
dungeon.genrooms()

print "Generating halls..."
dungeon.genhalls()

print "Generating floors..."
dungeon.genfloors()

print "Generating features..."
dungeon.genfeatures()

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

# Output a slice of the dungoen to the terminal if requested.
if (args.term is not None):
    dungeon.outputterminal(args.term)

# Output an html version.
if (args.html is not None):
    dungeon.outputhtml(args.html, args.force)

# Write the changes to teh world.
if (args.write):
    print "Writing blocks..."
    dungeon.applychanges(world)
    if (args.skiprelight is False):
        print "Relighting chunks..."
        world.generateLights()

# Save the world.
if (args.write):
    print "Saving..."
    world.saveInPlace()

print "Done!                   "
