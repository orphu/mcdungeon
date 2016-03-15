from copy import copy
import inspect
import math
import random
import sys

import cave_factory
import cfg
import items
import materials
import perlin
from pymclevel import nbt
from utils import (
    findChunkDepths,
    get_entity_mob_tags,
    get_entity_other_tags,
    get_entity_item_tags,
    iterate_cube,
    iterate_cylinder,
    iterate_disc,
    iterate_ellipse,
    iterate_four_walls,
    iterate_spiral,
    iterate_tube,
    Vec,
    Vec2f,
    weighted_choice,
)

_desert_biomes = (2, 17, 130)
_ice_biomes = (140, 12)
_mesa_biomes = (37, 38, 39, 165, 166, 167)
_swamp_jungle_biomes = (6, 21, 22, 23, 149, 151)


class Blank(object):
    _name = 'blank'
    _dnamesA = (
        ('', 10),
        ('Abysmal ', 10),
        ('Accursed ', 10),
        ('Ancient ', 10),
        ('Bitter ', 10),
        ('Black ', 10),
        ('Bleak ', 10),
        ('Brutal ', 10),
        ('Corrupt ', 10),
        ('Crooked ', 10),
        ('Cruel ', 10),
        ('Crumbling ', 10),
        ('Cursed ', 10),
        ('Dark ', 10),
        ('Decayed ', 10),
        ('Defiled ', 10),
        ('Devious ', 10),
        ('Deep ', 10),
        ('Dim ', 10),
        ('Dire ', 10),
        ('Dusk ', 10),
        ('Endless ', 10),
        ('Evil ', 10),
        ('Faded ', 10),
        ('Fallen ', 10),
        ('Forbidden ', 10),
        ('Forgotten ', 10),
        ('Forsaken ', 10),
        ('Foul ', 10),
        ('Grey ', 10),
        ('Grievous ', 10),
        ('Grim ', 10),
        ('Grizzly ', 10),
        ('Harrowing ', 10),
        ('Harsh ', 10),
        ('Hoary ', 10),
        ('Haunted ', 10),
        ('Hidden ', 10),
        ('Howling ', 10),
        ('Infernal ', 10),
        ('Lost ', 10),
        ('Low ', 10),
        ('Miasmic ', 10),
        ('Misty ', 10),
        ('Mouldering ', 10),
        ('Mysterious ', 10),
        ('Murderous ', 10),
        ('Murky ', 10),
        ('Oppressive ', 10),
        ('Putrid ', 10),
        ('Rotting ', 10),
        ('Ruined ', 10),
        ('Serpentine ', 10),
        ('Shadow ', 10),
        ('Sunken ', 10),
        ('Tainted ', 10),
        ('Torturous ', 10),
        ('Vicious ', 10),
        ('Vile ', 10),
        ('Wailing ', 10),
        ('Wicked ', 10),
        ('Wretched ', 10),
        ('Whispering ', 10),
    )
    _dnamesB = (
        ('{A}Catacombs', 3),
        ('{A}Crypt', 1),
        ('{{owners}} Crypt', 1),
        ('Crypt of {{owner}}', 1),
        ('{A}Dungeon', 3),
        ('{A}Fortress', 1),
        ('{{owners}} Fortress', 1),
        ('Fortress of {{owner}}', 1),
        ('{{owners}} Hall', 3),
        ('{A}Keep', 1),
        ('{{owners}} Keep', 1),
        ('{A}Mines', 3),
        ('{A}Ruins', 3),
        ('{A}Temple', 1),
        ('{{owners}} Temple', 1),
        ('Temple to {{owner}}', 1),
        ('{A}Tomb', 1),
        ('{{owners}} Tomb', 1),
        ('Tomb of {{owner}}', 1),
    )

    def __init__(self, parent):
        self.parent = parent
        self.pos = copy(parent.pos)
        cx = (parent.parent.position.x + parent.loc.x) >> 4
        cz = (parent.parent.position.z + parent.loc.z) >> 4
        self.chunk = Vec(cx, 0, cz)
        # print 'ruin chunk:', self.chunk

    def placed(self, world):
        self.depth = self.parent.parent.good_chunks[(
            self.chunk.x,
            self.chunk.z
        )]
        self.vtrans = max(
            self.parent.parent.position.y - 1,
            self.depth
        ) - self.parent.parent.position.y
        self.loc = Vec(self.pos.x * self.parent.parent.room_size,
                       -self.vtrans,
                       self.pos.z * self.parent.parent.room_size)
        self.setData()

    @classmethod
    def nameDungeon(self):
        # Name this place
        A = weighted_choice(self._dnamesA)
        name = weighted_choice(self._dnamesB).format(A=A)
        return name

    def setData(self):
        pass

    def render(self):
        pass


class EvilRunestones(Blank):
    _name = 'evilrunestones'
    _dnamesB = (
        ('{A}Gates', 2),
        ('{A}Pillars', 2),
        ('{A}Pit', 2),
        ('{A}Runestones', 2),
        ('{A}Stones', 2),
        ('{A}Teeth', 2),
    )

    def render(self):
        # For most of this one, we render directly to the chunk structure.
        # This works out better in the end.
        height = int(self.parent.parent.room_height * cfg.tower)
        # This chunk
        cx = (self.parent.parent.position.x + self.parent.loc.x) >> 4
        cz = (self.parent.parent.position.z + self.parent.loc.z) >> 4
        chunk = self.parent.parent.world.getChunk(cx, cz)
        # dungeon y
        dy = self.parent.parent.position.y
        # Noise function
        pn = perlin.SimplexNoise(256)

        # Replacement setblock function.
        def sb(p, mat, chunk=chunk):
            chunk.Blocks[p.x, p.z, p.y] = mat.val
            chunk.Data[p.x, p.z, p.y] = mat.data

        # Height of the runestones
        runes = {}
        for x in xrange(16):
            for z in xrange(16):
                runes[x, z] = random.randint(height / 2, height)
        # Iterate over the chunk
        for x in xrange(16):
            for z in xrange(16):
                # find the height at this block
                y = chunk.HeightMap[z, x]
                while (
                    y > 0 and
                    chunk.Blocks[x, z, y] not in materials.heightmap_solids
                ):
                    y = y - 1
                q = Vec(x, y, z)
                # create a chest
                if (x == 2 and z == 2):
                    cp = Vec(cx * 16 + x - self.parent.parent.position.x,
                             self.parent.parent.position.y - y - 1,
                             cz * 16 + z - self.parent.parent.position.z)
                    self.parent.parent.setblock(cp, materials.Chest)
                    self.parent.parent.addchest(cp, 0)
                    # The portal exit point is here
                    self.parent.parent.dinfo['portal_exit'] = cp.up(2)

                    for r in iterate_cube(q.down(2), q.trans(0, height, 0)):
                        sb(r, materials.Air)
                    continue
                # If we are above the entrance, clear the air and continue
                if (x >= 6 and x <= 9 and z >= 6 and z <= 9):
                    for r in iterate_cube(
                        Vec(q.x, dy, q.z),
                        q.trans(0, height, 0)
                    ):
                        sb(r, materials.Air)
                    continue
                # Draw some creeping Netherrack and SoulSand.
                # Clear the air above
                for r in iterate_cube(q.down(1), q.trans(0, height, 0)):
                    if chunk.Blocks[r.x, r.z, r.y] != materials.Obsidian.val:
                        sb(r, materials.Air)
                d = ((Vec2f(q.x, q.z) - Vec2f(7, 7)).mag()) / 16
                n = (pn.noise3(q.x / 4.0, 0, q.z / 4.0) + 1.0) / 2.0
                if (n >= d + .20):
                    sb(q, materials.Netherrack)
                    # Netherrack might be on fire!
                    if random.randint(1, 100) <= 5:
                        sb(q.down(1), materials.Fire)
                elif (n > d):
                    sb(q, materials.SoulSand)
                # We are on an edge. Draw a runestone.
                # N/S edges
                if ((x == 0 or x == 15) and z >= 3 and z <= 9 and z % 3 == 0):
                    h = runes[x, z]
                    for r in iterate_cube(q, q.trans(0, h, 0)):
                        sb(r, materials.Obsidian)
                    for r in iterate_cube(q.trans(0, h, 0), q.trans(0, h, 3)):
                        sb(r, materials.Obsidian)
                    for r in iterate_cube(q.trans(0, 0, 3), q.trans(0, h, 3)):
                        sb(r, materials.Obsidian)
                # E/W edges
                if ((z == 0 or z == 15) and x >= 3 and x <= 9 and x % 3 == 0):
                    h = runes[x, z]
                    for r in iterate_cube(q, q.trans(0, h, 0)):
                        sb(r, materials.Obsidian)
                    for r in iterate_cube(q.trans(0, h, 0), q.trans(3, h, 0)):
                        sb(r, materials.Obsidian)
                    for r in iterate_cube(q.trans(3, 0, 0), q.trans(3, h, 0)):
                        sb(r, materials.Obsidian)


