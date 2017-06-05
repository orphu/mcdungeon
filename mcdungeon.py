#!/usr/bin/env python

import argparse
import copy
import logging
import numpy
import os
import platform
import re
import sys
import time
import traceback

if platform.system() != 'Windows':
    import concurrent.futures as cf

# Version info
__version__ = '0.18.0'
__version_info__ = tuple([num for num in __version__.split('.')])
_vstring = '%%(prog)s %s' % (__version__)

# Globals
world = None
cache_path = None


def parseArgs():
    # Argument parsers
    parser = argparse.ArgumentParser(
        description='Generate a tile-based dungeon in a Minecraft map.')
    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version=_vstring,
                        help='Print version and exit')
    parser.add_argument('-q',
                        '--quiet',
                        action='store_true',
                        dest='quiet',
                        help='Suppress progress messages')
    subparsers = parser.add_subparsers(
        description='See "COMMAND --help" for additional help.',
        title='Available commands')

    # Interactive subcommand parser
    parser_inter = subparsers.add_parser('interactive',
                                         help='Interactive mode.')
    parser_inter.set_defaults(command='interactive')
    parser_inter.add_argument('--skip-relight',
                              action='store_true',
                              dest='skiprelight',
                              help='Skip relighting the level')
    parser_inter.add_argument('-t',
                              '--term',
                              type=int,
                              dest='term',
                              metavar='FLOOR',
                              help='Print a text version of a given floor to the \
                              terminal')
    parser_inter.add_argument('--html',
                              dest='html',
                              metavar='HTMLPATH',
                              help='Output html versions of the dungeon to the \
                              specified path. You can optionally include the keyword \
                              __DUNGEON__ which will be replaced with the dungeon \
                              name.')
    parser_inter.add_argument('--debug',
                              action='store_true',
                              dest='debug',
                              help='Provide additional debug info')
    parser_inter.add_argument('--force',
                              action='store_true',
                              dest='force',
                              help='Force overwriting of html output files')
    parser_inter.add_argument('-s', '--seed',
                              dest='seed',
                              metavar='SEED',
                              help='Provide a seed for this dungeon. This can be \
                              anything')
    parser_inter.add_argument('-o', '--offset',
                              dest='offset',
                              nargs=3,
                              type=int,
                              metavar=('X', 'Y', 'Z'),
                              help='Provide a location offset in blocks')
    parser_inter.add_argument('--force-bury',
                              action='store_true',
                              dest='bury',
                              help='Attempt to calculate Y when using --offset')
    parser_inter.add_argument('-e', '--entrance',
                              dest='entrance',
                              nargs=2,
                              type=int,
                              metavar=('X', 'Z'),
                              help='Provide an offset for the entrance in chunks')
    parser_inter.add_argument('--spawn',
                              dest='spawn',
                              nargs=2,
                              type=int,
                              metavar=('X', 'Z'),
                              help='Override spawn point')
    parser_inter.add_argument('--dir',
                              dest='dir',
                              metavar='SAVEDIR',
                              help='Override the default map directory.')
    parser_inter.add_argument('--mapstore',
                              dest='mapstore',
                              metavar='PATH',
                              help='Provide an alternate world to store maps.')
    parser_inter.add_argument('--outputdir',
                            dest='outputdir',
                            metavar='PATH',
                            help='Give the location for the OverViewer output path.')
    parser_inter.add_argument('--regionfile',
                            dest='regionfile',
                            metavar='PATH',
                            help='Give the location for the regions.yml output path.\
                            This is usually located in plugins/WorldGuard/worlds/<name>/regions.yml \
                            Make sure you take a backup of this file first!')
    parser_inter.add_argument('--workers',
                              dest='workers',
                              type=int,
                              metavar='WORKERS',
                              help='Number of child processes to use for the \
                              worker pool. Defaults to the number of reported \
                              cores on your machine.')

    # AddTH subcommand parser
    parser_addth = subparsers.add_parser('addth', help='Add new treasure hunts.')
    parser_addth.set_defaults(command='addth')
    parser_addth.add_argument('world',
                            metavar='SAVEDIR',
                            help='Target world (path to save directory)')
    parser_addth.add_argument('distance',
                            help='Number of chunks per step, or provide a \
                            range.')
    parser_addth.add_argument('steps',
                            metavar='STEPS',
                            help='Number of steps. Enter a positive value, or \
                            provide a range.')
    parser_addth.add_argument('-c', '--config',
                            dest='config',
                            metavar='CFGFILE',
                            default='default.cfg',
                            help='Alternate config file. Default: default.cfg')
    parser_addth.add_argument('--write',
                            action='store_true',
                            dest='write',
                            help='Write the treasure hunt to disk')
    parser_addth.add_argument('--skip-relight',
                              action='store_true',
                              dest='skiprelight',
                              help='Skip relighting the level')
    parser_addth.add_argument('--debug',
                            action='store_true',
                            dest='debug',
                            help='Provide additional debug info')
    parser_addth.add_argument('-s', '--seed',
                            dest='seed',
                            metavar='SEED',
                            help='Provide a seed for this treasure hunt. This can be \
                            anything')
    parser_addth.add_argument('-o', '--offset',
                            dest='offset',
                            nargs=3,
                            type=int,
                            metavar=('X', 'Y', 'Z'),
                            help='Provide a location offset in blocks for start')
    parser_addth.add_argument('--spawn',
                            dest='spawn',
                            nargs=2,
                            type=int,
                            metavar=('X', 'Z'),
                            help='Override spawn point')
    parser_addth.add_argument('-n',
                            '--number',
                            type=int,
                            dest='number',
                            metavar='NUM',
                            default=1,
                            help='Number of treasure hunts to generate. -1 will \
                            create as many as possible given X, Z, and STEPS \
                            settings.')
    parser_addth.add_argument('--mapstore',
                            dest='mapstore',
                            metavar='PATH',
                            help='Provide an alternate world to store maps.')
    parser_addth.add_argument('--workers',
                              dest='workers',
                              type=int,
                              metavar='WORKERS',
                              help='Number of child processes to use for the \
                              worker pool. Defaults to the number of reported \
                              cores on your machine.')

    # Add subcommand parser
    parser_add = subparsers.add_parser('add', help='Add new dungeons.')
    parser_add.set_defaults(command='add')
    parser_add.add_argument('world',
                            metavar='SAVEDIR',
                            help='Target world (path to save directory)')
    parser_add.add_argument('x',
                            metavar='X',
                            help='Number of rooms West -> East, or provide a \
                            range.')
    parser_add.add_argument('z',
                            metavar='Z',
                            help='Number of rooms North -> South, or provide a \
                            range. (ie: 4-7)')
    parser_add.add_argument('levels',
                            metavar='LEVELS',
                            help='Number of levels. Enter a positive value, or \
                            provide a range.')
    parser_add.add_argument('-c', '--config',
                            dest='config',
                            metavar='CFGFILE',
                            default='default.cfg',
                            help='Alternate config file. Default: default.cfg')
    parser_add.add_argument('--write',
                            action='store_true',
                            dest='write',
                            help='Write the dungeon to disk')
    parser_add.add_argument('--skip-relight',
                            action='store_true',
                            dest='skiprelight',
                            help='Skip relighting the level')
    parser_add.add_argument('-t',
                            '--term',
                            type=int,
                            dest='term',
                            metavar='FLOOR',
                            help='Print a text version of a given floor to the \
                            terminal')
    parser_add.add_argument('--html',
                            dest='html',
                            metavar='HTMLPATH',
                            help='Output html versions of the dungeon to the \
                            specified path. You can optionally include the keyword \
                            __DUNGEON__ which will be replaced with the dungeon \
                            name.')
    parser_add.add_argument('--debug',
                            action='store_true',
                            dest='debug',
                            help='Provide additional debug info')
    parser_add.add_argument('--force',
                            action='store_true',
                            dest='force',
                            help='Force overwriting of html output files')
    parser_add.add_argument('-s', '--seed',
                            dest='seed',
                            metavar='SEED',
                            help='Provide a seed for this dungeon. This can be \
                            anything')
    parser_add.add_argument('-o', '--offset',
                            dest='offset',
                            nargs=3,
                            type=int,
                            metavar=('X', 'Y', 'Z'),
                            help='Provide a location offset in blocks')
    parser_add.add_argument('--force-bury',
                            action='store_true',
                            dest='bury',
                            help='Attempt to calculate Y when using --offset')
    parser_add.add_argument('-e', '--entrance',
                            dest='entrance',
                            nargs=2,
                            type=int,
                            metavar=('X', 'Z'),
                            help='Provide an offset for the entrance in chunks')
    parser_add.add_argument('--spawn',
                            dest='spawn',
                            nargs=2,
                            type=int,
                            metavar=('X', 'Z'),
                            help='Override spawn point')
    parser_add.add_argument('-n',
                            '--number',
                            type=int,
                            dest='number',
                            metavar='NUM',
                            default=1,
                            help='Number of dungeons to generate. -1 will \
                            create as many as possible given X, Z, and LEVEL \
                            settings.')
    parser_add.add_argument('--mapstore',
                            dest='mapstore',
                            metavar='PATH',
                            help='Provide an alternate world to store maps.')
    parser_add.add_argument('--workers',
                              dest='workers',
                              type=int,
                              metavar='WORKERS',
                              help='Number of child processes to use for the \
                              worker pool. Defaults to the number of reported \
                              cores on your machine.')

    # List subcommand parser
    parser_list = subparsers.add_parser('list',
                                        help='List known dungeons in a map.')
    parser_list.set_defaults(command='list')
    parser_list.add_argument('world',
                            metavar='SAVEDIR',
                            help='Target world (path to save directory)')
    parser_list.add_argument('--debug',
                              action='store_true',
                              dest='debug',
                              help='Provide additional debug info')
    parser_list.add_argument('--workers',
                              dest='workers',
                              type=int,
                              metavar='WORKERS',
                              help='Number of child processes to use for the \
                              worker pool. Defaults to the number of reported \
                              cores on your machine.')

    # GenPOI subcommand parser
    parser_genpoi = subparsers.add_parser('genpoi',
                            help='Create OverViewer POI configuration for known dungeons in a map.')
    parser_genpoi.set_defaults(command='genpoi')
    parser_genpoi.add_argument('--debug',
                              action='store_true',
                              dest='debug',
                              help='Provide additional debug info')
    parser_genpoi.add_argument('world',
                            metavar='SAVEDIR',
                            help='Target world (path to save directory)')
    parser_genpoi.add_argument('--outputdir',
                            dest='outputdir',
                            metavar='PATH',
                            help='Give the location for the OverViewer output path.')
    parser_genpoi.add_argument('--workers',
                              dest='workers',
                              type=int,
                              metavar='WORKERS',
                              help='Number of child processes to use for the \
                              worker pool. Defaults to the number of reported \
                              cores on your machine.')

    # GenRegions subcommand parser
    parser_genreg = subparsers.add_parser('genregions',
                            help='Create WorldGuard regions.yml definitions for known dungeons in a map.')
    parser_genreg.set_defaults(command='genreg')
    parser_genreg.add_argument('--debug',
                              action='store_true',
                              dest='debug',
                              help='Provide additional debug info')
    parser_genreg.add_argument('world',
                            metavar='SAVEDIR',
                            help='Target world (path to world directory)')
    parser_genreg.add_argument('--regionfile',
                            dest='regionfile',
                            metavar='PATH',
                            help='Give the location for the regions.yml output path.\
                            This is usually located in plugins/WorldGuard/worlds/<name>/regions.yml \
                            Make sure you take a backup of this file first!')
    parser_genreg.add_argument('--workers',
                              dest='workers',
                              type=int,
                              metavar='WORKERS',
                              help='Number of child processes to use for the \
                              worker pool. Defaults to the number of reported \
                              cores on your machine.')

    # Delete subcommand parser
    parser_del = subparsers.add_parser('delete',
                                       help='Delete dungeons from a map.')
    parser_del.set_defaults(command='delete')
    parser_del.add_argument('--debug',
                              action='store_true',
                              dest='debug',
                              help='Provide additional debug info')
    parser_del.add_argument('world',
                            metavar='SAVEDIR',
                            help='Target world (path to save directory)')
    parser_del.add_argument('-d', '--dungeon',
                            metavar=('X', 'Z'),
                            nargs=2,
                            action='append',
                            dest='dungeons',
                            type=int,
                            help='The X Z coordinates of a dungeon or treasure \
                            hunt to delete. \
                            NOTE: These will be rounded to the nearest chunk. \
                            Multiple -d flags can be specified.')
    parser_del.add_argument('-a', '--all',
                            dest='all',
                            action='store_true',
                            help='Delete all known dungeons. Overrides -d.')
    parser_del.add_argument('--mapstore',
                            dest='mapstore',
                            metavar='PATH',
                            help='Provide an alternate world to store maps.')
    parser_del.add_argument('--workers',
                              dest='workers',
                              type=int,
                              metavar='WORKERS',
                              help='Number of child processes to use for the \
                              worker pool. Defaults to the number of reported \
                              cores on your machine.')

    # Regnerate subcommand parser
    parser_regen = subparsers.add_parser('regenerate',
                                         help='Regenerate dungeons in a map.')
    parser_regen.set_defaults(command='regenerate')
    parser_regen.add_argument('world',
                              metavar='SAVEDIR',
                              help='Target world (path to save directory)')
    parser_regen.add_argument('-d', '--dungeon',
                              metavar=('X', 'Z'),
                              nargs=2,
                              action='append',
                              dest='dungeons',
                              type=int,
                              help='The X Z coordinates of a dungeon to \
                              regenerate. NOTE: These will be rounded to the \
                              nearest chunk. Multiple -d flags can be \
                              specified.')
    parser_regen.add_argument('-c', '--config',
                              dest='config',
                              metavar='CFGFILE',
                              default='default.cfg',
                              help='Alternate config file. Default: default.cfg')
    parser_regen.add_argument('--debug',
                              action='store_true',
                              dest='debug',
                              help='Provide additional debug info')
    parser_regen.add_argument('--html',
                              dest='html',
                              metavar='HTMLPATH',
                              help='Output html versions of the dungeon to the \
                              specified path. You can optionally include the keyword \
                              __DUNGEON__ which will be replaced with the dungeon \
                              name.')
    parser_regen.add_argument('--force',
                              action='store_true',
                              dest='force',
                              help='Force overwriting of html output files')
    parser_regen.add_argument('-t',
                              '--term',
                              type=int,
                              dest='term',
                              metavar='FLOOR',
                              help='Print a text version of a given floor to the \
                              terminal')
    parser_regen.add_argument('--skip-relight',
                              action='store_true',
                              dest='skiprelight',
                              help='Skip relighting the level')
    parser_regen.add_argument('--mapstore',
                              dest='mapstore',
                              metavar='PATH',
                              help='Provide an alternate world to store maps.')
    parser_regen.add_argument('-a', '--all',
                              dest='all',
                              action='store_true',
                              help='Regenerate all known dungeons. Overrides -d.')
    parser_regen.add_argument('--workers',
                              dest='workers',
                              type=int,
                              metavar='WORKERS',
                              help='Number of child processes to use for the \
                              worker pool. Defaults to the number of reported \
                              cores on your machine.')


    # Parse the args
    args = parser.parse_args()

    # On Windows, we can't yet use multiprocessing.
    if platform.system() == 'Windows':
        args.workers = 0

    return args


