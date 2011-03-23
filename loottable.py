import ConfigParser
import sys
import random

import cfg
import items

_maxtier = -1
_master_loot = {}

class Loot (object):
    def __init__ (self, slot, count, id, damage):
        self.slot = slot
        self.id = id
        self.value = id
        self.damage = damage
        self.data = damage
        self.count = count

    def __str__ (self):
        return 'Slot: %d, ID: %d, Damage: %d, Count: %d'%(self.slot,
                                                          self.id,
                                                          self.damage,
                                                          self.count)


def Load ():
    print 'Reading loot tables...'
    global _maxtier

    while (cfg.parser.has_section('tier%d'%(_maxtier+1))):
        _maxtier += 1
        tiername = 'tier%d'%(_maxtier)
        #print 'Reading loot table for:',tiername
        loots = cfg.parser.items(tiername)
        _master_loot[tiername] = {}
        thistable =  _master_loot[tiername]
        for line in loots:
            chance, minimum, maximum = line[1].split(',')
            item = items.byName(line[0])
            thistable[line[0]] = dict([
                ('item', item),
                ('chance', int(chance)),
                ('min', int(minimum)),
                ('max', int(maximum))
            ])


def rollLoot (tier):
    tiername = 'tier%s'%(tier)
    slot = 0
    for loot in _master_loot[tiername].values():
        if (loot['chance'] >= random.randint(1,100)):
            amount = random.randint(loot['min'], loot['max'])
            item = loot['item']
            while (amount > 0):
                if (amount > item.maxstack):
                    thisamount = item.maxstack
                    amount -= item.maxstack
                else:
                    thisamount = amount
                    amount = 0
                if (slot < 27):
                    thisloot = Loot(slot, thisamount, item.value, item.data)
                    yield thisloot
                    slot += 1