class StepPyramid(Blank):
    _name = 'steppyramid'
    _dnamesB = (
        ('{A}Catacombs', 3),
        ('{A}Ruins', 3),
        ('{A}Temple', 1),
        ('{{owners}} Temple', 1),
        ('Temple to {{owner}}', 1),
        ('{A}Tomb', 1),
        ('{{owners}} Tomb', 1),
        ('Tomb of {{owner}}', 1),
        ('{A}Pyramid', 1),
        ('{{owners}} Pyramid', 1),
        ('Pyramid of {{owner}}', 1),
    )

    def setData(self):
        # The StepPyramid will be 4x4 chunks.
        # Figure out if we have to move West or North to fit.
        xsize = self.parent.parent.xsize
        zsize = self.parent.parent.zsize
        self.spos = copy(self.pos)
        while self.spos.x > xsize - 4:
            self.spos.x -= 1
        while self.spos.z > zsize - 4:
            self.spos.z -= 1
        # Now go through and override the ruins on any chunks we cover
        # to be blank.
        for p in iterate_cube(Vec(self.spos.x, 0, self.spos.z),
                              Vec(self.spos.x + 3, 0, self.spos.z + 3)):
            if p == self.pos:
                continue
            blank = new('blank', self.parent.parent.rooms[p])
            self.parent.parent.rooms[p].ruins = [blank]
        # Find the low point in this region
        for p in iterate_cube(Vec(self.spos.x, 0, self.spos.z),
                              Vec(self.spos.x + 3, 0, self.spos.z + 3)):
            cx = (self.parent.parent.position.x >> 4) + p.x
            cz = (self.parent.parent.position.z >> 4) + p.z
            self.depth = min(self.depth,
                             self.parent.parent.good_chunks[(cx, cz)])
        self.depth = max(self.depth, 62, self.parent.parent.position.y)
        self.vtrans = self.depth - self.parent.parent.position.y + 1
        self.loc = Vec(self.spos.x * self.parent.parent.room_size,
                       -self.vtrans,
                       self.spos.z * self.parent.parent.room_size)
        # Figure out how high the entrances should be.
        # min is 2, max is 22.
        cx = self.parent.parent.position.x >> 4
        cz = self.parent.parent.position.z >> 4
        world = self.parent.parent.world
        # N side
        (low1, high1) = findChunkDepths(Vec(cx, 0, cz + 1), world)
        (low2, high2) = findChunkDepths(Vec(cx, 0, cz + 2), world)
        self.ent_n = min(
            22, max(
                1, high1 - self.depth, high2 - self.depth) + 1)
        # S side
        (low1, high1) = findChunkDepths(Vec(cx + 3, 0, cz + 1), world)
        (low2, high2) = findChunkDepths(Vec(cx + 3, 0, cz + 2), world)
        self.ent_s = min(
            22, max(
                1, high1 - self.depth, high2 - self.depth) + 1)
        # E side
        (low1, high1) = findChunkDepths(Vec(cx + 1, 0, cz + 3), world)
        (low2, high2) = findChunkDepths(Vec(cx + 2, 0, cz + 3), world)
        self.ent_e = min(
            22, max(
                1, high1 - self.depth, high2 - self.depth) + 1)
        # W side
        (low1, high1) = findChunkDepths(Vec(cx + 1, 0, cz), world)
        (low2, high2) = findChunkDepths(Vec(cx + 2, 0, cz), world)
        self.ent_w = min(
            22, max(
                1, high1 - self.depth, high2 - self.depth) + 1)

    def render(self):
        # Biome materials
        if self.parent.parent.biome in _desert_biomes:
            mat_ext = materials.SmoothSandstone
            mat_block = materials.meta_decoratedsandstone
            mat_ruins = materials.meta_decoratedsandstone
            mat_stair = materials.SandstoneStairs
            mat_slab = materials.SandstoneSlab
            mat_floor = materials.Sand
        elif self.parent.parent.biome in _ice_biomes:
            mat_ext = materials.PackedIce
            mat_block = materials.Ice
            mat_ruins = materials.PackedIce
            mat_stair = materials.QuartzStairs
            mat_slab = materials.QuartzSlab
            mat_floor = materials.PackedIce
        elif self.parent.parent.biome in _mesa_biomes:
            mat_ext = materials.SmoothRedSandstone
            mat_block = materials.meta_decoratedredsandstone
            mat_ruins = materials.meta_decoratedredsandstone
            mat_stair = materials.RedSandstoneStairs
            mat_slab = materials.RedSandstoneSlab
            mat_floor = materials.RedSand
        elif self.parent.parent.biome in _swamp_jungle_biomes:
            mat_ext = materials.meta_mossycobble
            mat_block = materials.meta_mossycobble
            mat_ruins = materials.meta_mossystonebrick
            mat_stair = materials.StoneStairs
            mat_slab = materials.StoneBrickSlab
            mat_floor = materials.Stone
        else:
            mat_ext = materials.meta_mossystonebrick
            mat_block = materials.meta_mossystonebrick
            mat_ruins = materials.meta_mossystonebrick
            mat_stair = materials.StoneBrickStairs
            mat_slab = materials.StoneSlab
            mat_floor = materials.Stone

        c1 = self.loc
        c3 = c1 + Vec(self.parent.parent.room_size * 4 - 1,
                      0,
                      self.parent.parent.room_size * 4 - 1)
        # corner of the inner shaft
        start = Vec(self.parent.loc.x + 5,
                    c1.y,
                    self.parent.loc.z + 5)
        # Walls and airspace of the pyramid
        for y in xrange(29):
            for p in iterate_cube(c1.trans(y + 1, -y, y + 1),
                                  c3.trans(-y - 1, -y, -y - 1)):
                self.parent.parent.setblock(p, materials.Air)
            for p in iterate_four_walls(c1.trans(y, -y, y),
                                        c3.trans(-y, -y, -y), 0):
                self.parent.parent.setblock(p, mat_ext)
                # In swamp/jungle the steps are extra steppy.
                if (
                    y % 2 == 0 and
                    self.parent.parent.biome in _swamp_jungle_biomes
                ):
                    self.parent.parent.setblock(p.up(1), mat_ext)
        # Floor. From pyramid base to just above ceiling.
        for p in iterate_four_walls(c1,
                                    c3, c1.y):
            self.parent.parent.setblock(p, mat_ext, hide=True)
        # Cover the floor with stuff
        pn = perlin.SimplexNoise(256)
        for p in iterate_cube(c1, c3):
            d = ((Vec2f(p.x, p.z) - Vec2f(c1.x + 32, c1.z + 32)).mag()) / 64
            n = (pn.noise3(p.x / 4.0, p.y / 4.0, p.z / 4.0) + 1.0) / 2.0
            if (n >= d + .20):
                self.parent.parent.setblock(p, mat_floor)
            elif (n >= d + .10):
                self.parent.parent.setblock(p, mat_ruins)
            elif (n >= d):
                self.parent.parent.setblock(p, materials.Gravel)
            else:
                self.parent.parent.setblock(p, mat_block)
        # Build internal ruins.
        cchance = 80
        for p in iterate_cube(Vec(0, 0, 0), Vec(3, 0, 3)):
            wfunc = iterate_four_walls
            if random.randint(1, 100) <= 50:
                wfunc = iterate_tube
            pp1 = c1.trans(p.x * 16 + 1, 0, p.z * 16 + 1)
            pp2 = pp1.trans(13, 0, 13)
            # place a chest here
            if random.randint(1, 100) <= cchance:
                cchance /= 5
                cp = pp1.trans(3, -1, 3)
                if random.randint(1, 100) <= 50:
                    self.parent.parent.setblock(cp, materials.Chest)
                    self.parent.parent.addchest(cp, 0)
                else:
                    self.parent.parent.setblock(cp, materials.Spawner)
                    self.parent.parent.addspawner(cp, tier=0)
            height = 5
            for j in wfunc(pp1, pp2, 0):
                depth = (pn.noise3(j.x / 4.0,
                                   0,
                                   j.z / 4.0) + 1.0) / 2.0 * height
                for x in iterate_cube(j, j.up(depth)):
                    if (
                        x in self.parent.parent.blocks and
                        self.parent.parent.blocks[x].material == materials.Air
                    ):
                        self.parent.parent.setblock(x, mat_ruins)

        # Clean up the stairwell shaft. Clear the air, make a half step around
        # it, extend the walls, and redraw the stairs.
        self.parent.parent.entrance.height = abs(-c1.y - 2) + 2
        for p in iterate_cube(start, start.trans(5, -c1.y - 1, 5)):
            self.parent.parent.setblock(p, materials.Air)
        for p in iterate_four_walls(Vec(start.x, -1, start.z),
                                    Vec(start.x + 5, -1, start.z + 5), -c1.y - 2):
            self.parent.parent.setblock(p, materials._wall)
        for p in iterate_four_walls(start, start.trans(5, 0, 5), 0):
            self.parent.parent.setblock(p, materials.StoneSlab)
        mat = materials.OakWoodSlab
        if random.randint(1, 100) <= 50:
            mat = materials.StoneSlab
        for p in iterate_spiral(Vec(start.x + 1, 7, start.z + 1),
                                Vec(start.x + 5, 7, start.z + 5),
                                (abs(c1.y) + 3) * 2):
            self.parent.parent.setblock(
                Vec(p.x, 0 + int(p.y / 2), p.z), mat, mat.data + ((p.y & 1) ^ 1) * 8)
        # Entrances.
        # Draw stairs up the sides.
        for y in xrange(29):
            # North Side
            # caps on either side
            self.parent.parent.setblock(c1.trans(y, -y - 1, 29), mat_slab)
            self.parent.parent.setblock(c1.trans(y, -y - 1, 34), mat_slab)
            # draw different stuff depending on the height
            # Go ahead and draw exterior stairs at every level.
            # (we'll overwrite some below)
            for p in iterate_cube(c1.trans(y, -y, 30),
                                  c1.trans(y, -y, 33)):
                self.parent.parent.setblock(p,
                                            mat_stair, 0)
                self.parent.parent.delblock(p.up(1))
                self.parent.parent.setblock(p.trans(1, 0, 0),
                                            mat_block)
            # Above floor, but below entry level,
            # draw the interior stairs and airspace.
            if (y > 0 and y <= self.ent_n):
                for p in iterate_cube(c1.trans(y, -y, 28),
                                      c1.trans(y, -y, 35)):
                    for x in xrange(2, 6):
                        self.parent.parent.setblock(p.trans(x, 0, 0),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(6, 0, 0),
                                                mat_stair, 0)
                    self.parent.parent.setblock(p.trans(7, 0, 0),
                                                mat_block, 0)
            # At entry level, draw a platform floor.
            if (self.ent_n == y):
                for p in iterate_cube(c1.trans(y + 1, -y, 30),
                                      c1.trans(y + 8, -y, 33)):
                    self.parent.parent.setblock(p, mat_block)
            # Above the entry platform, draw some walls
            if (y > self.ent_n and y < self.ent_n + 4):
                p = c1.trans(y, -y, 30)
                self.parent.parent.setblock(p, mat_block)
                self.parent.parent.setblock(p.trans(1, 0, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 0, 1), materials.Air)
                self.parent.parent.setblock(p.trans(1, 0, 1), materials.Air)
                self.parent.parent.setblock(p.trans(0, 0, 2), materials.Air)
                self.parent.parent.setblock(p.trans(1, 0, 2), materials.Air)
                self.parent.parent.setblock(p.trans(0, 0, 3), mat_block)
                self.parent.parent.setblock(p.trans(1, 0, 3), mat_block)
            # Add a ceiling for the entryway.
            if (y == self.ent_n + 4):
                p = c1.trans(y - 3, -y, 30)
                self.parent.parent.setblock(p.trans(1, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 2, 0), mat_block)
                p = c1.trans(y - 3, -y, 33)
                self.parent.parent.setblock(p.trans(1, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 2, 0), mat_block)
                for p in iterate_cube(c1.trans(y - 3, -y, 30),
                                      c1.trans(y + 1, -y, 33)):
                    self.parent.parent.setblock(p, mat_block)

            # South Side
            self.parent.parent.setblock(c1.trans(63 - y, -y - 1, 29), mat_slab)
            self.parent.parent.setblock(c1.trans(63 - y, -y - 1, 34), mat_slab)
            for p in iterate_cube(c1.trans(63 - y, -y, 30),
                                  c1.trans(63 - y, -y, 33)):
                self.parent.parent.setblock(p,
                                            mat_stair, 1)
                self.parent.parent.delblock(p.up(1))
                self.parent.parent.setblock(p.trans(-1, 0, 0),
                                            mat_block, 0)
            if (y > 0 and y <= self.ent_s):
                for p in iterate_cube(c1.trans(63 - y, -y, 28),
                                      c1.trans(63 - y, -y, 35)):
                    for x in xrange(2, 6):
                        self.parent.parent.setblock(p.trans(-x, 0, 0),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(-6, 0, 0),
                                                mat_stair, 1)
                    self.parent.parent.setblock(p.trans(-7, 0, 0),
                                                mat_block, 0)
            if (self.ent_s == y):
                for p in iterate_cube(c1.trans(63 - y - 1, -y, 30),
                                      c1.trans(63 - y - 8, -y, 33)):
                    self.parent.parent.setblock(p, mat_block)
            if (y > self.ent_s and y < self.ent_s + 4):
                p = c1.trans(63 - y, -y, 30)
                self.parent.parent.setblock(p, mat_block)
                self.parent.parent.setblock(p.trans(-1, 0, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 0, 1), materials.Air)
                self.parent.parent.setblock(p.trans(-1, 0, 1), materials.Air)
                self.parent.parent.setblock(p.trans(0, 0, 2), materials.Air)
                self.parent.parent.setblock(p.trans(-1, 0, 2), materials.Air)
                self.parent.parent.setblock(p.trans(0, 0, 3), mat_block)
                self.parent.parent.setblock(p.trans(-1, 0, 3), mat_block)
            if (y == self.ent_s + 4):
                p = c1.trans(63 - y + 3, -y, 30)
                self.parent.parent.setblock(p.trans(-1, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 2, 0), mat_block)
                p = c1.trans(63 - y + 3, -y, 33)
                self.parent.parent.setblock(p.trans(-1, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 2, 0), mat_block)
                for p in iterate_cube(c1.trans(63 - y + 3, -y, 30),
                                      c1.trans(63 - y - 1, -y, 33)):
                    self.parent.parent.setblock(p, mat_block)

            # West Side
            self.parent.parent.setblock(c1.trans(29, -y - 1, y), mat_slab)
            self.parent.parent.setblock(c1.trans(34, -y - 1, y), mat_slab)
            for p in iterate_cube(c1.trans(30, -y, y),
                                  c1.trans(33, -y, y)):
                self.parent.parent.setblock(p, mat_stair, 2)
                self.parent.parent.delblock(p.up(1))
                self.parent.parent.setblock(p.trans(0, 0, 1),
                                            mat_block, 0)
            if (y > 0 and y <= self.ent_w):
                for p in iterate_cube(c1.trans(28, -y, y),
                                      c1.trans(35, -y, y)):
                    for x in xrange(2, 6):
                        self.parent.parent.setblock(p.trans(0, 0, x),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(0, 0, 6),
                                                mat_stair, 2)
                    self.parent.parent.setblock(p.trans(0, 0, 7),
                                                mat_block, 0)
            if (self.ent_w == y):
                for p in iterate_cube(c1.trans(30, -y, y + 1),
                                      c1.trans(33, -y, y + 8)):
                    self.parent.parent.setblock(p, mat_block)
            if (y > self.ent_w and y < self.ent_w + 4):
                p = c1.trans(30, -y, y)
                self.parent.parent.setblock(p, mat_block)
                self.parent.parent.setblock(p.trans(0, 0, 1), mat_block)
                self.parent.parent.setblock(p.trans(1, 0, 0), materials.Air)
                self.parent.parent.setblock(p.trans(1, 0, 1), materials.Air)
                self.parent.parent.setblock(p.trans(2, 0, 0), materials.Air)
                self.parent.parent.setblock(p.trans(2, 0, 1), materials.Air)
                self.parent.parent.setblock(p.trans(3, 0, 0), mat_block)
                self.parent.parent.setblock(p.trans(3, 0, 1), mat_block)
            if (y == self.ent_w + 4):
                p = c1.trans(30, -y, y - 3)
                self.parent.parent.setblock(p.trans(0, 1, 1), mat_block)
                self.parent.parent.setblock(p.trans(0, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 2, 0), mat_block)
                p = c1.trans(33, -y, y - 3)
                self.parent.parent.setblock(p.trans(0, 1, 1), mat_block)
                self.parent.parent.setblock(p.trans(0, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 2, 0), mat_block)
                for p in iterate_cube(c1.trans(30, -y, y - 3),
                                      c1.trans(33, -y, y + 1)):
                    self.parent.parent.setblock(p, mat_block)

            # East Side
            self.parent.parent.setblock(c1.trans(29, -y - 1, 63 - y), mat_slab)
            self.parent.parent.setblock(c1.trans(34, -y - 1, 63 - y), mat_slab)
            for p in iterate_cube(c1.trans(30, -y, 63 - y),
                                  c1.trans(33, -y, 63 - y)):
                self.parent.parent.setblock(p,
                                            mat_stair, 3)
                self.parent.parent.delblock(p.up(1))
                self.parent.parent.setblock(p.trans(0, 0, -1),
                                            mat_block, 0)
            if (y > 0 and y <= self.ent_e):
                for p in iterate_cube(c1.trans(28, -y, 63 - y),
                                      c1.trans(35, -y, 63 - y)):
                    for x in xrange(2, 6):
                        self.parent.parent.setblock(p.trans(0, 0, -x),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(0, 0, -6),
                                                mat_stair, 3)
                    self.parent.parent.setblock(p.trans(0, 0, -7),
                                                mat_block, 0)
            if (self.ent_e == y):
                for p in iterate_cube(c1.trans(30, -y, 63 - y - 1),
                                      c1.trans(33, -y, 63 - y - 8)):
                    self.parent.parent.setblock(p, mat_block)
            if (y > self.ent_e and y < self.ent_e + 4):
                p = c1.trans(30, -y, 63 - y)
                self.parent.parent.setblock(p, mat_block)
                self.parent.parent.setblock(p.trans(0, 0, -1), mat_block)
                self.parent.parent.setblock(p.trans(1, 0, 0), materials.Air)
                self.parent.parent.setblock(p.trans(1, 0, -1), materials.Air)
                self.parent.parent.setblock(p.trans(2, 0, 0), materials.Air)
                self.parent.parent.setblock(p.trans(2, 0, -1), materials.Air)
                self.parent.parent.setblock(p.trans(3, 0, 0), mat_block)
                self.parent.parent.setblock(p.trans(3, 0, -1), mat_block)
            if (y == self.ent_e + 4):
                p = c1.trans(30, -y, 63 - y + 3)
                self.parent.parent.setblock(p.trans(0, 1, -1), mat_block)
                self.parent.parent.setblock(p.trans(0, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 2, 0), mat_block)
                p = c1.trans(33, -y, 63 - y + 3)
                self.parent.parent.setblock(p.trans(0, 1, -1), mat_block)
                self.parent.parent.setblock(p.trans(0, 1, 0), mat_block)
                self.parent.parent.setblock(p.trans(0, 2, 0), mat_block)
                for p in iterate_cube(c1.trans(30, -y, 63 - y + 3),
                                      c1.trans(33, -y, 63 - y - 1)):
                    self.parent.parent.setblock(p, mat_block)

        # Topper
        # Deserts have a fancy glass tipped pyramid
        if (
            self.parent.parent.biome in _desert_biomes or
            self.parent.parent.biome in _mesa_biomes
        ):
            # Orange glass in mesas
            if (self.parent.parent.biome in _mesa_biomes):
                topperglass = materials.OrangeStainedGlass
            else:
                topperglass = materials.Glass
            for y in xrange(29, 33):
                for p in iterate_cube(c1.trans(y, -y, y),
                                      c3.trans(-y, -y, -y)):
                    self.parent.parent.setblock(p, materials.Air)
                for p in iterate_four_walls(c1.trans(y - 1, -y, y - 1),
                                            c3.trans(-y + 1, -y, -y + 1), 0):
                    self.parent.parent.setblock(p, topperglass)
            for p in iterate_cube(c1.trans(29, -28, 29),
                                  c3.trans(-29, -28, -29)):
                self.parent.parent.setblock(p, mat_block)
            for p in iterate_cube(c1.trans(32, -31, 32),
                                  c3.trans(-32, -28, -32)):
                self.parent.parent.setblock(p, materials.Air)
            # holes in the glass
            for p in iterate_cube(c1.trans(32, -30, 28),
                                  c3.trans(-32, -29, -28)):
                self.parent.parent.setblock(p, materials.Air)
            for p in iterate_cube(c1.trans(28, -30, 32),
                                  c3.trans(-28, -29, -32)):
                self.parent.parent.setblock(p, materials.Air)
                # Spires
            if self.parent.parent.biome in _desert_biomes:
                for y in xrange(6):
                    self.parent.parent.setblock(c1.trans(20, -20 - y, 20),
                                                materials.ChiseledSandstone)
                    self.parent.parent.setblock(c1.trans(43, -20 - y, 20),
                                                materials.ChiseledSandstone)
                    self.parent.parent.setblock(c3.trans(-20, -20 - y, -20),
                                                materials.ChiseledSandstone)
                    self.parent.parent.setblock(c3.trans(-43, -20 - y, -20),
                                                materials.ChiseledSandstone)
                for y in xrange(2):
                    self.parent.parent.setblock(c1.trans(20, -26 - y, 20),
                                                materials.Fence)
                    self.parent.parent.setblock(c1.trans(43, -26 - y, 20),
                                                materials.Fence)
                    self.parent.parent.setblock(c3.trans(-20, -26 - y, -20),
                                                materials.Fence)
                    self.parent.parent.setblock(c3.trans(-43, -26 - y, -20),
                                                materials.Fence)
        # swamps and jungles are myan-like
        elif self.parent.parent.biome in _swamp_jungle_biomes:
            # Supports
            self.parent.parent.setblock(c1.trans(29, -29, 29),
                                        materials.StoneBrickStairs)
            self.parent.parent.setblock(c1.trans(29, -30, 29),
                                        materials.StoneBrickStairs, 1)
            self.parent.parent.setblock(c1.trans(29, -31, 29),
                                        materials.StoneBrickStairs)
            self.parent.parent.setblock(c1.trans(34, -29, 29),
                                        materials.StoneBrickStairs, 1)
            self.parent.parent.setblock(c1.trans(34, -30, 29),
                                        materials.StoneBrickStairs)
            self.parent.parent.setblock(c1.trans(34, -31, 29),
                                        materials.StoneBrickStairs, 1)
            self.parent.parent.setblock(c1.trans(29, -29, 34),
                                        materials.StoneBrickStairs)
            self.parent.parent.setblock(c1.trans(29, -30, 34),
                                        materials.StoneBrickStairs, 1)
            self.parent.parent.setblock(c1.trans(29, -31, 34),
                                        materials.StoneBrickStairs)
            self.parent.parent.setblock(c3.trans(-29, -29, -29),
                                        materials.StoneBrickStairs, 1)
            self.parent.parent.setblock(c3.trans(-29, -30, -29),
                                        materials.StoneBrickStairs)
            self.parent.parent.setblock(c3.trans(-29, -31, -29),
                                        materials.StoneBrickStairs, 1)
            # Roof
            for p in iterate_cube(c1.trans(29, -32, 29),
                                  c3.trans(-29, -32, -29)):
                self.parent.parent.setblock(p, materials.ChiseledStoneBrick)
            for p in iterate_cube(c1.trans(29, -28, 29),
                                  c3.trans(-29, -28, -29)):
                self.parent.parent.setblock(p, mat_floor)
            for p in iterate_cube(c1.trans(32, -32, 32),
                                  c3.trans(-32, -28, -32)):
                self.parent.parent.setblock(p, materials.Air)
        # Other toppers
        else:
            # Supports
            self.parent.parent.setblock(c1.trans(29, -29, 29), mat_block)
            self.parent.parent.setblock(c1.trans(29, -30, 29), mat_block)
            self.parent.parent.setblock(c1.trans(34, -29, 29), mat_block)
            self.parent.parent.setblock(c1.trans(34, -30, 29), mat_block)
            self.parent.parent.setblock(c1.trans(29, -29, 34), mat_block)
            self.parent.parent.setblock(c1.trans(29, -30, 34), mat_block)
            self.parent.parent.setblock(c3.trans(-29, -29, -29), mat_block)
            self.parent.parent.setblock(c3.trans(-29, -30, -29), mat_block)
            # Roof
            for p in iterate_cube(c1.trans(28, -31, 28),
                                  c3.trans(-28, -31, -28)):
                self.parent.parent.setblock(p, mat_slab)
            for p in iterate_cube(c1.trans(29, -28, 29),
                                  c3.trans(-29, -28, -29)):
                self.parent.parent.setblock(p, mat_block)
            for p in iterate_cube(c1.trans(32, -31, 32),
                                  c3.trans(-32, -28, -32)):
                self.parent.parent.setblock(p, materials.Air)
        # Supply chest
        p = c1.trans(30, -29, 30)
        self.parent.parent.setblock(p, materials.Chest)
        self.parent.parent.addchest(p, 0)
        # Portal exit point
        self.parent.parent.dinfo['portal_exit'] = Vec(p.x + 1,
                                                      p.y,
                                                      p.z)