def loadWorld(world_name):
    '''Attempt to load a world file. Look in the literal path first, then look
    in the typical save directory for the given platform. Check to see if the
    mcdungeon cache directory exists, and create it if not.'''
    # Attempt to open the world. Look in cwd first, then try to search the
    # user's save directory.
    global cfg
    global cache_path

    world = None
    clean_name = world_name.encode('utf-8').strip()
    try:
        if args.quiet is False:
            print "Trying to open:", clean_name
        world = mclevel.fromFile(world_name)
    except:
        saveFileDir = mclevel.saveFileDir
        world_name = os.path.join(saveFileDir, world_name)
        if args.quiet is False:
            print "Trying to open:", clean_name
        try:
            world = mclevel.fromFile(world_name)
        except:
            print "Failed to open world:", clean_name
            sys.exit(1)
    if args.quiet is False:
        print 'Loaded world: %s (%d chunks, %d blocks high)' % (
            clean_name,
            world.chunkCount,
            world.Height
            )
    # Create the mcdungeon cache dir if needed.
    cache_path = os.path.join(world_name, cfg.cache_dir)
    if os.path.exists(cache_path) is False:
        os.makedirs(cache_path)

    # Find the mapstore path
    if args.quiet is False:
        print 'Looking for data directory...'
    if not os.path.exists(os.path.join(cfg.mapstore, 'data')):
        cfg.mapstore = os.path.join(mclevel.saveFileDir, cfg.mapstore)
        if args.quiet is False:
            print 'Looking for data directory...'
        if not os.path.exists(os.path.join(cfg.mapstore, 'data')):
            print "Cannot find world data directory!"
            sys.exit(1)

    return world


def classifyChunk(c):
    cx = c[0]
    cz = c[1]

    # Load the chunk
    chunk = world.getChunk(cx, cz)

    # Incomplete chunk
    # These keys may be optional in older MC versions.
    if (
        cfg.use_incomplete_chunks != True and
        'LightPopulated' in chunk.root_tag['Level'] and
        'TerrainPopulated' in chunk.root_tag['Level']
    ):
        if (
            chunk.root_tag['Level']['LightPopulated'].value == 0 or
            chunk.root_tag['Level']['TerrainPopulated'].value == 0
        ):
            return cx, cz, 'I', None, 0

    # Biomes
    biomes = chunk.Biomes.flatten()
    biome_type = numpy.argmax(numpy.bincount(biomes))

    # Exclude chunks that are 20% river.
    for river_biome in cfg.river_biomes:
        if (biomes == river_biome).sum() > 50:
            return cx, cz, 'R', river_biome, 0

    # Exclude Oceans
    if biome_type in cfg.ocean_biomes:
        return cx, cz, 'O', biome_type, 0

    # Structures
    if (len(cfg.structure_values) > 0):
        mats = cfg.structure_values
        t = False
        i = 0
        while (t == False and i < len(mats)):
            x = (chunk.Blocks[:] == mats[i])
            t = x.any()
            i += 1
        if t:
            return cx, cz, 'S', biome_type, 0

    # Depths
    min_depth = world.Height
    max_depth = 0
    for x in xrange(16):
        for z in xrange(16):
            y = chunk.HeightMap[x, z] - 1
            while (y > 0 and
                   chunk.Blocks[x, z, y] not in
                   materials.heightmap_solids):
                y = y - 1
            min_depth = min(y, min_depth)
            max_depth = max(y, max_depth)

    # Surface too close to the max height
    if max_depth > world.Height - 27:
        return cx, cz, 'H', biome_type, min_depth

    # Surface too close to the bottom of the world
    if min_depth < 12:
        return cx, cz, 'L', biome_type, min_depth

    # Chunk is good
    return cx, cz, 'G', biome_type, min_depth


