# Cave factory produces a cave-like structure with no disconnected
# rooms. Caves typically have a smooth, twisty appearance with lots of
# alcoves. This is based largely on the cellular automata examples at:
#
#  http://roguebasin.roguelikedevelopment.org
#
# It also borrows code for joining disconnected cells from Dana Larose's 
# example:
# http://pixelenvy.ca/wa/ca_cave.html
#
# I've tweaked the CA generations a bit to smooth out the cell joins, and added
# support for building connecting edges. I use this to build connected tiles of
# caves and hallways joining to other parts of the dungeon.
import sys
from random import randrange, random, choice

from disjoint_set import DisjointSet

FLOOR = 1
WALL = 2
TUNNEL = 3

class new:
    def __init__(self,length,width,walls=0.40):
        self.__length = length
        self.__width = width
        self.__exits = []
        self.__map = []
        self.__buf_map = []
        self.__gen_initial_map(walls)
        self.__ds = DisjointSet()
        self.__cpt = (int(self.__length/2),int(self.__width/2))

    def print_map(self):
        for c in xrange(0,self.__width):
            for r in xrange(0,self.__length):
                if self.__map[r][c] == WALL:
                    sys.stdout.write('#')
                elif self.__map[r][c] == TUNNEL:
                    sys.stdout.write('+')
                else:
                    sys.stdout.write(' ')
            print
        print

    def iterate_walls(self):
        for c in xrange(0,self.__width):
            for r in xrange(0,self.__length):
                if self.__map[r][c] == WALL:
                    if (self.__adj_flr_count(r, c) > 0):
                        yield (c, r)

    def iterate_map(self, cell_type):
        for c in xrange(0,self.__width):
            for r in xrange(0,self.__length):
                if self.__map[r][c] == cell_type:
                    yield (c, r)

    def add_exit(self, pt1, pt2):
        while (pt1 != pt2):
            if (pt1[0] < 0 or
                pt1[0] >= self.__width or
                pt1[1] < 0 or
                pt1[1] >= self.__length):
                print 'WARN: Exit out of range',pt1
            else:
                self.__exits.append(pt1)
            pt1 = (pt1[0] + cmp(pt2[0], pt1[0]),
                   pt1[1] + cmp(pt2[1], pt1[1]))

    def purge_exits(self):
        self.__exits = []
        for c in xrange(0,self.__width):
            for r in xrange(0,self.__length):
                if (c == 0 or c == self.__width-1 or
                    r == 0 or r == self.__length-1):
                    self.__map[r][c] == WALL

    def grow_map(self):
        self.__generation(1, 2, -1)

    def reduce_map(self):
        self.__generation(1, 7, -1)

    def gen_map(self, mode='default'):
        if mode == 'room':
            # One large cavern room
            self.__generation(4, 5, -1)
            self.__join_rooms()
            self.__generation(1, 5, -1)
        else:
            # Windey passages. 
            #Repeat 4: W?(p) = R1(p) ? 5 || R2(p) ? 2
            #Repeat 3: W?(p) = R1(p) ? 5
            # We do the above, with a cave join pass right before the final
            # iteration. This helps smooth out any sharp edges after the join
            # pass.
            self.__generation(4, 5, 2)
            self.__generation(2, 5, -1)
            self.__join_rooms()
            self.__generation(1, 5, -1)

    def __generation(self, count, r1_cutoff, r2_cutoff):
        while (count > 0):
            self.__buf_map = [[WALL for i in xrange(self.__width)]
                              for j in xrange(self.__length)]
            self.__gen_walls(self.__buf_map)
            self.__gen_walls(self.__map)
            for r in xrange(1,self.__length-1):
                for c in xrange(1,self.__width-1):
                    adjcount_r1 = self.__adj_wall_count(r,c,1)
                    adjcount_r2 = self.__adj_wall_count(r,c,2)
                    if(adjcount_r1 >= r1_cutoff or
                       adjcount_r2 <= r2_cutoff):
                        self.__buf_map[r][c] = WALL
                    else:
                        self.__buf_map[r][c] = FLOOR
            self.__map = list(self.__buf_map)
            count -= 1

    def __gen_initial_map(self, fillprob):
        def rwall(fillprob):
            if (random() < fillprob):
                return WALL
            return FLOOR

        self.__map = [[rwall(fillprob) for i in xrange(self.__width)]
                      for j in xrange(self.__length)]
        self.__gen_walls(self.__map)

    def __gen_walls(self, a_map):
        for j in range(0,self.__length):
            a_map[j][0] = WALL
            a_map[j][self.__width-1] = WALL

        for j in range(0,self.__width):
            a_map[0][j] = WALL
            a_map[self.__length-1][j] = WALL

        # Force the exits to be floor. We grow them out from the edge a bit to
        # make sure they don't get sealed off. 
        for pos in self.__exits:
            a_map[pos[0]][pos[1]] = FLOOR
            for pos2 in ((-1,0), (1,0), (0,-1), (0,1),
                         (-2,0), (2,0), (0,-2), (0,2)):
                p = (pos[0]+pos2[0], pos[1]+pos2[1])
                if (p[0] < 1 or p[1] < 1):
                    continue
                if (p[0] >= self.__width-1 or
                    p[1] >= self.__length-1):
                    continue
                a_map[p[0]][p[1]] = FLOOR

    def __adj_flr_count(self,sr,sc):
        count = 0
        for pos in ((-1,0), (1,0), (0,-1), (0,1)):
            p = (sr+pos[0], sc+pos[1])
            if (p[0] < 0 or p[1] < 0):
                continue
            if (p[0] > self.__width-1 or
                p[1] > self.__length-1):
                continue
            if (self.__map[p[0]][p[1]] == FLOOR):
                count += 1
        return count

    def __adj_wall_count(self,sr,sc,rng=1):
        count = 0

        for r in xrange(-rng,rng+1):
            for c in xrange(-rng,rng+1):
                #if (r == 0 and c == 0):
                #    continue
                if (abs(r) == 2 and abs(c) == 2):
                    continue
                if (sr + r < 0 or sc + c < 0):
                    continue
                if (sr + r >= self.__length or sc + c >= self.__width):
                    continue
                if self.__map[sr + r][sc + c] == WALL:
                    count += 1

        return count

    def __join_rooms(self):
        # Divide all cells into joined sets
        for r in xrange(0,self.__length):
            for c in xrange(0,self.__width):
                if self.__map[r][c] != WALL:
                    self.__union_adj_sqr(r,c)

        all_caves = self.__ds.split_sets()

        while len(all_caves) > 1:
            self.__join_points(all_caves[choice(all_caves.keys())][0])
            all_caves = self.__ds.split_sets()

    def __union_adj_sqr(self,sr,sc):
        loc = (sr,sc)
        root1 = self.__ds.find(loc)
        # A cell is connected to other cells only in cardinal directions.
        # (diagonals don't count for movement).
        for pos in ((-1,0), (1,0), (0,-1), (0,1)):
            if (sr+pos[0] < 0 or sc+pos[1] < 0):
                continue
            if (sr+pos[0] >= self.__length or
                sc+pos[1] >= self.__width):
                continue
            nloc = (sr+pos[0],sc+pos[1])
            if self.__map[nloc[0]][nloc[1]] == FLOOR:
                root2 = self.__ds.find(nloc)
                if root1 != root2:
                    self.__ds.union(root1,root2)

    def __join_points(self,pt1):
        next_pt = pt1
        while 1:
            dir = self.__get_tunnel_dir(pt1,self.__cpt)
            move = randrange(0,3)

            if move == 0:
                next_pt = (pt1[0] + dir[0],pt1[1])
            elif move == 1:
                next_pt = (pt1[0],pt1[1] + dir[1])
            else:
                next_pt = (pt1[0] + dir[0],pt1[1] + dir[1])

            root1 = self.__ds.find(next_pt)
            root2 = self.__ds.find(pt1)

            if root1 != root2:
                self.__ds.union(root1,root2)

            for pos in ((0,0), (-1,0), (1,0), (0,-1), (0,1)):
                if (next_pt[0]+pos[0] < 0 or next_pt[1]+pos[1] < 0 or
                    next_pt[0]+pos[0] >= self.__length or
                    next_pt[1]+pos[1] >= self.__width):
                    continue
                if (self.__map[next_pt[0]+pos[0]][next_pt[1]+pos[1]] == WALL):
                    self.__map[next_pt[0]+pos[0]][next_pt[1]+pos[1]] = TUNNEL

            if self.__stop_drawing(pt1,next_pt,self.__cpt):
                return

            pt1 = next_pt

    def __stop_drawing(self,pt,npt,cpt):
        if self.__ds.find(npt) == self.__ds.find(cpt):
            return 1
        if (self.__ds.find(pt) != self.__ds.find(npt) and
            self.__map[npt[0]][npt[1]] != WALL):
            return 1
        return 0

    def __get_tunnel_dir(self,pt1,pt2):
        if pt1[0] < pt2[0]:
            h_dir = +1
        elif pt1[0] > pt2[0]:
            h_dir = -1
        else:
            h_dir = 0

        if pt1[1] < pt2[1]:
            v_dir = +1
        elif pt1[1] > pt2[1]:
            v_dir = -1
        else:
            v_dir = 0

        return (h_dir,v_dir)
