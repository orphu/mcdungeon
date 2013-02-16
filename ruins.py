import sys
import inspect

import materials
import cfg
import perlin
from utils import *


class Blank(object):
    _name = 'blank'

    def __init__ (self, parent):
        self.parent = parent
        self.pos = copy(parent.pos)
        cx = (parent.parent.position.x + parent.loc.x) >>4
        cz = (parent.parent.position.z + parent.loc.z) >>4
        self.chunk = Vec(cx,0,cz)
        #print 'ruin chunk:', self.chunk

    def placed (self, world):
        self.depth = self.parent.parent.good_chunks[(self.chunk.x, self.chunk.z)]
        self.vtrans = max(self.parent.parent.position.y-1, self.depth) - \
                self.parent.parent.position.y
        #print 'ruin depth:', self.parent.parent.position.y, self.depth, -self.vtrans
        self.loc = Vec(self.pos.x * self.parent.parent.room_size,
                       -self.vtrans,
                       self.pos.z * self.parent.parent.room_size)
        self.setData()

    def setData (self):
        pass

    def render (self):
        pass

class EvilRunestones(Blank):
    _name = 'evilrunestones'

    def render(self):
        # For most of this one, we render directly to the chunk structure.
        # This works out better in the end.
        height = int(self.parent.parent.room_height*cfg.tower)
        # This chunk
        cx = (self.parent.parent.position.x + self.parent.loc.x) >>4
        cz = (self.parent.parent.position.z + self.parent.loc.z) >>4
        chunk = self.parent.parent.world.getChunk(cx,cz)
        # dungeon y
        dy = self.parent.parent.position.y
        # Noise function
        pn = perlin.SimplexNoise(256)
        # Replacement setblock function. 
        def sb(p, mat, chunk=chunk):
            chunk.Blocks[p.x,p.z,p.y] = mat.val
            chunk.Data[p.x,p.z,p.y] = mat.data

        # list of IDs that are solid. (for our purposes anyway)
        solids = ( 1, 2, 3, 4, 7, 8, 9, 12, 13, 24, 48, 60, 82)
        # Height of the runestones
        runes = {}
        for x in xrange(16):
            for z in xrange(16):
                runes[x, z] = random.randint(height/2, height)
        # Iterate over the chunk
        for x in xrange(16):
            for z in xrange(16):
                # find the height at this block
                y = chunk.HeightMap[z, x]
                while (y > 0 and
                       chunk.Blocks[x, z, y] not in solids):
                    y = y - 1
                q = Vec(x, y, z)
                # create a chest
                if (x == 2 and z == 2):
                    cp = Vec(cx*16+x-self.parent.parent.position.x,
                             self.parent.parent.position.y - y - 1,
                             cz*16+z-self.parent.parent.position.z)
                    self.parent.parent.setblock(cp, materials.Chest)
                    self.parent.parent.addchest(cp, 0)
                    # The portal exit point is here
                    self.parent.parent.dinfo['portal_exit'] = cp.up(2)

                    for r in iterate_cube(q.down(2), q.trans(0,height,0)):
                        sb(r, materials.Air)
                    continue
                # If we are above the entrance, clear the air and continue
                if (x >= 6 and x <= 9 and
                    z >= 6 and z <= 9):
                    for r in iterate_cube(Vec(q.x, dy, q.z),
                                          q.trans(0,height,0)):
                        sb(r, materials.Air)
                    continue
                # Draw some creeping Netherrack and SoulSand. 
                # Clear the air above
                for r in iterate_cube(q.down(1), q.trans(0,height,0)):
                    if chunk.Blocks[r.x,r.z,r.y] != materials.Obsidian.val:
                        sb(r, materials.Air)
                d = ((Vec2f(q.x, q.z) - Vec2f(7, 7)).mag()) / 16
                n = (pn.noise3(q.x / 4.0, 0, q.z / 4.0) + 1.0) / 2.0
                if (n >= d+.20):
                    sb(q, materials.Netherrack)
                    # Netherrack might be on fire!
                    if random.randint(1,100) <= 5:
                        sb(q.down(1), materials.Fire)
                elif (n > d):
                    sb(q, materials.SoulSand)
                # We are on an edge. Draw a runestone.
                # N/S edges
                if ((x == 0 or x == 15) and
                    z >= 3 and z <= 9 and
                    z%3 == 0):
                    h = runes[x, z]
                    for r in iterate_cube(q, q.trans(0,h,0)):
                        sb(r, materials.Obsidian)
                    for r in iterate_cube(q.trans(0,h,0), q.trans(0,h,3)):
                        sb(r, materials.Obsidian)
                    for r in iterate_cube(q.trans(0,0,3), q.trans(0,h,3)):
                        sb(r, materials.Obsidian)
                # E/W edges
                if ((z == 0 or z == 15) and
                    x >= 3 and x <= 9 and
                    x%3 == 0):
                    h = runes[x, z]
                    for r in iterate_cube(q, q.trans(0,h,0)):
                        sb(r, materials.Obsidian)
                    for r in iterate_cube(q.trans(0,h,0), q.trans(3,h,0)):
                        sb(r, materials.Obsidian)
                    for r in iterate_cube(q.trans(3,0,0), q.trans(3,h,0)):
                        sb(r, materials.Obsidian)

