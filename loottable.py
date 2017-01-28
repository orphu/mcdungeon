import random
import math
import sys

import cfg
import items
import utils
from pymclevel import nbt

# Armor enchantments
PROTECTION = 0
FIRE_PROTECTION = 1
FEATHER_FALLING = 2
BLAST_PROTECTION = 3
PROJECTILE_PROTECTION = 4
RESPIRATION = 5
AQUA_AFFINITY = 6
THORNS = 7
DEPTH_STRIDER = 8
FROST_WALKER = 9
CURSE_OF_BINDING = 10

# Weapon enchantments
SHARPNESS = 16
SMITE = 17
BANE_OF_ARTHROPODS = 18
KNOCKBACK = 19
FIRE_ASPECT = 20
LOOTING = 21
SWEEPING_EDGE = 22

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

# Fishing Rod Enchantments
LUCK_OF_THE_SEA = 61
LURE = 62

# Treasure Enchantments
MENDING = 70
CURSE_OF_VANISHING = 71

# Enchantment names
_ench_name = {
    PROTECTION: 'Protection',
    FIRE_PROTECTION: 'Fire Protection',
    FEATHER_FALLING: 'Feather Fall',
    BLAST_PROTECTION: 'Blast Protection',
    PROJECTILE_PROTECTION: 'Projectile Protection',
    RESPIRATION: 'Respiration',
    AQUA_AFFINITY: 'Aqua Affinity',
    THORNS: 'Thorns',
    DEPTH_STRIDER: 'Depth Strider',
    SHARPNESS: 'Sharpness',
    SMITE: 'Smite',
    BANE_OF_ARTHROPODS: 'Bane of Arthropods',
    KNOCKBACK: 'Knockback',
    FIRE_ASPECT: 'Fire Aspect',
    LOOTING: 'Looting',
    SWEEPING_EDGE: 'Sweeping Edge',
    EFFICIENCY: 'Efficiency',
    SILK_TOUCH: 'Silk Touch',
    UNBREAKING: 'Unbreaking',
    FORTUNE: 'Fortune',
    POWER: 'Power',
    PUNCH: 'Punch',
    FLAME: 'Flame',
    INFINITY: 'Infinity',
    LUCK_OF_THE_SEA: 'Luck of the Sea',
    LURE: 'Lure',
    FROST_WALKER: 'Frost Walker',
    MENDING: 'Mending',
    CURSE_OF_BINDING: 'Curse of Binding',
    CURSE_OF_VANISHING: 'Curse of Vanishing'
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
    THORNS: 1,
    DEPTH_STRIDER: 1,
    SHARPNESS: 10,
    SMITE: 5,
    BANE_OF_ARTHROPODS: 5,
    KNOCKBACK: 5,
    FIRE_ASPECT: 2,
    LOOTING: 2,
    SWEEPING_EDGE: 2,
    EFFICIENCY: 10,
    SILK_TOUCH: 1,
    UNBREAKING: 5,
    FORTUNE: 2,
    POWER: 10,
    PUNCH: 2,
    FLAME: 2,
    INFINITY: 1,
    LUCK_OF_THE_SEA: 5,
    LURE: 5,
    FROST_WALKER: 2,
    MENDING: 2,
    CURSE_OF_BINDING: 1,
    CURSE_OF_VANISHING: 1
}

