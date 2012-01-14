import ConfigParser
import sys
import random
import math

import cfg
import items
import utils

# Armor enchantments
PROTECTION = 0
FIRE_PROTECTION = 1
FEATHER_FALLING = 2
BLAST_PROTECTION = 3
PROJECTILE_PROTECTION = 4
RESPIRATION = 5
AQUA_AFFINITY = 6

# Weapon enchantments
SHARPNESS = 16
SMITE = 17
BANE_OF_ARTHROPODS = 18
KNOCKBACK = 19
FIRE_ASPECT = 20
LOOTING = 21

# Tool enchantments
EFFICIENCY = 32
SILK_TOUCH = 33
UNBREAKING = 34
FORTUNE = 35

# Bow Enchantments
POWER = 48
PUNCH = 49
FLAME = 50
INFINITY = 51

# Enchantment names
_ench_name = {
    PROTECTION: 'Protection',
    FIRE_PROTECTION: 'Fire Protection',
    FEATHER_FALLING: 'Feather Fall',
    BLAST_PROTECTION: 'Blast Protection',
    PROJECTILE_PROTECTION: 'Projectile Protection',
    RESPIRATION: 'Respiration',
    AQUA_AFFINITY: 'Aqua Affinity',
    SHARPNESS: 'Sharpness',
    SMITE: 'Smite',
    BANE_OF_ARTHROPODS: 'Bane of Arthropods',
    KNOCKBACK: 'Knockback',
    FIRE_ASPECT: 'Fire Aspect',
    LOOTING: 'Looting',
    EFFICIENCY: 'Efficiency',
    SILK_TOUCH: 'Silk Touch',
    UNBREAKING: 'Unbreaking',
    FORTUNE: 'Fortune',
    POWER: 'Power',
    PUNCH: 'Punch',
    FLAME: 'Flame',
    INFINITY: 'Infinity'
}

# Level names
_level_name = {
    1: 'I',
    2: 'II',
    3: 'III',
    4: 'IV',
    5: 'V'
}

# Enchantment selection probabilities (weights)
_ench_prob = {
    PROTECTION: 10,
    FIRE_PROTECTION: 5,
    FEATHER_FALLING: 5,
    BLAST_PROTECTION: 2,
    PROJECTILE_PROTECTION: 5,
    RESPIRATION: 2,
    AQUA_AFFINITY: 2,
    SHARPNESS: 2,
    SMITE: 5,
    BANE_OF_ARTHROPODS: 5,
    KNOCKBACK: 5,
    FIRE_ASPECT: 2,
    LOOTING: 2,
    EFFICIENCY: 10,
    SILK_TOUCH: 1,
    UNBREAKING: 5,
    FORTUNE: 2,
    POWER: 10,
    PUNCH: 2,
    FLAME: 2,
    INFINITY: 1
}

# Enchantment level table
_ench_level = {
    # Enchantment               I         II       III        IV        V
    PROTECTION:            [(  1, 21),( 17, 37),( 33, 53),( 49, 69),(  0,  0)],
    FIRE_PROTECTION:       [( 10, 22),( 16, 30),( 26, 38),( 34, 46),(  0,  0)],
    FEATHER_FALLING:       [(  5, 15),( 11, 21),( 17, 27),( 23, 33),(  0,  0)],
    BLAST_PROTECTION:      [(  5, 17),( 13, 25),( 21, 33),( 29, 41),(  0,  0)],
    PROJECTILE_PROTECTION: [(  3, 18),(  9, 24),( 15, 30),( 21, 36),(  0,  0)],
    RESPIRATION:           [( 10, 40),( 20, 50),( 30, 60),(  0,  0),(  0,  0)],
    AQUA_AFFINITY:         [(  1, 41),(  0,  0),(  0,  0),(  0,  0),(  0,  0)],
    SHARPNESS:             [(  1, 21),( 17, 37),( 33, 53),( 49, 69),( 65, 85)],
    SMITE:                 [(  5, 17),( 13, 25),( 21, 33),( 29, 41),( 37, 49)],
    BANE_OF_ARTHROPODS:    [(  5, 17),( 13, 25),( 21, 33),( 29, 41),( 37, 49)],
    KNOCKBACK:             [(  5, 25),( 25, 75),(  0,  0),(  0,  0),(  0,  0)],
    FIRE_ASPECT:           [( 10, 60),( 30, 80),(  0,  0),(  0,  0),(  0,  0)],
    LOOTING:               [( 20, 70),( 32, 82),( 44, 94),(  0,  0),(  0,  0)],
    EFFICIENCY:            [(  1, 51),( 16, 66),( 33, 81),( 46, 96),( 61,111)],
    SILK_TOUCH:            [( 25, 75),(  0,  0),(  0,  0),(  0,  0),(  0,  0)],
    UNBREAKING:            [(  5, 55),( 15, 65),( 25, 75),(  0,  0),(  0,  0)],
    FORTUNE:               [( 20, 70),( 32, 82),( 44, 94),(  0,  0),(  0,  0)],
    POWER:                 [(  1, 16),( 11, 26),( 21, 36),( 31, 46),( 41, 56)],
    PUNCH:                 [( 12, 37),( 32, 57),(  0,  0),(  0,  0),(  0,  0)],
    FLAME:                 [( 20, 50),(  0,  0),(  0,  0),(  0,  0),(  0,  0)],
    INFINITY:              [( 20, 50),(  0,  0),(  0,  0),(  0,  0),(  0,  0)]
}

