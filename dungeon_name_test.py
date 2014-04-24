#!/usr/bin/env python
import random
import sys

import ruins
import namegenerator

print
for x in xrange(50):
    n = namegenerator.namegenerator(random.randint(0, 39))
    o = n.genroyalname()
    if o.endswith("s"):
        os = o + "'"
    else:
        os = o + "'s"
    print random.choice([
        ruins.Blank.nameDungeon().format(
            owner=o,
            owners=os
        ),
        ruins.RuinedFane.nameDungeon().format(
            owner=o,
            owners=os
        ),
        ruins.StepPyramid.nameDungeon().format(
            owner=o,
            owners=os
        ),
        ruins.Barrow.nameDungeon().format(
            owner=o,
            owners=os
        ),
        ruins.EvilRunestones.nameDungeon().format(
            owner=o,
            owners=os
        ),
        ruins.Oasis.nameDungeon().format(
            owner=o,
            owners=os
        ),
        ruins.SquareTower.nameDungeon().format(
            owner=o,
            owners=os
        ),
    ])