# Enchantment level table
_ench_level = {
    # Enchantment               I         II       III        IV        V
    PROTECTION: [(1, 21), (12, 32), (23, 43), (34, 54), (0, 0)],
    FIRE_PROTECTION: [(10, 22), (18, 30), (26, 38), (34, 46), (0, 0)],
    FEATHER_FALLING: [(5, 15), (11, 21), (17, 27), (23, 33), (0, 0)],
    BLAST_PROTECTION: [(5, 17), (13, 25), (21, 33), (29, 41), (0, 0)],
    PROJECTILE_PROTECTION: [(3, 18), (9, 24), (15, 30), (21, 36), (0, 0)],
    RESPIRATION: [(10, 40), (20, 50), (30, 60), (0, 0), (0, 0)],
    AQUA_AFFINITY: [(1, 41), (0, 0), (0, 0), (0, 0), (0, 0)],
    THORNS: [(10, 60), (30, 80), (50, 100), (0, 0), (0, 0)],
    DEPTH_STRIDER: [(10, 25), (20, 35), (30, 45), (0, 0), (0, 0)],
    SHARPNESS: [(1, 21), (12, 32), (23, 43), (34, 54), (45, 65)],
    SMITE: [(5, 25), (13, 33), (21, 41), (29, 49), (37, 57)],
    BANE_OF_ARTHROPODS: [(5, 25), (13, 33), (21, 41), (29, 49), (37, 57)],
    KNOCKBACK: [(5, 55), (25, 75), (0, 0), (0, 0), (0, 0)],
    FIRE_ASPECT: [(10, 60), (30, 80), (0, 0), (0, 0), (0, 0)],
    LOOTING: [(15, 65), (34, 74), (33, 83), (0, 0), (0, 0)],
    SWEEPING_EDGE: [(5, 20), (14, 29), (23, 38), (0, 0), (0, 0)],
    EFFICIENCY: [(1, 51), (11, 61), (21, 71), (31, 81), (41, 91)],
    SILK_TOUCH: [(15, 65), (0, 0), (0, 0), (0, 0), (0, 0)],
    UNBREAKING: [(5, 55), (13, 63), (21, 71), (0, 0), (0, 0)],
    FORTUNE: [(15, 65), (24, 74), (33, 83), (0, 0), (0, 0)],
    POWER: [(1, 16), (11, 26), (21, 36), (31, 46), (41, 56)],
    PUNCH: [(12, 37), (32, 57), (0, 0), (0, 0), (0, 0)],
    FLAME: [(20, 50), (0, 0), (0, 0), (0, 0), (0, 0)],
    INFINITY: [(20, 50), (0, 0), (0, 0), (0, 0), (0, 0)],
    LUCK_OF_THE_SEA: [(15, 65), (24, 74), (33, 83), (0, 0), (0, 0)],
    LURE: [(15, 65), (24, 74), (33, 83), (0, 0), (0, 0)],
    FROST_WALKER: [(10, 25), (20, 35), (0, 0), (0, 0), (0, 0)],
    MENDING: [(25, 75), (0, 0), (0, 0), (0, 0), (0, 0)],
    CURSE_OF_BINDING: [(25, 50), (0, 0), (0, 0), (0, 0), (0, 0)],
    CURSE_OF_VANISHING: [(25, 50), (0, 0), (0, 0), (0, 0), (0, 0)]
}

# Enchantment valid items tables
# table+book: All legal enchants achieved with tables and books.
_ench_items_table_book = {
    # Enchantment
    PROTECTION: ['book', 'helmet', 'chestplate', 'leggings', 'boots'],
    FIRE_PROTECTION: ['book', 'helmet', 'chestplate', 'leggings', 'boots'],
    FEATHER_FALLING: ['book', 'boots'],
    BLAST_PROTECTION: ['book', 'helmet', 'chestplate', 'leggings', 'boots'],
    PROJECTILE_PROTECTION: ['book', 'helmet', 'chestplate', 'leggings', 'boots'],
    RESPIRATION: ['book', 'helmet'],
    AQUA_AFFINITY: ['book', 'helmet'],
    THORNS: ['book', 'helmet', 'chestplate', 'leggings', 'boots'],
    DEPTH_STRIDER: ['book','boots'],
    SHARPNESS: ['book', 'sword', 'axe'],
    SMITE: ['book', 'sword', 'axe'],
    BANE_OF_ARTHROPODS: ['book', 'sword', 'axe'],
    KNOCKBACK: ['book', 'sword'],
    FIRE_ASPECT: ['book', 'sword'],
    LOOTING: ['book', 'sword'],
    SWEEPING_EDGE: ['book', 'sword'],
    EFFICIENCY: ['book', 'tool', 'axe', 'shears'],
    SILK_TOUCH: ['book', 'tool', 'axe', 'shears'],
    UNBREAKING: ['book', 'helmet', 'chestplate', 'leggings', 'boots',
                 'sword', 'tool', 'axe', 'bow', 'hoe', 'fishing rod',
                 'shears', 'flint and steel', 'carrot on a stick',
                 'shield', 'elytra'],
    FORTUNE: ['book', 'tool', 'axe'],
    POWER: ['book', 'bow'],
    PUNCH: ['book', 'bow'],
    FLAME: ['book', 'bow'],
    INFINITY: ['book', 'bow'],
    LUCK_OF_THE_SEA: ['book', 'fishing rod'],
    LURE: ['book', 'fishing rod'],
    FROST_WALKER: ['book', 'boots'],
    MENDING: ['book', 'helmet', 'chestplate', 'leggings', 'boots',
                 'sword', 'tool', 'axe', 'bow', 'hoe', 'fishing rod',
                 'shears', 'flint and steel', 'carrot on a stick',
                 'elytra'],
    CURSE_OF_BINDING: ['book', 'helmet', 'chestplate', 'leggings', 'boots'],
    CURSE_OF_VANISHING: ['book', 'helmet', 'chestplate', 'leggings', 'boots',
                 'sword', 'tool', 'axe', 'bow', 'hoe', 'fishing rod',
                 'shears', 'flint and steel', 'carrot on a stick',
                 'elytra']
}