_maxtier = -1
_master_loot = {}

class Loot (object):
    def __init__ (self, slot, count, id, damage, enchantments):
        self.slot = slot
        self.id = id
        self.value = id
        self.damage = damage
        self.data = damage
        self.count = count
        self.enchantments = enchantments

    def __str__ (self):
        return 'Slot: %d, ID: %d, Dmg: %d, Cnt: %d, E: %s'%(self.slot,
                                                     self.id,
                                                     self.damage,
                                                     self.count,
                                                     self.enchantments)


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
        num = 0
        for line in loots:
            chance, minmax, enchant = [x.strip() for x in line[1].split(',')]
            minimum = minmax.split('-')[0]
            maximum = minmax.split('-')[-1]
            if enchant is not '0':
                minimum = 1
                maximum = 1

            ilist = []
            for i in line[0].split(','):
                ilist.append(items.byName(i.strip()))
            thistable[num] = dict([
                ('item', ilist),
                ('chance', int(chance)),
                ('min', int(minimum)),
                ('max', int(maximum)),
                ('ench', enchant)
            ])
            num += 1

def rollLoot (tier, level):
    tiername = 'tier%s'%(tier)
    slot = 0
    for key, loot in _master_loot[tiername].items():
        if (loot['chance'] >= random.randint(1,100)):
            amount = random.randint(loot['min'], loot['max'])
            item = random.choice(loot['item'])

            if 'level*' in loot['ench']:
                ench_level = int(level*float(loot['ench'].split('level*')[-1]))
                ench_level = max(1, ench_level)
            elif '-' in loot['ench']:
                min_ench = int(loot['ench'].split('-')[0])
                max_ench = int(loot['ench'].split('-')[-1])
                ench_level = random.randint(min_ench, max_ench)
            else:
                try:
                    ench_level = int(loot['ench'])
                except:
                    ench_level = 0

            enchantments = []
            if ench_level > 0:
                enchantments = list(enchant(item.name, ench_level))

            while (amount > 0):
                if (amount > item.maxstack):
                    thisamount = item.maxstack
                    amount -= item.maxstack
                else:
                    thisamount = amount
                    amount = 0
                if (slot < 27):
                    thisloot = Loot(slot,
                                    thisamount,
                                    item.value,
                                    item.data,
                                    enchantments)
                    yield thisloot
                    slot += 1