class RoundTowerEntrance(Blank):
    _name = 'roundtowerentrance'
    _ruin = False
    _mat = materials.meta_mossystonebrick
    _stair = materials.StoneBrickStairs
    _biome = True
    _dnamesB = (
        ('{A}Catacombs', 3),
        ('{A}Crypt', 1),
        ('{{owners}} Crypt', 1),
        ('Crypt of {{owner}}', 1),
        ('{A}Dungeon', 3),
        ('{A}Fortress', 1),
        ('{{owners}} Fortress', 1),
        ('Fortress of {{owner}}', 1),
        ('{{owners}} Hall', 3),
        ('{A}Keep', 1),
        ('{{owners}} Keep', 1),
        ('{A}Mines', 3),
        ('{A}Ruins', 3),
        ('{A}Tower', 3),
        ('{{owners}} Tower', 3),
        ('Tower to {{owner}}', 3),
        ('{A}Tomb', 1),
        ('{{owners}} Tomb', 1),
        ('Tomb of {{owner}}', 1),
    )

    def render(self):
        # adjust to biomes if needed
        if self._biome is True:
            # Desert
            if self.parent.parent.biome in _desert_biomes:
                self._mat = materials.meta_decoratedsandstone
                self._stair = materials.SandstoneStairs
            # Ice Spikes
            elif self.parent.parent.biome in _ice_biomes:
                self._mat = materials.PackedIce
                self._stair = materials.QuartzStairs
            # Mesas
            elif self.parent.parent.biome in _mesa_biomes:
                self._mat = materials.HardenedClay
                self._stair = materials.OakWoodStairs
            # Swamps and such
            elif self.parent.parent.biome in _swamp_jungle_biomes:
                self._mat = materials.meta_mossycobble
                self._stair = materials.StoneStairs

        # The room floor Y location
        room_floor = self.parent.loc.y + self.parent.parent.room_height - 3
        # The height of one room
        rheight = self.parent.parent.room_height
        # Entrance Level
        elev = room_floor - self.parent.parent.entrance.low_height
        # Ground level
        glev = room_floor - self.parent.parent.entrance.high_height
        # Chest level
        clev = glev - rheight
        # Battlement level
        blev = glev - rheight * 2 * cfg.tower
        maxlev = (self.parent.parent.world.Height -
                  self.parent.parent.position.y)
        if -blev >= maxlev:
            blev = -maxlev + 2

        # corner of the inner shaft
        start = Vec(self.parent.loc.x + 6,
                    glev,
                    self.parent.loc.z + 6)
        # Corner of the inner wall
        wstart = start.trans(-1, 0, -1)
        # B Level is the upper battlements level
        b1 = Vec(wstart.x - 1, blev, wstart.z - 1)
        b2 = b1.trans(7, 0, 0)
        b3 = b1.trans(7, 0, 7)
        b4 = b1.trans(0, 0, 7)
        # C level is the chest level
        c1 = Vec(wstart.x - 4, clev, wstart.z - 4)
        c2 = c1.trans(13, 0, 0)
        c3 = c1.trans(13, 0, 13)
        c4 = c1.trans(0, 0, 13)
        # lower tower from ground up to chest level.
        #    The floor
        for p in iterate_cylinder(Vec(c1.x, glev, c1.z),
                                  Vec(c3.x, elev + 1, c3.z)):
            self.parent.parent.setblock(p, self._mat)
        #    The ceiling
        for p in iterate_cylinder(Vec(c1.x, clev + 1, c1.z),
                                  Vec(c3.x, clev + 1, c3.z)):
            self.parent.parent.setblock(p, self._mat)
        #    Outer wall and airspace
        for p in iterate_cylinder(c1.down(2),
                                  Vec(c3.x, glev, c3.z)):
            self.parent.parent.setblock(p, materials.Air)
        for p in iterate_tube(Vec(c1.x, elev, c1.z),
                              Vec(c3.x, elev, c3.z),
                              abs(elev - clev)):
            self.parent.parent.setblock(p, self._mat)
        #    Battlements
        for p in iterate_cube(Vec(0, 0, 0), Vec(5, 0, 5)):
            if (((p.x + p.z) & 1) == 1):
                self.parent.parent.setblock(c1 + p, materials.Air)
                self.parent.parent.setblock(c2.trans(-p.x, p.y, p.z),
                                            materials.Air)
                self.parent.parent.setblock(c3.trans(-p.x, p.y, -p.z),
                                            materials.Air)
                self.parent.parent.setblock(c4.trans(p.x, p.y, -p.z),
                                            materials.Air)
        # Upper tower from chest level to battlement
        for p in iterate_cylinder(b1, Vec(b3.x, clev, b3.z)):
            self.parent.parent.setblock(p, self._mat)
        for p in iterate_cube(Vec(0, 0, 0), Vec(4, 0, 4)):
            if (((p.x + p.z) & 1) == 1):
                self.parent.parent.setblock(b1 + p, materials.Air)
                self.parent.parent.setblock(b2.trans(-p.x, p.y, p.z),
                                            materials.Air)
                self.parent.parent.setblock(b3.trans(-p.x, p.y, -p.z),
                                            materials.Air)
                self.parent.parent.setblock(b4.trans(p.x, p.y, -p.z),
                                            materials.Air)
        # Chest level openings
        # W/E
        for p in iterate_cube(Vec(b1.x + 3, clev, b1.z),
                              Vec(b1.x + 4, clev - 2, b1.z + 7)):
            self.parent.parent.setblock(p, materials.Air)
        # N/S
        for p in iterate_cube(Vec(b1.x, clev, b1.z + 3),
                              Vec(b1.x + 7, clev - 2, b1.z + 4)):
            self.parent.parent.setblock(p, materials.Air)
        # Ground level openings
        # W side
        for p in iterate_cube(wstart.trans(2, 0, 0), wstart.trans(3, -2, -4)):
            self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(wstart.trans(2, 0, 5), wstart.trans(3, -2, 9)):
            self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(wstart.trans(0, 0, 2), wstart.trans(-4, -2, 3)):
            self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(wstart.trans(5, 0, 2), wstart.trans(9, -2, 3)):
            self.parent.parent.setblock(p, materials.Air)
        # Clear air space inside the stairwell shaft
        for p in iterate_cube(Vec(wstart.x + 1, elev + 1, wstart.z + 1),
                              Vec(wstart.x + 4, blev - 2, wstart.z + 4)):
            self.parent.parent.setblock(p, materials.Air)
        # Internal columns
        for p in iterate_cube(Vec(b1.x + 1, elev, b1.z + 1),
                              Vec(b1.x + 1, clev, b1.z + 1)):
            self.parent.parent.setblock(p, materials.StoneDoubleSlab)
        for p in iterate_cube(Vec(b2.x - 1, elev, b2.z + 1),
                              Vec(b2.x - 1, clev, b2.z + 1)):
            self.parent.parent.setblock(p, materials.StoneDoubleSlab)
        for p in iterate_cube(Vec(b3.x - 1, elev, b3.z - 1),
                              Vec(b3.x - 1, clev, b3.z - 1)):
            self.parent.parent.setblock(p, materials.StoneDoubleSlab)
        for p in iterate_cube(Vec(b4.x + 1, elev, b4.z - 1),
                              Vec(b4.x + 1, clev, b4.z - 1)):
            self.parent.parent.setblock(p, materials.StoneDoubleSlab)
        # (re)draw the staircase
        self.parent.parent.entrance.height = abs(room_floor - elev - 1)
        mat = materials.OakWoodSlab
        if random.randint(1, 100) <= 50:
            mat = materials.StoneSlab
        for p in iterate_spiral(Vec(start.x, room_floor + 4, start.z),
                                Vec(start.x + 4, room_floor + 4, start.z + 4),
                                (room_floor - blev) * 2):
            self.parent.parent.setblock(
                Vec(p.x, p.y / 2, p.z), mat, mat.data + ((p.y & 1) ^ 1) * 8)
        # Supply chest
        pos = Vec(b1.x, clev, b1.z - 1)
        self.parent.parent.setblock(pos, materials.Chest)
        self.parent.parent.addchest(pos, 0)
        # Portal exit point
        self.parent.parent.dinfo['portal_exit'] = Vec(pos.w(1).x,
                                                      clev,
                                                      pos.s(1).z)

        # Add a few details with upside-down stairs
        N = 2 + 4  # Data values for a north side stair
        S = 3 + 4  # South
        E = 1 + 4  # East
        W = 0 + 4  # West
        sb = self.parent.parent.setblock
        # Ground level archways
        sb(c1.trans(6, 3, 0), self._stair, E)
        sb(c1.trans(7, 3, 0), self._stair, W)
        sb(c4.trans(6, 3, 0), self._stair, E)
        sb(c4.trans(7, 3, 0), self._stair, W)
        sb(c1.trans(0, 3, 6), self._stair, S)
        sb(c1.trans(0, 3, 7), self._stair, N)
        sb(c2.trans(0, 3, 6), self._stair, S)
        sb(c2.trans(0, 3, 7), self._stair, N)

        # Ruin
        if self._ruin is True:
            ruinBlocks(b1.trans(0, rheight - 1, 0),
                       b3.trans(0, rheight - 1, 0),
                       rheight,
                       self.parent.parent)
        # Sandbar island
        if (self.parent.parent.entrance.inwater is False):
            return
        d = 2
        s1 = Vec(wstart.x - 3, glev + 1, wstart.z - 3)
        s3 = Vec(wstart.x + 8, glev + 1, wstart.z + 8)
        for y in xrange(rheight):
            for p in iterate_disc(s1.trans(-d, y, -d),
                                  s3.trans(d, y, d)):
                if (p not in self.parent.parent.blocks):
                    self.parent.parent.setblock(p, materials._sandbar)
            d += 1


