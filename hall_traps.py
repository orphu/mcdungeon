import inspect
import random
import sys

import cfg
import materials
from utils import (
    Vec,
    enum,
    iterate_cube,
    get_tile_entity_tags,
    weighted_choice
)

dv = [
    Vec(0, -1, 0),
    Vec(1, 0, 0),
    Vec(0, 1, 0),
    Vec(-1, 0, 0)
]
dirs = enum('N', 'E', 'S', 'W')


class Blank(object):
    _name = 'blank'
    _min_width = 0
    _max_width = 32
    _min_length = 0
    _max_length = 32

    def __init__(self, parent, position, size, length, direction):
        self.parent = parent
        self.position = position
        self.size = size
        self.length = length
        self.direction = direction
        # Set delta width and length vectors based on halleasy direction.
        if direction == dirs.E:
            self.dl = Vec(1, 0, 0)
            self.dw = Vec(0, 0, 1)
        else:
            self.dl = Vec(0, 0, 1)
            self.dw = Vec(1, 0, 0)

    def apply_template(self, tmpl, cmds, mat, reps, pos):
        '''
        Apply a template.
        tmpl = the actual template
        mat = materials lookup
        reps for each template row
        pos = starting position
        '''
        for l in xrange(len(tmpl[0])):
            for rl in xrange(reps['l'][l]):
                for d in xrange(len(tmpl)):
                    repw = 0
                    for w in xrange(len(tmpl[d][l])):
                        for rw in xrange(reps['w'][w]):
                            q = pos + self.dw * repw \
                                    + Vec(0, -1, 0) * d
                            repw += 1
                            if tmpl[d][l][w] == 'XX':
                                continue
                            elif tmpl[d][l][w] == '~T':
                                if random.randint(1, 100) <= 90:
                                    self.parent.setblock(
                                        q,
                                        materials.RedstoneWire,
                                        hide=True
                                    )
                                else:
                                    self.parent.setblock(
                                        q,
                                        materials.TNT,
                                        hide=True
                                    )
                                continue
                            elif (
                                tmpl[d][l][w][0] == '~' and
                                random.randint(1, 100) <= 50
                            ):
                                continue
                            self.parent.setblock(
                                q,
                                mat[tmpl[d][l][w]][0],
                                mat[tmpl[d][l][w]][1],
                                hide=True
                            )
                            if tmpl[d][l][w] in cmds:
                                self.parent.addtileentity(
                                    get_tile_entity_tags(
                                        eid='Control',
                                        Pos=q,
                                        Command=cmds[tmpl[d][l][w]]
                                    )
                                )
                pos += self.dl

    def mark_hallway(self, mat):
        ''' Handy way to mark the location of a hall trap on the map. For
        debugging.'''
        for p in iterate_cube(
            self.position,
            self.position + self.dw * (self.size - 1) + self.dl * (self.length - 1)
        ):
            self.parent.setblock(p, mat)

    def render(self):
        pass


