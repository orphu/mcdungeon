import sys
import inspect

import materials
import utils
import rooms
import loottable
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
        #print 'ruin depth:', self.parent.parent.position.y, self.depth, -vtrans
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
        size = self.parent.parent.room_size
        height = int(self.parent.parent.room_height*cfg.tower)
        p = self.loc
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
                self.parent.parent.setblock(p, materials.meta_mossycobble)
        # Floor. From pyramid base to just above ceiling. 
        for p in iterate_four_walls(c1,
                                    c3, c1.y):
            self.parent.parent.setblock(p, materials.meta_mossystonebrick, hide=True)
        # Cover the floor with sand
        pn = perlin.SimplexNoise(256)
        for p in iterate_cube(c1, c3):
            d = ((Vec2f(p.x, p.z) - Vec2f(c1.x+32, c1.z+32)).mag()) / 64
            n = (pn.noise3(p.x / 4.0, p.y / 4.0, p.z / 4.0) + 1.0) / 2.0
            if (n >= d+.20):
                self.parent.parent.setblock(p, materials.Sand)
            elif (n >= d+.10):
                self.parent.parent.setblock(p, materials.Sandstone)
            elif (n >= d):
                self.parent.parent.setblock(p, materials.Gravel)
            else:
                self.parent.parent.setblock(p, materials.meta_mossycobble)
        # Build internal ruins. 
        cchance =80
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
                self.parent.parent.setblock(cp, materials.Chest)
                self.parent.parent.addchest(cp, 0)
            height = 5
            for j in wfunc(pp1, pp2, 0):
                depth = (pn.noise3(j.x / 4.0,
                                   0,
                                   j.z / 4.0) + 1.0) / 2.0 * height
                for x in iterate_cube(j, j.up(depth)):
                    if (x in self.parent.parent.blocks and
                        self.parent.parent.blocks[x].material == materials.Air):
                        self.parent.parent.setblock(x, materials.Sandstone)

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
        mat1 = materials.WoodenSlab
        mat2 = materials.WoodPlanks
        if random.randint(1,100) <= 0:
            mat1 = materials.StoneSlab
            mat2 = materials.DoubleSlab
        for p in iterate_spiral(Vec(start.x+1,7,start.z+1),
                                Vec(start.x+5,7,start.z+5),
                                (abs(c1.y)+3)*2):
            mat = mat1
            if ((p.y%2) == 0):
                mat = mat2
            self.parent.parent.setblock(Vec(p.x,
                                        0+int(p.y/2),
                                        p.z), mat)
        # Entrances.
        # Draw stairs up the sides.
        for y in xrange(29):
            # North Side
            # caps on either side
            self.parent.parent.setblock(c1.trans(y,-y-1,29),
                                        materials.SandstoneSlab)
            self.parent.parent.setblock(c1.trans(y,-y-1,34),
                                        materials.SandstoneSlab)
            # draw different stuff depending on the height
            # Go ahead and draw exterior stairs at every level.
            # (we'll overwrite some below)
            for p in iterate_cube(c1.trans(y, -y, 30),
                                  c1.trans(y, -y, 33)):
                self.parent.parent.setblock(p,
                                            materials.StoneStairs, 0)
                self.parent.parent.setblock(p.trans(1,0,0),
                                            materials.meta_mossycobble, 0)
            # Above floor, but below entry level, 
            # draw the interior stairs and airspace.
            if (y > 0 and y <= self.ent_n):
                for p in iterate_cube(c1.trans(y, -y, 28),
                                      c1.trans(y, -y, 35)):
                    for x in xrange(2,6):
                        self.parent.parent.setblock(p.trans(x,0,0),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(6,0,0),
                                                materials.StoneStairs, 0)
                    self.parent.parent.setblock(p.trans(7,0,0),
                                                materials.meta_mossycobble, 0)
            # At entry level, draw a platform floor. 
            if (self.ent_n == y):
                for p in iterate_cube(c1.trans(y+1, -y, 30),
                                      c1.trans(y+8, -y, 33)):
                    self.parent.parent.setblock(p, materials.Stone)
            # Above the entry platform, draw some walls
            if (y > self.ent_n and y < self.ent_n+4):
                p = c1.trans(y, -y, 30)
                self.parent.parent.setblock(p, materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(1,0,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(1,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(0,0,2), materials.Air)
                self.parent.parent.setblock(p.trans(1,0,2), materials.Air)
                self.parent.parent.setblock(p.trans(0,0,3), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(1,0,3), materials.meta_mossycobble)
            # Add a ceiling for the entryway.
            if (y ==  self.ent_n+4):
                p = c1.trans(y-3, -y, 30)
                self.parent.parent.setblock(p.trans(1,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,2,0), materials.meta_mossycobble)
                p = c1.trans(y-3, -y, 33)
                self.parent.parent.setblock(p.trans(1,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,2,0), materials.meta_mossycobble)
                for p in iterate_cube(c1.trans(y-3, -y, 30),
                                      c1.trans(y+1, -y, 33)):
                    self.parent.parent.setblock(p, materials.meta_mossycobble)


            # South Side
            self.parent.parent.setblock(c1.trans(63-y,-y-1,29),
                                        materials.SandstoneSlab)
            self.parent.parent.setblock(c1.trans(63-y,-y-1,34),
                                        materials.SandstoneSlab)
            for p in iterate_cube(c1.trans(63-y, -y, 30),
                                  c1.trans(63-y, -y, 33)):
                self.parent.parent.setblock(p,
                                            materials.StoneStairs, 1)
                self.parent.parent.setblock(p.trans(-1,0,0),
                                            materials.meta_mossycobble, 0)
            if (y > 0 and y <= self.ent_s):
                for p in iterate_cube(c1.trans(63-y, -y, 28),
                                      c1.trans(63-y, -y, 35)):
                    for x in xrange(2,6):
                        self.parent.parent.setblock(p.trans(-x,0,0),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(-6,0,0),
                                                materials.StoneStairs, 1)
                    self.parent.parent.setblock(p.trans(-7,0,0),
                                                materials.meta_mossycobble, 0)
            if (self.ent_s == y):
                for p in iterate_cube(c1.trans(63-y-1, -y, 30),
                                      c1.trans(63-y-8, -y, 33)):
                    self.parent.parent.setblock(p, materials.Stone)
            if (y > self.ent_s and y < self.ent_s+4):
                p = c1.trans(63-y, -y, 30)
                self.parent.parent.setblock(p, materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(-1,0,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(-1,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(0,0,2), materials.Air)
                self.parent.parent.setblock(p.trans(-1,0,2), materials.Air)
                self.parent.parent.setblock(p.trans(0,0,3), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(-1,0,3), materials.meta_mossycobble)
            if (y ==  self.ent_s+4):
                p = c1.trans(63-y+3, -y, 30)
                self.parent.parent.setblock(p.trans(-1,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,2,0), materials.meta_mossycobble)
                p = c1.trans(63-y+3, -y, 33)
                self.parent.parent.setblock(p.trans(-1,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,2,0), materials.meta_mossycobble)
                for p in iterate_cube(c1.trans(63-y+3, -y, 30),
                                      c1.trans(63-y-1, -y, 33)):
                    self.parent.parent.setblock(p, materials.meta_mossycobble)

            # West Side
            self.parent.parent.setblock(c1.trans(29,-y-1,y),
                                        materials.SandstoneSlab)
            self.parent.parent.setblock(c1.trans(34,-y-1,y),
                                        materials.SandstoneSlab)
            for p in iterate_cube(c1.trans(30, -y, y),
                                  c1.trans(33, -y, y)):
                self.parent.parent.setblock(p, materials.StoneStairs, 2)
                self.parent.parent.setblock(p.trans(0,0,1),
                                            materials.meta_mossycobble, 0)
            if (y > 0 and y <= self.ent_w):
                for p in iterate_cube(c1.trans(28, -y, y),
                                      c1.trans(35, -y, y)):
                    for x in xrange(2,6):
                        self.parent.parent.setblock(p.trans(0,0,x),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(0,0,6),
                                                materials.StoneStairs, 2)
                    self.parent.parent.setblock(p.trans(0,0,7),
                                                materials.meta_mossycobble, 0)
            if (self.ent_w == y):
                for p in iterate_cube(c1.trans(30, -y, y+1),
                                      c1.trans(33, -y, y+8)):
                    self.parent.parent.setblock(p, materials.Stone)
            if (y > self.ent_w and y < self.ent_w+4):
                p = c1.trans(30, -y, y)
                self.parent.parent.setblock(p, materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,0,1), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(1,0,0), materials.Air)
                self.parent.parent.setblock(p.trans(1,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(2,0,0), materials.Air)
                self.parent.parent.setblock(p.trans(2,0,1), materials.Air)
                self.parent.parent.setblock(p.trans(3,0,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(3,0,1), materials.meta_mossycobble)
            if (y ==  self.ent_w+4):
                p = c1.trans(30, -y, y-3)
                self.parent.parent.setblock(p.trans(0,1,1), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,2,0), materials.meta_mossycobble)
                p = c1.trans(33, -y, y-3)
                self.parent.parent.setblock(p.trans(0,1,1), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,2,0), materials.meta_mossycobble)
                for p in iterate_cube(c1.trans(30, -y, y-3),
                                      c1.trans(33, -y, y+1)):
                    self.parent.parent.setblock(p, materials.meta_mossycobble)

            # East Side
            self.parent.parent.setblock(c1.trans(29,-y-1,63-y),
                                        materials.SandstoneSlab)
            self.parent.parent.setblock(c1.trans(34,-y-1,63-y),
                                        materials.SandstoneSlab)
            for p in iterate_cube(c1.trans(30, -y, 63-y),
                                  c1.trans(33, -y, 63-y)):
                self.parent.parent.setblock(p,
                                            materials.StoneStairs, 3)
                self.parent.parent.setblock(p.trans(0,0,-1),
                                            materials.meta_mossycobble, 0)
            if (y > 0 and y <= self.ent_e):
                for p in iterate_cube(c1.trans(28, -y, 63-y),
                                      c1.trans(35, -y, 63-y)):
                    for x in xrange(2,6):
                        self.parent.parent.setblock(p.trans(0,0,-x),
                                                    materials.Air, 0)
                    self.parent.parent.setblock(p.trans(0,0,-6),
                                                materials.StoneStairs, 3)
                    self.parent.parent.setblock(p.trans(0,0,-7),
                                                materials.meta_mossycobble, 0)
            if (self.ent_e == y):
                for p in iterate_cube(c1.trans(30, -y, 63-y-1),
                                      c1.trans(33, -y, 63-y-8)):
                    self.parent.parent.setblock(p, materials.Stone)
            if (y > self.ent_e and y < self.ent_e+4):
                p = c1.trans(30, -y, 63-y)
                self.parent.parent.setblock(p, materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,0,-1), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(1,0,0), materials.Air)
                self.parent.parent.setblock(p.trans(1,0,-1), materials.Air)
                self.parent.parent.setblock(p.trans(2,0,0), materials.Air)
                self.parent.parent.setblock(p.trans(2,0,-1), materials.Air)
                self.parent.parent.setblock(p.trans(3,0,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(3,0,-1), materials.meta_mossycobble)
            if (y ==  self.ent_e+4):
                p = c1.trans(30, -y, 63-y+3)
                self.parent.parent.setblock(p.trans(0,1,-1), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,2,0), materials.meta_mossycobble)
                p = c1.trans(33, -y, 63-y+3)
                self.parent.parent.setblock(p.trans(0,1,-1), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,1,0), materials.meta_mossycobble)
                self.parent.parent.setblock(p.trans(0,2,0), materials.meta_mossycobble)
                for p in iterate_cube(c1.trans(30, -y, 63-y+3),
                                      c1.trans(33, -y, 63-y-1)):
                    self.parent.parent.setblock(p, materials.meta_mossycobble)

        # Topper
        # Supports
        self.parent.parent.setblock(c1.trans(29, -29, 29), materials.Sandstone)
        self.parent.parent.setblock(c1.trans(29, -30, 29), materials.Sandstone)
        self.parent.parent.setblock(c1.trans(34, -29, 29), materials.Sandstone)
        self.parent.parent.setblock(c1.trans(34, -30, 29), materials.Sandstone)
        self.parent.parent.setblock(c1.trans(29, -29, 34), materials.Sandstone)
        self.parent.parent.setblock(c1.trans(29, -30, 34), materials.Sandstone)
        self.parent.parent.setblock(c3.trans(-29, -29,-29), materials.Sandstone)
        self.parent.parent.setblock(c3.trans(-29, -30,-29), materials.Sandstone)
        # Roof
        for p in iterate_cube(c1.trans(28, -31, 28),c3.trans(-28, -31, -28)):
            self.parent.parent.setblock(p, materials.SandstoneSlab)
        for p in iterate_cube(c1.trans(29, -28, 29),c3.trans(-29, -28, -29)):
            self.parent.parent.setblock(p, materials.Stone)
        for p in iterate_cube(c1.trans(32, -31, 32),c3.trans(-32, -28, -32)):
            self.parent.parent.setblock(p, materials.Air)
        # Supply chest
        p = c1.trans(30, -29, 30)
        self.parent.parent.setblock(p, materials.Chest)
        self.parent.parent.addchest(p, 0)



class RoundTowerEntrance(Blank):
    _name = 'roundtowerentrance'
    _ruin = False
    _mat = materials.meta_mossycobble

    def render (self):
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
        maxlev = 127 - self.parent.parent.position.y
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
        mat1 = materials.WoodenSlab
        mat2 = materials.WoodPlanks
        if random.randint(1,100) <= 50:
            mat1 = materials.StoneSlab
            mat2 = materials.DoubleSlab
        for p in iterate_spiral(Vec(start.x,room_floor+4,start.z),
                                Vec(start.x+4,room_floor+4,start.z+4),
                                (room_floor-blev)*2):
            mat = mat1
            if ((p.y%2) == 0):
                mat = mat2
            self.parent.parent.setblock(Vec(p.x,
                                        p.y/2,
                                        p.z), mat)
        # Supply chest
        pos = Vec(b1.x, clev, b1.z-1)
        self.parent.parent.setblock(pos, materials.Chest)
        self.parent.parent.addchest(pos, 0)

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
    _mat = materials.meta_mossycobble

    def render (self):
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
        maxlev = 127 - self.parent.parent.position.y
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
        mat1 = materials.WoodenSlab
        mat2 = materials.WoodPlanks
        if random.randint(1,100) <= 50:
            mat1 = materials.StoneSlab
            mat2 = materials.DoubleSlab
        for p in iterate_spiral(Vec(start.x,room_floor+4,start.z),
                                Vec(start.x+4,room_floor+4,start.z+4),
                                (room_floor-blev)*2):
            mat = mat1
            if ((p.y%2) == 0):
                mat = mat2
            self.parent.parent.setblock(Vec(p.x,
                                        p.y/2,
                                        p.z), mat)
        # Supply chest
        pos = c1.trans(1, 0, 1)
        self.parent.parent.setblock(pos, materials.Chest)
        self.parent.parent.addchest(pos, 0)

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

class SquareTowerEntranceStoneBrick(SquareTowerEntrance):
    _name = 'squaretowerentrancestonebrick'
    _ruin = False
    _mat = materials.meta_mossystonebrick

class RuinedSquareTowerEntrance(SquareTowerEntrance):
    _name = 'ruinedsquaretowerentrance'
    _ruin = True
    _mat = materials.meta_mossycobble

class RuinedSquareTowerEntranceStoneBrick(SquareTowerEntrance):
    _name = 'ruinedsquaretowerentrancestonebrick'
    _ruin = True
    _mat = materials.meta_mossystonebrick

class RoundTowerEntranceStoneBrick(RoundTowerEntrance):
    _name = 'roundtowerentrancestonebrick'
    _ruin = False
    _mat = materials.meta_mossystonebrick

class RuinedRoundTowerEntrance(RoundTowerEntrance):
    _name = 'ruinedroundtowerentrance'
    _ruin = True
    _mat = materials.meta_mossycobble

class RuinedRoundTowerEntranceStoneBrick(RoundTowerEntrance):
    _name = 'ruinedroundtowerentrancestonebrick'
    _ruin = True
    _mat = materials.meta_mossystonebrick

class CircularTower(Blank):
    _name = 'circulartower'

    def setData(self):
        self.wallsf = iterate_tube

    def render(self):
        c1 = self.loc.trans(3, 0, 3)
        c3 = c1 + Vec(self.parent.parent.room_size-7,
                      0,
                      self.parent.parent.room_size-7)
        height = int(self.parent.parent.room_height*1.5)
        #print 'ruin:', c1, c3, height
        for p in self.wallsf(c1, c3, height):
            self.parent.parent.setblock(p, materials.meta_mossystonebrick, hide=True)
        ruinBlocks(c1, c3, height, self.parent.parent)


class SquareTower(CircularTower):
    _name = 'squaretower'

    def setData(self):
        self.wallsf = iterate_four_walls


class Arches(Blank):
    _name = 'arches'

    def render(self):
        height = self.parent.parent.room_height*2
        sb = self.parent.parent.setblock
        mat = materials.meta_mossystonebrick
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
                sb(p.trans(1,0,0), mat)
                sb(p.trans(6,0,0), mat)
                sb(p.trans(0,0,1), mat)
                sb(p.trans(7,0,1), mat)
                sb(p.trans(0,0,6), mat)
                sb(p.trans(7,0,6), mat)
                sb(p.trans(1,0,7), mat)
                sb(p.trans(6,0,7), mat)
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
                sb(p.trans(2,0,0), mat)
                sb(p.trans(5,0,0), mat)
                sb(p.trans(0,0,2), mat)
                sb(p.trans(7,0,2), mat)
                sb(p.trans(0,0,5), mat)
                sb(p.trans(7,0,5), mat)
                sb(p.trans(2,0,7), mat)
                sb(p.trans(5,0,7), mat)
                # Top layer
                p = p.trans(0,-1,0)
                for p in iterate_four_walls(p, p.trans(7,0,7), 0):
                    if (cfg.ruin_ruins == False or
                        random.randint(1,100) <= 50):
                        if (random.randint(1,100) <= 25):
                            sb(p, materials.StoneBrickSlab)
                        else:
                            sb(p, materials.CobblestoneSlab)

                # Maybe ruin this section
                if (random.randint(1,100) <= 50):
                    ruinBlocks(c1, c3, height, self.parent.parent)


def ruinBlocks (p1, p2, height, dungeon, override=False):
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

