# Please note: This project is not under active development and the last supported version is Minecraft 1.12. See the issue queue for more information.

#MCDungeon#

MCDungeon will create a procedurally generated dungeon in a preexisting
Minecraft map. It is not yet feature complete, but can already generate
dungeons with quite a bit of variety. 

Website: http://mcdungeon.bubblemod.org

Documentation: http://mcdungeon-docs.bubblemod.org

##CURRENT FEATURES:##

   * Automatically finds a good location on a map based on range, size, and
     depth parameters. Can detect player structures and try not to overwrite
     them. Avoids placing dungeons in the middle of the ocean.

   * Dungeons can be removed from a map later and the landscape allowed to
     regenerate. 

   * Dungeons can be regenerated in place with a new layout, mobs, and 
     treasure.

   * Can generate multiple dungeons in a map, or try to fill the map with as
     many dungeons as possible.

   * Generates room layouts based on a random weighted selection
     of rooms. Rooms are filled with random hallways, floors, room
     features, and ruins on the surface, all of which are configurable.

   * The density and placement of doors, portcullises, and torches are 
     configurable. Option to place fewer torches as levels go down. Less 
     light == more danger!

   * A "fill caves" mode that will fill in nearby natural caves in an attempt
     to concentrate random monster spawns inside the dungeon.

   * Places stairwells between levels, and a random entrance with a
     spiraling staircase. Some entrances have a configurable height so it 
     can be seen from far away.

   * Places chests with loot around the dungeon in (probably) hard
     to reach places. An arbitrary number of loot tables can be configured
     to provide variety. The density of chests is configurable. Custom
     potions, magic items, and armor. The heads of legendary adventurers. 

   * Places mob spawners throughout the dungeon. These will likely be near
     chests, but not always. Mob types are configurable. The density of
     spawners is configurable. Some 'non-standard' mobs are available.
     Custom mob spawners can be created with an NBT editor.

   * Optional in-game maps of dungeons.

   * Random placement of secret traps and puzzles.

   * Output floor maps to a terminal with color on ANSI systems.

   * Output entire dungeon maps to HTML.

##TODO##

   * More room, hall, floor, feature, and ruin types.
   * More traps!
   * Harder hard mode!
   * More stuff as Minecraft evolves!

##QUICK START##

   The stand-alone versions for Windows and OS X, include a 
   "launcher" script that will run in interactive mode. For advanced
   usage, run the mcdungeon executable from the command line like
   the python version. 

   List available subcommands and options:

   ```
   $ python mcdungeon.py --help
   $ ./mcdungeon --help
   ```

   Help on a specific subcommand:

   ```
   $ python mcdungeon.py <subcommand> --help
   $ ./mcdungeon <subcommand> --help
   ```

##PYTHON REQUIREMENTS##

   * Python 2.7
   * numpy
   * pyyaml
   * nbt2yaml
   * futures (Linux and OSX)

##PYTHON EXAMPLES##

   These also work for the stand-alone version. Just replace 
   "python mcdungeon.py" with "mcdungeon"

   ```
   $ python mcdungeon.py interactive
   ```

   Run in interactive mode. From here you can add, list, delete or regenerate
   dungeons.

   ```
   $ python mcdungeon.py add Dungeon 5 4 3 --term 1
   ```

   Load a world named 'Dungeon', generate a 5x4x3 dungeon layout
   (5 rooms E/W, 4 rooms N/S, and 3 levels deep) and display
   the results in a terminal window. (In color on ANSI terminals
   only. Sorry Windows) The world files will not be modified, but
   are required. Basically a "dry run."

   ```
   $ python mcdungeon.py add Dungeon 4-6 4-6 5-8 -n 5 --write
   ```

   Generate five random dungeons between the sizes of 4x4x5 and 6x6x8
   and save them to the world.

##EXAMPLE CONFIGURATIONS##

   Several example configs are included. These can be copied and/or modifed
   to suit your own tastes.

   * default.cfg
   
     A little of everything. This one is heavily commented. If you want to
     know what a config option does, look here.

   * more_mobs.cfg
 
     This produces maps that are the same as the default, but with
     more types of monsters and more spawners.

   * caverns.cfg   

     Mostly cavern type rooms. Very few "dungeon" looking rooms
     except the treasure chambers. It's a bit like exploring caves
     with the occasional dungeon room.

   * maze.cfg 

     Basically bumps up the number of corridor type rooms and the
     number of loops the dungeon layout has. You'll end up with
     fewer rooms and lots of twisty halls to get lost in. 

   * easy_mode.cfg 

     Better treasure, fewer monsters and traps. Easier dungeon layout
     (very linear) and maps of every level.

   * hard_mode.cfg

     Less treasure in upper levels, more confusing dungeon layout
     (lots of loops) more monster spawners. Hidden spawners. Creepers
     are more common. Buffed monster spawners. No maps. It also
     fills in all the surrounding underground caves so that monsters
     spawn inside the dungeon much more frequently. No exit portals.

##CREDITS##

Thanks to the following for their code, interest, inspiration, and great
ideas!  (in no particular order)

BeeTLe BeTHLeHeM, codewarrior, Link1999, SoNick, Commander Keen,
Yelik, NoiGren, whoiscraig, ChocolateySyrup, Sevminer, AnderZ EL,
SuddenLee, Silre, NuclearDemon, bking1138, BarthVader,  koredozo,
janxious, compgurusteve, Meindratheal, ChosenLama, JiFish, djchrisblue,
sshipway, denemanow.