class ArrowTrap(Blank):
    _name = 'arrowtrap'
    _min_width = 3
    _min_length = 3
    _explosions = False

    def render(self):
        # Figure out what sort of thing will be fired
        name = weighted_choice(cfg.master_projectile_traps)
        data_tag = cfg.lookup_projectile_traps[name][2]
        name = cfg.lookup_projectile_traps[name][0]

        # Start position
        pos = self.position.down(5) + self.dl - self.dw

        # Materials lookup
        # Default is looking East
        mat = {
            'RW': [materials.RedstoneWire, 0],
            '*>': [materials.RedstoneRepeaterOff, 2],
            '<*': [materials.RedstoneRepeaterOff, 0],
            'C1': [materials.CommandBlock, 0],
            'C2': [materials.CommandBlock, 0],
            '[]': [materials.StoneBrick, 3],
            '~P': [materials.StonePressurePlate, 0],
            '~T': [materials.TNT, 0],
        }

        # Commands
        cmds = {
            'C1': '/summon {0} ~ ~3 ~1.8 {{Motion:{1},direction:{1},{2}}}'.format(
                name,
                '[0.0,0.2,1.0]',
                data_tag),
            'C2': '/summon {0} ~ ~3 ~-1.8 {{Motion:{1},direction:{1},{2}}}'.format(
                name,
                '[0.0,0.2,-1.0]',
                data_tag)}

        # If looking South, rotate some materials, and adjust the command
        # blocks.
        if self.direction == dirs.S:
            mat['*>'][1] = 1
            mat['<*'][1] = 3
            cmds = {
                'C1': '/summon {0} ~1.8 ~3 ~ {{Motion:{1},direction:{1},{2}}}'.format(
                    name,
                    '[1.0,0.2,0.0]',
                    data_tag),
                'C2': '/summon {0} ~-1.8 ~3 ~ {{Motion:{1},direction:{1},{2}}}'.format(
                    name,
                    '[-1.0,0.2,0.0]',
                    data_tag)}

        # Trap template.
        # tmpl[level][dl][dw]
        tmpl = [[
            ['C1', '<*', 'RW', '*>', 'C2'],
        ], [
            ['XX', 'XX', 'XX', 'XX', 'XX'],
        ], [
            ['XX', 'XX', '~P', 'XX', 'XX'],
        ], [
            ['XX', '[]', 'XX', '[]', 'XX'],
        ]]

        # Make boom!
        if self._explosions:
            tmpl[0][0][2] = '~T'
            tmpl[0][0][0] = '[]'
            tmpl[0][0][4] = '[]'

        # Repetitions for each template row and column.
        reps = {
            'w': [1, 1, self.size - 2, 1, 1],
            'l': [self.length - 2],
        }

        self.apply_template(tmpl, cmds, mat, reps, pos)

        # Vary the timing on the repeaters
        for p in iterate_cube(
            self.position.down(5),
            self.position.down(5) + self.dw * (self.size - 1) + self.dl * (self.length - 1)
        ):
            if (
                p in self.parent.blocks and
                self.parent.blocks[p].material == materials.RedstoneRepeaterOff
            ):
                self.parent.blocks[p].data += random.choice((4, 8, 12))


class ExplodingArrowTrap(ArrowTrap):
    _name = 'explodingarrowtrap'
    _explosions = True

    def render(self):
        super(ExplodingArrowTrap, self).render()