class SquareTowerEntrance(Blank):
    _name = 'squaretowerentrance'
    _ruin = False
    _mat = materials.meta_mossystonebrick
    _stair = materials.StoneBrickStairs
    _support = materials.StoneBrickStairs
    _biome = True
    _dnamesB = (
        ('{A}Catacombs', 3),
        ('{A}Crypt', 1),
        ('{{owners}} Crypt', 1),
        ('Crypt of {{owner}}', 1),
        ('{A}Dungeon', 3),
        ('{A}Fortress', 1),
        ('{{owners}} Fortress', 1),
        ('Fortress of {{owner}}', 1),
        ('{{owners}} Hall', 3),
        ('{A}Keep', 1),
        ('{{owners}} Keep', 1),
        ('{A}Mines', 3),
        ('{A}Ruins', 3),
        ('{A}Tower', 3),
        ('{{owners}} Tower', 3),
        ('Tower to {{owner}}', 3),
        ('{A}Tomb', 1),
        ('{{owners}} Tomb', 1),
        ('Tomb of {{owner}}', 1),
    )

    def render(self):
        # adjust to biomes if needed
        if self._biome is True:
            # Desert
            if self.parent.parent.biome in _desert_biomes:
                self._mat = materials.meta_decoratedsandstone
                self._support = materials.OakWoodStairs
                self._stair = materials.SandstoneStairs
            # Ice Spikes
            elif self.parent.parent.biome in _ice_biomes:
                self._mat = materials.PackedIce
                self._support = materials.QuartzStairs
                self._stair = materials.QuartzStairs
            # Mesas
            elif self.parent.parent.biome in _mesa_biomes:
                self._mat = materials.HardenedClay
                self._support = materials.OakWoodStairs
                self._stair = materials.OakWoodStairs
            # Swamps and such
            elif self.parent.parent.biome in _swamp_jungle_biomes:
                self._mat = materials.meta_mossycobble
                self._support = materials.StoneStairs
                self._stair = materials.StoneStairs

        # The room floor Y location
        room_floor = self.parent.loc.y + self.parent.parent.room_height - 3
        # The height of one room
        rheight = self.parent.parent.room_height
        # Entrance Level
        elev = room_floor - self.parent.parent.entrance.low_height
        # Ground level
        glev = room_floor - self.parent.parent.entrance.high_height
        # Chest level
        clev = glev - rheight
        # Battlement level
        blev = glev - rheight * 2 * cfg.tower
        maxlev = (self.parent.parent.world.Height -
                  self.parent.parent.position.y)
        if -blev >= maxlev:
            blev = -maxlev + 2

        # corner of the inner shaft
        start = Vec(self.parent.loc.x + 6,
                    glev,
                    self.parent.loc.z + 6)
        # Corner of the inner wall
        wstart = start.trans(-1, 0, -1)
        # B Level is the upper battlements level
        b1 = Vec(wstart.x - 1, blev, wstart.z - 1)
        b2 = b1.trans(7, 0, 0)
        b3 = b1.trans(7, 0, 7)
        b4 = b1.trans(0, 0, 7)
        # C level is the chest level
        c1 = Vec(wstart.x - 2, clev, wstart.z - 2)
        c2 = c1.trans(9, 0, 0)
        c3 = c1.trans(9, 0, 9)
        c4 = c1.trans(0, 0, 9)
        # Chest level battlements
        #    This is the solid outer wall right under the battlements
        for p in iterate_cube(c1, c3):
            self.parent.parent.setblock(p, self._mat)
        #    The "floor" This extends to the ground to make the base thicker.
        for p in iterate_cube(c1.trans(1, 1, 1),
                              Vec(c3.x - 1, elev, c3.z - 1)):
            self.parent.parent.setblock(p, self._mat)
        #    Place the battlement blocks on the wall
        for p in iterate_cube(Vec(0, -1, 0), Vec(4, -1, 4)):
            if (((p.x + p.z) & 1) == 0):
                self.parent.parent.setblock(c1 + p, self._mat)
                self.parent.parent.setblock(c2.trans(-p.x, p.y, p.z),
                                            self._mat)
                self.parent.parent.setblock(c3.trans(-p.x, p.y, -p.z),
                                            self._mat)
                self.parent.parent.setblock(c4.trans(p.x, p.y, -p.z),
                                            self._mat)
        #     Carve out a walkway
        for p in iterate_cube(c1.trans(1, 0, 1),
                              c3.trans(-1, -10, -1)):
            self.parent.parent.setblock(p, materials.Air)
        # Battlements (top of the tower)
        #    This is the solid outer wall right under the battlements
        for p in iterate_cube(b1, b3):
            self.parent.parent.setblock(p, self._mat)
        #    Place the battlement blocks on the wall
        for p in iterate_cube(Vec(0, -1, 0), Vec(2, -1, 2)):
            if (((p.x + p.z) & 1) == 0):
                self.parent.parent.setblock(b1 + p, self._mat)
                self.parent.parent.setblock(b2.trans(-p.x, p.y, p.z),
                                            self._mat)
                self.parent.parent.setblock(b3.trans(-p.x, p.y, -p.z),
                                            self._mat)
                self.parent.parent.setblock(b4.trans(p.x, p.y, -p.z),
                                            self._mat)
        # Clear air space inside the tower
        for p in iterate_cube(Vec(wstart.x, elev, wstart.z),
                              Vec(wstart.x + 5, blev - 2, wstart.z + 5)):
            self.parent.parent.setblock(p, materials.Air)
        # Walls
        for p in iterate_four_walls(Vec(wstart.x, elev, wstart.z),
                                    Vec(wstart.x + 5, elev, wstart.z + 5),
                                    elev - blev - 1):
            self.parent.parent.setblock(p, self._mat)
        # Chest level openings
        # W side
        for p in iterate_cube(c1.trans(3, 0, 2), c1.trans(6, -3, 2)):
            self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(c1.trans(3, 0, 7), c1.trans(6, -3, 7)):
            self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(c1.trans(2, 0, 3), c1.trans(2, -3, 6)):
            self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(c1.trans(7, 0, 3), c1.trans(7, -3, 6)):
            self.parent.parent.setblock(p, materials.Air)
        # Ground level openings
        # W side
        for p in iterate_cube(wstart.trans(2, 0, 0),
                              wstart.trans(3, -3, -1)):
            self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(wstart.trans(2, 0, 5), wstart.trans(3, -3, 6)):
            self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(wstart.trans(0, 0, 2), wstart.trans(-1, -3, 3)):
            self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(wstart.trans(5, 0, 2), wstart.trans(6, -3, 3)):
            self.parent.parent.setblock(p, materials.Air)
        # (re)draw the staircase
        self.parent.parent.entrance.height = abs(room_floor - elev - 1)
        mat = materials.OakWoodSlab
        if random.randint(1, 100) <= 50:
            mat = materials.StoneSlab
        for p in iterate_spiral(Vec(start.x, room_floor + 4, start.z),
                                Vec(start.x + 4, room_floor + 4, start.z + 4),
                                (room_floor - blev) * 2):
            self.parent.parent.setblock(
                Vec(p.x, p.y / 2, p.z), mat, mat.data + ((p.y & 1) ^ 1) * 8)
        # Supply chest
        pos = c1.trans(1, 0, 1)
        self.parent.parent.setblock(pos, materials.Chest)
        self.parent.parent.addchest(pos, 0)
        # Portal exit point
        self.parent.parent.dinfo['portal_exit'] = Vec(pos.s(2).x,
                                                      clev,
                                                      pos.s(2).z)

        # Add a few details with upside-down stairs
        N = 2 + 4  # Data values for a north side stair
        S = 3 + 4  # South
        E = 1 + 4  # East
        W = 0 + 4  # West
        sb = self.parent.parent.setblock
        # Some supports under the lower battlements
        sb(c1.trans(3, 1, 0), self._support, N)
        sb(c1.trans(6, 1, 0), self._support, N)
        sb(c4.trans(3, 1, 0), self._support, S)
        sb(c4.trans(6, 1, 0), self._support, S)
        sb(c1.trans(0, 1, 3), self._support, W)
        sb(c1.trans(0, 1, 6), self._support, W)
        sb(c2.trans(0, 1, 3), self._support, E)
        sb(c2.trans(0, 1, 6), self._support, E)
        # Supports under the upper battlements
        sb(b1.trans(2, 1, 0), self._support, N)
        sb(b1.trans(5, 1, 0), self._support, N)
        sb(b4.trans(2, 1, 0), self._support, S)
        sb(b4.trans(5, 1, 0), self._support, S)
        sb(b1.trans(0, 1, 2), self._support, W)
        sb(b1.trans(0, 1, 5), self._support, W)
        sb(b2.trans(0, 1, 2), self._support, E)
        sb(b2.trans(0, 1, 5), self._support, E)
        # Ground level archways
        sb(c1.trans(4, 3, 1), self._stair, E)
        sb(c1.trans(5, 3, 1), self._stair, W)
        sb(c4.trans(4, 3, -1), self._stair, E)
        sb(c4.trans(5, 3, -1), self._stair, W)
        sb(c1.trans(1, 3, 4), self._stair, S)
        sb(c1.trans(1, 3, 5), self._stair, N)
        sb(c2.trans(-1, 3, 4), self._stair, S)
        sb(c2.trans(-1, 3, 5), self._stair, N)
        # Chest level archways
        sb(c1.trans(3, -3, 2), self._stair, E)
        sb(c1.trans(6, -3, 2), self._stair, W)
        sb(c4.trans(3, -3, -2), self._stair, E)
        sb(c4.trans(6, -3, -2), self._stair, W)
        sb(c1.trans(2, -3, 3), self._stair, S)
        sb(c1.trans(2, -3, 6), self._stair, N)
        sb(c2.trans(-2, -3, 3), self._stair, S)
        sb(c2.trans(-2, -3, 6), self._stair, N)

        # Ruin
        if self._ruin is True:
            ruinBlocks(b1.trans(0, rheight - 1, 0),
                       b3.trans(0, rheight - 1, 0),
                       rheight,
                       self.parent.parent)
        # Sandbar island
        if (self.parent.parent.entrance.inwater is False):
            return
        d = 2
        s1 = Vec(wstart.x - 3, glev + 1, wstart.z - 3)
        s3 = Vec(wstart.x + 8, glev + 1, wstart.z + 8)
        for y in xrange(rheight):
            for p in iterate_disc(s1.trans(-d, y, -d),
                                  s3.trans(d, y, d)):
                if (p not in self.parent.parent.blocks):
                    self.parent.parent.setblock(p, materials._sandbar)
            d += 1


# Square tower variants
class RuinedSquareTowerEntrance(SquareTowerEntrance):
    _name = 'ruinedsquaretowerentrance'
    _ruin = True


class SquareTowerEntranceStoneBrick(SquareTowerEntrance):
    _name = 'squaretowerentrancestonebrick'
    _ruin = False
    _mat = materials.meta_mossystonebrick
    _stair = materials.StoneBrickStairs
    _biome = False


class RuinedSquareTowerEntranceStoneBrick(SquareTowerEntrance):
    _name = 'ruinedsquaretowerentrancestonebrick'
    _ruin = True
    _mat = materials.meta_mossystonebrick
    _stair = materials.StoneBrickStairs
    _biome = False


class SquareTowerEntranceCobble(SquareTowerEntrance):
    _name = 'squaretowerentrancecobble'
    _ruin = False
    _mat = materials.meta_mossycobble
    _stair = materials.StoneStairs
    _biome = False


class RuinedSquareTowerEntranceCobble(SquareTowerEntrance):
    _name = 'ruinedsquaretowerentrancecobble'
    _ruin = True
    _mat = materials.meta_mossycobble
    _stair = materials.StoneStairs
    _biome = False


# Round tower variants
class RuinedRoundTowerEntrance(RoundTowerEntrance):
    _name = 'ruinedroundtowerentrance'
    _ruin = True


class RoundTowerEntranceCobble(RoundTowerEntrance):
    _name = 'roundtowerentrancecobble'
    _ruin = False
    _mat = materials.meta_mossycobble
    _stair = materials.StoneStairs
    _biome = False


class RuinedRoundTowerEntranceCobble(RoundTowerEntrance):
    _name = 'ruinedroundtowerentrancecobble'
    _ruin = True
    _mat = materials.meta_mossycobble
    _stair = materials.StoneStairs
    _biome = False


class RoundTowerEntranceStoneBrick(RoundTowerEntrance):
    _name = 'roundtowerentrancestonebrick'
    _ruin = False
    _mat = materials.meta_mossystonebrick
    _stair = materials.StoneBrickStairs
    _biome = False


class RuinedRoundTowerEntranceStoneBrick(RoundTowerEntrance):
    _name = 'ruinedroundtowerentrancestonebrick'
    _ruin = True
    _mat = materials.meta_mossystonebrick
    _stair = materials.StoneBrickStairs
    _biome = False


