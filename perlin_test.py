#!/usr/bin/env python
size = 16
factor = float(size) * 0.25
i = [' ', '.', ',', 'o', 'O', '@', '#']
import perlin
pn = perlin.SimplexNoise(256)
for y in xrange(size):
    for x in xrange(size):
        print i[int((pn.noise3(x / factor, 0, y / factor) + 1.0) / 2 * 6)],
    print