class LavaTrap(Blank):
    _name = 'lavatrap'
    _min_width = 3
    _max_width = 4
    _min_length = 9

    def render(self):
        # Length of the actual trap door part.
        tlength = self.length - 8

        # Materials lookup
        # Default is looking East
        mat = {
            'CC': [materials._ceiling, 0],
            'SF': [materials._subfloor, 0],
            'RW': [materials.RedstoneWire, 0],
            'RB': [materials.BlockOfRedstone, 0],
            '-*': [materials.RedstoneTorchOn, 3],
            '*-': [materials.RedstoneTorchOn, 4],
            'P>': [materials.StickyPiston, 3 + 8],
            '-|': [materials.PistonExtension, 3 + 8],
            '<P': [materials.StickyPiston, 2 + 8],
            '|-': [materials.PistonExtension, 2 + 8],
            'C1': [materials.CommandBlock, 0],
            'C2': [materials.CommandBlock, 0],
            'C3': [materials.CommandBlock, 0],
            'C4': [materials.CommandBlock, 0],
            'C5': [materials.CommandBlock, 0],
            'C6': [materials.CommandBlock, 0],
            'C7': [materials.CommandBlock, 0],
            'C8': [materials.CommandBlock, 0],
            'PP': [materials.StonePressurePlate, 0],
            'AR': [materials.Air, 0],
            'LA': [materials.Lava, 0],
            'ST': [materials.Stone, 0],
        }
        # Commands that open and close the trap.
        cmds = {'C1': '/fill ~2 ~1 ~-1 ~{} ~1 ~-1 minecraft:stone 0 replace'.format(tlength + 1),
                'C2': '/fill ~2 ~1 ~1 ~{} ~1 ~1 minecraft:stone 0 replace'.format(tlength + 1),
                'C3': '/fill ~-2 ~1 ~-1 ~-{} ~1 ~-1 minecraft:stone 0 replace'.format(tlength + 1),
                'C4': '/fill ~-2 ~1 ~1 ~-{} ~1 ~1 minecraft:stone 0 replace'.format(tlength + 1),
                'C5': '/fill ~2 ~0 ~0 ~{} ~0 ~0 minecraft:redstone_block 0 replace'.format(tlength + 1),
                'C6': '/fill ~2 ~0 ~0 ~{} ~0 ~0 minecraft:redstone_block 0 replace'.format(tlength + 1),
                'C7': '/fill ~-2 ~0 ~0 ~-{} ~0 ~0 minecraft:redstone_block 0 replace'.format(tlength + 1),
                'C8': '/fill ~-2 ~0 ~0 ~-{} ~0 ~0 minecraft:redstone_block 0 replace'.format(tlength + 1),
                }

        # If looking South, rotate some materials, and adjust the command
        # blocks.
        if self.direction == dirs.S:
            mat['-*'][1] = 1
            mat['*-'][1] = 2
            mat['P>'][1] = 5 + 8
            mat['-|'][1] = 5 + 8
            mat['<P'][1] = 4 + 8
            mat['|-'][1] = 4 + 8
            cmds = {'C1': '/fill ~-1 ~1 ~2 ~-1 ~1 ~{} minecraft:stone 0 replace'.format(tlength + 1),
                    'C2': '/fill ~1 ~1 ~2 ~1 ~1 ~{} minecraft:stone 0 replace'.format(tlength + 1),
                    'C3': '/fill ~-1 ~1 ~-2 ~-1 ~1 ~-{} minecraft:stone 0 replace'.format(tlength + 1),
                    'C4': '/fill ~1 ~1 ~-2 ~1 ~1 ~-{} minecraft:stone 0 replace'.format(tlength + 1),
                    'C5': '/fill ~0 ~0 ~2 ~0 ~0 ~{} minecraft:redstone_block 0 replace'.format(tlength + 1),
                    'C6': '/fill ~0 ~0 ~2 ~0 ~0 ~{} minecraft:redstone_block 0 replace'.format(tlength + 1),
                    'C7': '/fill ~0 ~0 ~-2 ~0 ~0 ~-{} minecraft:redstone_block 0 replace'.format(tlength + 1),
                    'C8': '/fill ~0 ~0 ~-2 ~0 ~0 ~-{} minecraft:redstone_block 0 replace'.format(tlength + 1),
                    }

        # Trap template.
        # tmpl[level][dl][dw]
        tmpl = [[
            ['SF', 'SF', 'SF', 'SF', 'SF', 'SF'],
            ['SF', 'SF', 'LA', 'LA', 'SF', 'SF'],
            ['SF', 'SF', 'LA', 'LA', 'SF', 'SF'],
            ['SF', 'SF', 'LA', 'LA', 'SF', 'SF'],
            ['SF', 'SF', 'SF', 'SF', 'SF', 'SF'],
        ], [
            ['*-', 'C1', 'XX', 'XX', 'C2', '-*'],
            ['AR', 'RW', 'XX', 'XX', 'RW', 'AR'],
            ['P>', '-|', 'XX', 'XX', '|-', '<P'],
            ['AR', 'RW', 'XX', 'XX', 'RW', 'AR'],
            ['*-', 'C3', 'XX', 'XX', 'C4', '-*'],
        ], [
            ['C5', 'XX', 'XX', 'XX', 'XX', 'C6'],
            ['ST', 'XX', 'PP', 'PP', 'XX', 'ST'],
            ['RB', 'XX', 'XX', 'XX', 'XX', 'RB'],
            ['ST', 'XX', 'PP', 'PP', 'XX', 'ST'],
            ['C7', 'XX', 'XX', 'XX', 'XX', 'C8'],
        ]]
        # Repetitions for each template row and column.
        reps = {
            'w': [1, 1, 1, 1, 1, 1],
            'l': [1, 1, tlength, 1, 1],
        }
        # Starting position. Always the NW corner.
        pos = self.position.down(5) - self.dw + self.dl * 2

        # 1 width hallway
        if self.size < 4:
            tmpl = [[e[:3] for e in d] for d in tmpl]

        self.apply_template(tmpl, cmds, mat, reps, pos)