class RuinedFane(Blank):
    _name = 'ruinedfane'
    _dnamesB = (
        ('{A}Catacombs', 3),
        ('{A}Crypt', 1),
        ('{{owners}} Crypt', 1),
        ('Crypt of {{owner}}', 1),
        ('{A}Fortress', 1),
        ('{{owners}} Fortress', 1),
        ('Fortress of {{owner}}', 1),
        ('{{owners}} Hall', 3),
        ('{A}Keep', 1),
        ('{{owners}} Keep', 1),
        ('{A}Fane', 3),
        ('{A}Ruins', 3),
        ('{A}Temple', 1),
        ('{{owners}} Temple', 1),
        ('Temple to {{owner}}', 1),
        ('{A}Tomb', 1),
        ('{{owners}} Tomb', 1),
        ('Tomb of {{owner}}', 1),
    )

    def render(self):

        wall = materials.StoneBrick
        buttress = materials.Cobblestone
        buttressStair = materials.StoneStairs
        soil = materials.Dirt
        topsoil = materials.Grass
        floor = materials.Stone
        singleSlab = materials.StoneSlab
        doubleSlab = materials.StoneDoubleSlab
        stair = materials.StoneBrickStairs

        N = 3  # Data values for a north ascending stair
        S = 2  # South
        E = 0  # East
        W = 1  # West

        # Desert
        if self.parent.parent.biome in _desert_biomes:
            wall = materials.SmoothSandstone
            buttress = materials.Sandstone
            buttressStair = materials.SandstoneStairs
            soil = materials.Sand
            topsoil = materials.Sand
            floor = materials.Stone
            singleSlab = materials.SandstoneSlab
            doubleSlab = materials.ChiseledSandstone
            stair = materials.OakWoodStairs
        # Ice Spikes
        elif self.parent.parent.biome in _ice_biomes:
            wall = materials.PackedIce
            buttress = materials.Ice
            buttressStair = materials.QuartzStairs
            soil = materials.SnowBlock
            topsoil = materials.SnowBlock
            floor = materials.SnowBlock
            singleSlab = materials.QuartzSlab
            doubleSlab = materials.ChiseledQuartz
            stair = materials.QuartzStairs
        # Mesas
        elif self.parent.parent.biome in _mesa_biomes:
            wall = materials.HardenedClay
            buttress = materials.HardenedClay
            buttressStair = materials.OakWoodStairs
            soil = materials.RedSand
            topsoil = materials.RedSand
            floor = materials.BrownStainedClay
            singleSlab = materials.OrangeStainedClay
            doubleSlab = materials.OrangeStainedClay
            stair = materials.OakWoodStairs

        # the fane is 2 chunks by 3 chunks
        # do we need to move it west or north?
        xsize = self.parent.parent.xsize
        zsize = self.parent.parent.zsize
        self.spos = copy(self.pos)
        movedX = 0
        movedZ = 0
        if self.spos.x > xsize - 2:
            self.spos.x -= 1
            movedX += 1
        if self.spos.z > zsize - 3:
            self.spos.z -= 2
            movedZ += 2
        # Now go through and override the ruins on any chunks we covered to
        # be blank.
        for p in iterate_cube(Vec(self.spos.x, 0, self.spos.z),
                              Vec(self.spos.x + 1, 0, self.spos.z + 2)):
            if p == self.pos:
                continue
            blank = new('blank', self.parent.parent.rooms[p])
            self.parent.parent.rooms[p].ruins = [blank]

        # where to begin
        # Floor height at NW corner
        start = self.parent.loc + Vec(0, self.parent.parent.room_height - 3, 0)
        # translate it 4 on the x/z to surround the stairs, translate it
        # more x/z if we had to move the building inside the dungeon
        # boundary. Move up to ground level for the entrance.
        start = start.trans(4 - self.parent.parent.room_size * movedX,
                            -self.parent.parent.entrance.low_height,
                            4 - self.parent.parent.room_size * movedZ)

        # clear the inside
        for p in iterate_cube(start.trans(1, 0, 1),
                              start.trans(22, -9, 38)):
            self.parent.parent.setblock(p, materials.Air)
        for p in iterate_cube(start.trans(8, -9, 1),
                              start.trans(15, -15, 38)):
            self.parent.parent.setblock(p, materials.Air)
        for p in iterate_cube(start.trans(0, 1, 0),
                              start.trans(23, self.parent.loc.y - start.y, 39)):
            self.parent.parent.setblock(p, soil)
        for p in iterate_cube(start.trans(0, 0, 0),
                              start.trans(23, 0, 39)):
            self.parent.parent.setblock(p, topsoil)

        # make four corner towers
        locs = [
            start,
            start.trans(16, 0, 0),
            start.trans(0, 0, 32),
            start.trans(16, 0, 32)
        ]

        for loc in locs:
            # level one
            for p in iterate_cube(loc, loc.trans(7, 0, 7)):
                self.parent.parent.setblock(p, floor)

            for p in iterate_four_walls(loc, loc.trans(7, 0, 7), 10):
                self.parent.parent.setblock(p, wall)

            for p in iterate_cube(loc.down(3), loc.up(10)):
                self.parent.parent.setblock(p.trans(1, 0, -1), buttress)
                self.parent.parent.setblock(p.trans(3, 0, -1), buttress)
                self.parent.parent.setblock(p.trans(4, 0, -1), buttress)
                self.parent.parent.setblock(p.trans(6, 0, -1), buttress)
                self.parent.parent.setblock(p.trans(1, 0, 8), buttress)
                self.parent.parent.setblock(p.trans(3, 0, 8), buttress)
                self.parent.parent.setblock(p.trans(4, 0, 8), buttress)
                self.parent.parent.setblock(p.trans(6, 0, 8), buttress)
                self.parent.parent.setblock(p.trans(-1, 0, 1), buttress)
                self.parent.parent.setblock(p.trans(-1, 0, 3), buttress)
                self.parent.parent.setblock(p.trans(-1, 0, 4), buttress)
                self.parent.parent.setblock(p.trans(-1, 0, 6), buttress)
                self.parent.parent.setblock(p.trans(8, 0, 1), buttress)
                self.parent.parent.setblock(p.trans(8, 0, 3), buttress)
                self.parent.parent.setblock(p.trans(8, 0, 4), buttress)
                self.parent.parent.setblock(p.trans(8, 0, 6), buttress)

            for p in [Vec(1, -11, -1),
                      Vec(3, -11, -1),
                      Vec(4, -11, -1),
                      Vec(6, -11, -1)]:
                self.parent.parent.setblock(loc.trans(p.x, p.y, p.z),
                                            buttressStair,
                                            S)
            for p in [Vec(1, -11, 8),
                      Vec(3, -11, 8),
                      Vec(4, -11, 8),
                      Vec(6, -11, 8)]:
                self.parent.parent.setblock(loc.trans(p.x, p.y, p.z),
                                            buttressStair,
                                            N)
            for p in [Vec(-1, -11, 1),
                      Vec(-1, -11, 3),
                      Vec(-1, -11, 4),
                      Vec(-1, -11, 6)]:
                self.parent.parent.setblock(loc.trans(p.x, p.y, p.z),
                                            buttressStair,
                                            E)
            for p in [Vec(8, -11, 1),
                      Vec(8, -11, 3),
                      Vec(8, -11, 4),
                      Vec(8, -11, 6)]:
                self.parent.parent.setblock(loc.trans(p.x, p.y, p.z),
                                            buttressStair,
                                            W)

            # level 2
            for p in iterate_cube(loc.up(11), loc.up(20)):
                self.parent.parent.setblock(p.trans(0, 0, 0), wall)
                self.parent.parent.setblock(p.trans(1, 0, 0), buttress)
                self.parent.parent.setblock(p.trans(2, 0, 0), wall)
                self.parent.parent.setblock(p.trans(3, 0, 0), buttress)
                self.parent.parent.setblock(p.trans(4, 0, 0), buttress)
                self.parent.parent.setblock(p.trans(5, 0, 0), wall)
                self.parent.parent.setblock(p.trans(6, 0, 0), buttress)
                self.parent.parent.setblock(p.trans(7, 0, 0), wall)
                self.parent.parent.setblock(p.trans(0, 0, 7), wall)
                self.parent.parent.setblock(p.trans(1, 0, 7), buttress)
                self.parent.parent.setblock(p.trans(2, 0, 7), wall)
                self.parent.parent.setblock(p.trans(3, 0, 7), buttress)
                self.parent.parent.setblock(p.trans(4, 0, 7), buttress)
                self.parent.parent.setblock(p.trans(5, 0, 7), wall)
                self.parent.parent.setblock(p.trans(6, 0, 7), buttress)
                self.parent.parent.setblock(p.trans(7, 0, 7), wall)

                self.parent.parent.setblock(p.trans(0, 0, 1), buttress)
                self.parent.parent.setblock(p.trans(0, 0, 2), wall)
                self.parent.parent.setblock(p.trans(0, 0, 3), buttress)
                self.parent.parent.setblock(p.trans(0, 0, 4), buttress)
                self.parent.parent.setblock(p.trans(0, 0, 5), wall)
                self.parent.parent.setblock(p.trans(0, 0, 6), buttress)
                self.parent.parent.setblock(p.trans(7, 0, 1), buttress)
                self.parent.parent.setblock(p.trans(7, 0, 2), wall)
                self.parent.parent.setblock(p.trans(7, 0, 3), buttress)
                self.parent.parent.setblock(p.trans(7, 0, 4), buttress)
                self.parent.parent.setblock(p.trans(7, 0, 5), wall)
                self.parent.parent.setblock(p.trans(7, 0, 6), buttress)

            for p in [Vec(1, -21, 0),
                      Vec(3, -21, 0),
                      Vec(4, -21, 0),
                      Vec(6, -21, 0)]:
                self.parent.parent.setblock(loc.trans(p.x, p.y, p.z),
                                            buttressStair,
                                            S)
            for p in [Vec(1, -21, 7),
                      Vec(3, -21, 7),
                      Vec(4, -21, 7),
                      Vec(6, -21, 7)]:
                self.parent.parent.setblock(loc.trans(p.x, p.y, p.z),
                                            buttressStair,
                                            N)
            for p in [Vec(0, -21, 1),
                      Vec(0, -21, 3),
                      Vec(0, -21, 4),
                      Vec(0, -21, 6)]:
                self.parent.parent.setblock(loc.trans(p.x, p.y, p.z),
                                            buttressStair,
                                            E)
            for p in [Vec(7, -21, 1),
                      Vec(7, -21, 3),
                      Vec(7, -21, 4),
                      Vec(7, -21, 6)]:
                self.parent.parent.setblock(loc.trans(p.x, p.y, p.z),
                                            buttressStair,
                                            W)

            # level 3
            for p in iterate_cube(loc.up(21), loc.up(30)):
                self.parent.parent.setblock(p.trans(1, 0, 1), buttress)
                self.parent.parent.setblock(p.trans(2, 0, 1), wall)
                self.parent.parent.setblock(p.trans(3, 0, 1), buttress)
                self.parent.parent.setblock(p.trans(4, 0, 1), buttress)
                self.parent.parent.setblock(p.trans(5, 0, 1), wall)
                self.parent.parent.setblock(p.trans(6, 0, 1), buttress)
                self.parent.parent.setblock(p.trans(1, 0, 6), buttress)
                self.parent.parent.setblock(p.trans(2, 0, 6), wall)
                self.parent.parent.setblock(p.trans(3, 0, 6), buttress)
                self.parent.parent.setblock(p.trans(4, 0, 6), buttress)
                self.parent.parent.setblock(p.trans(5, 0, 6), wall)
                self.parent.parent.setblock(p.trans(6, 0, 6), buttress)

                self.parent.parent.setblock(p.trans(1, 0, 2), wall)
                self.parent.parent.setblock(p.trans(1, 0, 3), buttress)
                self.parent.parent.setblock(p.trans(1, 0, 4), buttress)
                self.parent.parent.setblock(p.trans(1, 0, 5), wall)
                self.parent.parent.setblock(p.trans(6, 0, 2), wall)
                self.parent.parent.setblock(p.trans(6, 0, 3), buttress)
                self.parent.parent.setblock(p.trans(6, 0, 4), buttress)
                self.parent.parent.setblock(p.trans(6, 0, 5), wall)

            # follies
            for p in iterate_cube(loc.up(32), loc.up(33)):
                self.parent.parent.setblock(p.trans(2, 0, 2), wall)
                self.parent.parent.setblock(p.trans(2, 0, 5), wall)
                self.parent.parent.setblock(p.trans(5, 0, 2), wall)
                self.parent.parent.setblock(p.trans(5, 0, 5), wall)

            for p in iterate_cube(loc.trans(2, -31, 2), loc.trans(5, -31, 5)):
                self.parent.parent.setblock(p, wall)

            # Randomly ruin
            if random.random() < .50:
                h = random.randint(0, 10)
                ruinBlocks(loc.trans(0, -25 + h, 0),
                           loc.trans(7, -25 + h, 7),
                           10 + h,
                           self.parent.parent,
                           aggressive=True)

        # curtains
        for p in iterate_cube(start.trans(1, 0, 8),
                              start.trans(1, -9, 31)):
            self.parent.parent.setblock(p, wall)
        for p in iterate_cube(start.trans(22, 0, 8),
                              start.trans(22, -9, 31)):
            self.parent.parent.setblock(p, wall)
        for p in iterate_cube(start.trans(8, 0, 1),
                              start.trans(15, -15, 1)):
            self.parent.parent.setblock(p, wall)
        for p in iterate_cube(start.trans(8, 0, 38),
                              start.trans(15, -15, 38)):
            self.parent.parent.setblock(p, wall)

        # wing ceilings
        for p in iterate_cube(start.trans(1, -10, 8),
                              start.trans(7, -10, 31)):
            self.parent.parent.setblock(p, wall)
        for p in iterate_cube(start.trans(15, -10, 8),
                              start.trans(22, -10, 31)):
            self.parent.parent.setblock(p, wall)

        # tall ceiling
        for p in iterate_cube(start.trans(8, -15, 1),
                              start.trans(15, -15, 38)):
            if (p.z % 7 != 0):
                self.parent.parent.setblock(p, wall)
        # and curtains
        for p in iterate_cube(start.trans(8, -10, 1),
                              start.trans(8, -15, 38)):
            self.parent.parent.setblock(p, wall)
            self.parent.parent.setblock(p.trans(7, 0, 0), wall)

        # floors
        for p in iterate_cube(start.trans(8, 0, 1),
                              start.trans(15, 0, 38)):
            self.parent.parent.setblock(p, floor)
        for p in iterate_cube(start.trans(1, 0, 8),
                              start.trans(7, 0, 31)):
            self.parent.parent.setblock(p, floor)
            self.parent.parent.setblock(p.trans(14, 0, 0), floor)

        # interior   bring it in from 1,0,8  21,0,31
        for p in iterate_cube(start.trans(3, 0, 12),
                              start.trans(19, 0, 29)):
            if(p.x == start.x + 11 or p.x == start.x + 12):
                # carpet would probably have deteriorated on a top floor
                continue
            elif p.z % 2 == 0:
                # pew
                self.parent.parent.setblock(p.up(1), stair, S)

        # raised altar
        for p in iterate_cube(start.trans(8, -1, 2),
                              start.trans(15, -1, 7)):
            self.parent.parent.setblock(p, wall)
        for p in iterate_cube(start.trans(7, -1, 8),
                              start.trans(16, -1, 8)):
            self.parent.parent.setblock(p, stair, N)

        mats = [
            materials.Air,       # 0
            buttress,            # 1
            doubleSlab,          # 2
            materials.IronBars,  # 3
            singleSlab           # 4
        ]
        template = [
            [[0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 2, 2, 2, 2, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0],
             [3, 3, 3, 0, 0, 3, 3, 3]],
            [[0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 4, 0, 0, 4, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 0]],
            [[4, 0, 0, 0, 0, 0, 0, 4],
             [1, 0, 0, 0, 0, 0, 0, 1],
             [1, 0, 0, 0, 0, 0, 0, 1],
             [4, 0, 0, 0, 0, 0, 0, 4],
             [1, 0, 0, 0, 0, 0, 0, 1],
             [0, 0, 0, 0, 0, 0, 0, 0]]
        ]

        o = start.trans(8, -2, 2)
        for y in xrange(3):
            for x in xrange(8):
                for z in xrange(6):
                    p = o.trans(x, -y, z)
                    self.parent.parent.setblock(p, mats[template[y][z][x]])

        # Supply chest
        loc = start.trans(8 + 3, -2, 2 + 2)
        self.parent.parent.setblock(loc, materials.Chest, 2)
        self.parent.parent.setblock(loc.trans(1, 0, 0), materials.Chest, 2)
        self.parent.parent.addchest(loc, 0)

        # Exit Portal
        self.parent.parent.dinfo['portal_exit'] = loc.s(10)

        # Random chance of a villager priest running around in here.
        if random.random() < .25:
            self.parent.parent.addentity(
                get_entity_mob_tags('Villager', Pos=loc.n(1), Profession=2)
            )

        self.parent.parent.addentity(
            get_entity_other_tags('Painting',
                                  Pos=loc.n(3).up(3),
                                  Facing='S',
                                  Motive='Wither')
        )

        # windows
        locs = [Vec(1, -3, 12),
                Vec(22, -3, 12),
                Vec(1, -3, 20),
                Vec(22, -3, 20),
                Vec(1, -3, 28),
                Vec(22, -3, 28)]
        for loc in locs:
            self.parent.parent.delblock(start.trans(loc.x, loc.y - 5, loc.z))
            for p in iterate_cube(start.trans(loc.x, loc.y, loc.z),
                                  start.trans(loc.x, loc.y - 4, loc.z)):
                self.parent.parent.delblock(p.trans(0, 0, -1))
                self.parent.parent.delblock(p)
                self.parent.parent.delblock(p.trans(0, 0, 1))

        # door
        self.parent.parent.delblock(start.trans(11, -11, 38))
        self.parent.parent.delblock(start.trans(12, -11, 38))
        for p in iterate_cube(start.trans(10, -1, 38),
                              start.trans(13, -10, 38)):
            self.parent.parent.delblock(p)

        # inner doorways
        locs = [Vec(5, -1, 7),
                Vec(2 + 16, -1, 7),
                Vec(7, -1, 32 + 2),
                Vec(16, -1, 32 + 2)]
        for loc in locs:
            self.parent.parent.setblock(start.trans(loc.x, loc.y, loc.z),
                                        materials.Air)
            self.parent.parent.setblock(start.trans(loc.x, loc.y - 1, loc.z),
                                        materials.Air)

        # extend the stair up
        estart = self.parent.loc.up(self.parent.parent.room_height - 3)
        for p in iterate_cube(estart.trans(6, 0, 6), estart.trans(9, -6, 9)):
            self.parent.parent.setblock(p, materials.Air)
        mat = materials.StoneSlab
        for p in iterate_spiral(Vec(estart.x + 6, estart.y, estart.z + 6),
                                Vec(estart.x + 6 + 4, estart.y, estart.z + 6 + 4),
                                10):
            self.parent.parent.setblock(
                Vec(p.x, p.y / 2, p.z), mat, mat.data + ((p.y & 1) ^ 1) * 8)
        for p in iterate_four_walls(estart.trans(5, 0, 5),
                                    estart.trans(10, 0, 10),
                                    3):
            self.parent.parent.setblock(p, wall)