def enchant (item, level, debug=False):
    # Based on the info available in the wiki as of 1.1:
    # http://http://www.minecraftwiki.net/wiki/Enchanting
    #
    # NBT for an item in a chest looks like this:
    #
    # Iron Sword (267) with Smite V, Knockback II, and Fire Aspect II
    #
    # TAG_List( "Items" ):
    #     TAG_Compound():
    #         TAG_Short( "id" ): 267
    #         TAG_Short( "Damage" ): 0
    #         TAG_Byte( "Count" ): 1
    #         TAG_Compound( "tag" ):
    #             TAG_List( "ench" ):
    #                 TAG_Compound():
    #                     TAG_Short( "id" ): 17
    #                     TAG_Short( "lvl" ): 5
    # 
    #                 TAG_Compound():
    #                     TAG_Short( "id" ): 19
    #                     TAG_Short( "lvl" ): 2
    # 
    #                 TAG_Compound():
    #                     TAG_Short( "id" ): 20
    #                     TAG_Short( "lvl" ): 2

    # Determine what type of item we are dealing with
    type = 'none'
    if 'sword' in item:
        type = 'weapon'
    elif 'bow' in item:
        type = 'bow'
    elif ('pickaxe' in item or
          'shovel' in item or
          'axe' in item):
        type = 'tool'
    elif ('helmet' in item or
          'chestplate' in item or
          'leggings' in item or
          'boots' in item):
        type = 'armor'

    enchantability = 0.0
    material = ''
    # Determine material enchantability
    if 'wooden' in item:
        material = 'wood'
        enchantability = 1.0
    elif 'leather' in item:
        material = 'leather'
        enchantability = 1.0
    elif 'stone' in item:
        material = 'stone'
        enchantability = 5.0
    elif 'iron' in item:
        material = 'iron'
        enchantability = 14.0
        if type == 'armor':
            enchantability = 9.0
    elif 'chainmail' in item:
        material = 'chainmail'
        enchantability = 12.0
    elif 'diamond' in item:
        material = 'diamond'
        enchantability = 12.0
        if type == 'armor':
            enchantability = 10.0
    elif 'gold' in item:
        material = 'gold'
        enchantability = 22.0
        if type == 'armor':
            enchantability = 25.0

    # Modify the enchantment level
    mean = enchantability/2
    std = math.sqrt(mean)
    emod = random.normalvariate(mean, std) + 1
    mod= random.uniform(0.75, 1.25)
    mlevel = int((level + emod) * mod + .5)

    # Further determine the type
    if 'helmet' in item:
        type = 'helmet'
    elif 'boots' in item:
        type = 'boots'

    # Gather a list of possible enchantments and levels
    enchantments = {}
    prob = []

    def check_enchantment(ench, mlevel):
        for x in xrange(4, -1, -1):
            if (mlevel >= _ench_level[ench][x][0] and
                mlevel <= _ench_level[ench][x][1]):
                enchantments[ench] = x+1
                prob.append((ench, _ench_prob[ench]))
                return
        return

    # Armors
    if (type == 'armor' or
        type == 'helmet' or
        type == 'boots'):
        check_enchantment(PROTECTION, mlevel)
        check_enchantment(FIRE_PROTECTION, mlevel)
        check_enchantment(BLAST_PROTECTION, mlevel)
        check_enchantment(PROJECTILE_PROTECTION, mlevel)

    if type == 'boots':
        check_enchantment(FEATHER_FALLING, mlevel)

    if type == 'helmet':
        check_enchantment(RESPIRATION, mlevel)
        check_enchantment(AQUA_AFFINITY, mlevel)

    # Weapons
    if type == 'weapon':
        check_enchantment(SHARPNESS, mlevel)
        check_enchantment(SMITE, mlevel)
        check_enchantment(BANE_OF_ARTHROPODS, mlevel)
        check_enchantment(KNOCKBACK, mlevel)
        check_enchantment(FIRE_ASPECT, mlevel)
        check_enchantment(LOOTING, mlevel)

    # Tools
    if type == 'tool':
        check_enchantment(EFFICIENCY, mlevel)
        check_enchantment(SILK_TOUCH, mlevel)
        check_enchantment(UNBREAKING, mlevel)
        check_enchantment(FORTUNE, mlevel)

    # Bows
    if type == 'bow':
        check_enchantment(POWER, mlevel)
        check_enchantment(PUNCH, mlevel)
        check_enchantment(FLAME, mlevel)
        check_enchantment(INFINITY, mlevel)

    # Item did not result in any enchantments
    if len(enchantments) == 0:
        return

    if debug is True:
        print 'Enchanting', item
        print 'Enchantability of', material, '=', enchantability
        print 'Modified level:', '(', level, '+', emod, ') *', mod, '~=', mlevel
        print 'Possible enchantments for', type, '@', 'level', mlevel
        for k, v in enchantments.items():
            print '\t', _ench_name[k], _level_name[v], '@', _ench_prob[k]

    # Pick some enchantments
    final = {}
    while True:
        # Pick one.
        ench = utils.weighted_choice(prob)
        # Add it.
        final[ench] = enchantments[ench]
        # Remove it so we don't pick again.
        prob.remove((ench, _ench_prob[ench]))
        # Some enchantments conflict with each other. If we picked one, remove
        # its counterparts. 
        if ench in [PROTECTION, FIRE_PROTECTION, BLAST_PROTECTION,
                    PROJECTILE_PROTECTION]:
            for x in [PROTECTION, FIRE_PROTECTION,
                      BLAST_PROTECTION,PROJECTILE_PROTECTION]:
                if (x, _ench_prob[x]) in prob:
                    prob.remove((x, _ench_prob[x]))

        if ench in [SHARPNESS, SMITE, BANE_OF_ARTHROPODS]:
            for x in [SHARPNESS, SMITE, BANE_OF_ARTHROPODS]:
                if (x, _ench_prob[x]) in prob:
                    prob.remove((x, _ench_prob[x]))
        # Abort if we ran out of enchantments
        if len(prob) == 0:
            break
        # Check for additional enchantments
        mlevel /= 2
        if random.randint(1,50) > mlevel+1:
            break

    if debug is True:
        print 'Final enchantments'
        for k, v in final.items():
            print '\t', _ench_name[k], _level_name[v]

    for k, v in final.items():
        yield dict({'id':k, 'lvl':v})

def print_enchant(item, level, debug=True):
    for ench in enchant(item, level, debug):
        if debug is not True:
            print _ench_name[ench['id']], _level_name[ench['lvl']]
