#!/usr/bin/env python
from random import randrange

import cave_factory

print '16x16 tile with exits on the East and West ends:'
cave = cave_factory.new(16, 16)
# North
width = randrange(1, 5)
offset = randrange(1, 16 - width)
cave.add_exit((0, offset), (0, offset + width))
# South
width = randrange(1, 5)
offset = randrange(1, 16 - width)
cave.add_exit((15, offset), (15, offset + width))
# Cave!
cave.gen_map()
cave.print_map()

del(cave)

print '16x16 tile with (room type)'
cave = cave_factory.new(16, 16)
# North
cave.add_exit((1, 0), (14, 0))
# Cave!
cave.gen_map(mode='room')
cave.print_map()

del(cave)

print '32x32 tile with two exits to the East, and one to the South:'
cave = cave_factory.new(32, 32)
# East
width = randrange(1, 5)
offset = randrange(1, 16 - width)
cave.add_exit((31, offset), (31, offset + width))
width = randrange(1, 5)
offset = randrange(16, 32 - width)
cave.add_exit((31, offset), (31, offset + width))
# South
width = randrange(1, 5)
offset = randrange(1, 32 - width)
cave.add_exit((offset, 31), (offset + width, 31))
# Cave!
cave.gen_map(mode='room')
cave.print_map()
# Resize
cave.resize_map(48, 48)
cave.print_map()

# del(cave)
#cave = cave_factory.new(32, 32)
#cave.add_exit((offset, 0), (offset+width, 0))
# cave.gen_map()
# cave.print_map()

# for p in cave.iterate_map(cave_factory.FLOOR):
#    print p

# for p in cave.iterate_map(cave_factory.WALL):
#    print p