class Barrow(Blank):
    _name = 'barrow'
    _earth = materials.Dirt
    _grass = materials.Grass
    _floor = materials.meta_mossycobble
    _stones = materials.ChiseledStoneBrick
    _tallgrass = materials.TallGrass

    _dnamesB = (
        ('{A}Cairn', 1),
        ('{{owners}} Cairn', 1),
        ('Cairn of {{owner}}', 1),
        ('{A}Barrow', 1),
        ('{{owners}} Barrow', 2),
        ('Barrow of {{owner}}', 2),
        ('{A}Kurgan', 1),
        ('{{owners}} Kurgan', 1),
        ('Kurgan of {{owner}}', 1),
        ('{A}Henge', 1),
        ('{A}Menhir', 1),
        ('{A}Stones', 1),
        ('{A}Tomb', 1),
        ('{{owners}} Tomb', 1),
        ('Tomb of {{owner}}', 1),
        ('{A}Tumulus', 1),
        ('{{owners}} Tumulus', 2),
        ('Tumulus of {{owner}}', 2),
    )

    def setData(self):
        # Desert
        if self.parent.parent.biome in _desert_biomes:
            self._earth = materials.Sandstone
            self._grass = materials.SmoothSandstone
            self._stones = materials.ChiseledSandstone
            self._tallgrass = materials.Air
        # Mesas
        elif self.parent.parent.biome in _mesa_biomes:
            self._earth = materials.RedSand
            self._grass = materials.HardenedClay
            self._stones = materials.BrownStainedClay
            self._tallgrass = materials.Air
        # Ice spikes
        elif self.parent.parent.biome in _ice_biomes:
            self._earth = materials.SnowBlock
            self._grass = materials.SnowBlock
            self._stones = materials.ChiseledQuartz
            self._tallgrass = materials.PackedIce
        # Swamps, rivers, and jungles
        elif self.parent.parent.biome in _swamp_jungle_biomes:
            self._earth = materials.Dirt
            self._grass = materials.Grass
            self._stones = materials.ChiseledStoneBrick
            self._tallgrass = materials.TallGrass

        # The Dolmen will be 2x2 chunks.
        # Figure out if we have to move West or North to fit.
        xsize = self.parent.parent.xsize
        zsize = self.parent.parent.zsize
        self.spos = copy(self.pos)
        while self.spos.x > xsize - 2:
            self.spos.x -= 1
        while self.spos.z > zsize - 2:
            self.spos.z -= 1
        # Now go through and override the ruins on any chunks we cover
        # to be blank.
        for p in iterate_cube(Vec(self.spos.x, 0, self.spos.z),
                              Vec(self.spos.x + 1, 0, self.spos.z + 1)):
            if p == self.pos:
                continue
            blank = new('blank', self.parent.parent.rooms[p])
            self.parent.parent.rooms[p].ruins = [blank]
        # Find the high/low points in this region
        self.low = 1024
        self.high = 0
        for p in iterate_cube(Vec(self.spos.x, 0, self.spos.z),
                              Vec(self.spos.x + 1, 0, self.spos.z + 1)):
            cx = (self.parent.parent.position.x >> 4) + p.x
            cz = (self.parent.parent.position.z >> 4) + p.z
            (a, b) = findChunkDepths(Vec(cx, 0, cz),
                                     self.parent.parent.world)
            self.low = min(self.low, a)
            self.high = max(self.high, b)
        self.depth = self.low
        self.depth = max(self.depth, self.parent.parent.position.y)
        self.vtrans = self.depth - self.parent.parent.position.y
        self.loc = Vec(self.spos.x * self.parent.parent.room_size,
                       -self.vtrans,
                       self.spos.z * self.parent.parent.room_size)

    def render(self):
        sb = self.parent.parent.setblock
        c1 = self.loc
        c3 = self.loc + Vec(self.parent.parent.room_size * 2 - 1,
                            0,
                            self.parent.parent.room_size * 2 - 1)

        # Mound
        height = max(self.high - self.low + 2, 6)
        for z in xrange(32):
            for x in xrange(32):
                x1 = (x - 16) / 16.0
                z1 = (z - 16) / 16.0
                if math.sqrt(x1 * x1 + z1 * z1) > 1:
                    continue
                y = math.sqrt(abs(1.0 - x1 * x1 - z1 * z1))
                for yy in xrange(int(y * height)):
                    sb(c1 + Vec(x, -yy, z), self._earth)
                sb(c1 + Vec(x, 0, z), self._floor)
                sb(c1 + Vec(x, -y * height, z), self._grass)

        # Standing stones
        for p in iterate_ellipse(c1 + Vec(8, 0, 8), c3 - Vec(8, 0, 8)):
            if (random.randint(0, 100) < 80):
                continue
            for y in xrange(1, int(height) + 4):
                sb(p.up(y), self._stones)

        # Hollow it out.
        air = []
        blocks = self.parent.parent.blocks
        for x in xrange(32):
            for z in xrange(32):
                for y in xrange(1, 5):
                    p = c1 + Vec(x, -y, z)
                    if (
                        p in blocks and
                        x is not 16 and
                        z is not 16 and
                        p.up(1) in blocks and
                        p.n(1) in blocks and
                        p.s(1) in blocks and
                        p.w(1) in blocks and
                        p.e(1) in blocks
                    ):
                        air.append(p)
        for p in air:
            sb(p, materials.Air)

        # A way in.
        for x in xrange(15, 18):
            for z in xrange(15, 18):
                for y in xrange(1, int(height) + 1):
                    p = c1 + Vec(x, -y, z)
                    sb(p, materials.Air)
        for x in xrange(15, 18):
            for z in xrange(15, 18):
                for y in xrange(1, int(height) + 1):
                    p = c1 + Vec(x, -y, z)
                    self.parent.parent.vines(p, grow=True)

        # More vines
        for x in xrange(32):
            for z in xrange(32):
                for y in xrange(int(height), int(height) + 4):
                    if (random.randint(0, 100) < 30):
                        p = c1 + Vec(x, -y, z)
                        self.parent.parent.vines(p, grow=True)

        # Coffins
        def ssb(p, m, d):
            if (
                p in blocks and
                (
                    blocks[p].material == self._earth or
                    blocks[p].material == materials.Air
                )
            ):
                sb(p, m, d)

        def addnameplate(p, name):
            if (
                p in blocks and
                blocks[p].material == materials.WallSign
            ):
                self.parent.parent.addsign(p,
                                           '',
                                           name,
                                           '',
                                           '')

        matsE = {
            'W': (materials.OakWoodSlab, random.randint(2, 3)),
            '-': (materials.StoneBrickSlab, 5 + 8),
            '_': (materials.StoneBrickSlab, 5),
            '1': (materials.StoneBrickStairs, 0 + 4),
            '2': (materials.StoneBrickStairs, 1 + 4),
            '3': (materials.StoneBrickStairs, 1),
            '4': (materials.StoneBrickStairs, 0),
            '#': (materials.meta_mossystonebrick, 0),
            '*': (materials.Air, 0),
        }
        matsW = {
            'W': (materials.OakWoodSlab, random.randint(0, 3)),
            '-': (materials.StoneBrickSlab, 5 + 8),
            '_': (materials.StoneBrickSlab, 5),
            '1': (materials.StoneBrickStairs, 1 + 4),
            '2': (materials.StoneBrickStairs, 0 + 4),
            '3': (materials.StoneBrickStairs, 0),
            '4': (materials.StoneBrickStairs, 1),
            '#': (materials.meta_mossystonebrick, 0),
            '*': (materials.Air, 0),
        }
        matsN = {
            'W': (materials.OakWoodSlab, random.randint(0, 3)),
            '-': (materials.StoneBrickSlab, 5 + 8),
            '_': (materials.StoneBrickSlab, 5),
            '1': (materials.StoneBrickStairs, 2 + 4),
            '2': (materials.StoneBrickStairs, 3 + 4),
            '3': (materials.StoneBrickStairs, 3),
            '4': (materials.StoneBrickStairs, 2),
            '#': (materials.meta_mossystonebrick, 0),
            '*': (materials.Air, 0),
        }
        matsS = {
            'W': (materials.OakWoodSlab, random.randint(0, 3)),
            '-': (materials.StoneBrickSlab, 5 + 8),
            '_': (materials.StoneBrickSlab, 5),
            '1': (materials.StoneBrickStairs, 3 + 4),
            '2': (materials.StoneBrickStairs, 2 + 4),
            '3': (materials.StoneBrickStairs, 2),
            '4': (materials.StoneBrickStairs, 3),
            '#': (materials.meta_mossystonebrick, 0),
            '*': (materials.Air, 0),
        }
        mid = (('2', '*', '*', '*', '1', '#'),
               ('3', 'W', 'W', 'W', '4', '#'))
        out = (('2', '-', '*', '-', '1', '#'),
               ('3', '_', '*', '_', '4', '#'))

        def placeCorpse(pos, rot, invisible=0):
            '''Arrange a couple of ArmorStands to look like a corpse.
            pos = position. About where the chest should be
            rot = rotation of the corpse.
                s = Head facing South
                w = Head facing West
                n = head facign North
                e = head facing East'''

            # Some offsets 
            # South
            if rot is 's':
                off1 = (0.5, 0.0, 1.0)
                off2 = (0.5, -0.75, -0.5)
                r = 180
            # East
            elif rot is 'e':
                off1 = (1.0, 0.0, 0.5)
                off2 = (-0.5, -0.75, 0.5)
                r = 90
            # North
            elif rot is 'n':
                off1 = (0.5, 0.0, 0.0)
                off2 = (0.5, -0.75, 1.5)
                r = 0
            # West
            elif rot is 'w':
                off1 = (0.0, 0.0, 0.5)
                off2 = (1.5, -0.75, 0.5)
                r = 270
            else:
                return

            # generate some armor and stuff. Some parts might be missing.
            head = None
            chest = None
            legs = None
            if random.random() < .85:
                head = items.byName(
                    random.choice((
                        "leather helmet",
                        "skeleton skull",
                    ))
                )
            if random.random() < .85:
                chest = items.byName("leather chestplate")
            if random.random() < .85:
                legs = items.byName("leather leggings")

            # The first ArmorStand covers the head, chest and arms.
            pose = nbt.TAG_Compound()
            pose['Body'] = nbt.TAG_List()
            pose['Body'].append(nbt.TAG_Float(-90))
            pose['Body'].append(nbt.TAG_Float(0))
            pose['Body'].append(nbt.TAG_Float(0))
            pose['Head'] = nbt.TAG_List()
            pose['Head'].append(nbt.TAG_Float(-90))
            pose['Head'].append(nbt.TAG_Float(0))
            pose['Head'].append(nbt.TAG_Float(0))
            pose['LeftArm'] = nbt.TAG_List()
            pose['LeftArm'].append(nbt.TAG_Float(-100))
            pose['LeftArm'].append(nbt.TAG_Float(0))
            pose['LeftArm'].append(nbt.TAG_Float(0))
            pose['RightArm'] = nbt.TAG_List()
            pose['RightArm'].append(nbt.TAG_Float(-100))
            pose['RightArm'].append(nbt.TAG_Float(0))
            pose['RightArm'].append(nbt.TAG_Float(0))

            tags = get_entity_other_tags("ArmorStand",
                                         ShowArms=1,
                                         NoGravity=1,
                                         Invisible=invisible,
                                         Pose=pose,
                                         DisabledSlots=2039583,
                                         NoBasePlate=1,
                                         Rotation=Vec(0,r,0),
                                         Pos = (pos.x+off1[0],
                                                pos.y+off1[1],
                                                pos.z+off1[2]))
            if chest is not None:
                tags['ArmorItems'][2]['id'] = nbt.TAG_String(chest.id)
            if head is not None:
                tags['ArmorItems'][3]['id'] = nbt.TAG_String(head.id)
            self.parent.parent.addentity(tags)

            # The second covers the legs
            pose = nbt.TAG_Compound()
            pose['LeftLeg'] = nbt.TAG_List()
            pose['LeftLeg'].append(nbt.TAG_Float(-90))
            pose['LeftLeg'].append(nbt.TAG_Float(0))
            pose['LeftLeg'].append(nbt.TAG_Float(0))
            pose['RightLeg'] = nbt.TAG_List()
            pose['RightLeg'].append(nbt.TAG_Float(-90))
            pose['RightLeg'].append(nbt.TAG_Float(0))
            pose['RightLeg'].append(nbt.TAG_Float(0))

            tags = get_entity_other_tags("ArmorStand",
                                         NoGravity=1,
                                         Invisible=1,
                                         Pose=pose,
                                         DisabledSlots=2039583,
                                         NoBasePlate=1,
                                         Rotation=Vec(0,r+180,0),
                                         Pos = (pos.x+off2[0],
                                                pos.y+off2[1],
                                                pos.z+off2[2]))
            if legs is not None:
                tags['ArmorItems'][1]['id'] = nbt.TAG_String(legs.id)
            self.parent.parent.addentity(tags)

        # Build the tombs.
        for x in xrange(3, 16):
            # The stone parts
            for y in xrange(4):
                p = c1 + Vec(16, -4, 16) + Vec(x, y, 0)
                ssb(p,
                    matsE[mid[y % 2][(x - 3) % 6]][0],
                    matsE[mid[y % 2][(x - 3) % 6]][1])
                ssb(p.n(1),
                    matsE[out[y % 2][(x - 3) % 6]][0],
                    matsE[out[y % 2][(x - 3) % 6]][1])
                ssb(p.s(1),
                    matsE[out[y % 2][(x - 3) % 6]][0],
                    matsE[out[y % 2][(x - 3) % 6]][1])

                p = c1 + Vec(16, -4, 16) + Vec(-x, y, 0)
                ssb(p,
                    matsW[mid[y % 2][(x - 3) % 6]][0],
                    matsW[mid[y % 2][(x - 3) % 6]][1])
                ssb(p.n(1),
                    matsW[out[y % 2][(x - 3) % 6]][0],
                    matsW[out[y % 2][(x - 3) % 6]][1])
                ssb(p.s(1),
                    matsW[out[y % 2][(x - 3) % 6]][0],
                    matsW[out[y % 2][(x - 3) % 6]][1])

                p = c1 + Vec(16, -4, 16) + Vec(0, y, x)
                ssb(p,
                    matsN[mid[y % 2][(x - 3) % 6]][0],
                    matsN[mid[y % 2][(x - 3) % 6]][1])
                ssb(p.e(1),
                    matsN[out[y % 2][(x - 3) % 6]][0],
                    matsN[out[y % 2][(x - 3) % 6]][1])
                ssb(p.w(1),
                    matsN[out[y % 2][(x - 3) % 6]][0],
                    matsN[out[y % 2][(x - 3) % 6]][1])

                p = c1 + Vec(16, -4, 16) + Vec(0, y, -x)
                ssb(p,
                    matsS[mid[y % 2][(x - 3) % 6]][0],
                    matsS[mid[y % 2][(x - 3) % 6]][1])
                ssb(p.e(1),
                    matsS[out[y % 2][(x - 3) % 6]][0],
                    matsS[out[y % 2][(x - 3) % 6]][1])
                ssb(p.w(1),
                    matsS[out[y % 2][(x - 3) % 6]][0],
                    matsS[out[y % 2][(x - 3) % 6]][1])

                # Name plates
                if (
                    (x + 1) % 6 == 0 and
                    y % 2 == 1
                ):
                    p = c1 + Vec(16, -4, 16) + Vec(x, y, 0)
                    name = self.parent.parent.namegen.genname()
                    ssb(p.n(1), materials.StoneBrickStairs, 3)
                    ssb(p.n(2), materials.WallSign, 2)
                    addnameplate(p.n(2), name)
                    ssb(p.s(1), materials.StoneBrickStairs, 2)
                    ssb(p.s(2), materials.WallSign, 3)
                    addnameplate(p.s(2), name)

                    p = c1 + Vec(16, -4, 16) + Vec(-x, y, 0)
                    name = self.parent.parent.namegen.genname()
                    ssb(p.n(1), materials.StoneBrickStairs, 3)
                    ssb(p.n(2), materials.WallSign, 2)
                    addnameplate(p.n(2), name)
                    ssb(p.s(1), materials.StoneBrickStairs, 2)
                    ssb(p.s(2), materials.WallSign, 3)
                    addnameplate(p.s(2), name)

                    p = c1 + Vec(16, -4, 16) + Vec(0, y, x)
                    name = self.parent.parent.namegen.genname()
                    ssb(p.e(1), materials.StoneBrickStairs, 0)
                    ssb(p.e(2), materials.WallSign, 5)
                    addnameplate(p.e(2), name)
                    ssb(p.w(1), materials.StoneBrickStairs, 1)
                    ssb(p.w(2), materials.WallSign, 4)
                    addnameplate(p.w(2), name)

                    p = c1 + Vec(16, -4, 16) + Vec(0, y, -x)
                    name = self.parent.parent.namegen.genname()
                    ssb(p.e(1), materials.StoneBrickStairs, 0)
                    ssb(p.e(2), materials.WallSign, 5)
                    addnameplate(p.e(2), name)
                    ssb(p.w(1), materials.StoneBrickStairs, 1)
                    ssb(p.w(2), materials.WallSign, 4)
                    addnameplate(p.w(2), name)

                # Corpses
                if (
                    (x + 1) % 6 == 0 and
                    y == 1
                ):
                    # East
                    placeCorpse(c1 + Vec(16, -1.5, 16) + Vec(x, y, 0),
                                'e')
                    placeCorpse(c1 + Vec(16, -3.5, 16) + Vec(x, y, 0),
                                'e', invisible=1)
                    # West
                    placeCorpse(c1 + Vec(16, -1.5, 16) + Vec(-x, y, 0),
                                'w')
                    placeCorpse(c1 + Vec(16, -3.5, 16) + Vec(-x, y, 0),
                                'w', invisible=1)
                    # North
                    placeCorpse(c1 + Vec(16, -1.5, 16) + Vec(0, y, -x),
                                'n')
                    placeCorpse(c1 + Vec(16, -3.5, 16) + Vec(0, y, -x),
                                'n', invisible=1)
                    # South
                    placeCorpse(c1 + Vec(16, -1.5, 16) + Vec(0, y, x),
                                's')
                    placeCorpse(c1 + Vec(16, -3.5, 16) + Vec(0, y, x),
                                's', invisible=1)

        # Grass
        for x in xrange(32):
            for z in xrange(32):
                for y in xrange(1, int(height) + 1):
                    if (random.randint(0, 100) < 80):
                        continue
                    p = c1 + Vec(x, -y, z)
                    if (
                        p not in blocks and
                        p.down(1) in blocks and
                        blocks[p.down(1)].material == self._grass
                    ):
                        sb(p, self._tallgrass, soft=True)

        # Stairwell height
        self.parent.parent.entrance.height = abs(-c1.y - 2) + 5

        # Supply chest
        loc = c1 + Vec(14, -int(height), 14)
        sb(loc, materials.Chest, 2)
        self.parent.parent.addchest(loc, 0)

        # Exit Portal
        self.parent.parent.dinfo['portal_exit'] = c1 + Vec(16, -1, 16)