class Portcullis(Blank):
    _name = 'portcullis'
    _min_width = 5
    _min_length = 7

    def render(self):
        pos = self.position.down(4) \
            - self.dw * 2 \
            + self.dl * (random.randint(0, max(0, self.length - 7)))

        mat = {
            'RW': [materials.RedstoneWire, 0],
            '^^': [materials.RedstoneRepeaterOff, 1 + 12],
            ']]': [materials.WoodenButton, 3],
            '[[': [materials.WoodenButton, 4],
            'C1': [materials.CommandBlock, 0],
            'C2': [materials.CommandBlock, 0],
            'oo': [materials.Fence, 0],
            'C3': [materials.CommandBlock, 0],
            'C4': [materials.CommandBlock, 0],
            'C5': [materials.CommandBlock, 0],
            'C6': [materials.CommandBlock, 0],
            'WA': [materials._wall, 0],
        }

        # Random gate material.
        gate = random.choice((
            (materials.Fence, 'fence'),
            (materials.NetherBrickFence, 'nether_brick_fence'),
            (materials.IronBars, 'iron_bars'),
            (materials.CobblestoneWall, 'cobblestone_wall'),
        ))
        mat['oo'][0] = gate[0]

        cmds = {
            'C1': '/playsound minecraft:block.piston.contract blocks @p',
            'C2': '/playsound minecraft:block.piston.extend blocks @p',
            'C3': '/fill ~-2 ~2 ~2 ~-2 ~2 ~{} minecraft:{} 0 replace'.format(self.size - 1, gate[1]),
            'C4': '/fill ~-2 ~0 ~2 ~-2 ~0 ~{} minecraft:{} 0 replace'.format(self.size - 1, gate[1]),
            'C5': '/fill ~-2 ~1 ~-2 ~-2 ~1 ~-{} minecraft:air 0 replace'.format(self.size - 1),
        }

        tmpl = [[
            ['XX', 'XX', 'RW', 'XX', 'XX', 'XX', 'RW', 'XX', 'XX'],
            ['XX', 'RW', 'RW', 'XX', 'XX', 'XX', 'RW', 'RW', 'XX'],
            ['XX', '^^', 'RW', 'XX', 'XX', 'XX', 'RW', '^^', 'XX'],
            ['C1', 'C3', 'C2', 'XX', 'XX', 'XX', 'C2', 'C5', 'C1'],
        ], [
            ['XX', 'XX', 'WA', ']]', 'XX', '[[', 'WA', 'XX', 'XX'],
            ['XX', 'XX', 'XX', 'oo', 'oo', 'oo', 'XX', 'XX', 'XX'],
            ['XX', 'XX', 'WA', ']]', 'XX', '[[', 'WA', 'XX', 'XX'],
            ['XX', 'C4', 'XX', 'XX', 'XX', 'XX', 'XX', 'C5', 'XX'],
        ], [
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
            ['XX', 'XX', 'XX', 'oo', 'oo', 'oo', 'XX', 'XX', 'XX'],
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
        ], [
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
            ['XX', 'XX', 'XX', 'oo', 'oo', 'oo', 'XX', 'XX', 'XX'],
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
        ], [
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
            ['XX', 'XX', 'XX', 'oo', 'oo', 'oo', 'XX', 'XX', 'XX'],
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
            ['XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
        ]]

        reps = {
            'w': [1, 1, 1, 1, self.size - 4, 1, 1, 1, 1],
            'l': [1, 1, 1, 1],
        }

        if self.direction == dirs.S:
            mat[']]'][1] = 1
            mat['[['][1] = 2
            mat['^^'][1] = 2 + 12
            cmds[
                'C3'] = '/fill ~2 ~2 ~-2 ~{} ~2 ~-2 minecraft:{} 0 replace'.format(self.size - 1, gate[1])
            cmds[
                'C4'] = '/fill ~2 ~0 ~-2 ~{} ~0 ~-2 minecraft:{} 0 replace'.format(self.size - 1, gate[1])
            cmds[
                'C5'] = '/fill ~-2 ~1 ~-2 ~-{} ~1 ~-2 minecraft:air 0 replace'.format(self.size - 1)

        self.apply_template(tmpl, cmds, mat, reps, pos)

# Catalog the halls we know about.
_hall_traps = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses if of hall_traps.Blank
    if issubclass(obj, Blank):
        _hall_traps[obj._name] = obj


def new(name, parent, position, size, length, direction):
    '''Return a new instance of the trap of a given name. Supply the parent
    hall object.'''
    if name in _hall_traps.keys():
        return _hall_traps[name](parent, position, size, length, direction)
    return Blank(parent, position, size, length, direction)
