import ConfigParser
import os
import sys
import random
from copy import copy

import items
import loottable

_shops = []

class ShopInfo(object):
    def __init__(self, name, profession = 0, trades = []):
        self.name = str(name)
        self.profession = int(profession)
        self.trades = []
        for t in trades:
            self.AddTrade(t)
        
    def addTrade(self, trade):
        self.trades.append(trade)
        
    def __str__ (self):
        return 'Name: %s, Prof: %d, Trades: %s'%(
            self.name,
            self.profession,
            self.trades)
            
class TradeInfo(object):
    def __init__(self, chance, max_uses, output, input, input2 = None, limited = False):
        self.chance = int(chance)
        self.max_uses = int(max_uses)
        self.output = self.stringToLoot(output)
        self.input  = self.stringToLoot(input)
        self.input2 = self.stringToLoot(input2)
        self.limited = limited
        
    def stringToLoot(self,inloot):
        if inloot == None:
            return None
        loot = inloot.lower().split(',')
        item = items.byName(loot[0])
        if item == None:
            sys.exit('%s not found'% loot[0])
        if len(loot) < 2:
            count = 1
        else:
            count = int(loot[1])
        if len(loot) < 3:
            enchantments = []
            if item.name.startswith('magic_'):
                ench_level = 0
                if len(item.ench) > 0:
                    for e in item.ench.split(','):
                        k = int(e.split('-')[0])
                        v = int(e.split('-')[-1])
                        enchantments.append(dict({'id': k, 'lvl': v}))
        else:
            enchantments = list(loottable.enchant(item.name, int(loot[2])))
        return loottable.Loot(0,
                              count,
                              item.value,
                              item.data,
                              enchantments,
                              item.p_effect,
                              item.customname,
                              item.flag,
                              item.flagparam,
                              item.lore,
                              item.file)
   
    def __str__ (self):
        return 'Chance: %s, Max U: %d,\nOutput: %s\nInput: %s\nInput2: %s'%(
            self.chance,
            self.max_uses,
            self.output,
            self.input,
            self.input2)

def LoadShop(filename):
    global _shops

    temp = os.path.join(sys.path[0], 'shops', filename)
    try:
        fh = open(temp)
        fh.close
        filename = temp
    except:
        filename = os.path.join('shops', filename)

    parser = ConfigParser.SafeConfigParser()

    #print 'Reading config from', filename, '...'
    try:
        parser.readfp(open(filename))
    except Exception, e:
        print "Failed to read config file!"
        sys.exit(e.message)
    
    name = parser.get('shop', 'name')
    profession = parser.get('shop', 'profession_id')
    shop = ShopInfo(name,profession)
    maxtrade = 1
    while (parser.has_section('trade%d' % maxtrade)):
        chance = parser.get('trade%d' % maxtrade, 'chance')
        max_uses = parser.get('trade%d' % maxtrade, 'max_uses')
        input = parser.get('trade%d' % maxtrade, 'input')
        if parser.has_option('trade%d' % maxtrade, 'input2'):
            input2 = parser.get('trade%d' % maxtrade, 'input2')
        else:
            input2 = None
        limited = False
        if parser.has_option('trade%d' % maxtrade, 'limited'):
            limited = parser.get('trade%d' % maxtrade, 'limited')
        output = parser.get('trade%d' % maxtrade, 'output')
        shop.addTrade(TradeInfo(chance,max_uses,output,input,input2,limited=limited))
        maxtrade += 1
    _shops.append(shop)


def Load(dir_shops):
    # Make a list of all the cfg files in the books directory
    if os.path.isdir(os.path.join(sys.path[0], dir_shops)):
        shop_path = os.path.join(sys.path[0], dir_shops)
    elif os.path.isdir(dir_shops):
        shop_path = dir_shops
    else:
        shop_path = ''
    shoplist = []
    if shop_path != '':
        for file in os.listdir(shop_path):
            if str(file.lower()).endswith(".cfg"):
                shoplist.append(file)
    for shop in shoplist:
        LoadShop(shop)
    print 'Loaded', len(shoplist), 'shops.'

# A Random shop with random trades
def rollShop():
    shop = copy(random.choice(_shops))
    trades = []
    # Roll random trades
    for t in shop.trades:
        if random.randint(1, 100) <= t.chance:
            trades.append(t)
    shop.trades = trades
    return shop