class Oasis(Blank):
    _name = 'oasis'
    _dnamesB = (
        ('Oasis', 1),
        ('{A}Oasis', 5),
    )

    def setData(self):
        # The Oasis will be 3x3 chunks.
        # Figure out if we have to move West or North to fit.
        xsize = self.parent.parent.xsize
        zsize = self.parent.parent.zsize
        self.spos = copy(self.pos)
        while self.spos.x > xsize - 3:
            self.spos.x -= 1
        while self.spos.z > zsize - 3:
            self.spos.z -= 1
        # Now go through and override the ruins on any chunks we cover
        # to be blank.
        for p in iterate_cube(Vec(self.spos.x, 0, self.spos.z),
                              Vec(self.spos.x + 2, 0, self.spos.z + 2)):
            if p == self.pos:
                continue
            blank = new('blank', self.parent.parent.rooms[p])
            self.parent.parent.rooms[p].ruins = [blank]
        # Find the high/low points in this region
        self.low = 1024
        self.high = 0
        for p in iterate_cube(Vec(self.spos.x, 0, self.spos.z),
                              Vec(self.spos.x + 1, 0, self.spos.z + 1)):
            cx = (self.parent.parent.position.x >> 4) + p.x
            cz = (self.parent.parent.position.z >> 4) + p.z
            (a, b) = findChunkDepths(Vec(cx, 0, cz),
                                     self.parent.parent.world)
            self.low = min(self.low, a)
            self.high = max(self.high, b)
        self.depth = self.low + 1
        self.depth = max(self.depth, self.parent.parent.position.y)
        self.vtrans = self.depth - self.parent.parent.position.y
        self.loc = Vec(self.spos.x * self.parent.parent.room_size,
                       -self.vtrans,
                       self.spos.z * self.parent.parent.room_size)

    def render(self):
        sb = self.parent.parent.setblock
        c1 = self.loc

        # Cave shape for the water
        pond = cave_factory.new(32, 32)
        pond.resize_map(48, 48)
        # Add the area of the stairwell as an exit.
        x1 = (self.pos.x - self.spos.x) * 16 + 5
        y1 = (self.pos.z - self.spos.z) * 16 + 5
        stairwell = []
        for p in xrange(y1, y1 + 6):
            pond.add_exit((p, x1), (p, x1 + 5))
            for x in xrange(6):
                stairwell.append(c1 + Vec(x1 + x, 0, p))
        pond.gen_map(mode=random.choice(('default', 'room')))

        # The water
        for p in pond.iterate_map(cave_factory.FLOOR):
            q = c1 + Vec(p[0], 0, p[1])
            sb(q.down(1), materials.Sandstone)
            sb(q, materials.Water)

        # A couple of passes with grass.
        # First band is where reeds might grow.
        reeds = []
        for p in pond.iterate_walls():
            q = c1 + Vec(p[0], 0, p[1])
            reeds.append(q)
            sb(q, materials.Grass)
        # Second pass is where palms may grow.
        pond.reduce_map()
        palms = []
        for p in pond.iterate_walls():
            q = c1 + Vec(p[0], 0, p[1])
            palms.append(q)
            sb(q, materials.Grass)
        pond.reduce_map()

        # Now progressively clear out space above.
        # Now add air.
        for h in xrange(1, self.high - self.low + 10):
            for p in pond.iterate_map(cave_factory.FLOOR):
                q = c1 + Vec(p[0], -h, p[1])
                sb(q, materials.Air)
            pond.reduce_map()

        # Reeds
        notchest = []
        for p in reeds:
            if p in stairwell:
                continue
            if random.randint(1, 100) <= 10:
                notchest.append(p)
                sb(p.up(1), materials.SugarCane)
                sb(p.up(2), materials.SugarCane)
                sb(p.up(3), materials.SugarCane)
            elif random.randint(1, 100) <= 50:
                sb(p.up(1), materials.TallGrass, random.randint(0, 2))

        # Palms
        for p in palms:
            if p in stairwell or p in reeds:
                continue
            if random.randint(1, 100) <= 10:
                notchest.append(p)
                h = random.randint(4, 8)
                # Fronds
                sb(p.up(h + 1), materials.JungleLeaves)
                sb(p.up(h).n(1), materials.JungleLeaves)
                sb(p.up(h).s(1), materials.JungleLeaves)
                sb(p.up(h).e(1), materials.JungleLeaves)
                sb(p.up(h).w(1), materials.JungleLeaves)
                if random.randint(1, 100) <= 50:
                    sb(p.up(h).n(2), materials.JungleLeaves)
                    sb(p.up(h).s(2), materials.JungleLeaves)
                    sb(p.up(h).e(2), materials.JungleLeaves)
                    sb(p.up(h).w(2), materials.JungleLeaves)
                # Trunk
                for q in iterate_cube(p.up(1), p.up(h)):
                    sb(q, materials.Jungle)
            elif random.randint(1, 100) <= 60:
                sb(p.up(1), materials.TallGrass, random.randint(0, 2))

        # Draw a little cistern around the stairwell.
        mats = [
            materials.HardenedClay,
            materials.WhiteStainedClay,
            materials.OrangeStainedClay,
            materials.YellowStainedClay,
            materials.LightGrayStainedClay,
        ]
        random.shuffle(mats)
        st = c1 + Vec((self.pos.x - self.spos.x) * 16 + 5,
                      -1,
                      (self.pos.z - self.spos.z) * 16 + 5)
        for p in iterate_cube(st, st.up(4)):
            sb(p, mats[0])
            sb(p.trans(5, 0, 0), mats[0])
            sb(p.trans(0, 0, 5), mats[0])
            sb(p.trans(5, 0, 5), mats[0])
        sb(st.trans(1, -3, 0), mats[0])
        sb(st.trans(4, -3, 0), mats[0])
        sb(st.trans(1, -3, 5), mats[0])
        sb(st.trans(4, -3, 5), mats[0])
        sb(st.trans(0, -3, 1), mats[0])
        sb(st.trans(0, -3, 4), mats[0])
        sb(st.trans(5, -3, 1), mats[0])
        sb(st.trans(5, -3, 4), mats[0])
        for p in iterate_cube(st.trans(1, -4, 0), st.trans(4, -4, 0)):
            sb(p, mats[1])
            sb(p.s(5), mats[1])
        for p in iterate_cube(st.trans(0, -4, 1), st.trans(0, -4, 4)):
            sb(p, mats[1])
            sb(p.e(5), mats[1])
        for p in iterate_four_walls(st.trans(1, -5, 1), st.trans(4, -5, 4), 0):
            sb(p, mats[2])
        for p in iterate_four_walls(st.trans(2, -6, 2), st.trans(3, -6, 3), 0):
            sb(p, mats[3])

        # Stairwell height
        self.parent.parent.entrance.height = abs(-c1.y - 2) + 5

        # Supply chest
        loc = random.choice(list((set(reeds) & set(palms)) - set(notchest)))
        sb(loc.up(1), materials.Chest, 2)
        self.parent.parent.addchest(loc.up(1), 0)

        # Exit Portal
        self.parent.parent.dinfo['portal_exit'] = c1 + Vec(24, -3, 24)


# Other ruins

class CircularTower(Blank):
    _name = 'circulartower'

    def setData(self):
        self.wallsf = iterate_tube

    def render(self):
        # Use sandstone for deserts
        if self.parent.parent.biome in _desert_biomes:
            mat = materials.meta_decoratedsandstone
        # Mesas
        elif self.parent.parent.biome in _mesa_biomes:
            mat = materials.HardenedClay
        # Ice Spikes
        elif self.parent.parent.biome in _ice_biomes:
            mat = materials.PackedIce
        # Use cobblestone for jungle and swamp
        elif self.parent.parent.biome in _swamp_jungle_biomes:
            mat = materials.meta_mossycobble
        # Otherwise use stone brick
        else:
            mat = materials.meta_mossystonebrick

        c1 = self.loc
        c3 = c1 + Vec(self.parent.parent.room_size - 2,
                      0,
                      self.parent.parent.room_size - 2)
        # Jitter!
        scale = random.randint(0, 8)
        x_jitter = random.randint(0, scale)
        z_jitter = random.randint(0, scale)
        c1 += Vec(scale - x_jitter, 0, scale - z_jitter)
        c3 += Vec(-x_jitter, 0, -z_jitter)

        height = int(self.parent.parent.room_height * 1.5)
        for p in self.wallsf(c1, c3, height):
            self.parent.parent.setblock(p, mat, hide=True)
        ruinBlocks(c1.up(1), c3.up(1), height, self.parent.parent)


class SquareTower(CircularTower):
    _name = 'squaretower'

    def setData(self):
        self.wallsf = iterate_four_walls


class Arches(Blank):
    _name = 'arches'

    def render(self):
        height = self.parent.parent.room_height * 2
        sb = self.parent.parent.setblock
        # Sandstone in deserts
        if self.parent.parent.biome in _desert_biomes:
            mat = materials.meta_decoratedsandstone
            stair = materials.SandstoneStairs
            slab1 = materials.SandstoneSlab
            slab2 = materials.SandstoneSlab
        # Ice Spikes
        elif self.parent.parent.biome in _ice_biomes:
            mat = materials.PackedIce
            stair = materials.Ice
            slab1 = materials.QuartzSlab
            slab2 = materials.QuartzSlab
        # Mesas
        elif self.parent.parent.biome in _mesa_biomes:
            mat = materials.HardenedClay
            stair = materials.OakWoodStairs
            slab1 = materials.HardenedClay
            slab2 = materials.HardenedClay
        # Swamps and jungles are cobblestone
        elif self.parent.parent.biome in _desert_biomes:
            mat = materials.meta_mossycobble
            stair = materials.StoneStairs
            slab1 = materials.CobblestoneSlab
            slab2 = materials.StoneSlab
        else:
            mat = materials.meta_mossystonebrick
            stair = materials.StoneBrickStairs
            slab1 = materials.StoneBrickSlab
            slab2 = materials.CobblestoneSlab

        for xo in xrange(2):
            for zo in xrange(2):
                c1 = self.loc + Vec(8 * xo, 0, 8 * zo)
                c3 = c1 + Vec(7, 0, 7)
                # columns
                for p in iterate_cube(c1, c1.trans(0, -height, 0)):
                    sb(p, mat, hide=True)
                    sb(p.trans(7, 0, 0), mat, hide=True)
                    sb(p.trans(7, 0, 7), mat, hide=True)
                    sb(p.trans(0, 0, 7), mat, hide=True)
                # First level
                p = c1.trans(0, -height + 2, 0)
                sb(p.trans(1, 0, 0), stair, 1 + 4)
                sb(p.trans(6, 0, 0), stair, 0 + 4)
                sb(p.trans(0, 0, 1), stair, 3 + 4)
                sb(p.trans(7, 0, 1), stair, 3 + 4)
                sb(p.trans(0, 0, 6), stair, 2 + 4)
                sb(p.trans(7, 0, 6), stair, 2 + 4)
                sb(p.trans(1, 0, 7), stair, 1 + 4)
                sb(p.trans(6, 0, 7), stair, 0 + 4)
                # Second level
                p = p.trans(0, -1, 0)
                sb(p.trans(1, 0, 0), mat)
                sb(p.trans(6, 0, 0), mat)
                sb(p.trans(0, 0, 1), mat)
                sb(p.trans(7, 0, 1), mat)
                sb(p.trans(0, 0, 6), mat)
                sb(p.trans(7, 0, 6), mat)
                sb(p.trans(1, 0, 7), mat)
                sb(p.trans(6, 0, 7), mat)
                # ---
                sb(p.trans(2, 0, 0), stair, 1 + 4)
                sb(p.trans(5, 0, 0), stair, 0 + 4)
                sb(p.trans(0, 0, 2), stair, 3 + 4)
                sb(p.trans(7, 0, 2), stair, 3 + 4)
                sb(p.trans(0, 0, 5), stair, 2 + 4)
                sb(p.trans(7, 0, 5), stair, 2 + 4)
                sb(p.trans(2, 0, 7), stair, 1 + 4)
                sb(p.trans(5, 0, 7), stair, 0 + 4)
                # Top layer
                p = p.trans(0, -1, 0)
                for p in iterate_four_walls(p, p.trans(7, 0, 7), 0):
                    if (
                        cfg.ruin_ruins is False or
                        random.randint(1, 100) <= 50
                    ):
                        if (random.randint(1, 100) <= 25):
                            sb(p, slab1)
                        else:
                            sb(p, slab2)

                # Maybe ruin this section
                if (random.randint(1, 100) <= 50):
                    ruinBlocks(c1.up(1), c3.up(1), height, self.parent.parent)