# Table: Only enchants that can be achieved with an enchanting table.
_ench_items_table = {
    # Enchantment
    PROTECTION: ['book', 'helmet', 'chestplate', 'leggings', 'boots'],
    FIRE_PROTECTION: ['book', 'helmet', 'chestplate', 'leggings', 'boots'],
    FEATHER_FALLING: ['book', 'boots'],
    BLAST_PROTECTION: ['book', 'helmet', 'chestplate', 'leggings', 'boots'],
    PROJECTILE_PROTECTION: ['book', 'helmet', 'chestplate', 'leggings', 'boots'],
    RESPIRATION: ['book', 'helmet'],
    AQUA_AFFINITY: ['book', 'helmet'],
    THORNS: ['book', 'chestplate'],
    DEPTH_STRIDER: ['book', 'boots'],
    SHARPNESS: ['book', 'sword'],
    SMITE: ['book', 'sword'],
    BANE_OF_ARTHROPODS: ['book', 'sword'],
    KNOCKBACK: ['book', 'sword'],
    FIRE_ASPECT: ['book', 'sword'],
    LOOTING: ['book', 'sword'],
    SWEEPING_EDGE: ['book', 'sword'],
    EFFICIENCY: ['book', 'tool', 'axe'],
    SILK_TOUCH: ['book', 'tool', 'axe'],
    UNBREAKING: ['book', 'tool', 'axe'],
    FORTUNE: ['book', 'tool', 'axe'],
    POWER: ['book', 'bow'],
    PUNCH: ['book', 'bow'],
    FLAME: ['book', 'bow'],
    INFINITY: ['book', 'bow'],
    LUCK_OF_THE_SEA: ['book', 'fishing rod'],
    LURE: ['book', 'fishing rod'],
    FROST_WALKER: ['book'],
    MENDING: ['book'],
    CURSE_OF_BINDING: ['book'],
    CURSE_OF_VANISHING: ['book']
}

# Extended: As normal, but all weapon enchants can appear on axes,
#           pickaxes and shovels. Sweeping Edge not included as only swords
#           can do Sweep Attacks.
_ench_items_extended = _ench_items_table_book.copy()
for i in (SHARPNESS, SMITE, BANE_OF_ARTHROPODS, KNOCKBACK, FIRE_ASPECT, LOOTING):
    _ench_items_extended[i] = ['book', 'sword', 'axe', 'tool']

# Zistonian: As extended, but all weapon enchants can appear on all
# normally non-enchantable items
_ench_items_zistonian = _ench_items_extended.copy()
for i in (SHARPNESS, SMITE, BANE_OF_ARTHROPODS, KNOCKBACK, FIRE_ASPECT, LOOTING):
    _ench_items_zistonian[i] = ['book', 'sword', 'axe', 'tool', 'none']

# Anything: Complete madness! Anything on anything.
_ench_items_anything = {}
for (enchant, name) in _ench_name.items():
    _ench_items_anything[enchant] = ['any']

_maxtier = -1
_master_loot = {}