def checkDInfo(c):
    cx = c[0]
    cz = c[1]
    key = '%s,%s' % (cx * 16, cz * 16)
    for tileEntity in world.getChunk(cx, cz).TileEntities:
        if (
            tileEntity['id'].value == 'Sign' and
            '[MCD]' in tileEntity['Text1'].value
        ):
            key = '%s,%s' % (
                tileEntity["x"].value,
                tileEntity["z"].value
            )
            return key, 'dungeon', tileEntity
        if (
            (tileEntity['id'].value == 'Chest' or tileEntity['id'].value == 'minecraft:chest') and
            'CustomName' in tileEntity and
            tileEntity['CustomName'].value == 'MCDungeon Data Library'
        ):
            key = '%s,%s' % (
                tileEntity["x"].value,
                tileEntity["z"].value
            )
            return key, 'dungeon', tileEntity
        if (
            (tileEntity['id'].value == 'Chest' or tileEntity['id'].value == 'minecraft:chest') and
            'CustomName' in tileEntity and
            tileEntity['CustomName'].value == 'MCDungeon THunt Data Library'
        ):
            key = '%s,%s' % (
                tileEntity["x"].value,
                tileEntity["z"].value
            )
            return key, 'thunt', tileEntity

    return key, None, None


def loadCaches(expand_fill_caves=False, genpoi=False):
    '''Scan a world for dungeons and treasure hunts. Try to cache
    the results and only look at chunks that have changed since the
    last run.'''

    global world
    global cache_path
    pm = pmeter.ProgressMeter()

    # Try to load the dungeon cache
    dungeonCacheOld, mtime = utils.loadDungeonCache(cache_path)
    dungeonCache = {}

    # Try to load the treasure hunt cache
    tHuntCacheOld, mtime = utils.loadTHuntCache(cache_path)
    tHuntCache = {}

    count = world.chunkCount

    # Pass 1 will prefilter the chunks for ones that might be interesting.
    if genpoi is False:
        print 'Scanning world for existing dungeons and treasure hunts:'
        pm.init(count, label='Pass 1:')

    chunks = set()
    for c in world.allChunks:
        cx = c[0]
        cz = c[1]
        key = '%s,%s' % (cx * 16, cz * 16)
        cmtime = world.worldFolder.getRegionForChunk(cx, cz).getTimestamp(cx, cz)
        if (cmtime > mtime or key in dungeonCacheOld or key in tHuntCacheOld):
            chunks.add(c)
        count -= 1
        if genpoi is False and count%200 == 0:
            pm.update_left(count)

    # Pass 2 will evaluate the interesting chunks.
    count = world.chunkCount
    if genpoi is False:
        pm.set_complete()
        pm.init(count, label='Pass 2:')

    # Handle this in the main thread if we aren't multiprocessing.
    if args.workers is not None and args.workers < 2:
        if args.debug:
            print 'Working with a single process.'
        for c in chunks:
            (key, d_type, entity) = checkDInfo(c)
            if entity:
                if d_type == 'dungeon':
                    dungeonCache[key] = entity
                else:
                    tHuntCache[key] = entity

            count -= 1
            if genpoi is False and count%200 == 0:
                pm.update_left(count)
    # Process chunks in parallel.
    else:
        if args.debug:
            print 'Working with multiple processes. workers =', args.workers
        with cf.ProcessPoolExecutor(max_workers = args.workers) as executor:
            chunk_scans = {executor.submit(checkDInfo, c): c for c in chunks}
            for future in cf.as_completed(chunk_scans):
                (key, d_type, entity) = future.result()
                if entity:
                    if d_type == 'dungeon':
                        dungeonCache[key] = entity
                    else:
                        tHuntCache[key] = entity

                count -= 1
                if genpoi is False and count%200 == 0:
                    pm.update_left(count)

    if genpoi is False:
        pm.set_complete()

    # Save the caches
    utils.saveDungeonCache(cache_path, dungeonCache)
    utils.saveTHuntCache(cache_path, tHuntCache)

    output = ''
    poiOutput = ''

    # Process the dungeons
    dungeons = []
    output += "Known dungeons on this map:\n"
    output += '+-----------+----------------+---------+-------+----+'\
              '-------------------------+\n'
    output += '| %9s | %14s | %7s | %5s | %2s | %23s |\n' % (
        'Pos',
        'Date/Time',
        'Ver',
        'Size',
        'Lv',
        'Name'
    )
    output += '+-----------+----------------+---------+-------+----+'\
              '-------------------------+\n'

    for tileEntity in dungeonCache.values():
        info = utils.decodeDungeonInfo(tileEntity)
        try:
            (major, minor, patch) = info['version'].split('.')
        except KeyError:
            print 'Strange Dungeon Info cache found?'
            continue
        version = float(major + '.' + minor)

        xsize = info['xsize']
        zsize = info['zsize']
        levels = info['levels']
        offset = 0

        if (
            expand_fill_caves is True and
            info['fill_caves'] is True
        ):
            offset = 5
        dungeons.append((info["position"].x - offset,
                         info["position"].z - offset,
                         xsize + offset,
                         zsize + offset,
                         info,
                         levels,
                         info["position"].x,
                         info["position"].y,
                         info["position"].z,
                         version))
        if  genpoi is True:
            # If we have a 'new' format, with a defined portal_exit,
            # then we use that.  Otherwise, identify the top of the
            # entrance stairway and use that instead.
            if ((info["portal_exit"] is None) or (info["portal_exit"].x==0 and info["portal_exit"].y==0 and info["portal_exit"].z==0)):
                # use <<4 instead of room_size because we can't get that
                px = info["position"].x + ( info["entrance_pos"].x << 4 ) + 8
                py = info["position"].y + info["entrance_height"]
                pz = info["position"].z + ( info["entrance_pos"].z << 4 ) + 8
            else:
                px = info["position"].x + info["portal_exit"].x
                py = info["position"].y - info["portal_exit"].y # reversed!
                pz = info["position"].z + info["portal_exit"].z
            # Output the POI format for OverViewer
            fn = info.get('full_name', 'Dungeon')
            fn = fn.replace("'","\\'")
            poiOutput += '\t\t{\'id\':\'MCDungeon\',\n\t\t\'x\':%d,\n\t\t\'y\':%d,\n\t\t\'z\':%d,\n\t\t\'name\':\'%s\',\n\t\t\'description\':\'%s\\n%d Levels, Size %dx%d\'},\n' % (
                px,py,pz,
                fn,
                fn,levels,xsize,zsize
            )
        else:
            output += '| %9s | %14s | %7s | %5s | %2d | %23s |\n' % (
				'%d %d' % (info["position"].x, info["position"].z),
				time.strftime('%x %H:%M', time.localtime(info['timestamp'])),
				info['version'],
				'%dx%d' % (xsize, zsize),
				levels,
				info.get('full_name', 'Dungeon')[:23]
            )

    if genpoi is False:
        output += '+-----------+----------------+---------+-------+----+'\
            '-------------------------+\n'

    # Process the treasure hunts
    tHunts = []
    output += '\n'
    if genpoi is False:
        output += "Known treasure hunts on this map:\n"
        output += '+-----------+----------------+---------+-------+----+'\
                  '-------------------------+\n'
        output += '| %9s | %14s | %7s | %5s | %2s | %23s |\n' % (
            'Pos',
            'Date/Time',
            'Ver',
            'Range',
            'St',
            'Name'
        )
        output += '+-----------+----------------+---------+-------+----+'\
                  '-------------------------+\n'

    for tileEntity in tHuntCache.values():
        info = utils.decodeTHuntInfo(tileEntity)
        try:
            (major, minor, patch) = info['version'].split('.')
        except KeyError:
            continue
        version = float(major + '.' + minor)

        try:
            minrange = info['min_distance']
            maxrange = info['max_distance']
        except KeyError:
            minrange = 1
            maxrange = 20

        steps = info['steps']
        offset = 0

        tHunts.append((
                         info["position"].x,
                         info["position"].z,
                         minrange,
                         maxrange,
                         info,
                         steps,
                         info["position"].x,
                         info["position"].y,
                         info["position"].z,
                         version))
        if genpoi is True :
            fn = info.get('full_name', 'Treasure Hunt')
            fn = fn.replace("'","\\'")
            poiOutput += '\t\t{\'id\':\'MCDungeonTH\',\n\t\t\'x\':%d,\n\t\t\'y\':%d,\n\t\t\'z\':%d,\n\t\t\'name\':"%s",\n\t\t\'description\':"%s\\n%d Steps, Range %d - %d"},\n' % (
                info["landmarks"][0].x+8,
                info["landmarks"][0].y,
                info["landmarks"][0].z+8,
                fn,
                fn, steps-1, minrange, maxrange
            )
            # Here, we should also iterate through the waypoints
            i = 0
            for l in info["landmarks"]:
                i = i + 1
                if i == 1:
                    continue
                if i == steps:
                    stepname = "Final location"
                else:
                    stepname = "Waypoint %d" % (i-1)
                poiOutput += '\t\t{\'id\':\'MCDungeonTHW\',\n\t\t\'x\':%d,\n\t\t\'y\':%d,\n\t\t\'z\':%d,\n\t\t\'name\':"%s (%s)",\n\t\t\'description\':"%s\\n%s\\n(%d steps)"},\n' % (
                    l.x+8,
                    l.y,
                    l.z+8,
                    fn, stepname,
                    fn, stepname, steps-1
                )
        else:
            output += '| %9s | %14s | %7s | %5s | %2d | %23s |\n' % (
                '%d %d' % (info["position"].x, info["position"].z),
                time.strftime('%x %H:%M', time.localtime(info['timestamp'])),
                info['version'],
                '%d-%d' % (minrange,maxrange),
                steps,
                info.get('full_name', 'Treasure')[:23]
            )

    if genpoi is False:
        output += '+-----------+----------------+---------+-------+----+'\
            '-------------------------+\n'

    if genpoi is True:
        print poiOutput
    elif len(tHunts) > 0 or len(dungeons) > 0:
        print output
    else:
        print 'No dungeons or treasure hunts found!'

    return dungeons, tHunts