class StepPyramid(Blank):
    _name = 'steppyramid'

    def setData(self):
        # The StepPyramid will be 4x4 chunks.
        # Figure out if we have to move West or North to fit.
        xsize = self.parent.parent.xsize
        zsize = self.parent.parent.zsize
        self.spos = copy(self.pos)
        while self.spos.x > xsize-4:
            self.spos.x -= 1
        while self.spos.z > zsize-4:
            self.spos.z -= 1
        # Now go through and override the ruins on any chunks we cover
        # to be blank. 
        for p in iterate_cube(Vec(self.spos.x, 0, self.spos.z),
                              Vec(self.spos.x+3, 0, self.spos.z+3)):
            if p == self.pos:
                continue
            blank = new('blank', self.parent.parent.rooms[p])
            self.parent.parent.rooms[p].ruins = [blank]
        # Find the low point in this region
        for p in iterate_cube(Vec(self.spos.x, 0, self.spos.z),
                              Vec(self.spos.x+3, 0, self.spos.z+3)):
            cx = (self.parent.parent.position.x>>4) + p.x
            cz = (self.parent.parent.position.z>>4) + p.z
            self.depth = min(self.depth,
                             self.parent.parent.good_chunks[(cx, cz)])
        self.depth = max(self.depth, 62, self.parent.parent.position.y)
        self.vtrans = self.depth - self.parent.parent.position.y + 1
        self.loc = Vec(self.spos.x * self.parent.parent.room_size,
                       -self.vtrans,
                       self.spos.z * self.parent.parent.room_size)
        # Figure out how high the entrances should be.
        # min is 2, max is 22. 
        cx = self.parent.parent.position.x>>4
        cz = self.parent.parent.position.z>>4
        world = self.parent.parent.world
        # N side
        (low1, high1) = findChunkDepths(Vec(cx, 0, cz+1), world)
        (low2, high2) = findChunkDepths(Vec(cx, 0, cz+2), world)
        self.ent_n = min(22, max(1, high1-self.depth, high2-self.depth)+1)
        # S side
        (low1, high1) = findChunkDepths(Vec(cx+3, 0, cz+1), world)
        (low2, high2) = findChunkDepths(Vec(cx+3, 0, cz+2), world)
        self.ent_s = min(22,max(1, high1-self.depth, high2-self.depth)+1)
        # E side
        (low1, high1) = findChunkDepths(Vec(cx+1, 0, cz+3), world)
        (low2, high2) = findChunkDepths(Vec(cx+2, 0, cz+3), world)
        self.ent_e = min(22,max(1, high1-self.depth, high2-self.depth)+1)
        # W side
        (low1, high1) = findChunkDepths(Vec(cx+1, 0, cz), world)
        (low2, high2) = findChunkDepths(Vec(cx+2, 0, cz), world)
        self.ent_w = min(22,max(1, high1-self.depth, high2-self.depth)+1)

    def render (self):
        # Biome materials
        if self.parent.parent.biome in [2, 17]:
            mat_ext = materials.SmoothSandstone
            mat_block = materials.meta_decoratedsandstone
            mat_ruins = materials.meta_decoratedsandstone
            mat_stair = materials.SandstoneStairs
            mat_slab = materials.SandstoneSlab
            mat_floor = materials.Sand
        elif self.parent.parent.biome in [6, 7, 11, 21, 22]:
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
        c3 = c1 + Vec(self.parent.parent.room_size*4-1,
                      0,
                      self.parent.parent.room_size*4-1)
        # corner of the inner shaft
        start = Vec(self.parent.loc.x+5,
                    c1.y,
                    self.parent.loc.z+5)
        # Walls and airspace of the pyramid
        for y in xrange(29):
            for p in iterate_cube(c1.trans(y+1,-y,y+1),
                                        c3.trans(-y-1,-y,-y-1)):
                self.parent.parent.setblock(p, materials.Air)
            for p in iterate_four_walls(c1.trans(y,-y,y),
                                        c3.trans(-y,-y,-y), 0):
                self.parent.parent.setblock(p, mat_ext)
                # In swamp/jungle the steps are extra steppy.
                if (y%2 == 0 and self.parent.parent.biome in [6, 7, 11, 21, 22]):
                    self.parent.parent.setblock(p.up(1), mat_ext)
        # Floor. From pyramid base to just above ceiling. 
        for p in iterate_four_walls(c1,
                                    c3, c1.y):
            self.parent.parent.setblock(p, mat_ext, hide=True)
        # Cover the floor with stuff
        pn = perlin.SimplexNoise(256)
        for p in iterate_cube(c1, c3):
            d = ((Vec2f(p.x, p.z) - Vec2f(c1.x+32, c1.z+32)).mag()) / 64
            n = (pn.noise3(p.x / 4.0, p.y / 4.0, p.z / 4.0) + 1.0) / 2.0
            if (n >= d+.20):
                self.parent.parent.setblock(p, mat_floor)
            elif (n >= d+.10):
                self.parent.parent.setblock(p, mat_ruins)
            elif (n >= d):
                self.parent.parent.setblock(p, materials.Gravel)
            else:
                self.parent.parent.setblock(p, mat_block)
        # Build internal ruins. 
        cchance = 80
        for p in iterate_cube(Vec(0, 0, 0), Vec(3, 0, 3)):
            wfunc = iterate_four_walls
            if random.randint(1,100) <= 50:
                wfunc = iterate_tube
            pp1 = c1.trans(p.x*16+1, 0, p.z*16+1)
            pp2 = pp1.trans(13, 0, 13)
            # place a chest here
            if random.randint(1,100) <= cchance:
                cchance /= 5
                cp = pp1.trans(3,-1,3)
                if random.randint(1,100) <= 50:
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
                    if (x in self.parent.parent.blocks and
                        self.parent.parent.blocks[x].material == materials.Air):
                        self.parent.parent.setblock(x, mat_ruins)

        # Clean up the stairwell shaft. Clear the air, make a half step around
        # it, extend the walls, and redraw the stairs. 
        self.parent.parent.entrance.height = abs(-c1.y-2)+2
        for p in iterate_cube(start, start.trans(5,-c1.y-1,5)):
            self.parent.parent.setblock(p, materials.Air)
        for p in iterate_four_walls(Vec(start.x, -1, start.z),
                                    Vec(start.x+5, -1, start.z+5),-c1.y-2):
            self.parent.parent.setblock(p, materials._wall)
        for p in iterate_four_walls(start, start.trans(5,0,5),0):
            self.parent.parent.setblock(p, materials.StoneSlab)
        mat = materials.WoodenSlab
        if random.randint(1,100) <= 50:
            mat = materials.StoneSlab
        for p in iterate_spiral(Vec(start.x+1,7,start.z+1),
                                Vec(start.x+5,7,start.z+5),
                                (abs(c1.y)+3)*2):
            self.parent.parent.setblock(Vec(p.x,
                                        0+int(p.y/2),
                                        p.z), mat, mat.data+((p.y&1)^1)*8)
        # Entrances.
        # Draw stairs up the sides.
        for y in xrange(29):
            # North Side
            # caps on either side
            self.parent.parent.setblock(c1.trans(y,-y-1,29), mat_slab)
            self.parent.parent.setblock(c1.trans(y,-y-1,34), mat_slab)
            # draw different stuff depending on the height
            # Go ahead and draw exterior stairs at every level.
            # (we'll overwrite some below)
            for p in iterate_cube(c1.trans(y, -y, 30),
                                  c1.trans(y, -y, 33)):
                self.parent.parent.setblock(p,
                                            mat_stair, 0)
                self.parent.parent.delblock(p.up(1))
                self.parent.parent.setblock(p.trans(1,0,0),
                                            mat_block)
            # Above floor, but below entry level, 
            # draw the interior stairs and airspace.
            if (y > 0 and y <= self.ent_n):
                for p in iterate_cube(c1.trans(y, -y, 28),
                                      c1.trans(y, -y, 35)):
                    for x in xrange(2,6):
                        self.parent.parent.setblock(p.trans(x,0,0),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(6,0,0),
                                                mat_stair, 0)
                    self.parent.parent.setblock(p.trans(7,0,0),
                                                mat_block, 0)
            # At entry level, draw a platform floor. 
            if (self.ent_n == y):
                for p in iterate_cube(c1.trans(y+1, -y, 30),
                                      c1.trans(y+8, -y, 33)):
                    self.parent.parent.setblock(p, mat_block)
            # Above the entry platform, draw some walls
            if (y > self.ent_n and y < self.ent_n+4):
                p = c1.trans(y, -y, 30)
                self.parent.parent.setblock(p, mat_block)
                self.parent.parent.setblock(p.trans(1,0,0), mat_block)
                self.parent.parent.setblock(p.trans(0,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(1,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(0,0,2), materials.Air)
                self.parent.parent.setblock(p.trans(1,0,2), materials.Air)
                self.parent.parent.setblock(p.trans(0,0,3), mat_block)
                self.parent.parent.setblock(p.trans(1,0,3), mat_block)
            # Add a ceiling for the entryway.
            if (y ==  self.ent_n+4):
                p = c1.trans(y-3, -y, 30)
                self.parent.parent.setblock(p.trans(1,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,2,0), mat_block)
                p = c1.trans(y-3, -y, 33)
                self.parent.parent.setblock(p.trans(1,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,2,0), mat_block)
                for p in iterate_cube(c1.trans(y-3, -y, 30),
                                      c1.trans(y+1, -y, 33)):
                    self.parent.parent.setblock(p, mat_block)


            # South Side
            self.parent.parent.setblock(c1.trans(63-y,-y-1,29), mat_slab)
            self.parent.parent.setblock(c1.trans(63-y,-y-1,34), mat_slab)
            for p in iterate_cube(c1.trans(63-y, -y, 30),
                                  c1.trans(63-y, -y, 33)):
                self.parent.parent.setblock(p,
                                            mat_stair, 1)
                self.parent.parent.delblock(p.up(1))
                self.parent.parent.setblock(p.trans(-1,0,0),
                                            mat_block, 0)
            if (y > 0 and y <= self.ent_s):
                for p in iterate_cube(c1.trans(63-y, -y, 28),
                                      c1.trans(63-y, -y, 35)):
                    for x in xrange(2,6):
                        self.parent.parent.setblock(p.trans(-x,0,0),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(-6,0,0),
                                                mat_stair, 1)
                    self.parent.parent.setblock(p.trans(-7,0,0),
                                                mat_block, 0)
            if (self.ent_s == y):
                for p in iterate_cube(c1.trans(63-y-1, -y, 30),
                                      c1.trans(63-y-8, -y, 33)):
                    self.parent.parent.setblock(p, mat_block)
            if (y > self.ent_s and y < self.ent_s+4):
                p = c1.trans(63-y, -y, 30)
                self.parent.parent.setblock(p, mat_block)
                self.parent.parent.setblock(p.trans(-1,0,0), mat_block)
                self.parent.parent.setblock(p.trans(0,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(-1,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(0,0,2), materials.Air)
                self.parent.parent.setblock(p.trans(-1,0,2), materials.Air)
                self.parent.parent.setblock(p.trans(0,0,3), mat_block)
                self.parent.parent.setblock(p.trans(-1,0,3), mat_block)
            if (y ==  self.ent_s+4):
                p = c1.trans(63-y+3, -y, 30)
                self.parent.parent.setblock(p.trans(-1,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,2,0), mat_block)
                p = c1.trans(63-y+3, -y, 33)
                self.parent.parent.setblock(p.trans(-1,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,2,0), mat_block)
                for p in iterate_cube(c1.trans(63-y+3, -y, 30),
                                      c1.trans(63-y-1, -y, 33)):
                    self.parent.parent.setblock(p, mat_block)

            # West Side
            self.parent.parent.setblock(c1.trans(29,-y-1,y), mat_slab)
            self.parent.parent.setblock(c1.trans(34,-y-1,y), mat_slab)
            for p in iterate_cube(c1.trans(30, -y, y),
                                  c1.trans(33, -y, y)):
                self.parent.parent.setblock(p, mat_stair, 2)
                self.parent.parent.delblock(p.up(1))
                self.parent.parent.setblock(p.trans(0,0,1),
                                            mat_block, 0)
            if (y > 0 and y <= self.ent_w):
                for p in iterate_cube(c1.trans(28, -y, y),
                                      c1.trans(35, -y, y)):
                    for x in xrange(2,6):
                        self.parent.parent.setblock(p.trans(0,0,x),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(0,0,6),
                                                mat_stair, 2)
                    self.parent.parent.setblock(p.trans(0,0,7),
                                                mat_block, 0)
            if (self.ent_w == y):
                for p in iterate_cube(c1.trans(30, -y, y+1),
                                      c1.trans(33, -y, y+8)):
                    self.parent.parent.setblock(p, mat_block)
            if (y > self.ent_w and y < self.ent_w+4):
                p = c1.trans(30, -y, y)
                self.parent.parent.setblock(p, mat_block)
                self.parent.parent.setblock(p.trans(0,0,1), mat_block)
                self.parent.parent.setblock(p.trans(1,0,0), materials.Air)
                self.parent.parent.setblock(p.trans(1,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(2,0,0), materials.Air)
                self.parent.parent.setblock(p.trans(2,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(3,0,0), mat_block)
                self.parent.parent.setblock(p.trans(3,0,1), mat_block)
            if (y ==  self.ent_w+4):
                p = c1.trans(30, -y, y-3)
                self.parent.parent.setblock(p.trans(0,1,1), mat_block)
                self.parent.parent.setblock(p.trans(0,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,2,0), mat_block)
                p = c1.trans(33, -y, y-3)
                self.parent.parent.setblock(p.trans(0,1,1), mat_block)
                self.parent.parent.setblock(p.trans(0,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,2,0), mat_block)
                for p in iterate_cube(c1.trans(30, -y, y-3),
                                      c1.trans(33, -y, y+1)):
                    self.parent.parent.setblock(p, mat_block)

            # East Side
            self.parent.parent.setblock(c1.trans(29,-y-1,63-y), mat_slab)
            self.parent.parent.setblock(c1.trans(34,-y-1,63-y), mat_slab)
            for p in iterate_cube(c1.trans(30, -y, 63-y),
                                  c1.trans(33, -y, 63-y)):
                self.parent.parent.setblock(p,
                                            mat_stair, 3)
                self.parent.parent.delblock(p.up(1))
                self.parent.parent.setblock(p.trans(0,0,-1),
                                            mat_block, 0)
            if (y > 0 and y <= self.ent_e):
                for p in iterate_cube(c1.trans(28, -y, 63-y),
                                      c1.trans(35, -y, 63-y)):
                    for x in xrange(2,6):
                        self.parent.parent.setblock(p.trans(0,0,-x),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(0,0,-6),
                                                mat_stair, 3)
                    self.parent.parent.setblock(p.trans(0,0,-7),
                                                mat_block, 0)
            if (self.ent_e == y):
                for p in iterate_cube(c1.trans(30, -y, 63-y-1),
                                      c1.trans(33, -y, 63-y-8)):
                    self.parent.parent.setblock(p, mat_block)
            if (y > self.ent_e and y < self.ent_e+4):
                p = c1.trans(30, -y, 63-y)
                self.parent.parent.setblock(p, mat_block)
                self.parent.parent.setblock(p.trans(0,0,-1), mat_block)
                self.parent.parent.setblock(p.trans(1,0,0), materials.Air)
                self.parent.parent.setblock(p.trans(1,0,-1), materials.Air)
                self.parent.parent.setblock(p.trans(2,0,0), materials.Air)
                self.parent.parent.setblock(p.trans(2,0,-1), materials.Air)
                self.parent.parent.setblock(p.trans(3,0,0), mat_block)
                self.parent.parent.setblock(p.trans(3,0,-1), mat_block)
            if (y ==  self.ent_e+4):
                p = c1.trans(30, -y, 63-y+3)
                self.parent.parent.setblock(p.trans(0,1,-1), mat_block)
                self.parent.parent.setblock(p.trans(0,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,2,0), mat_block)
                p = c1.trans(33, -y, 63-y+3)
                self.parent.parent.setblock(p.trans(0,1,-1), mat_block)
                self.parent.parent.setblock(p.trans(0,1,0), mat_block)
                self.parent.parent.setblock(p.trans(0,2,0), mat_block)
                for p in iterate_cube(c1.trans(30, -y, 63-y+3),
                                      c1.trans(33, -y, 63-y-1)):
                    self.parent.parent.setblock(p, mat_block)

        # Topper
        # Deserts have a fancy glass tipped pyramid
        if self.parent.parent.biome in [2, 17]:
            for y in xrange(29, 33):
                for p in iterate_cube(c1.trans(y,-y,y),
                                            c3.trans(-y,-y,-y)):
                    self.parent.parent.setblock(p, materials.Air)
                for p in iterate_four_walls(c1.trans(y-1,-y,y-1),
                                            c3.trans(-y+1,-y,-y+1), 0):
                    self.parent.parent.setblock(p, materials.Glass)
            for p in iterate_cube(c1.trans(29, -28, 29),c3.trans(-29, -28, -29)):
                self.parent.parent.setblock(p, mat_block)
            for p in iterate_cube(c1.trans(32, -31, 32),c3.trans(-32, -28, -32)):
                self.parent.parent.setblock(p, materials.Air)
            # holes in the glass
            for p in iterate_cube(c1.trans(32, -30, 28),c3.trans(-32, -29, -28)):
                self.parent.parent.setblock(p, materials.Air)
            for p in iterate_cube(c1.trans(28, -30, 32),c3.trans(-28, -29, -32)):
                self.parent.parent.setblock(p, materials.Air)
            # Spires
            for y in xrange(6):
                self.parent.parent.setblock(c1.trans(20,-20-y,20),
                                            materials.ChiseledSandstone)
                self.parent.parent.setblock(c1.trans(43,-20-y,20),
                                            materials.ChiseledSandstone)
                self.parent.parent.setblock(c3.trans(-20,-20-y,-20),
                                            materials.ChiseledSandstone)
                self.parent.parent.setblock(c3.trans(-43,-20-y,-20),
                                            materials.ChiseledSandstone)
            for y in xrange(2):
                self.parent.parent.setblock(c1.trans(20,-26-y,20),
                                            materials.Fence)
                self.parent.parent.setblock(c1.trans(43,-26-y,20),
                                            materials.Fence)
                self.parent.parent.setblock(c3.trans(-20,-26-y,-20),
                                            materials.Fence)
                self.parent.parent.setblock(c3.trans(-43,-26-y,-20),
                                            materials.Fence)
        # swamps and jungles are myan-like
        elif self.parent.parent.biome in [6, 7, 11, 21, 22]:
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
            self.parent.parent.setblock(c3.trans(-29, -29,-29),
                                        materials.StoneBrickStairs, 1)
            self.parent.parent.setblock(c3.trans(-29, -30,-29),
                                        materials.StoneBrickStairs)
            self.parent.parent.setblock(c3.trans(-29, -31,-29),
                                        materials.StoneBrickStairs, 1)
            # Roof
            for p in iterate_cube(c1.trans(29, -32, 29),c3.trans(-29, -32, -29)):
                self.parent.parent.setblock(p, materials.CircleStoneBrick)
            for p in iterate_cube(c1.trans(29, -28, 29),c3.trans(-29, -28, -29)):
                self.parent.parent.setblock(p, mat_floor)
            for p in iterate_cube(c1.trans(32, -32, 32),c3.trans(-32, -28, -32)):
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
            self.parent.parent.setblock(c3.trans(-29, -29,-29), mat_block)
            self.parent.parent.setblock(c3.trans(-29, -30,-29), mat_block)
            # Roof
            for p in iterate_cube(c1.trans(28, -31, 28),c3.trans(-28, -31, -28)):
                self.parent.parent.setblock(p, mat_slab)
            for p in iterate_cube(c1.trans(29, -28, 29),c3.trans(-29, -28, -29)):
                self.parent.parent.setblock(p, mat_block)
            for p in iterate_cube(c1.trans(32, -31, 32),c3.trans(-32, -28, -32)):
                self.parent.parent.setblock(p, materials.Air)
        # Supply chest
        p = c1.trans(30, -29, 30)
        self.parent.parent.setblock(p, materials.Chest)
        self.parent.parent.addchest(p, 0)
        # Portal exit point
        self.parent.parent.dinfo['portal_exit'] = p+Vec(p.w(1).x,
                                                        c1.y + 29,
                                                        p.s(1).z1)


class RoundTowerEntrance(Blank):
    _name = 'roundtowerentrance'
    _ruin = False
    _mat = materials.meta_mossystonebrick
    _stair = materials.StoneBrickStairs
    _biome = True

    def render (self):
        # adjust to biomes if needed
        if self._biome == True:
            # Desert
            if self.parent.parent.biome in [2, 17]:
                self._mat = materials.meta_decoratedsandstone
                self._stair = materials.SandstoneStairs
            elif self.parent.parent.biome in [6, 7, 11, 21, 22]:
                self._mat = materials.meta_mossycobble
                self._stair = materials.StoneStairs

        # The room floor Y location
        room_floor = self.parent.loc.y+self.parent.parent.room_height-3
        # The height of one room
        rheight = self.parent.parent.room_height
        # Entrance Level
        elev = room_floor - self.parent.parent.entrance.low_height
        # Ground level
        glev = room_floor - self.parent.parent.entrance.high_height
        # Chest level
        clev = glev - rheight
        # Battlement level
        blev = glev  - rheight * 2 * cfg.tower
        maxlev = self.parent.parent.world.Height - self.parent.parent.position.y
        if -blev >= maxlev:
            blev = -maxlev+2

        # corner of the inner shaft
        start = Vec(self.parent.loc.x+6,
                    glev,
                    self.parent.loc.z+6)
        # Corner of the inner wall
        wstart = start.trans(-1,0,-1)
        # B Level is the upper battlements level
        b1 = Vec(wstart.x-1, blev, wstart.z-1)
        b2 = b1.trans(7,0,0)
        b3 = b1.trans(7,0,7)
        b4 = b1.trans(0,0,7)
        # C level is the chest level
        c1 = Vec(wstart.x-4, clev, wstart.z-4)
        c2 = c1.trans(13,0,0)
        c3 = c1.trans(13,0,13)
        c4 = c1.trans(0,0,13)
        # lower tower from ground up to chest level. 
        #    The floor
        for p in iterate_cylinder(Vec(c1.x, glev, c1.z),Vec(c3.x, elev+1, c3.z)):
            self.parent.parent.setblock(p, self._mat)
        #    The ceiling
        for p in iterate_cylinder(Vec(c1.x, clev+1, c1.z),Vec(c3.x, clev+1, c3.z)):
            self.parent.parent.setblock(p, self._mat)
        #    Outer wall and airspace
        for p in iterate_cylinder(c1.down(2),Vec(c3.x, glev, c3.z)):
            self.parent.parent.setblock(p, materials.Air)
        for p in iterate_tube(Vec(c1.x,elev,c1.z),
                              Vec(c3.x,elev,c3.z),
                              abs(elev-clev)):
            self.parent.parent.setblock(p, self._mat)
        #    Battlements
        for p in iterate_cube(Vec(0,0,0), Vec(5,0,5)):
            if (((p.x+p.z)&1) == 1):
                self.parent.parent.setblock(c1+p, materials.Air)
                self.parent.parent.setblock(c2.trans(-p.x,p.y,p.z),
                                            materials.Air)
                self.parent.parent.setblock(c3.trans(-p.x,p.y,-p.z),
                                            materials.Air)
                self.parent.parent.setblock(c4.trans(p.x,p.y,-p.z),
                                            materials.Air)
        # Upper tower from chest level to battlement
        for p in iterate_cylinder(b1,Vec(b3.x, clev, b3.z)):
            self.parent.parent.setblock(p, self._mat)
        for p in iterate_cube(Vec(0,0,0), Vec(4,0,4)):
            if (((p.x+p.z)&1) == 1):
                self.parent.parent.setblock(b1+p, materials.Air)
                self.parent.parent.setblock(b2.trans(-p.x,p.y,p.z),
                                            materials.Air)
                self.parent.parent.setblock(b3.trans(-p.x,p.y,-p.z),
                                            materials.Air)
                self.parent.parent.setblock(b4.trans(p.x,p.y,-p.z),
                                            materials.Air)
        # Chest level openings
        # W/E
        for p in iterate_cube(Vec(b1.x+3,clev,b1.z),
                              Vec(b1.x+4,clev-2,b1.z+7)):
                self.parent.parent.setblock(p, materials.Air)
        # N/S 
        for p in iterate_cube(Vec(b1.x,clev,b1.z+3),
                              Vec(b1.x+7,clev-2,b1.z+4)):
                self.parent.parent.setblock(p, materials.Air)
        # Ground level openings
        # W side
        for p in iterate_cube(wstart.trans(2,0,0), wstart.trans(3,-2,-4)):
                self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(wstart.trans(2,0,5), wstart.trans(3,-2,9)):
                self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(wstart.trans(0,0,2), wstart.trans(-4,-2,3)):
                self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(wstart.trans(5,0,2), wstart.trans(9,-2,3)):
                self.parent.parent.setblock(p, materials.Air)
        # Clear air space inside the stairwell shaft
        for p in iterate_cube(Vec(wstart.x+1, elev+1, wstart.z+1),
                              Vec(wstart.x+4, blev-2, wstart.z+4)):
            self.parent.parent.setblock(p, materials.Air)
        # Internal columns
        for p in iterate_cube(Vec(b1.x+1, elev, b1.z+1),
                              Vec(b1.x+1, clev, b1.z+1)):
            self.parent.parent.setblock(p, materials.DoubleSlab)
        for p in iterate_cube(Vec(b2.x-1, elev, b2.z+1),
                              Vec(b2.x-1, clev, b2.z+1)):
            self.parent.parent.setblock(p, materials.DoubleSlab)
        for p in iterate_cube(Vec(b3.x-1, elev, b3.z-1),
                              Vec(b3.x-1, clev, b3.z-1)):
            self.parent.parent.setblock(p, materials.DoubleSlab)
        for p in iterate_cube(Vec(b4.x+1, elev, b4.z-1),
                              Vec(b4.x+1, clev, b4.z-1)):
            self.parent.parent.setblock(p, materials.DoubleSlab)
        # (re)draw the staircase
        self.parent.parent.entrance.height = abs(room_floor-elev-1)
        mat = materials.WoodenSlab
        if random.randint(1,100) <= 50:
            mat = materials.StoneSlab
        for p in iterate_spiral(Vec(start.x,room_floor+4,start.z),
                                Vec(start.x+4,room_floor+4,start.z+4),
                                (room_floor-blev)*2):
            self.parent.parent.setblock(Vec(p.x,
                                        p.y/2,
                                        p.z), mat, mat.data+((p.y&1)^1)*8)
        # Supply chest
        pos = Vec(b1.x, clev, b1.z-1)
        self.parent.parent.setblock(pos, materials.Chest)
        self.parent.parent.addchest(pos, 0)
        # Portal exit point
        self.parent.parent.dinfo['portal_exit'] = Vec(pos.w(1).x,
                                                      clev,
                                                      pos.s(1).z)

        # Add a few details with upside-down stairs
        N = 2+4 # Data values for a north side stair
        S = 3+4 # South
        E = 1+4 # East 
        W = 0+4 # West
        sb = self.parent.parent.setblock
        # Ground level archways
        sb(c1.trans(6,3,0), self._stair, E)
        sb(c1.trans(7,3,0), self._stair, W)
        sb(c4.trans(6,3,0), self._stair, E)
        sb(c4.trans(7,3,0), self._stair, W)
        sb(c1.trans(0,3,6), self._stair, S)
        sb(c1.trans(0,3,7), self._stair, N)
        sb(c2.trans(0,3,6), self._stair, S)
        sb(c2.trans(0,3,7), self._stair, N)

        # Ruin
        if self._ruin == True:
            ruinBlocks(b1.trans(0,rheight-1,0),
                       b3.trans(0,rheight-1,0),
                       rheight,
                       self.parent.parent)
        # Sandbar island
        if (self.parent.parent.entrance.inwater is False):
            return
        d = 2
        s1 = Vec(wstart.x-3, glev+1, wstart.z-3)
        s3 = Vec(wstart.x+8, glev+1, wstart.z+8)
        for y in xrange(rheight):
            for p in iterate_disc(s1.trans(-d,y,-d),
                                  s3.trans(d,y,d)):
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

    def render (self):
        # adjust to biomes if needed
        if self._biome == True:
            # Desert
            if self.parent.parent.biome in [2, 17]:
                self._mat = materials.meta_decoratedsandstone
                self._support = materials.WoodenStairs
                self._stair = materials.SandstoneStairs
            elif self.parent.parent.biome in [6, 7, 11, 21, 22]:
                self._mat = materials.meta_mossycobble
                self._support = materials.StoneStairs
                self._stair = materials.StoneStairs

        # The room floor Y location
        room_floor = self.parent.loc.y+self.parent.parent.room_height-3
        # The height of one room
        rheight = self.parent.parent.room_height
        # Entrance Level
        elev = room_floor - self.parent.parent.entrance.low_height
        # Ground level
        glev = room_floor - self.parent.parent.entrance.high_height
        # Chest level
        clev = glev - rheight
        # Battlement level
        blev = glev  - rheight * 2 * cfg.tower
        maxlev = self.parent.parent.world.Height - self.parent.parent.position.y
        if -blev >= maxlev:
            blev = -maxlev+2

        # corner of the inner shaft
        start = Vec(self.parent.loc.x+6,
                    glev,
                    self.parent.loc.z+6)
        # Corner of the inner wall
        wstart = start.trans(-1,0,-1)
        # B Level is the upper battlements level
        b1 = Vec(wstart.x-1, blev, wstart.z-1)
        b2 = b1.trans(7,0,0)
        b3 = b1.trans(7,0,7)
        b4 = b1.trans(0,0,7)
        # C level is the chest level
        c1 = Vec(wstart.x-2, clev, wstart.z-2)
        c2 = c1.trans(9,0,0)
        c3 = c1.trans(9,0,9)
        c4 = c1.trans(0,0,9)
        # Chest level battlements
        #    This is the solid outer wall right under the battlements
        for p in iterate_cube(c1,c3):
            self.parent.parent.setblock(p, self._mat)
        #    The "floor" This extends to the ground to make the base thicker. 
        for p in iterate_cube(c1.trans(1,1,1),Vec(c3.x-1,
                                                  elev,
                                                  c3.z-1)):
            self.parent.parent.setblock(p, self._mat)
        #    Place the battlement blocks on the wall
        for p in iterate_cube(Vec(0,-1,0), Vec(4,-1,4)):
            if (((p.x+p.z)&1) == 0):
                self.parent.parent.setblock(c1+p, self._mat)
                self.parent.parent.setblock(c2.trans(-p.x,p.y,p.z),
                                            self._mat)
                self.parent.parent.setblock(c3.trans(-p.x,p.y,-p.z),
                                            self._mat)
                self.parent.parent.setblock(c4.trans(p.x,p.y,-p.z),
                                            self._mat)
        #     Carve out a walkway
        for p in iterate_cube(c1.trans(1,0,1),
                              c3.trans(-1,-10,-1)):
            self.parent.parent.setblock(p, materials.Air)
        # Battlements (top of the tower)
        #    This is the solid outer wall right under the battlements
        for p in iterate_cube(b1,b3):
            self.parent.parent.setblock(p, self._mat)
        #    Place the battlement blocks on the wall
        for p in iterate_cube(Vec(0,-1,0), Vec(2,-1,2)):
            if (((p.x+p.z)&1) == 0):
                self.parent.parent.setblock(b1+p, self._mat)
                self.parent.parent.setblock(b2.trans(-p.x,p.y,p.z),
                                            self._mat)
                self.parent.parent.setblock(b3.trans(-p.x,p.y,-p.z),
                                            self._mat)
                self.parent.parent.setblock(b4.trans(p.x,p.y,-p.z),
                                            self._mat)
        # Clear air space inside the tower
        for p in iterate_cube(Vec(wstart.x, elev, wstart.z),
                              Vec(wstart.x+5, blev-2, wstart.z+5)):
            self.parent.parent.setblock(p, materials.Air)
        # Walls
        for p in iterate_four_walls(Vec(wstart.x, elev, wstart.z),
                                    Vec(wstart.x+5, elev, wstart.z+5),
                                    elev-blev-1):
            self.parent.parent.setblock(p, self._mat)
        # Chest level openings
        # W side
        for p in iterate_cube(c1.trans(3,0,2), c1.trans(6,-3,2)):
            self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(c1.trans(3,0,7), c1.trans(6,-3,7)):
            self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(c1.trans(2,0,3), c1.trans(2,-3,6)):
            self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(c1.trans(7,0,3), c1.trans(7,-3,6)):
            self.parent.parent.setblock(p, materials.Air)
        # Ground level openings
        # W side
        for p in iterate_cube(wstart.trans(2,0,0),
                              wstart.trans(3,-3,-1)):
                self.parent.parent.setblock(p, materials.Air)
        # E side
        for p in iterate_cube(wstart.trans(2,0,5), wstart.trans(3,-3,6)):
                self.parent.parent.setblock(p, materials.Air)
        # N side
        for p in iterate_cube(wstart.trans(0,0,2), wstart.trans(-1,-3,3)):
                self.parent.parent.setblock(p, materials.Air)
        # S side
        for p in iterate_cube(wstart.trans(5,0,2), wstart.trans(6,-3,3)):
                self.parent.parent.setblock(p, materials.Air)
        # (re)draw the staircase
        self.parent.parent.entrance.height = abs(room_floor-elev-1)
        mat = materials.WoodenSlab
        if random.randint(1,100) <= 50:
            mat = materials.StoneSlab
        for p in iterate_spiral(Vec(start.x,room_floor+4,start.z),
                                Vec(start.x+4,room_floor+4,start.z+4),
                                (room_floor-blev)*2):
            self.parent.parent.setblock(Vec(p.x,
                                        p.y/2,
                                        p.z), mat, mat.data+((p.y&1)^1)*8)
        # Supply chest
        pos = c1.trans(1, 0, 1)
        self.parent.parent.setblock(pos, materials.Chest)
        self.parent.parent.addchest(pos, 0)
        # Portal exit point
        self.parent.parent.dinfo['portal_exit'] = Vec(pos.s(2).x,
                                                      clev,
                                                      pos.s(2).z)

        # Add a few details with upside-down stairs
        N = 2+4 # Data values for a north side stair
        S = 3+4 # South
        E = 1+4 # East 
        W = 0+4 # West
        sb = self.parent.parent.setblock
        # Some supports under the lower battlements
        sb(c1.trans(3,1,0), self._support, N)
        sb(c1.trans(6,1,0), self._support, N)
        sb(c4.trans(3,1,0), self._support, S)
        sb(c4.trans(6,1,0), self._support, S)
        sb(c1.trans(0,1,3), self._support, W)
        sb(c1.trans(0,1,6), self._support, W)
        sb(c2.trans(0,1,3), self._support, E)
        sb(c2.trans(0,1,6), self._support, E)
        # Supports under the upper battlements
        sb(b1.trans(2,1,0), self._support, N)
        sb(b1.trans(5,1,0), self._support, N)
        sb(b4.trans(2,1,0), self._support, S)
        sb(b4.trans(5,1,0), self._support, S)
        sb(b1.trans(0,1,2), self._support, W)
        sb(b1.trans(0,1,5), self._support, W)
        sb(b2.trans(0,1,2), self._support, E)
        sb(b2.trans(0,1,5), self._support, E)
        # Ground level archways
        sb(c1.trans(4,3,1), self._stair, E)
        sb(c1.trans(5,3,1), self._stair, W)
        sb(c4.trans(4,3,-1), self._stair, E)
        sb(c4.trans(5,3,-1), self._stair, W)
        sb(c1.trans(1,3,4), self._stair, S)
        sb(c1.trans(1,3,5), self._stair, N)
        sb(c2.trans(-1,3,4), self._stair, S)
        sb(c2.trans(-1,3,5), self._stair, N)
        # Chest level archways
        sb(c1.trans(3,-3,2), self._stair, E)
        sb(c1.trans(6,-3,2), self._stair, W)
        sb(c4.trans(3,-3,-2), self._stair, E)
        sb(c4.trans(6,-3,-2), self._stair, W)
        sb(c1.trans(2,-3,3), self._stair, S)
        sb(c1.trans(2,-3,6), self._stair, N)
        sb(c2.trans(-2,-3,3), self._stair, S)
        sb(c2.trans(-2,-3,6), self._stair, N)

        # Ruin
        if self._ruin == True:
            ruinBlocks(b1.trans(0,rheight-1,0),
                       b3.trans(0,rheight-1,0),
                       rheight,
                       self.parent.parent)
        # Sandbar island
        if (self.parent.parent.entrance.inwater is False):
            return
        d = 2
        s1 = Vec(wstart.x-3, glev+1, wstart.z-3)
        s3 = Vec(wstart.x+8, glev+1, wstart.z+8)
        for y in xrange(rheight):
            for p in iterate_disc(s1.trans(-d,y,-d),
                                  s3.trans(d,y,d)):
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

    def render (self):

        wall = materials.StoneBrick
        buttress = materials.Cobblestone
        buttressStair = materials.StoneStairs
        soil = materials.Dirt
        topsoil = materials.Grass
        floor = materials.Stone
        singleSlab = materials.StoneSlab
        doubleSlab = materials.DoubleSlab
        stair = materials.StoneBrickStairs

        N = 3 # Data values for a north ascending stair
        S = 2 # South
        E = 0 # East 
        W = 1 # West

        # Desert
        if self.parent.parent.biome in [2, 17]:
            wall = materials.SmoothSandstone
            buttress = materials.Sandstone
            buttressStair = materials.SandstoneStairs
            soil = materials.Sand
            topsoil = materials.Sand
            floor = materials.Stone
            singleSlab = materials.SandstoneSlab
            doubleSlab = materials.ChiseledSandstone
            stair = materials.WoodenStairs

        # the fane is 2 chunks by 3 chunks
        # do we need to move it west or north?
        xsize = self.parent.parent.xsize
        zsize = self.parent.parent.zsize
        self.spos = copy(self.pos)
        movedX = 0
        movedZ = 0
        if self.spos.x > xsize-2:
            self.spos.x -= 1
            movedX += 1
        if self.spos.z > zsize-3:
            self.spos.z -= 2
            movedZ += 2
        # Now go through and override the ruins on any chunks we covered to be blank. 
        for p in iterate_cube(Vec(self.spos.x, 0, self.spos.z),
                              Vec(self.spos.x+1, 0, self.spos.z+2)):
            if p == self.pos:
                continue
            blank = new('blank', self.parent.parent.rooms[p])
            self.parent.parent.rooms[p].ruins = [blank]

        # where to begin
        # Floor height at NW corner
        start = self.parent.loc + Vec(0,self.parent.parent.room_height-3,0)
        # translate it 4 on the x/z to surround the stairs, translate it more x/z if
        # we had to move the building inside the dungeon boundary.
        # Move up to ground level for the entrance.
        start = start.trans( 4-self.parent.parent.room_size*movedX,
                             -self.parent.parent.entrance.low_height,
                             4-self.parent.parent.room_size*movedZ )

        #clear the inside
        for p in iterate_cube(start.trans(1,0,1), start.trans(22,-9,38) ):
            self.parent.parent.setblock(p, materials.Air )
        for p in iterate_cube(start.trans(8,-9,1), start.trans(15,-15,38) ):
            self.parent.parent.setblock(p, materials.Air )
        for p in iterate_cube(start.trans(0,1,0), start.trans(23,
                                                              self.parent.loc.y-start.y,
                                                              39) ):
            self.parent.parent.setblock(p, soil )
        for p in iterate_cube(start.trans(0,0,0), start.trans(23,0,39) ):
            self.parent.parent.setblock(p, topsoil )

        #make four corner towers
        locs = [ start, start.trans(16,0,0), start.trans(0,0,32), start.trans(16,0,32) ]

        for loc in locs:

            #level one
            for p in iterate_cube(loc, loc.trans(7,0,7) ):
                self.parent.parent.setblock(p , floor )

            for p in iterate_four_walls( loc, loc.trans(7,0,7), 10 ):
                self.parent.parent.setblock(p, wall)

            for p in iterate_cube( loc.down(3), loc.up(10) ):
                self.parent.parent.setblock(p.trans(1,0,-1), buttress)
                self.parent.parent.setblock(p.trans(3,0,-1), buttress)
                self.parent.parent.setblock(p.trans(4,0,-1), buttress)
                self.parent.parent.setblock(p.trans(6,0,-1), buttress)
                self.parent.parent.setblock(p.trans(1,0,8), buttress)
                self.parent.parent.setblock(p.trans(3,0,8), buttress)
                self.parent.parent.setblock(p.trans(4,0,8), buttress)
                self.parent.parent.setblock(p.trans(6,0,8), buttress)
                self.parent.parent.setblock(p.trans(-1,0,1), buttress)
                self.parent.parent.setblock(p.trans(-1,0,3), buttress)
                self.parent.parent.setblock(p.trans(-1,0,4), buttress)
                self.parent.parent.setblock(p.trans(-1,0,6), buttress)
                self.parent.parent.setblock(p.trans(8,0,1), buttress)
                self.parent.parent.setblock(p.trans(8,0,3), buttress)
                self.parent.parent.setblock(p.trans(8,0,4), buttress)
                self.parent.parent.setblock(p.trans(8,0,6), buttress)

            for p in [ Vec(1,-11,-1), Vec(3,-11,-1), Vec(4,-11,-1), Vec(6,-11,-1)]:
                self.parent.parent.setblock( loc.trans(p.x, p.y, p.z), buttressStair, S )
            for p in [ Vec(1,-11,8), Vec(3,-11,8), Vec(4,-11,8), Vec(6,-11,8)]:
                self.parent.parent.setblock( loc.trans(p.x, p.y, p.z), buttressStair, N )
            for p in [ Vec(-1,-11,1), Vec(-1,-11,3), Vec(-1,-11,4), Vec(-1,-11,6)]:
                self.parent.parent.setblock( loc.trans(p.x, p.y, p.z), buttressStair, E )
            for p in [ Vec(8,-11,1), Vec(8,-11,3), Vec(8,-11,4), Vec(8,-11,6)]:
                self.parent.parent.setblock( loc.trans(p.x, p.y, p.z), buttressStair, W )

            #level 2
            for p in iterate_cube( loc.up(11), loc.up(20) ):
                self.parent.parent.setblock(p.trans(0,0,0), wall)
                self.parent.parent.setblock(p.trans(1,0,0), buttress)
                self.parent.parent.setblock(p.trans(2,0,0), wall)
                self.parent.parent.setblock(p.trans(3,0,0), buttress)
                self.parent.parent.setblock(p.trans(4,0,0), buttress)
                self.parent.parent.setblock(p.trans(5,0,0), wall)
                self.parent.parent.setblock(p.trans(6,0,0), buttress)
                self.parent.parent.setblock(p.trans(7,0,0), wall)
                self.parent.parent.setblock(p.trans(0,0,7), wall)
                self.parent.parent.setblock(p.trans(1,0,7), buttress)
                self.parent.parent.setblock(p.trans(2,0,7), wall)
                self.parent.parent.setblock(p.trans(3,0,7), buttress)
                self.parent.parent.setblock(p.trans(4,0,7), buttress)
                self.parent.parent.setblock(p.trans(5,0,7), wall)
                self.parent.parent.setblock(p.trans(6,0,7), buttress)
                self.parent.parent.setblock(p.trans(7,0,7), wall)

                self.parent.parent.setblock(p.trans(0,0,1), buttress)
                self.parent.parent.setblock(p.trans(0,0,2), wall)
                self.parent.parent.setblock(p.trans(0,0,3), buttress)
                self.parent.parent.setblock(p.trans(0,0,4), buttress)
                self.parent.parent.setblock(p.trans(0,0,5), wall)
                self.parent.parent.setblock(p.trans(0,0,6), buttress)
                self.parent.parent.setblock(p.trans(7,0,1), buttress)
                self.parent.parent.setblock(p.trans(7,0,2), wall)
                self.parent.parent.setblock(p.trans(7,0,3), buttress)
                self.parent.parent.setblock(p.trans(7,0,4), buttress)
                self.parent.parent.setblock(p.trans(7,0,5), wall)
                self.parent.parent.setblock(p.trans(7,0,6), buttress)

            #for q in iterate_cube( p.trans( 2, 0 , 2), p.trans(6, 0 ,6) ):
            #    self.parent.parent.setblock( q, materials.Air )

            for p in [ Vec(1,-21,0), Vec(3,-21,0), Vec(4,-21,0), Vec(6,-21,0)]:
                self.parent.parent.setblock( loc.trans(p.x, p.y, p.z), buttressStair, S )
            for p in [ Vec(1,-21,7), Vec(3,-21,7), Vec(4,-21,7), Vec(6,-21,7)]:
                self.parent.parent.setblock( loc.trans(p.x, p.y, p.z), buttressStair, N )
            for p in [ Vec(0,-21,1), Vec(0,-21,3), Vec(0,-21,4), Vec(0,-21,6)]:
                self.parent.parent.setblock( loc.trans(p.x, p.y, p.z), buttressStair, E )
            for p in [ Vec(7,-21,1), Vec(7,-21,3), Vec(7,-21,4), Vec(7,-21,6)]:
                self.parent.parent.setblock( loc.trans(p.x, p.y, p.z), buttressStair, W )


            #level 3
            for p in iterate_cube( loc.up(21), loc.up(30) ):
                self.parent.parent.setblock(p.trans(1,0,1), buttress)
                self.parent.parent.setblock(p.trans(2,0,1), wall)
                self.parent.parent.setblock(p.trans(3,0,1), buttress)
                self.parent.parent.setblock(p.trans(4,0,1), buttress)
                self.parent.parent.setblock(p.trans(5,0,1), wall)
                self.parent.parent.setblock(p.trans(6,0,1), buttress)
                self.parent.parent.setblock(p.trans(1,0,6), buttress)
                self.parent.parent.setblock(p.trans(2,0,6), wall)
                self.parent.parent.setblock(p.trans(3,0,6), buttress)
                self.parent.parent.setblock(p.trans(4,0,6), buttress)
                self.parent.parent.setblock(p.trans(5,0,6), wall)
                self.parent.parent.setblock(p.trans(6,0,6), buttress)

                self.parent.parent.setblock(p.trans(1,0,2), wall)
                self.parent.parent.setblock(p.trans(1,0,3), buttress)
                self.parent.parent.setblock(p.trans(1,0,4), buttress)
                self.parent.parent.setblock(p.trans(1,0,5), wall)
                self.parent.parent.setblock(p.trans(6,0,2), wall)
                self.parent.parent.setblock(p.trans(6,0,3), buttress)
                self.parent.parent.setblock(p.trans(6,0,4), buttress)
                self.parent.parent.setblock(p.trans(6,0,5), wall)

            #for q in iterate_cube( p.trans( 3, 0 , 3), p.trans(5, 0 ,5) ):
            #    self.parent.parent.setblock( q, materials.Air )

            #follies
            for p in iterate_cube( loc.up(32), loc.up(33) ):
                self.parent.parent.setblock(p.trans(2,0,2), wall)
                self.parent.parent.setblock(p.trans(2,0,5), wall)
                self.parent.parent.setblock(p.trans(5,0,2), wall)
                self.parent.parent.setblock(p.trans(5,0,5), wall)

            for p in iterate_cube( loc.trans(2,-31,2), loc.trans( 5 ,-31, 5 )):
                self.parent.parent.setblock(p, wall)

            # Randomly ruin
            if random.random() < .50:
                h = random.randint(0,10)
                ruinBlocks(loc.trans(0, -25+h, 0), loc.trans(7,-25+h,7), 10+h,
                           self.parent.parent, aggressive=True)


        #curtains
        for p in iterate_cube(start.trans( 1,0,8), start.trans( 1,-9, 31 ) ):
            self.parent.parent.setblock(p, wall)
        for p in iterate_cube(start.trans( 22,0,8), start.trans( 22,-9, 31 ) ):
            self.parent.parent.setblock(p, wall)
        for p in iterate_cube(start.trans( 8,0,1), start.trans( 15,-15, 1 ) ):
            self.parent.parent.setblock(p, wall)
        for p in iterate_cube(start.trans( 8,0,38), start.trans( 15,-15, 38 ) ):
            self.parent.parent.setblock(p, wall)

        #wing ceilings
        for p in iterate_cube(start.trans( 1,-10,8 ), start.trans( 7,-10, 31)):
            self.parent.parent.setblock(p,wall)
        for p in iterate_cube(start.trans( 15,-10,8 ), start.trans( 22,-10, 31)):
            self.parent.parent.setblock(p,wall)

        #tall ceiling
        for p in iterate_cube(start.trans( 8,-15,1 ), start.trans( 15,-15, 38)):
            if ( p.z % 7 != 0 ):
                self.parent.parent.setblock(p,wall)
        #and curtains
        for p in iterate_cube(start.trans( 8,-10,1 ), start.trans( 8,-15, 38)):
            self.parent.parent.setblock(p,wall)
            self.parent.parent.setblock(p.trans(7,0,0),wall)

        #floors
        for p in iterate_cube(start.trans( 8,0,1 ), start.trans( 15,0, 38)):
            self.parent.parent.setblock(p,floor)
        for p in iterate_cube(start.trans( 1,0,8 ), start.trans( 7,0, 31)):
            self.parent.parent.setblock(p,floor)
            self.parent.parent.setblock(p.trans(14,0,0),floor)

        #interior   bring it in from 1,0,8  21,0,31
        for p in iterate_cube(start.trans( 3, 0, 12), start.trans( 19, 0, 29) ):
            if( p.x == start.x+11 or p.x == start.x+12 ):
                #carpet would probably have deteriorated on a top floor
                continue
            elif( p.z % 2 == 0 ):
                #pew
                self.parent.parent.setblock(p.up(1), stair, S)

        #raised altar
        for p in iterate_cube(start.trans( 8, -1, 2), start.trans( 15, -1, 7) ):
            self.parent.parent.setblock(p, wall)
        for p in iterate_cube(start.trans( 7, -1, 8), start.trans( 16, -1, 8) ):
            self.parent.parent.setblock(p, stair, N)

        mats =  [ materials.Air, #0
                  buttress,          #1
                  doubleSlab,  #2
                  materials.IronBars,    #3
                  singleSlab]   #4
        template = [
           [[ 0, 0, 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0, 0, 0],
            [ 0, 0, 2, 2, 2, 2, 0, 0],
            [ 0, 0, 0, 0, 0, 0, 0, 0],
            [ 3, 3, 3, 0, 0, 3, 3, 3]],
           [[ 0, 0, 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0, 0, 0],
            [ 0, 0, 4, 0, 0, 4, 0, 0],
            [ 0, 0, 0, 0, 0, 0, 0, 0],
            [ 0, 0, 0, 0, 0, 0, 0, 0]],
           [[ 4, 0, 0, 0, 0, 0, 0, 4],
            [ 1, 0, 0, 0, 0, 0, 0, 1],
            [ 1, 0, 0, 0, 0, 0, 0, 1],
            [ 4, 0, 0, 0, 0, 0, 0, 4],
            [ 1, 0, 0, 0, 0, 0, 0, 1],
            [ 0, 0, 0, 0, 0, 0, 0, 0]]
        ]

        o=start.trans(8,-2,2)
        for y in xrange(3):
            for x in xrange(8):
                for z in xrange(6):
                    p = o.trans(x,-y,z) 
                    self.parent.parent.setblock(p,
                                               mats[template[y][z][x]] )
        # Supply chest
        loc = start.trans(8+3, -2, 2+2)
        self.parent.parent.setblock(loc, materials.Chest,2)
        self.parent.parent.setblock(loc.trans(1,0,0), materials.Chest,2) #for symmetry's sake (:
        self.parent.parent.addchest(loc, 0)

        # Exit Portal
        self.parent.parent.dinfo['portal_exit'] = loc.s(10)

        #windows
        locs = [ Vec(1,-3,12), Vec(22,-3,12), Vec(1,-3,20), Vec(22,-3,20), Vec(1,-3,28), Vec(22,-3,28) ]
        for loc in locs:
            self.parent.parent.delblock( start.trans( loc.x,loc.y-5,loc.z) )
            for p in iterate_cube(start.trans( loc.x, loc.y, loc.z), start.trans( loc.x, loc.y-4, loc.z) ):
                self.parent.parent.delblock(p.trans(0,0,-1))
                self.parent.parent.delblock(p)
                self.parent.parent.delblock(p.trans(0,0,1))

        #door
        self.parent.parent.delblock(start.trans( 11,-11,38 ) )
        self.parent.parent.delblock(start.trans( 12,-11,38 ) )
        for p in iterate_cube(start.trans( 10, -1, 38 ), start.trans( 13, -10, 38 ) ):
            self.parent.parent.delblock(p)

        #inner doorways
        locs = [ Vec(5,-1,7), Vec(2+16,-1,7), Vec(7,-1,32+2), Vec(16,-1,32+2) ]
        for loc in locs:
            self.parent.parent.setblock( start.trans(loc.x, loc.y, loc.z), materials.Air )
            self.parent.parent.setblock( start.trans(loc.x, loc.y-1, loc.z), materials.Air )

        # extend the stair up
        estart = self.parent.loc.up(self.parent.parent.room_height-3)
        for p in iterate_cube(estart.trans(6,0,6), estart.trans(9,-6,9)):
            self.parent.parent.setblock(p, materials.Air)
        mat = materials.StoneSlab
        for p in iterate_spiral(Vec(estart.x+6,estart.y,estart.z+6),
                                Vec(estart.x+6+4,estart.y,estart.z+6+4),
                                10):
            self.parent.parent.setblock(Vec(p.x,
                                        p.y/2,
                                        p.z), mat, mat.data+((p.y&1)^1)*8)
        for p in iterate_four_walls(estart.trans(5,0,5),
                                    estart.trans(10,0,10),3):
            self.parent.parent.setblock(p, wall)


## Other ruins

class CircularTower(Blank):
    _name = 'circulartower'

    def setData(self):
        self.wallsf = iterate_tube

    def render(self):
        # Use sandstone for deserts
        if self.parent.parent.biome in [2, 17]:
            mat = materials.meta_decoratedsandstone
        # Use cobblestone for jungle and swamp
        elif self.parent.parent.biome in [6, 7, 11, 21, 22]:
            mat = materials.meta_mossycobble
        # Otherwise use stone brick
        else:
            mat = materials.meta_mossystonebrick

        c1 = self.loc
        c3 = c1 + Vec(self.parent.parent.room_size-2,
                      0,
                      self.parent.parent.room_size-2)
        # Jitter!
        scale = random.randint(0, 8)
        x_jitter = random.randint(0, scale)
        z_jitter = random.randint(0, scale)
        c1 += Vec(scale-x_jitter, 0, scale-z_jitter)
        c3 += Vec(-x_jitter, 0, -z_jitter)

        height = int(self.parent.parent.room_height*1.5)
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
        height = self.parent.parent.room_height*2
        sb = self.parent.parent.setblock
        # Sandstone in deserts
        if self.parent.parent.biome in [2, 17]:
            mat = materials.meta_decoratedsandstone
            stair = materials.SandstoneStairs
            slab1 = materials.SandstoneSlab
            slab2 = materials.SandstoneSlab
        # Swamps and jungles are cobblestone
        elif self.parent.parent.biome in [6, 7, 11, 21, 22]:
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
                c1 = self.loc + Vec(8*xo, 0, 8*zo)
                c3 = c1 + Vec(7, 0, 7)
                # columns
                for p in iterate_cube(c1, c1.trans(0,-height,0)):
                    sb(p,              mat, hide=True)
                    sb(p.trans(7,0,0), mat, hide=True)
                    sb(p.trans(7,0,7), mat, hide=True)
                    sb(p.trans(0,0,7), mat, hide=True)
                # First level
                p = c1.trans(0,-height+2,0)
                sb(p.trans(1,0,0), stair, 1+4)
                sb(p.trans(6,0,0), stair, 0+4)
                sb(p.trans(0,0,1), stair, 3+4)
                sb(p.trans(7,0,1), stair, 3+4)
                sb(p.trans(0,0,6), stair, 2+4)
                sb(p.trans(7,0,6), stair, 2+4)
                sb(p.trans(1,0,7), stair, 1+4)
                sb(p.trans(6,0,7), stair, 0+4)
                # Second level
                p = p.trans(0,-1,0)
                sb(p.trans(1,0,0), mat)
                sb(p.trans(6,0,0), mat)
                sb(p.trans(0,0,1), mat)
                sb(p.trans(7,0,1), mat)
                sb(p.trans(0,0,6), mat)
                sb(p.trans(7,0,6), mat)
                sb(p.trans(1,0,7), mat)
                sb(p.trans(6,0,7), mat)
                # ---
                sb(p.trans(2,0,0), stair, 1+4)
                sb(p.trans(5,0,0), stair, 0+4)
                sb(p.trans(0,0,2), stair, 3+4)
                sb(p.trans(7,0,2), stair, 3+4)
                sb(p.trans(0,0,5), stair, 2+4)
                sb(p.trans(7,0,5), stair, 2+4)
                sb(p.trans(2,0,7), stair, 1+4)
                sb(p.trans(5,0,7), stair, 0+4)
                # Top layer
                p = p.trans(0,-1,0)
                for p in iterate_four_walls(p, p.trans(7,0,7), 0):
                    if (cfg.ruin_ruins == False or
                        random.randint(1,100) <= 50):
                        if (random.randint(1,100) <= 25):
                            sb(p, slab1)
                        else:
                            sb(p, slab2)

                # Maybe ruin this section
                if (random.randint(1,100) <= 50):
                    ruinBlocks(c1.up(1), c3.up(1), height, self.parent.parent)


class HouseFrame(Blank):
    _name = 'houseframe'

    def render(self):
        # Use sandstone for deserts
        if self.parent.parent.biome in [2, 17]:
            mat = materials.meta_decoratedsandstone
            stair = materials.SandstoneStairs
        # Use cobblestone for jungle and swamp
        elif self.parent.parent.biome in [6, 7, 11, 21, 22]:
            mat = materials.meta_mossycobble
            stair = materials.StoneStairs
        # Otherwise use stone brick
        else:
            mat = materials.meta_mossystonebrick
            stair = materials.StoneBrickStairs

        #what direction will the stairs face?
        E = 0
        W = 1

        # got the mats. now draw the base. start one higher so it's less buried
        start = self.loc.trans(3+random.randint(0,2) , -1, 3+random.randint(0,2))
        for p in iterate_cube(start, start.trans(7,0,7) ):
            self.parent.parent.setblock(p, mat)

        # now draw the A frame
        start = start.trans(0,-1,0)

        #will the head be in the south (7) or north (0)
        head = random.randint(0,1) * 7;

        for p in iterate_cube(start.trans(0,0,head) , start.trans(6,-3,head) ):
            self.parent.parent.setblock(p, mat)

        for p in iterate_cube(start.trans(1,-4,head), start.trans(5,-4,head) ):
            self.parent.parent.setblock(p, mat)
        self.parent.parent.setblock(start.trans(0,-4,head), stair, E)
        self.parent.parent.setblock(start.trans(6,-4,head), stair, W)

        for p in iterate_cube(start.trans(2,-5,head), start.trans(4,-5,head) ):
            self.parent.parent.setblock(p, mat)
        self.parent.parent.setblock(start.trans(1,-5,head), stair, E)
        self.parent.parent.setblock(start.trans(5,-5,head), stair, W)

        self.parent.parent.setblock(start.trans(2,-6,head), stair, E)
        self.parent.parent.setblock(start.trans(3,-6,head), mat)
        self.parent.parent.setblock(start.trans(4,-6,head), stair, W)

        # cut out the window(s)
        if( random.randint(0,100) < 50 ):
            #two tall windows
            self.parent.parent.delblock(start.trans(2,-1,head))
            self.parent.parent.delblock(start.trans(4,-1,head))
            self.parent.parent.delblock(start.trans(2,-2,head))
            self.parent.parent.delblock(start.trans(4,-2,head))
            self.parent.parent.delblock(start.trans(2,-3,head))
            self.parent.parent.delblock(start.trans(4,-3,head))
        else:
            #one big arch
            for p in iterate_cube(start.trans(2,0,head), start.trans(4,-2,head) ):
                self.parent.parent.delblock(p)
            self.parent.parent.setblock(start.trans(2,-3,head), stair, W+4)
            self.parent.parent.delblock(start.trans(3,-3,head))
            self.parent.parent.setblock(start.trans(4,-3,head), stair, E+4)

        # then draw the long wall
        for p in iterate_cube(start, start.trans(0,0,7) ):
            self.parent.parent.setblock(p, mat)
            self.parent.parent.setblock(p.up(1), mat)
            if( random.randint(0,100) < 50 ):
                self.parent.parent.setblock(p.up(2), mat)

        # and the corner post opposite
        for p in iterate_cube(start.trans(7,0,7-head), start.trans(7,-3,7-head) ):
            self.parent.parent.setblock(p, mat)

        # and maybe some ancient pottery
        if (random.randint(1,100) < 10 ):
            self.parent.parent.setblock(start.trans(2+random.randint(0,3),0,2), materials.FlowerPot, soft=True)
            self.parent.parent.setblock(start.trans(2+random.randint(0,3),0,3), materials.FlowerPot, soft=True)

        #ruin it! (maybe)
        if (random.randint(1,100) < 50):
            ruinBlocks(start, start.trans(7,0,7), 7, self.parent.parent)


def ruinBlocks (p1, p2, height, dungeon, override=False, aggressive=False):
    pn = perlin.SimplexNoise(256)
    if (override == True or
        cfg.ruin_ruins == False):
        return
    for x in xrange(p1.x, p2.x+1):
        for z in xrange(p1.z, p2.z+1):
            depth = (pn.noise3(x / 4.0, 0, z / 4.0) + 1.0) / 2.0 * height
            for p in iterate_cube(Vec(x, p1.y-depth, z),
                                  Vec(x, p1.y-height, z)):
                dungeon.delblock(p)
    # Look for floating blocks
    floaters = []
    for p in iterate_cube(p1, Vec(p2.x, p2.y-height, p2.z)):
        if ((p in dungeon.blocks and
             dungeon.blocks[p].material != materials.Air) and
            (p.down(1) not in dungeon.blocks or
                 dungeon.blocks[p.down(1)].material == materials.Air) and
            (p.n(1) not in dungeon.blocks or
                 dungeon.blocks[p.n(1)].material == materials.Air) and
            (p.s(1) not in dungeon.blocks or
                 dungeon.blocks[p.s(1)].material == materials.Air) and
            (p.e(1) not in dungeon.blocks or
                 dungeon.blocks[p.e(1)].material == materials.Air) and
            (p.w(1) not in dungeon.blocks or
                 dungeon.blocks[p.w(1)].material == materials.Air)):
            floaters.append(p)
    for p in floaters:
        dungeon.delblock(p)
    # In aggressive mode, we'll cull out anything that is not supported directly
    # underneath. Usually this breaks the stairs, but looks better for some
    # structures.
    if aggressive is True:
        for p in iterate_cube(p1, p2):
            for q in xrange(p.y, p.up(height).y, -1):
                pp = Vec(p.x, q, p.z)
                if (pp.down(1) not in dungeon.blocks or
                     dungeon.blocks[pp.down(1)].material == materials.Air):
                    dungeon.delblock(pp)


# Catalog the ruins we know about. 
_ruins = {}
# List of classes in this module.
for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
    # Only count the ones that are subclasses if of ruins.Blank
    if issubclass(obj, Blank):
        _ruins[obj._name] = obj

def new (name, parent):
    '''Return a new instance of the ruin of a given name. Supply the parent
    dungeon object.'''
    if name in _ruins.keys():
        return _ruins[name](parent)
    return Blank(parent)