class Loot (object):

    def __init__(self, slot, count, id, damage, enchantments, p_effect='',
                 customname='', flag='', flagparam='', lore='', file=''):
        self.slot = slot
        self.id = id
        self.value = id
        self.damage = damage
        self.data = damage
        self.count = count
        self.enchantments = enchantments
        self.p_effect = p_effect
        self.customname = customname
        self.flag = flag
        self.flagparam = flagparam
        self.lore = lore
        self.file = file

    # Intentionally not printing lore
    def __str__(self):
        return 'Slot: %d, ID: %d, Dmg: %d, Cnt: %d, E: %s, PE: %s, N: %s, F: %s, FP: %s, File: %s' % (
            self.slot,
            self.id,
            self.damage,
            self.count,
            self.enchantments,
            self.p_effect,
            self.customname,
            self.flag,
            self.flagparam,
            self.file)


def Load():
    print 'Reading loot tables...'
    global _maxtier

    while (cfg.parser.has_section('tier%d' % (_maxtier + 1))):
        _maxtier += 1
        tiername = 'tier%d' % (_maxtier)
        # print 'Reading loot table for:',tiername
        loots = cfg.parser.items(tiername)
        _master_loot[tiername] = {}
        thistable = _master_loot[tiername]
        num = 0
        for line in loots:
            try:
                chance, minmax, enchant = [x.strip()
                                           for x in line[1].split(',')]
                minimum = minmax.split('-')[0]
                maximum = minmax.split('-')[-1]
            except:
                print 'WARNING: Cannot parse loot table entry around line:'
                print '  {}: {} (skipping...)'.format(
                    line[0],
                    line[1]
                )
                continue

            ilist = []
            for i in line[0].split(','):
                thisitem = items.byName(i.strip())
                if thisitem is None:
                    print 'ERROR: Tried to reference loot that does not exist.'
                    sys.exit()
                ilist.append(items.byName(i.strip()))
            thistable[num] = dict([
                ('item', ilist),
                ('chance', int(chance)),
                ('min', int(minimum)),
                ('max', int(maximum)),
                ('ench', enchant)
            ])
            num += 1


def rollLoot(tier, level):
    tiername = 'tier%s' % (tier)
    slot = 0
    for key, loot in _master_loot[tiername].items():
        if (loot['chance'] >= random.randint(1, 100)):
            amount = random.randint(loot['min'], loot['max'])
            item = random.choice(loot['item'])

            enchantments = []
            if item.name.startswith('magic_'):
                ench_level = 0
                if len(item.ench) > 0:
                    for e in item.ench.split(','):
                        k = int(e.split('-')[0])
                        v = int(e.split('-')[-1])
                        enchantments.append(dict({'id': k, 'lvl': v}))
            elif 'level*' in loot['ench']:
                ench_level = int(
                    level * float(loot['ench'].split('level*')[-1]))
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

            # Always treat enchantment items as stacks of 1
            if ench_level > 0:
                maxstack = 1
            else:
                maxstack = item.maxstack

            while (amount > 0):
                if (amount > maxstack):
                    thisamount = maxstack
                    amount -= maxstack
                else:
                    thisamount = amount
                    amount = 0
                if (slot < 27):
                    # Roll the enchantments after creating the stack
                    # This way each stack gets different enchantments
                    if ench_level > 0:
                        enchantments = list(enchant(item.name, ench_level))
                    thisloot = Loot(slot,
                                    thisamount,
                                    item.id,
                                    item.data,
                                    enchantments,
                                    item.p_effect,
                                    item.customname,
                                    item.flag,
                                    item.flagparam,
                                    item.lore,
                                    item.file)
                    yield thisloot
                    slot += 1


