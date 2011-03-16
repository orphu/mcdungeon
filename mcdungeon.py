#!/usr/bin/python

import sys
import argparse

import cfg
import loottable
from dungeon import *
from utils import *
from pymclevel import mclevel, nbt

parser = argparse.ArgumentParser(
    description='Generate some DungeonQuest-like dungeons in a Minecraft map.')
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
parser.add_argument('--term',
                    type=int,dest='term',
                    metavar='FLOOR',
                    help='Print a text version of a given floor to the \
                    terminal')
parser.add_argument('--html',
                    type=int,dest='html',
                    metavar='FLOOR',
                    help='Print an html version of a given floor to the \
                    terminal')
parser.add_argument('--seed',
                    dest='seed',
                    metavar='SEED',
                    help='Provide a seed for this dungeon. This can be \
                    anything.')
parser.add_argument('--world',
                    dest='world',
                    metavar='SAVEDIR',
                    required=True,
                    help='Target world (path to save directory)')
args = parser.parse_args()

# Do some initial error checking
if (args.z < 2):
    sys.exit('Too few rooms in Z direction. Try >= 2.')
if (args.x < 2):
    sys.exit('Too few rooms in X direction. Try >= 2.')
if (args.levels < 1 or args.levels > 18):
    sys.exit('Invalid number of levels.')

if (args.seed is not None):
    seed(args.seed)

# Load configs
cfg.Load(args.config)
loottable.Load()

# Attempt to open the world.
try:
    world = mclevel.fromFile(args.world)
except:
    print "Failed to open world:",args.world
    sys.exit(1)
print 'Loaded world: %s (%d chunks)' % (args.world, world.chunkCount)

print "Startup compete. "

# Define our dungeon.
dungeon = Dungeon(cfg.offset, args.x, args.z, args.levels)

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
dungeon.placetorches(cfg.torches)

print "Placing chests..."
dungeon.placechests()

# Output a slice of the dungoen to the terminal if requested.
if (args.term is not None):
    dungeon.outputterminal(args.term)

# Output an html version.
if (args.html is not None):
    dungeon.outputhtml(args.html)

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