def main():
    '''
    Main function.
    '''
    global world
    global cache_path
    dungeons = []
    tHunts = []
    dungeon_positions = {}
    total_rooms = 0
    chunk_cache = {}
    good_chunks = {}

    # Interactive mode
    if (args.command == 'interactive'):
        print 'Starting interactive mode!'

        # Pick a map
        if args.dir is not None:
            mclevel.saveFileDir = args.dir
        saveFileDir = mclevel.saveFileDir
        print '\nYour save directory is:\n', saveFileDir
        if (os.path.isdir(saveFileDir) is False):
            sys.exit('\nI cannot find your save directory! Aborting!')
        print '\nWorlds in your save directory:\n'
        count = 0
        worlds = []
        for file in os.listdir(saveFileDir):
            file_path = os.path.join(saveFileDir, file)
            if (
                os.path.isdir(file_path) and
                os.path.isfile(file_path + '/level.dat')
            ):
                print '\t[{}] {}'.format(count+1, file.encode('utf-8').strip())
                count += 1
                args.world = file_path
                worlds.append(file)
        if count == 0:
            sys.exit('There do not appear to be any worlds in your save direcory. \
                     Aborting!')
        if count > 1:
            w = -1
            while (w < 0 or w > len(worlds)-1):
                w = raw_input(
                    '\nEnter the number for the world you wish to modify: '
                    )
                try:
                    w = int(w)-1
                except:
                    w = -1
            args.world = os.path.join(saveFileDir, worlds[w])
        else:
            print '\nOnly one world available.'

        # Pick a mode
        print '\nChoose an action:\n-----------------\n'
        print '\t[a] Add new dungeon(s) to this map.'
        print '\t[t] Add new treasure hunt(s) to this map.'
        print '\t[l] List dungeons and treasure hunts already in this map.'
        print '\t[d] Delete dungeons or treasure hunts from this map.'
        print '\t[r] Regenerate a dungeon or treasure hunt in this map.'
        print '\t[p] Generate OverViewer POI file for dungeons and treasure hunts'
        print '\t    already in this map.'
        print '\t[w] Generate a WorldGuard regions file for dungeons already in'
        print '\t    this map.'
        command = raw_input('\nEnter choice or q to quit: ')

        if command == 'a':
            args.command = 'add'
            # Pick a config
            configDir = os.path.join(sys.path[0], 'configs')
            if (os.path.isdir(configDir) is False):
                configDir = 'configs'
            if (os.path.isdir(configDir) is False):
                sys.exit('\nI cannot find your configs directory! Aborting!')
            choices = ['default']
            for file in os.listdir(configDir):
                file_path = os.path.join(configDir, file)
                file = file.replace('.cfg', '')
                if (
                    os.path.isfile(file_path) and
                    file_path.endswith('.cfg') and
                    file != 'default'):
                    choices.append(file)
            print '\nConfigurations in your configs directory:\n'
            count = 1
            config = None
            for file in choices:
                    print '\t[{}] {}'.format(count, file)
                    count += 1
            while config is None:
                config = raw_input('\nChoose a config (enter for default): ')
                if config == '':
                    config = 'default'
                else:
                    if config in [str(x+1) for x in xrange(len(choices))]:
                        config = choices[int(config)-1]
                    else:
                        config = None
            args.config = str(config) + '.cfg'
            cfg.Load(args.config)

            # Prompt for a mapstore if we need to
            if (cfg.mapstore == '' and args.mapstore is None):
                print '\nSome configurations may generate dungeon maps. If you are'
                print 'using multiverse you need supply the name of your'
                print 'primary world for this to work. You can also provide this'
                print 'in the config file or as a command switch.'
                print '\n(if you don\'t use multiverse, just hit enter)'
                cfg.mapstore = raw_input('Name of primary multiverse world: ')

            # Prompt for max_dist
            print '\nEnter the maximum distance (in chunks) from spawn to place'
            print 'dungeons. Take care to pick a value that matches your needs.'
            print 'If this value is too high and you add few dungeons, they'
            print 'may be hard to find. If this value is too low and you'
            print 'add many dungeons, they will not cover much of the map.'
            input_max_dist = None
            while input_max_dist is None:
                input_max_dist = raw_input(
                    '\nMax Distance (leave blank for config value, ' +
                    str(cfg.max_dist) + '): '
                )
                if input_max_dist == '':
                    input_max_dist = cfg.max_dist
                else:
                    if input_max_dist.isdigit() and int(input_max_dist) >= 0:
                        input_max_dist = int(input_max_dist)
                    else:
                        input_max_dist = None
            cfg.max_dist = int(input_max_dist)

            print '\nEnter the size of the dungeon(s) in chunks from West to' \
                  ' East. (X size)'
            print 'You can enter a fixed value >= 4, or a range (ie: 4-7)'
            choice = None
            while choice is None:
                choice = raw_input('\nX size: ')
                if choice.isdigit():
                    if int(choice) < 4:
                        choice = None
                elif re.match(r'\d+-\d+', choice):
                    (a, b) = choice.split('-')
                    a = int(a)
                    b = int(b)
                    if a < 4 or b <= a:
                        choice = None
                else:
                    choice = None
            args.x = choice

            print '\nEnter the size of the dungeon(s) in chunks from North to' \
                  ' South. (Z size)'
            print 'You can enter a fixed value >= 4, or a range (ie: 4-7)'
            choice = None
            while choice is None:
                choice = raw_input('\nZ size: ')
                if choice.isdigit():
                    if int(choice) < 4:
                        choice = None
                elif re.match(r'\d+-\d+', choice):
                    (a, b) = choice.split('-')
                    a = int(a)
                    b = int(b)
                    if a < 4 or b <= a:
                        choice = None
                else:
                    choice = None
            args.z = choice

            print '\nEnter a number of levels.'
            print 'You can enter a fixed value between 1 and 42, or a range (ie: 3-5)'
            choice = None
            while choice is None:
                choice = raw_input('\nLevels: ')
                if choice.isdigit():
                    if int(choice) < 1:
                        choice = None
                elif re.match(r'\d+-\d+', choice):
                    (a, b) = choice.split('-')
                    a = int(a)
                    b = int(b)
                    if a < 1 or a > 42 or b <= a:
                        choice = None
                else:
                    choice = None
            args.levels = choice

            print '\nEnter the maximum number of dungeons to add.'
            print 'Depending on the characteristics of your world, and size ' \
                  ' of your'
            print 'dungeons, the actual number placed may be less.'
            print 'Enter -1 to add as many dungeons as possible.'
            choice = None
            while choice is None:
                choice = raw_input('\nNumber of dungeons (enter for 1): ')
                if choice == '':
                    choice = 1
                elif choice == '-1':
                    choice = -1
                else:
                    if choice.isdigit() and int(choice) >= 1:
                        choice = int(choice)
                    else:
                        choice = None
            args.number = int(choice)
            args.write = True

        elif command == 't':
            args.command = 'addth'
            # Pick a config
            configDir = os.path.join(sys.path[0], 'configs')
            if (os.path.isdir(configDir) is False):
                configDir = 'configs'
            if (os.path.isdir(configDir) is False):
                sys.exit('\nI cannot find your configs directory! Aborting!')
            choices = ['default']
            for file in os.listdir(configDir):
                file_path = os.path.join(configDir, file)
                file = file.replace('.cfg', '')
                if (
                    os.path.isfile(file_path) and
                    file_path.endswith('.cfg') and
                    file != 'default'):
                    choices.append(file)
            print '\nConfigurations in your configs directory:\n'
            count = 1
            config = None
            for file in choices:
                    print '\t[{}] {}'.format(count, file)
                    count += 1
            while config is None:
                config = raw_input('\nChoose a config (enter for default): ')
                if config == '':
                    config = 'default'
                else:
                    if config in [str(x+1) for x in xrange(len(choices))]:
                        config = choices[int(config)-1]
                    else:
                        config = None
            args.config = str(config) + '.cfg'
            cfg.Load(args.config)

            # Prompt for a mapstore if we need to
            if (cfg.mapstore == '' and args.mapstore is None):
                print '\nSome configurations may generate dungeon maps. If you are'
                print 'using multiverse you need supply the name of your'
                print 'primary world for this to work. You can also provide this'
                print 'in the config file or as a command switch.'
                print '\n(if you don\'t use multiverse, just hit enter)'
                cfg.mapstore = raw_input('Name of primary multiverse world: ')

            # Prompt for max_dist
            print '\nEnter the maximum distance (in chunks) from spawn to the start'
            print 'of the treasure hunt. Take care to pick a value that matches'
            print 'your needs.  If this value is too high and you add few hunts,'
            print 'they may be hard to find. If this value is too low and you'
            print 'add many hunts, they will overlap too much.\n'
            input_max_dist = None
            while input_max_dist is None:
                input_max_dist = raw_input(
                    '\nMax Distance (leave blank for config value, ' +
                    str(cfg.max_dist) + '): '
                )
                if input_max_dist == '':
                    input_max_dist = cfg.max_dist
                else:
                    if input_max_dist.isdigit() and int(input_max_dist) >= 0:
                        input_max_dist = int(input_max_dist)
                    else:
                        input_max_dist = None
            cfg.max_dist = int(input_max_dist)

            print '\nEnter the distance between waypoints in a hunt in chunks'
            print 'You can enter a fixed value >= 1 and <=16, or a range (eg: 5-10)'
            choice = None
            while choice is None:
                choice = raw_input('\nStep distance: ')
                if choice.isdigit():
                    if int(choice) < 1 or int(choice) > 16:
                        choice = None
                elif re.match(r'\d+-\d+', choice):
                    (a, b) = choice.split('-')
                    a = int(a)
                    b = int(b)
                    if a < 1 or b > 16 or b <= a:
                        choice = None
                else:
                    choice = None
            args.distance = choice

            print '\nEnter a number of steps (including the start).'
            print 'You can enter a fixed value > 1, or a range (ie: 3-5)'
            choice = None
            while choice is None:
                choice = raw_input('\nSteps: ')
                if choice.isdigit():
                    if int(choice) < 1:
                        choice = None
                elif re.match(r'\d+-\d+', choice):
                    (a, b) = choice.split('-')
                    a = int(a)
                    b = int(b)
                    if a < 1 or b <= a:
                        choice = None
                else:
                    choice = None
            args.steps = choice

            print '\nEnter the maximum number of treasure hunts to add.'
            print 'Depending on the characteristics of your world, and'
            print 'the number of steps, the actual number placed may be less.'
            print 'Enter -1 to add as many hunts as possible.'
            choice = None
            while choice is None:
                choice = raw_input('\nNumber of treasure hunts (enter for 1): ')
                if choice == '':
                    choice = 1
                elif choice == '-1':
                    choice = -1
                else:
                    if choice.isdigit() and int(choice) >= 1:
                        choice = int(choice)
                    else:
                        choice = None
            args.number = int(choice)
            args.write = True

        elif command == 'r':
            args.command = 'regenerate'
            # Pick a config
            configDir = os.path.join(sys.path[0], 'configs')
            if (os.path.isdir(configDir) is False):
                configDir = 'configs'
            if (os.path.isdir(configDir) is False):
                sys.exit('\nI cannot find your configs directory! Aborting!')
            choices = ['default']
            for file in os.listdir(configDir):
                file_path = os.path.join(configDir, file)
                file = file.replace('.cfg', '')
                if (
                    os.path.isfile(file_path) and
                    file_path.endswith('.cfg') and
                    file != 'default'):
                    choices.append(file)
            print '\nConfigurations in your configs directory:\n'
            count = 1
            config = None
            for file in choices:
                    print '\t[{}] {}'.format(count, file)
                    count += 1
            while config is None:
                config = raw_input('\nChoose a config (enter for default): ')
                if config == '':
                    config = 'default'
                else:
                    if config in [str(x+1) for x in xrange(len(choices))]:
                        config = choices[int(config)-1]
                    else:
                        config = None
            args.config = str(config) + '.cfg'
            cfg.Load(args.config)

            # Prompt for a mapstore if we need to
            if (cfg.maps > 0 and cfg.mapstore == '' and args.mapstore is None):
                print '\nThis configuration may generate dungeon maps. If you are'
                print 'using multiverse you need supply the name of your'
                print 'primary world for this to work. You can also provide this'
                print 'in the config file or as a command switch.'
                print '\n(if you don\'t use multiverse, just hit enter)'
                cfg.mapstore = raw_input('Name of primary multiverse world: ')

            if (cfg.mapstore == ''):
                cfg.mapstore = args.world

            args.dungeons = []
            args.all = False
            world = loadWorld(args.world)
            dlist, tlist = loadCaches()
            if len(dlist) == 0:
                sys.exit()
            print 'Choose a dungeon to regenerate:'
            print '-------------------------------\n'
            print '\t[a] Regenerate ALL dungeons in this map.'
            for i in xrange(len(dlist)):
                print '\t[%d] Dungeon at %d %d.' % (
                    i + 1,
                    dlist[i][0],
                    dlist[i][1]
                )
            while (args.all is False and args.dungeons == []):
                d = raw_input('\nEnter choice, or q to quit: ')
                if d == 'a':
                    args.all = True
                elif d.isdigit() and int(d) > 0 and int(d) <= len(dlist):
                    d = int(d)
                    args.dungeons = [[dlist[d - 1][0], dlist[d - 1][1]]]
                elif d == 'q':
                    print 'Quitting...'
                    sys.exit()
                else:
                    print '"%s" is not a valid choice!' % d

        elif command == 'l':
            args.command = 'list'
        elif command == 'p':
            args.command = 'genpoi'
        elif command == 'w':
            args.command = 'genreg'
        elif command == 'd':
            args.command = 'delete'
            args.dungeons = []
            args.all = False

            # Prompt for a mapstore if we need to
            if args.mapstore is None:
                print '\nIf you are using multiverse you need supply the'
                print 'name of your primary world so any existing dungeon maps'
                print 'can be removed. You can also provide this as a command'
                print 'switch.'
                print '\n(if you don\'t use multiverse, just hit enter)'
                cfg.mapstore = raw_input('Name of primary multiverse world: ')

            if (cfg.mapstore == ''):
                cfg.mapstore = args.world

            world = loadWorld(args.world)
            dungeons, tHunts = loadCaches()

            if len(dungeons) == 0 and len(tHunts) == 0:
                sys.exit()

            print 'Choose object(s) to delete:\n----------------------------\n'
            print '\t[a] Delete ALL dungeons and hunts from this map.'
            if len(dungeons) > 0:
                for i in xrange(len(dungeons)):
                    print '\t[%d] Dungeon at %d %d.' % (
                        i + 1,
                        dungeons[i][0],
                        dungeons[i][1]
                    )
            if len(tHunts) > 0:
                for i in xrange(len(tHunts)):
                    print '\t[%d] Treasure Hunt at %d %d.' % (
                        i + 1 + len(dungeons),
                        tHunts[i][0],
                        tHunts[i][1]
                    )

            while (args.all is False and args.dungeons == []):
                d = raw_input('\nEnter choice, or q to quit: ')
                if d == 'a':
                    args.all = True
                elif d.isdigit() and int(d) > 0 and int(d) <= (len(dungeons)+len(tHunts)):
                    d = int(d)
                    if d <= len(dungeons):
                        args.dungeons = [[dungeons[d - 1][0], dungeons[d - 1][1]]]
                    else:
                        args.dungeons = [[tHunts[d - 1 - len(dungeons)][0], tHunts[d - 1 - len(dungeons)][1]]]
                elif d == 'q':
                    print 'Quitting...'
                    sys.exit()
                else:
                    print '"%s" is not a valid choice!' % d
        else:
            print 'Quitting...'
            sys.exit()
    elif(args.command == 'add' or args.command == 'regenerate' or args.command == 'addth' ):
        cfg.Load(args.config)

    # Check to see if mapstore is being overridden
    if (hasattr(args, 'mapstore') and args.mapstore is not None):
        cfg.mapstore = args.mapstore
    if (cfg.mapstore == ''):
        cfg.mapstore = args.world

    # Load the world if we havent already
    if world is None:
        world = loadWorld(args.world)

    # List mode
    if (args.command == 'list'):
        # List the known dungeons and exit
        dungeons, tHunts = loadCaches()
        sys.exit()

    # GenPOI mode
    if (args.command == 'genpoi'):
        # List the known dungeons in OverViewer POI format, and exit
        args.quiet = True
        if args.outputdir is None:
            args.outputdir = 'C:\\overview'
        output = '#\n# Cut from here into your OverViewer config.py and customise\n#\n\n'
        output += 'worlds[\'%s\'] = "%s\\%s"\n' % ( args.world, mclevel.saveFileDir, args.world )
        output += 'outputdir = "%s"\n\n' % ( args.outputdir )
        output += 'def dungeonFilter(poi):\n\tif poi[\'id\'] == \'MCDungeon\':\n\t\ttry:\n\t\t\treturn (poi[\'name\'], poi[\'description\'])\n\t\texcept KeyError:\n\t\t\treturn poi[\'name\'] + \'\\n\'\n\n'
        output += 'def tHuntFilter(poi):\n\tif poi[\'id\'] == \'MCDungeonTH\':\n\t\ttry:\n\t\t\treturn (poi[\'name\'], poi[\'description\'])\n\t\texcept KeyError:\n\t\t\treturn poi[\'name\'] + \'\\n\'\n\n'
        output += 'def tHuntWPFilter(poi):\n\tif poi[\'id\'] == \'MCDungeonTHW\':\n\t\ttry:\n\t\t\treturn (poi[\'name\'], poi[\'description\'])\n\t\texcept KeyError:\n\t\t\treturn poi[\'name\'] + \'\\n\'\n\n'
        output += 'renders["mcdungeon"] = {\n\t\'world\': \'%s\',\n\t\'title\': \'MCDungeon\',\n\t\'rendermode\': \'smooth_lighting\',\n\t\'manualpois\':[' % ( args.world )
        print output

        dungeons, tHunts = loadCaches(genpoi=True)
        output = '\t],\n\t\'markers\': [\n'
        output += '\t\tdict(name="Dungeons", filterFunction=dungeonFilter, icon="icons/marker_tower_red.png", checked=True),\n'
        output += '\t\tdict(name="TreasureHunts", filterFunction=tHuntFilter, icon="icons/marker_chest_red.png", checked=True),\n'
        output += '\t\tdict(name="Waypoints", filterFunction=tHuntWPFilter, icon="icons/marker_chest.png", checked=False),\n'
        output += '\t]\n}\n'
        print output
        sys.exit()

    # Genregions mode
    if (args.command == 'genreg'):

        import yaml
        # load in the existing YAML, if any
        if( args.regionfile is None ):
            args.regionfile = 'regions.yml'

        print 'Generating WorldGuard regions file in %s\n' % (args.regionfile)

        try:
            stream = open( args.regionfile , 'r')
            regions = yaml.load( stream )
        except:
            print 'Unable to read any existing Region file.'
            regions = {}

        if 'regions' not in regions:
            # Create an empty default region file
            regions['regions'] = {
                '__global__': {
                    'flags': {},
                    'owners': {},
                    'members': {}
                },
                '__mcd_default__': {
                    'priority': 4,
                    'flags': {},
                    'owners': {},
                    'members': {}
                }
            }

        # load in the list of existing dungeons
        print 'Loading in list of dungeons...'
        dungeons, tHunts = loadCaches(genpoi=False)

        # Build/update YAML
        print 'Generating YAML...'
        dnames = {}
        for d in dungeons:
            info = d[4]
            name = 'mcd_' + re.sub('\W','',re.sub(' ','_',info.get('full_name', 'Dungeon'))).lower()
            dnames[name] = True
            if not name in regions['regions']:
                print 'Adding new region: %s' % (name)
                if '__mcd_default__' in regions['regions']:
                    regions['regions'][name] = copy.deepcopy(regions['regions']['__mcd_default__'])
                else:
                    regions['regions'][name] = {
                        'priority': 4,
                        'flags': {},
                        'owners': {},
                        'members': {},
                    }
                regions['regions'][name]['type'] = 'cuboid'
                regions['regions'][name]['min'] = {
                        'x': (info['position'].x + 0.0),
                        'y': 0.0,
                        'z': (info['position'].z + 0.0)
                    }
                regions['regions'][name]['max'] = {
                        'x': (info['position'].x + info['xsize'] * 16.0),
                        'y': 255.0,
                        'z': (info['position'].z + info['zsize'] * 16.0)
                    }

        for r in list(regions['regions'].keys()):
            if re.match('^mcd_',r) != None and not r in dnames:
                print 'Deleting old region: %s' % (r)
                del regions['regions'][r]

        # Write new YAML to file
        print 'Writing YAML...'
        try:
            stream = open( args.regionfile, 'w' )
            stream.write("# Created by MCDungeon\n")
            stream.write("# Be VERY CAREFUL if updating this file by hand!  Always keep backups!\n")
            stream.write("# Use /rg reload [-w world] to reload data if server is up\n")
            stream.write("# MCDungeon defaults are kept in the global region __mcd_default__\n#\n")
            yaml.dump( regions, stream )
        except:
            e = sys.exc_info()[0]
            print 'Unable to write to file "%s": %s' % ( args.regionfile, e )

        sys.exit()

    # Delete mode
    if (args.command == 'delete'):
        # Check to make sure the user specified what they want to do.
        if args.dungeons == None and args.all is False:
            print 'You must specify either --all or at least one -d option' \
                  ' when deleting dungeons or treasure hunts.'
            sys.exit(1)
        # Get a list of known dungeons and their size.
        if dungeons == [] and tHunts == []:
            dungeons, tHunts = loadCaches()
        # No dungeons. Exit.
        if len(dungeons) == 0 and len(tHunts) == 0:
            sys.exit()
        # A list of existing dungeon positions for convenience.
        existing = set()
        for d in dungeons:
            existing.add((d[0], d[1]))
        for t in tHunts:
            existing.add((t[0], t[1]))
        # Populate a list of dungeons to delete.
        # If --all was specified, populate the delete list will all known dungeons.
        # Otherwise just validate the -d options.
        to_delete = []
        if args.all is True:
            for d in dungeons:
                to_delete.append((d[0], d[1]))
            for t in tHunts:
                to_delete.append((t[0], t[1]))
        else:
            for d in args.dungeons:
                if (d[0], d[1]) not in existing:
                    sys.exit('Unable to locate dungeon/hunt at %d %d.' % (d[0], d[1]))
                to_delete.append(d)
        # Build a list of chunks to delete from the dungeon info.
        chunks = []
        # We need to update the caches for the chunks we are affecting
        dcache, dmtime = utils.loadDungeonCache(cache_path)
        tcache, tmtime = utils.loadTHuntCache(cache_path)
        ms = mapstore.new(cfg.mapstore, cfg.dir_paintings, cfg.mapcolor,
                          cfg.paintingcolor)
        for d in to_delete:
            p = [d[0] / 16, d[1] / 16]
            print 'Deleting dungeon/hunt at %d %d...' % (d[0], d[1])
            dkey = '%s,%s' % (d[0], d[1])
            ms.delete_maps(dkey)
            if dkey in dcache:
                del dcache[dkey]
            elif dkey in tcache:
                del tcache[dkey]
            else:
                print 'WARN: Object not in dungeon cache or thunt cache! ' + dkey
            xsize = 0
            zsize = 0
            for e in dungeons:
                if e[0] == d[0] and e[1] == d[1]:
                    xsize = e[2]
                    zsize = e[3]
                    # Fill caves. Delete all chunks.
                    if e[4]['fill_caves'] is True:
                        p[0] -= 5
                        p[1] -= 5
                        xsize += 10
                        zsize += 10
                    for x in xrange(xsize):
                        for z in xrange(zsize):
                            chunks.append((p[0] + x, p[1] + z))
                    break
            for e in tHunts:
                if e[0] == d[0] and e[1] == d[1]:
                    xsize = 1
                    zsize = 1
                    for l in e[4]['landmarks']:
                        chunks.append(((l.x+e[0])>>4,(l.z+e[1])>>4))
                    chunks.append((p[0], p[1]))
                    break
        # We need to update the caches for the chunks we are affecting
        ccache, cmtime = utils.loadChunkCache(cache_path)
        # Delete the chunks
        for c in chunks:
            if world.containsChunk(c[0], c[1]):
                world.deleteChunk(c[0], c[1])
                ckey = '%s,%s' % (c[0], c[1])
                if ckey in ccache:
                    del ccache[ckey]
                else:
                    print 'WARN: Chunk not in chunk cache! ' + ckey
        # Save the world.
        print "Saving..."
        world.saveInPlace()
        utils.saveDungeonCache(cache_path, dcache)
        utils.saveTHuntCache(cache_path, tcache)
        utils.saveChunkCache(cache_path, ccache)
        sys.exit()

    # Regenerate mode
    if (args.command == 'regenerate'):
        # Check to make sure the user specified what they want to do.
        if args.dungeons == None and args.all is False:
            print 'You must specify either --all or at least one -d option when ' \
                  'regnerating dungeons.'
            sys.exit(1)
        # Get a list of known dungeons and their size.
        if dungeons == []:
            dungeons, tHunts = loadCaches()
        # No dungeons. Exit.
        if len(dungeons) == 0:
            sys.exit()
        # Populate a list of dungeons to regenerate.
        # If --all was specified, populate the regen lst will contain all known
        # dungeons.
        to_regen = []
        if args.all is True:
            for d in dungeons:
                to_regen.append(d)
        else:
            for d in dungeons:
                for argd in args.dungeons:
                    if (d[0], d[1]) == (argd[0], argd[1]):
                        to_regen.append(d)

        if len(to_regen) == 0:
            print 'Unable to locate specified dungeons!'
            sys.exit(1)

        # We'll need caches and map stores
        dungeon_cache, dmtime = utils.loadDungeonCache(cache_path)
        chunk_cache, cmtime = utils.loadChunkCache(cache_path)
        map_store = mapstore.new(cfg.mapstore, cfg.dir_paintings, cfg.mapcolor,
                                 cfg.paintingcolor)
        loottable.Load()

        # Set/override some common parameters
        args.number = 1
        args.seed = None
        args.offset = None
        args.bury = False
        cfg.fill_caves = False
        args.write = True

        # Now go through each dungeon
        for d in to_regen:
            # Delete the existing maps for this dungeon so they can be recycled.
            map_store.delete_maps('%s,%s' % (d[0], d[1]))

            # Set some parameters for this specific dungeon
            cfg.min_x = cfg.max_x = d[2]
            cfg.min_z = cfg.max_z = d[3]
            cfg.min_levels = cfg.max_levels = d[5]
            cfg.offset = '%d %d %d' % (d[6], d[7], d[8])
            args.entrance = [d[4]['entrance_pos'].x, d[4]['entrance_pos'].z]
            args.entrance_height = d[4]['entrance_height']
            cfg.portal_exit = d[4].get('portal_exit', Vec(0, 0, 0))
            cfg.dungeon_name = d[4].get('dungeon_name', ruins.Blank.nameDungeon())

            print 'Regenerating dungeon at', cfg.offset, '...'
            dungeon = Dungeon(args,
                              world,
                              chunk_cache,
                              dungeon_cache,
                              good_chunks,
                              map_store)
            result = dungeon.generate(cache_path, __version__)
            if result is False:
                print 'Failed to regenerate dungeon! Aborting!'
                sys.ext(1)
        sys.exit()

    if (args.command == 'add'):
        # Validate size settings
        cfg.min_x = 4
        cfg.max_x = cfg.max_dist - cfg.min_dist
        cfg.min_z = 4
        cfg.max_z = cfg.max_dist - cfg.min_dist
        cfg.min_levels = 1
        cfg.max_levels = 8

        # Range for X
        result = re.search('(\d+)-(\d+)', args.x)
        if (result):
            cfg.min_x = int(result.group(1))
            cfg.max_x = int(result.group(2))
            if (cfg.min_x > cfg.max_x):
                sys.exit('Minimum X must be equal or less than maximum X.')
        else:
            try:
                cfg.min_x = int(args.x)
                cfg.max_x = int(args.x)
            except ValueError:
                sys.exit('X doesn\'t appear to be an integer!')
        if (cfg.min_x < 4):
            sys.exit('Minimum X must be equal or greater than 4.')

        # Range for Z
        result = re.search('(\d+)-(\d+)', args.z)
        if (result):
            cfg.min_z = int(result.group(1))
            cfg.max_z = int(result.group(2))
            if (cfg.min_z > cfg.max_z):
                sys.exit('Minimum Z must be equal or less than maximum Z.')
        else:
            try:
                cfg.min_z = int(args.z)
                cfg.max_z = int(args.z)
            except ValueError:
                sys.exit('Z doesn\'t appear to be an integer!')
        if (cfg.min_z < 4):
            sys.exit('Minimum Z must be equal or greater than 4.')

        # Range for Levels
        result = re.search('(\d+)-(\d+)', args.levels)
        if (result):
            cfg.min_levels = int(result.group(1))
            cfg.max_levels = int(result.group(2))
            if (cfg.min_levels > cfg.max_levels):
                sys.exit('Minimum levels must be equal or less than maximum levels.')
        else:
            try:
                cfg.min_levels = int(args.levels)
                cfg.max_levels = int(args.levels)
            except ValueError:
                sys.exit('Levels doesn\'t appear to be an integer!')
        if (cfg.min_levels < 1):
            sys.exit('Minimum levels must be equal or greater than 1.')
        if (cfg.max_levels > 42):
            sys.exit('Maximum levels must be equal or less than 42.')

        # Override bury
        if (args.bury is not None):
            cfg.bury = args.bury

        # Override offset
        if (args.offset is not None):
            cfg.offset = '%d, %d, %d' % (args.offset[0],
                                         args.offset[1],
                                         args.offset[2])

        if (
            args.entrance is not None and
                (
                    args.entrance[0] >= args.x or
                    args.entrance[0] < 0 or
                    args.entrance[1] >= args.z or
                    args.entrance[1] < 0
                )
        ):
            print 'Entrance offset values out of range.'
            print 'These should be >= 0 and < the maximum width or length of' \
                  ' the dungeon.'
            sys.exit(1)

    if (args.command == 'addth'):
        # Step count range for treasure hunts
        result = re.search('(\d+)-(\d+)', args.steps)
        if (result):
            cfg.min_steps = int(result.group(1))
            cfg.max_steps = int(result.group(2))
            if (cfg.min_steps > cfg.max_steps):
                sys.exit('Minimum steps must be equal or less than maximum steps.')
        else:
            try:
                cfg.min_steps = int(args.steps)
                cfg.max_steps = int(args.steps)
            except ValueError:
                sys.exit('Steps doesn\'t appear to be an integer!')
        if (cfg.min_steps <= 1):
            sys.exit('Minimum steps must be greater than 1.')
        if (cfg.max_steps > 20):
            sys.exit('Maximum steps must be equal or less than 20.')

        # Step distance for treasure hunts
        result = re.search('(\d+)-(\d+)', args.distance)
        if (result):
            cfg.min_distance = int(result.group(1))
            cfg.max_distance = int(result.group(2))
            if (cfg.min_distance > cfg.max_distance):
                sys.exit('Minimum step distance must be equal or less than maximum distance.')
        else:
            try:
                cfg.min_distance = int(args.distance)
                cfg.max_distance = int(args.distance)
            except ValueError:
                sys.exit('Distance doesn\'t appear to be an integer!')
        if (cfg.min_distance < 1):
            sys.exit('Minimum distance must be equal or greater than 1.')
        if (cfg.max_distance > 40):
            sys.exit('Maximum distance must be equal or less than 40.')
        args.min_levels = args.max_levels = 1
        args.min_x = args.max_x = 1
        args.min_z = args.max_z = 1

    # Everything below is add/regen mode


    # Some options don't work with multidungeons
    if args.number is not 1:
        if args.offset is not None:
            print 'WARN: Offset option is ignored when generating multiple ' \
                  ' dungeons.'
            cfg.offset = None
        if args.seed is not None:
            print 'WARN: Seed option is ignored when generating multiple dungeons.'
            args.seed = None
        if args.command is not 'addth':
            if args.entrance is not None:
                print 'WARN: Entrance option is ignored when generating multiple ' \
                      ' dungeons.'
                args.entrance = None
            if args.html is not None:
                print 'WARN: HTML option is ignored when generating multiple dungeons.'
                args.html = None

    # Load lewts
    loottable.Load()

    print "MCDungeon", __version__, "startup complete. "

    if args.debug:
        if (args.command == 'addth'):
            print 'S:', args.steps
            print '   ', cfg.min_steps
            print '   ', cfg.max_steps
            print 'D:', args.distance
            print '   ', cfg.min_distance
            print '   ', cfg.max_distance
        else:
            print 'Z:', args.z
            print '   ', cfg.min_z
            print '   ', cfg.max_z
            print 'X:', args.x
            print '   ', cfg.min_x
            print '   ', cfg.max_x
            print 'L:', args.levels
            print '   ', cfg.min_levels
            print '   ', cfg.max_levels

    # Look for good chunks
    if (cfg.offset is None or cfg.offset is ''):
        # Load the chunk cache
        chunk_cache, chunk_mtime = utils.loadChunkCache(cache_path)
        cached = 0
        notcached = 1

        # Store some stats
        chunk_stats = {
            'F': {
                'name': '          Far Chunks',
                'count': 0,
                'order': 1,
            },
            'N': {
                'name': '         Near Chunks',
                'count': 0,
                'order': 2,
            },
            'I': {
                'name': '          Incomplete',
                'count': 0,
                'order': 3,
            },
            'O': {
                'name': '              Oceans',
                'count': 0,
                'order': 4,
            },
            'S': {
                'name': '          Structures',
                'count': 0,
                'order': 5,
            },
            'H': {
                'name': '         High Chunks',
                'count': 0,
                'order': 6,
            },
            'L': {
                'name': '          Low Chunks',
                'count': 0,
                'order': 7,
            },
            'R': {
                'name': '              Rivers',
                'count': 0,
                'order': 8,
            },
            'G': {
                'name': '         Good Chunks',
                'count': 0,
                'order': 9,
            },
        }

        # Preprocess chunks
        # Pass 1 will prefilter the chunks, weeding out the trivial cases. This
        # saves setup time when multiprocessing in pass 2.
        print 'Finding good chunks:'
        pm = pmeter.ProgressMeter()
        pm.init(world.chunkCount, label='Pass 1:')
        cc = 0
        chunks = set()
        if args.spawn is not None:
            sx = args.spawn[0] >> 4
            sz = args.spawn[1] >> 4
        else:
            sx = world.playerSpawnPosition()[0] >> 4
            sz = world.playerSpawnPosition()[2] >> 4
        for c in world.allChunks:
            cx = c[0]
            cz = c[1]
            key = '%s,%s' % (cx, cz)
            # Far chunk
            if (numpy.sqrt((cx - sx) * (cx - sx) + (cz - sz) * (cz - sz)) > cfg.max_dist):
                chunk_stats['F']['count'] += 1
                continue
            # Near chunk
            if (numpy.sqrt((cx - sx) * (cx - sx) + (cz - sz) * (cz - sz)) < cfg.min_dist):
                chunk_stats['N']['count'] += 1
                continue
            # Cached chunk
            if (
                world.worldFolder.getRegionForChunk(cx, cz).getTimestamp(cx, cz) < chunk_mtime and
                key in chunk_cache
            ):
                chunk_stats[chunk_cache[key][0]]['count'] += 1
                if chunk_cache[key][0] == 'G':
                    good_chunks[(cx, cz)] = chunk_cache[key][2]
                cached += 1
                continue
            chunks.add(c)
        pm.set_complete()

        # Pass 2 will do the heavy lifting on the interesting chunks.
        pm = pmeter.ProgressMeter()
        pm.init(world.chunkCount, label='Pass 2:')
        cc = 0
        chunk_min = None
        chunk_max = None

        # Handle this in the main thread if we aren't multiprocessing.
        if args.workers is not None and args.workers < 2:
            if args.debug:
                print 'Working with a single process.'
            for c in chunks:
                (cx, cz, result, biome, depth) = classifyChunk(c)

                # Chunk map stuff
                if args.debug:
                    if chunk_min is None:
                        chunk_min = (cx, cz)
                    else:
                        chunk_min = (min(cx, chunk_min[0]), min(cz, chunk_min[1]))
                    if chunk_max is None:
                        chunk_max = (cx, cz)
                    else:
                        chunk_max = (max(cx, chunk_max[0]), max(cz, chunk_max[1]))

                # Classify chunks
                notcached += 1
                key = '%s,%s' % (cx, cz)
                chunk_stats[result]['count'] += 1
                chunk_cache[key] = [result, biome, depth]

                if result == 'G':
                    good_chunks[(cx, cz)] = chunk_cache[key][2]

                # Update progress.
                cc += 1
                if cc % 200 == 0:
                    pm.update(cc)

                # Save progress occasionally.
                if notcached % 10000 == 0:
                    utils.saveChunkCache(cache_path, chunk_cache)
        # Process chunks in parallel.
        else:
            if args.debug:
                print 'Working with multiple processes. workers =', args.workers
            with cf.ProcessPoolExecutor(max_workers = args.workers) as executor:
                chunk_scans = {executor.submit(classifyChunk, c): c for c in chunks}
                for future in cf.as_completed(chunk_scans):
                    (cx, cz, result, biome, depth) = future.result()

                    # Chunk map stuff
                    if args.debug:
                        if chunk_min is None:
                            chunk_min = (cx, cz)
                        else:
                            chunk_min = (min(cx, chunk_min[0]), min(cz, chunk_min[1]))
                        if chunk_max is None:
                            chunk_max = (cx, cz)
                        else:
                            chunk_max = (max(cx, chunk_max[0]), max(cz, chunk_max[1]))

                    # Classify chunks
                    notcached += 1
                    key = '%s,%s' % (cx, cz)
                    chunk_stats[result]['count'] += 1
                    chunk_cache[key] = [result, biome, depth]

                    if result == 'G':
                        good_chunks[(cx, cz)] = chunk_cache[key][2]

                    # Update progress.
                    cc += 1
                    if cc % 200 == 0:
                        pm.update(cc)

                    # Save progress occasionally.
                    if notcached % 10000 == 0:
                        utils.saveChunkCache(cache_path, chunk_cache)

        utils.saveChunkCache(cache_path, chunk_cache)
        pm.set_complete()

        # Load caches
        old_dungeons, old_thunts = loadCaches(expand_fill_caves=True)

        # Find old dungeons
        for d in old_dungeons:
            if args.debug:
                print 'old dungeon:', d
            p = (d[0] / 16, d[1] / 16)
            for x in xrange(int(d[2])):
                for z in xrange(int(d[3])):
                    if (p[0] + x, p[1] + z) in good_chunks:
                        del(good_chunks[(p[0] + x, p[1] + z)])
                        key = '%s,%s' % (p[0] + x, p[1] + z)
                        chunk_cache[key] = ['S', -1, 0]
                        chunk_stats['S']['count'] += 1
                        chunk_stats['G']['count'] -= 1

        # Find old hunts
        for t in old_thunts:
            if args.debug:
                print 'old treasure hunt:', t
            p = (t[0] / 16, t[1] / 16)
            if (p[0], p[1]) in good_chunks:
                del(good_chunks[(p[0], p[1])])
                key = '%s,%s' % (p[0], p[1])
                chunk_cache[key] = ['S', -1, 0]
                chunk_stats['S']['count'] += 1
                chunk_stats['G']['count'] -= 1
            for l in t[4]['landmarks']:
                cx = l.x >> 4
                cz = l.z >> 4
                if (cx, cz) in good_chunks:
                    del(good_chunks[(cx, cz)])
                    key = '%s,%s' % (cx, cz)
                    chunk_cache[key] = ['S', -1, 0]
                    chunk_stats['S']['count'] += 1
                    chunk_stats['G']['count'] -= 1

        # Funky little chunk map
        if args.debug and chunk_min and chunk_max:
            for cz in xrange(chunk_min[1], chunk_max[1] + 1):
                for cx in xrange(chunk_min[0], chunk_max[0] + 1):
                    key = '%s,%s' % (cx, cz)
                    if key in chunk_cache:
                        if chunk_cache[key][0] == 'I':
                            sys.stdout.write(materials.RED)
                        if chunk_cache[key][0] == 'O':
                            sys.stdout.write(materials.BLUE)
                        if chunk_cache[key][0] == 'R':
                            sys.stdout.write(materials.BLUE)
                        if chunk_cache[key][0] == 'S':
                            sys.stdout.write(materials.DGREY)
                        if chunk_cache[key][0] == 'H':
                            sys.stdout.write(materials.PURPLE)
                        if chunk_cache[key][0] == 'L':
                            sys.stdout.write(materials.PURPLE)
                        if chunk_cache[key][0] == 'G':
                            sys.stdout.write(materials.GREEN)
                        sys.stdout.write(chunk_cache[key][0])
                        sys.stdout.write(chunk_cache[key][0])
                        sys.stdout.write(materials.ENDC)
                    else:
                        sys.stdout.write('  ')
                print

        # Re-cache the chunks and update mtime
        utils.saveChunkCache(cache_path, chunk_cache)

        order = sorted(chunk_stats.items(), key=lambda x: x[1]['order'])
        for stat in order:
            print '   %s: %d' % (stat[1]['name'], stat[1]['count'])
        print ' Cache hit rate: %d/%d (%d%%)' % (cached, notcached + cached,
                                                 100 * cached / (notcached + cached))

    # Load the dungeon cache for updates later.
    dungeon_cache, mtime = utils.loadDungeonCache(cache_path)
    thunt_cache, tmtime = utils.loadTHuntCache(cache_path)
    # Create a map store
    map_store = mapstore.new(cfg.mapstore, cfg.dir_paintings, cfg.mapcolor,
                             cfg.paintingcolor)

    # Generate dungeons!
    count = 0
    result = True
    while (
        result is True and
        (
            count < args.number or
            args.number == -1
        )
    ):
        if (args.command == 'addth'):
            if args.number == -1:
                print '\n***** Placing treasure hunt {0} *****\n'.format(count + 1)
            else:
                print '\n***** Placing treasure hunt {0} of {1} *****\n'.format(count + 1,
                                                                      args.number)
            thunt = TreasureHunt(args,
                          world,
                          chunk_cache,
                          thunt_cache,
                          good_chunks,
                          map_store)
            result = thunt.generate(cache_path, __version__)
            del(thunt)
        else:
            if args.number == -1:
                print '\n***** Placing dungeon {0} *****\n'.format(count + 1)
            else:
                print '\n***** Placing dungeon {0} of {1} *****\n'.format(count + 1,
                                                                      args.number)
            dungeon = Dungeon(args,
                          world,
                          chunk_cache,
                          dungeon_cache,
                          good_chunks,
                          map_store)
            result = dungeon.generate(cache_path, __version__)
            del(dungeon)
        if result:
            count += 1


    if (count == 0):
        if (args.command == 'addth'):
            print 'No treasure hunts were generated!'
            print 'You may have asked for too many steps, or your allowed spawn'
            print 'region is too small.  Try disabling fill_caves, and check'
            print 'your min_distance and max_distance settings in your config.'
        else:
            print 'No dungeons were generated!'
            print 'You may have requested too deep or too large a dungeon, or your '
            print 'allowed spawn region is too small. If using fill_caves, remember '
            print 'to add 10 chunks in each direction to the size of your dungeon.'
            print 'Check min_dist, max_dist, and fill_caves settings in your config.'
        sys.exit(1)

    if (args.command == 'addth'):
        print 'Placed', count, 'treasure hunts!'
    else:
        print 'Placed', count, 'dungeons!'


if __name__ == "__main__":
    '''
    Command line invocation.
    '''
    print "MCDungeon", __version__

    import cfg
    import loottable
    from dungeon import Dungeon
    from treasure_hunt import TreasureHunt
    import utils
    from utils import Vec
    import mapstore
    import ruins
    import materials

    # Silence some logging from pymclevel
    logging.basicConfig(level=logging.CRITICAL)

    from pymclevel import mclevel
    import pmeter

    # Parse any command line arguments.
    args = parseArgs()

    try:
        # Execute the Main() function and return results.
        sys.exit(main())
    except SystemExit as e:
        # Clean exit, provide a return code.
        sys.exit(e.code)
    except:
        # Handle all other exceptions.
        ErrStr = traceback.format_exc()
        print('Exception in main loop. Exception info below:')
        sys.exit(ErrStr)
