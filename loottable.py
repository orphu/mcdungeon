import ConfigParser
import sys
import random

from items import *


class LootTable (object):
    maxtier = -1
    master_loot = {}

    def __init__ (self, filename = 'mcdungeon.cfg'):
        config = ConfigParser.SafeConfigParser()
        try:
            config.readfp(open(filename))
        except:
            print "Failed to read loot tables from config file:",filename
            sys.exit(1)
        while (config.has_section('tier%d'%(self.maxtier+1))):
            self.maxtier += 1
            tiername = 'tier%d'%(self.maxtier)
            print 'Reading loot table for:',tiername
            loots = config.items(tiername)
            self.master_loot[tiername] = {}
            thistable =  self.master_loot[tiername]
            for line in loots:
                chance, minimum, maximum = line[1].split(',')
                thistable[line[0]] = dict([
                    ('name', line[0]),
                    ('value', items.id(line[0])),
                    ('chance', int(chance)),
                    ('min', int(minimum)),
                    ('max', int(maximum))
                ])

    def rollLoot (self, tier):
        tiername = 'tier%s'%(tier)
        for loot in self.master_loot[tiername].values():
            if (loot['chance'] >= random.randint(1,100)):
                amount = random.randint(loot['min'], loot['max'])
                if (amount > 0):
                    yield loot['value'], amount

master_loot = LootTable()