def enchant(item, level, debug=False):
    # Based on the info available in the wiki as of 1.3.1:
    # http://www.minecraftwiki.net/wiki/Enchantment_Mechanics
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
        type = 'sword'
    elif 'bow' in item and 'bowl' not in item:
        type = 'bow'
    elif ('pickaxe' in item or
          'shovel' in item or
          'shears' in item or
          'hoe' in item or
          'fishing rod' in item or
          'carrot on a stick' in item or
          'flint and steel' in item or
          'axe' in item):
        type = 'tool'
    elif ('helmet' in item or
          'chestplate' in item or
          'leggings' in item or
          'boots' in item):
        type = 'armor'
    elif (item == 'enchanted book'):
        type = 'book'
    elif ('shield' in item):
        type = 'shield'
    elif (item == 'elytra'):
        type = 'elytra'

    enchantability = 1.0
    material = ''
    # Determine material enchantability
    if 'wooden' in item:
        material = 'wood'
        enchantability = 15.0
    elif 'leather' in item:
        material = 'leather'
        enchantability = 15.0
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
        enchantability = 10.0
        if type == 'armor':
            enchantability = 10.0
    elif 'gold' in item:
        material = 'gold'
        enchantability = 22.0
        if type == 'armor':
            enchantability = 25.0

    # Modify the enchantment level
    # Step 1 = level plus random 0 - enchantability plus one
    mlevel = level + random.triangular(0, enchantability) + 1
    # Step 2 = vary by +- 25%
    mlevel = int(mlevel * random.triangular(0.75, 1.25) + .5)

    # Further determine the type
    if 'helmet' in item:
        type = 'helmet'
    elif 'chestplate' in item:
        type = 'chestplate'
    elif 'leggings' in item:
        type = 'leggings'
    elif 'boots' in item:
        type = 'boots'
    elif 'shears' in item:
        type = 'shears'
    elif 'hoe' in item:
        type = 'hoe'
    elif 'fishing rod' in item:
        type = 'fishing rod'
    elif 'carrot on a stick' in item:
        type = 'carrot on a stick'
    elif 'flint and steel' in item:
        type = 'flint and steel'
    elif 'axe' in item and 'pickaxe' not in item:
        type = 'axe'

    # Gather a list of possible enchantments and levels
    enchantments = {}
    prob = []

    def check_enchantment(ench, mlevel):
        for x in xrange(4, -1, -1):
            if (mlevel >= _ench_level[ench][x][0] and
                    mlevel <= _ench_level[ench][x][1]):
                enchantments[ench] = x + 1
                prob.append((ench, _ench_prob[ench]))
                return
        return

    if (cfg.enchant_system == 'table'):
        item_filter = _ench_items_table
    elif (cfg.enchant_system == 'extended'):
        item_filter = _ench_items_extended
    elif (cfg.enchant_system == 'zistonian'):
        item_filter = _ench_items_zistonian
    elif (cfg.enchant_system == 'anything'):
        item_filter = _ench_items_anything
    else:   # "table+book" and catch anything else
        item_filter = _ench_items_table_book

    # Loop through every enchantment and do check_enchantment if there
    # is a match for the item type
    for (enchant, name) in _ench_name.items():
        if (item_filter[enchant][0] == 'any' or
                type in item_filter[enchant]):
            check_enchantment(enchant, mlevel)

    # Item did not result in any enchantments
    if len(enchantments) == 0:
        return

    if debug is True:
        print 'Enchanting', item
        print 'Enchantability of', material, '=', enchantability
        print 'Modified level:', '(', level, ') ~=', mlevel
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
                      BLAST_PROTECTION, PROJECTILE_PROTECTION]:
                if (x, _ench_prob[x]) in prob:
                    prob.remove((x, _ench_prob[x]))

        if ench in [SHARPNESS, SMITE, BANE_OF_ARTHROPODS]:
            for x in [SHARPNESS, SMITE, BANE_OF_ARTHROPODS]:
                if (x, _ench_prob[x]) in prob:
                    prob.remove((x, _ench_prob[x]))
        
        # Frost Walking conflicts with Depth strider
        if ench in [FROST_WALKER, DEPTH_STRIDER]:
            for x in [FROST_WALKER, DEPTH_STRIDER]:
                if (x, _ench_prob[x]) in prob:
                    prob.remove((x, _ench_prob[x]))
        # Abort if we ran out of enchantments
        if len(prob) == 0:
            break
        # Check for additional enchantments
        mlevel /= 2
        if random.randint(1, 50) > mlevel + 1:
            break

    if debug is True:
        print 'Final enchantments'
        for k, v in final.items():
            print '\t', _ench_name[k], _level_name[v]

    for k, v in final.items():
        yield dict({'id': k, 'lvl': v})


def enchant_tags(item, level, debug=False):
    tags = nbt.TAG_List()
    for ench in enchant(item, level, debug):
        e = nbt.TAG_Compound()
        e['id'] = nbt.TAG_Short(ench['id'])
        e['lvl'] = nbt.TAG_Short(ench['lvl'])
        tags.append(e)
    return tags


def print_enchant(item, level, debug=True):
    for ench in enchant(item, level, debug):
        if debug is not True:
            print _ench_name[ench['id']], _level_name[ench['lvl']]