class HouseFrame(Blank):
    _name = 'houseframe'

    def render(self):
        # Use sandstone for deserts
        if self.parent.parent.biome in _desert_biomes:
            mat = materials.meta_decoratedsandstone
            stair = materials.SandstoneStairs
        # Ice Spikes
        elif self.parent.parent.biome in _ice_biomes:
            mat = materials.PackedIce
            stair = materials.QuartzStairs
        # Mesas
        elif self.parent.parent.biome in _mesa_biomes:
            mat = materials.HardenedClay
            stair = materials.OakWoodStairs
        # Use cobblestone for jungle and swamp
        elif self.parent.parent.biome in _swamp_jungle_biomes:
            mat = materials.meta_mossycobble
            stair = materials.StoneStairs
        # Otherwise use stone brick
        else:
            mat = materials.meta_mossystonebrick
            stair = materials.StoneBrickStairs

        # what direction will the stairs face?
        E = 0
        W = 1

        # got the mats. now draw the base. start one higher so it's less buried
        start = self.loc.trans(3 + random.randint(0, 2),
                               -1,
                               3 + random.randint(0, 2))
        for p in iterate_cube(start, start.trans(7, 0, 7)):
            self.parent.parent.setblock(p, mat)

        # now draw the A frame
        start = start.trans(0, -1, 0)

        # will the head be in the south (7) or north (0)
        head = random.randint(0, 1) * 7

        for p in iterate_cube(start.trans(0, 0, head),
                              start.trans(6, -3, head)):
            self.parent.parent.setblock(p, mat)

        for p in iterate_cube(start.trans(1, -4, head),
                              start.trans(5, -4, head)):
            self.parent.parent.setblock(p, mat)
        self.parent.parent.setblock(start.trans(0, -4, head), stair, E)
        self.parent.parent.setblock(start.trans(6, -4, head), stair, W)

        for p in iterate_cube(start.trans(2, -5, head),
                              start.trans(4, -5, head)):
            self.parent.parent.setblock(p, mat)
        self.parent.parent.setblock(start.trans(1, -5, head), stair, E)
        self.parent.parent.setblock(start.trans(5, -5, head), stair, W)

        self.parent.parent.setblock(start.trans(2, -6, head), stair, E)
        self.parent.parent.setblock(start.trans(3, -6, head), mat)
        self.parent.parent.setblock(start.trans(4, -6, head), stair, W)

        # cut out the window(s)
        if(random.randint(0, 100) < 50):
            # two tall windows
            self.parent.parent.delblock(start.trans(2, -1, head))
            self.parent.parent.delblock(start.trans(4, -1, head))
            self.parent.parent.delblock(start.trans(2, -2, head))
            self.parent.parent.delblock(start.trans(4, -2, head))
            self.parent.parent.delblock(start.trans(2, -3, head))
            self.parent.parent.delblock(start.trans(4, -3, head))
        else:
            # one big arch
            for p in iterate_cube(start.trans(2, 0, head),
                                  start.trans(4, -2, head)):
                self.parent.parent.delblock(p)
            self.parent.parent.setblock(start.trans(2, -3, head), stair, W + 4)
            self.parent.parent.delblock(start.trans(3, -3, head))
            self.parent.parent.setblock(start.trans(4, -3, head), stair, E + 4)

        # then draw the long wall
        for p in iterate_cube(start, start.trans(0, 0, 7)):
            self.parent.parent.setblock(p, mat)
            self.parent.parent.setblock(p.up(1), mat)
            if(random.randint(0, 100) < 50):
                self.parent.parent.setblock(p.up(2), mat)

        # and the corner post opposite
        for p in iterate_cube(start.trans(7, 0, 7 - head),
                              start.trans(7, -3, 7 - head)):
            self.parent.parent.setblock(p, mat)

        # and maybe some ancient pottery
        if (random.randint(1, 100) < 10):
            self.parent.parent.setblock(start.trans(2 + random.randint(0, 3),
                                                    0,
                                                    2),
                                        materials.FlowerPot, 10, soft=True)
            self.parent.parent.setblock(start.trans(2 + random.randint(0, 3),
                                                    0,
                                                    3),
                                        materials.FlowerPot, 10, soft=True)

        # ruin it! (maybe)
        if (random.randint(1, 100) < 50):
            ruinBlocks(start, start.trans(7, 0, 7), 7, self.parent.parent)


class MazeEntrance(Blank):

    '''
    Maze-like entrance to a dungeon.
    '''
    _name = 'mazeentrance'
    _biome = True
    _mats = {
        'stone': ((materials.MossyStoneBrick, 7),
                  (materials.CrackedStoneBrick, 2),
                  (materials.ChiseledStoneBrick, 1)),
        'desert': ((materials.Sandstone, 5),
                   (materials.SmoothSandstone, 3),
                   (materials.ChiseledSandstone, 2)),
        'ice': ((materials.PackedIce, 8), (materials.Ice, 2)),
        'mesa': ((materials.HardenedClay, 1), (materials.HardenedClay, 1))
    }
    _size = 1

    _dnamesB = (
        ('{{owners}} Labyrinth', 5),
        ('{A}Labyrinth', 5),
        ('Labyrinth to {{owner}}', 5),
        ('The {A}Labyrinth', 5),
        ('{A}Catacombs', 1),
        ('{A}Ruins', 1),
        ('{A}Temple', 1),
        ('{{owners}} Temple', 1),
        ('Temple to {{owner}}', 1),
        ('{A}Tomb', 1),
        ('{{owners}} Tomb', 1),
        ('Tomb of {{owner}}', 1)
    )

    def setData(self):
        # the maze will be 3x3 if the entrance isn't on the edge of the
        # dungeon chunks it will be 1x1 otherwise
        xsize = self.parent.parent.xsize
        zsize = self.parent.parent.zsize
        if (
            self.pos.x > 0 and
            self.pos.z > 0 and
            self.pos.x < xsize - 1 and
            self.pos.z < zsize - 1
        ):
            self._size = 3

        maze_pos = self.pos

        # clear all ruins with 3x3 block around dungeon entrance
        # the maze will be 3x3 chunks with the entrance in the center chunk
        if self._size == 3:
            for p in iterate_cube(Vec(maze_pos.x - 1, 0, maze_pos.z - 1),
                                  Vec(maze_pos.x + 1, 0, maze_pos.z + 1)):
                if p == self.pos:
                    continue
                blank = new('blank', self.parent.parent.rooms[p])
                self.parent.parent.rooms[p].ruins = [blank]

    def _gen_maze_dfs(self):
        '''
        Generates a maze using caver algorithm.
        Returns 2D array of 1s and 0s that represent the maze.
        (0: wall, 1: open)
        '''
        cw = self._size * 16
        cl = self._size * 16
        canvas_width = cw - ((cw) + 1) % 2
        canvas_length = cl - ((cl) + 1) % 2
        blocks = [
            [0 for j in xrange(canvas_length)] for i in xrange(canvas_width)
        ]
        start_x = random.randint(0, canvas_width / 2 - 1) * 2 + 1
        start_z = 1
        unvisited = []  # keep track of the unvisited nodes in a stack
        cur = (start_x, start_z)
        while True:
            blocks[cur[0]][cur[1]] = 1
            neighbors = self._get_open_neighbors(blocks,
                                                 canvas_width,
                                                 canvas_length,
                                                 cur[0],
                                                 cur[1])
            if len(neighbors) > 0:
                # pick a neighbor, and add the rest to the back of unvisited
                next = neighbors.pop(random.randint(0, len(neighbors) - 1))
                if len(neighbors) > 0:
                    unvisited += [cur]
                # hollow out hole in between cur and next
                if next[0] < cur[0]:  # left
                    blocks[cur[0] - 1][cur[1]] = 1
                elif next[0] > cur[0]:  # right
                    blocks[cur[0] + 1][cur[1]] = 1
                elif next[1] < cur[1]:  # down
                    blocks[cur[0]][cur[1] - 1] = 1
                elif next[1] > cur[1]:  # up
                    blocks[cur[0]][cur[1] + 1] = 1
                cur = next
            elif len(unvisited) > 0:
                cur = unvisited.pop()
            else:
                break
        # add an entrance on each side
        # front
        x = random.randint(0, canvas_width / 2 - 1) * 2 + 1
        blocks[x][0] = 1
        # back
        x = random.randint(0, canvas_width / 2 - 1) * 2 + 1
        blocks[x][canvas_length - 1] = 1
        # left
        z = random.randint(0, canvas_length / 2 - 1) * 2 + 1
        blocks[0][z] = 1
        # right
        z = random.randint(0, canvas_length / 2 - 1) * 2 + 1
        blocks[canvas_width - 1][z] = 1

        # post-process to smooth out turns in the maze
        # use a sliding 2x2 window
        for i in xrange(canvas_width - 2):
            for j in xrange(canvas_length - 2):
                count = blocks[i][j] + \
                    2 * blocks[i + 1][j] + \
                    4 * blocks[i][j + 1] + \
                    8 * blocks[i + 1][j + 1]
                if count == 8:
                    blocks[i][j] = 1
                elif count == 4:
                    blocks[i + 1][j] = 1
                elif count == 2:
                    blocks[i][j + 1] = 1
                elif count == 1:
                    blocks[i + 1][j + 1] = 1

        return blocks

    def _get_open_neighbors(self, blocks, canvas_width, canvas_length, i, j):
        if i % 2 != 1 or j % 2 != 1:
            return
        neighbors = []
        # check 4 directions
        if i > 1 and blocks[i - 2][j] == 0:  # left
            neighbors.append((i - 2, j))
        if i < canvas_width - 2 and blocks[i + 2][j] == 0:  # right
            neighbors.append((i + 2, j))
        if j > 1 and blocks[i][j - 2] == 0:  # down
            neighbors.append((i, j - 2))
        if j < canvas_length - 2 and blocks[i][j + 2] == 0:
            neighbors.append((i, j + 2))
        return neighbors

    def render(self):
        '''
        Renders a maze around the entrance shaft.
        '''
        blocks = self._gen_maze_dfs()
        if len(blocks) == 0:  # not sure if this check is necessary...
            return
        mats = self._mats['stone']
        if self._biome is True:
            if self.parent.parent.biome in _desert_biomes:
                mats = self._mats['desert']
            elif self.parent.parent.biome in _ice_biomes:
                mats = self._mats['ice']
            elif self.parent.parent.biome in _mesa_biomes:
                mats = self._mats['mesa']

        # The room floor Y location
        room_floor = self.parent.loc.y + self.parent.parent.room_height - 3
        # The height of one room
        rheight = self.parent.parent.room_height
        # Ground level
        glev = room_floor - self.parent.parent.entrance.high_height
        # start = self.parent.loc.trans(-16, glev, -16)

        sc = int(self._size / 2) * 16
        start = Vec(self.loc.x - sc, self.parent.loc.y + glev, self.loc.z - sc)

        # render the floor of the labyrinth
        for i in xrange(len(blocks)):
            for j in xrange(len(blocks[0])):
                self.parent.parent.setblock(start.trans(i, 0, j),
                                            weighted_choice(mats))

        pn = perlin.SimplexNoise(256)

        open_x_start = sc + 4
        open_z_start = sc + 4
        open_x_end = sc + 11
        open_z_end = sc + 11

        for i in xrange(len(blocks)):
            for j in xrange(len(blocks[0])):
                if (
                    i <= open_x_start
                    or i >= open_x_end
                    or j <= open_z_start
                    or j >= open_z_end
                ):
                    # walls near the middle of the labyrinth are taller
                    # than the edges
                    height = (
                        (
                            pn.noise2(i / 32.0, j / 32.0) + 1.0
                        ) / 2.0 * self.parent.parent.room_height
                    ) * (
                        (16 * self._size) / (abs(j - (sc + 8)) + abs(i - (sc + 8)))
                    ) + 7
                    for y in xrange(int(height)):
                        if blocks[i][j] == 0:  # wall
                            self.parent.parent.setblock(
                                start.trans(i, -y, j),
                                weighted_choice(mats)
                            )
                        else:
                            self.parent.parent.setblock(
                                start.trans(i, -y, j),
                                materials.Air
                            )
                else:
                    for y in xrange(20):
                        self.parent.parent.setblock(
                            start.trans(i, -y, j),
                            materials.Air
                        )
                for y in xrange(abs(glev) + 1):
                    self.parent.parent.setblock(
                        start.trans(i, y, j),
                        weighted_choice(mats)
                    )

        # adjust the entrance height to match with the floor of the labyrinth
        self.parent.parent.entrance.height = abs(room_floor - glev)

        # Supply chest
        chest_pos = start.trans(sc + 7, -1, sc + 5)
        self.parent.parent.setblock(chest_pos, materials.Chest)
        self.parent.parent.addchest(chest_pos, 0)
        # Portal exit point
        self.parent.parent.dinfo['portal_exit'] = Vec(chest_pos.x + 1,
                                                      chest_pos.y,
                                                      chest_pos.z)

        # draw sandbar if necessary
        if (self.parent.parent.entrance.inwater):
            gstart = Vec(
                self.parent.loc.x - sc,
                glev,
                self.parent.loc.z - sc
            )
            d = 2
            s1 = Vec(gstart.x - 3, glev + 1, start.z - 3)
            s3 = Vec(gstart.x + self._size * 3 + 3,
                     glev + 1,
                     start.z + self._size * 3 + 3)
            for y in xrange(rheight):
                for p in iterate_disc(s1.trans(-d, y, -d),
                                      s3.trans(d, y, d)):
                    if (p not in self.parent.parent.blocks):
                        self.parent.parent.setblock(p, materials._sandbar)
                d += 1


def ruinBlocks(p1, p2, height, dungeon, override=False, aggressive=False):
    pn = perlin.SimplexNoise(256)
    if (
        override is True or
        cfg.ruin_ruins is False
    ):
        return
    for x in xrange(p1.x, p2.x + 1):
        for z in xrange(p1.z, p2.z + 1):
            depth = (pn.noise3(x / 4.0, 0, z / 4.0) + 1.0) / 2.0 * height
            for p in iterate_cube(Vec(x, p1.y - depth, z),
                                  Vec(x, p1.y - height, z)):
                dungeon.delblock(p)
    # Look for floating blocks
    floaters = []
    for p in iterate_cube(p1, Vec(p2.x, p2.y - height, p2.z)):
        if (
            (
                p in dungeon.blocks and
                dungeon.blocks[p].material != materials.Air
            ) and
            (
                p.down(1) not in dungeon.blocks or
                dungeon.blocks[p.down(1)].material == materials.Air
            ) and
            (
                p.n(1) not in dungeon.blocks or
                dungeon.blocks[p.n(1)].material == materials.Air
            ) and
            (
                p.s(1) not in dungeon.blocks or
                dungeon.blocks[p.s(1)].material == materials.Air
            ) and
            (
                p.e(1) not in dungeon.blocks or
                dungeon.blocks[p.e(1)].material == materials.Air
            ) and
            (
                p.w(1) not in dungeon.blocks or
                dungeon.blocks[p.w(1)].material == materials.Air
            )
        ):
            floaters.append(p)
    for p in floaters:
        dungeon.delblock(p)
    # In aggressive mode, we'll cull out anything that is not supported
    # directly underneath. Usually this breaks the stairs, but looks better
    # for some structures.
    if aggressive is True:
        for p in iterate_cube(p1, p2):
            for q in xrange(p.y, p.up(height).y, -1):
                pp = Vec(p.x, q, p.z)
                if (
                    pp.down(1) not in dungeon.blocks or
                    dungeon.blocks[pp.down(1)].material == materials.Air
                ):
                    dungeon.delblock(pp)


# Catalog the ruins we know about.
_ruins = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses if of ruins.Blank
    if issubclass(obj, Blank):
        _ruins[obj._name] = obj


def new(name, parent):
    '''Return a new instance of the ruin of a given name. Supply the parent
    dungeon object.'''
    if name in _ruins.keys():
        return _ruins[name](parent)
    return Blank(parent)
