import inspect
import sys
import os

import materials
from nbtyamlbridge import tagsfromfile

_items = {}


class ItemInfo (object):

    def __init__(self, name, id, data=0, maxstack=64, ench='', p_effect='',
                 customname='', flag='', flagparam='', lore='', file=''):
        self.name = str(name)
        self.id = id
        self.value = id     # Old name
        self.data = int(data)
        self.maxstack = int(maxstack)
        self.ench = ench
        self.p_effect = p_effect
        self.customname = str(customname)
        self.flag = str(flag)
        self.flagparam = str(flagparam)
        self.lore = str(lore)
        self.file = str(file)

    # Intentionally not printing lore
    def __str__(self):
        return 'Item: %s, ID: %d, Data: %d, MaxStack: %d,'\
               ' Ench: %s, PEff: %s, Name: %s, Flag: %s, '\
               ' FP: %s, File: %s' % (
                   self.name,
                   self.id,
                   self.data,
                   self.maxstack,
                   self.ench,
                   self.p_effect,
                   self.customname,
                   self.flag,
                   self.flagparam,
                   self.file
               )


def LoadItems(filename='items.txt'):
    # Try to load items from sys.path[0] if we can,
    # otherwise default to the cd.
    temp = os.path.join(sys.path[0], filename)
    try:
        fh = open(temp)
        fh.close
        filename = temp
    except:
        pass
    items = 0
    try:
        fh = open(filename)
    except IOError as e:
        sys.exit(e)
    fh.close()
    try:
        with file(filename) as f:
            items_txt = f.read()
    except Exception as e:
        print "Error reading items file: ", e
    for line in items_txt.split("\n"):
        try:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue

            if line.count(',') == 4:
                name, id, data, maxstack, flag = line.split(',')
            else:
                name, id, data, maxstack = line.split(',')
                flag = ''
            name = name.lower()
            _items[name] = ItemInfo(
                name,
                id,
                data,
                maxstack,
                flag=flag
            )
            items += 1
        except Exception as e:
            print "Error reading line:", e
            print "Line: ", line

    # Now import items from materials
    for material, obj in inspect.getmembers(materials):
        if (
            isinstance(obj, materials.Material) and
            obj.name not in _items
        ):
            _items[obj.name] = ItemInfo(
                obj.name,
                obj.id,
                obj.data,
                obj.stack,
                ''
            )
            items += 1
    print 'Loaded', items, 'items.'


def LoadMagicItems(filename='magic_items.txt'):
    # Try to load items from sys.path[0] if we can,
    # otherwise default to the cd.
    temp = os.path.join(sys.path[0], filename)
    try:
        fh = open(temp)
        fh.close
        filename = temp
    except:
        pass
    items = 0
    try:
        fh = open(filename)
    except IOError as e:
        sys.exit(e)
    fh.close()
    try:
        with file(filename) as f:
            items_txt = f.read()
    except Exception as e:
        print "Error reading items file: ", e
    for line in items_txt.split("\n"):
        try:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue

            if line.count(':') == 1:
                name, stuff = line.split(':')
                lore = ''
            else:
                name, stuff, lore = line.split(':', 2)
            item, ench = stuff.split(',', 1)
            customname = name
            name = 'magic_%s' % (name.lower())
            item = item.lower()
            id = _items[item].id
            data = _items[item].data
            flag = _items[item].flag
            flagparam = _items[item].flagparam
            p_effect = _items[item].p_effect

            _items[name] = ItemInfo(
                name,
                id,
                data=data,
                maxstack=1,
                ench=ench,
                customname=customname,
                flag=flag,
                flagparam=flagparam,
                p_effect=p_effect,
                lore=lore
            )
            # print _items[name]
            items += 1
        except Exception as e:
            print "Error reading line:", e
            print "Line: ", line
    print 'Loaded', items, 'magic items.'


def LoadPotions(filename='potions.txt'):
    # Try to load items from sys.path[0] if we can,
    # otherwise default to the cd.
    temp = os.path.join(sys.path[0], filename)
    hexdigits = "abcdefABCDEF0123456789"
    try:
        fh = open(temp)
        fh.close
        filename = temp
    except:
        pass
    items = 0
    try:
        fh = open(filename)
    except IOError as e:
        sys.exit(e)
    fh.close()
    try:
        with file(filename) as f:
            items_txt = f.read()
    except Exception as e:
        print "Error reading custom potions file: ", e
    for line in items_txt.split("\n"):
        try:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue
            
            s = line.split(',')
            name = s.pop(0)
            # Append section sign and r to name to reset style
            resetprefix = u"\u00A7r".encode('utf8')
            customname = name
            name = (name.lower())
            # Look for optional hex color and store in flagparam
            flagparam = ''
            if len(s[-1]) == 6 and all(c in hexdigits for c in s[-1]):
                flagparam = int(s.pop(), 16)
            # Look for optional flag
            flag = ''
            if s[-1] in ('HIDE_EFFECTS','HIDE_PARTICLES','HIDE_ALL'):
                flag = s.pop()

            # Join the rest back in to the effect list
            p_effect = ','.join(s)
            
            # Create the basic potion
            id = _items['water bottle'].id
            _items[name] = ItemInfo(name, id, data=0, maxstack=1,
                                    p_effect=p_effect, flag=flag,
                                    flagparam = flagparam,
                                    customname=resetprefix+customname)
                                    
            # Create the arrow version of the potion
            id = _items['tipped arrow'].id
            _items[name+' arrow'] = ItemInfo(name+' arrow', id, data=0, maxstack=64,
                                    p_effect=p_effect, flag=flag,
                                    flagparam = flagparam,
                                    customname=resetprefix+customname+' Arrow')

            # Create the splash version of the potion
            id = _items['splash water bottle'].id
            _items['splash '+name] = ItemInfo('splash '+name, id, data=0, maxstack=1,
                                    p_effect=p_effect, flag=flag,
                                    flagparam = flagparam,
                                    customname=resetprefix+'Splash '+customname)

            # Create the lingering version of the potion
            id = _items['lingering water bottle'].id
            _items['lingering '+name] = ItemInfo('lingering '+name, id, data=0, maxstack=1,
                                    p_effect=p_effect, flag=flag,
                                    flagparam = flagparam,
                                    customname=resetprefix+'Lingering '+customname)
            items += 1
        except Exception as e:
            print "Error reading line:", e
            print "Line: ", line
    print 'Loaded', items, 'custom potions.'


def LoadDyedArmour(filename='dye_colors.txt'):
    # Try to load items from sys.path[0] if we can,
    # otherwise default to the cd.
    temp = os.path.join(sys.path[0], filename)
    try:
        fh = open(temp)
        fh.close
        filename = temp
    except:
        pass
    items = 0
    try:
        fh = open(filename)
    except IOError as e:
        sys.exit(e)
    fh.close()
    try:
        with file(filename) as f:
            color_txt = f.read()
    except Exception as e:
        print "Error reading dyes file: ", e
    # leather armour types
    arms = ['leather helmet',
            'leather chestplate',
            'leather leggings',
            'leather boots']
    for line in color_txt.split("\n"):
        try:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue

            colorname, colorval = line.split(':')
            flag = 'DYED'
            flagparam = int(colorval, 16)

            for arm in arms:
                id = _items[arm].id
                name = '%s %s' % (colorname.lower(), _items[arm].name)
                _items[name] = ItemInfo(name, id, data=0, maxstack=1,
                                        flag=flag, flagparam=flagparam)
            # print _items[name]
            items += 1
        except Exception as e:
            print "Error reading line:", e
            print "Line: ", line
    print 'Loaded', items, 'dye colors.'


def LoadYAMLFiles(dirname='items'):
    # Test which path to use. If the path can't be found
    # just don't load any items.
    if os.path.isdir(os.path.join(sys.path[0], dirname)):
        item_path = os.path.join(sys.path[0], dirname)
    elif os.path.isdir(dirname):
        item_path = dirname
    else:
        print 'Could not find the items folder!'
        return
    # Make a list of all the .yaml files in the items directory
    itemlist = []
    for file in os.listdir(item_path):
        if (file.endswith(".yaml")):
            itemlist.append(file)
    items_count = 0
    for item in itemlist:
        # SomeItem.yaml would be referenced in loot as file_some_item
        name = 'file_' + item[:-5].lower()
        full_path = os.path.join(item_path, item)
        # Load the file and do some basic validation
        try:
            item_nbt = tagsfromfile(full_path)
            item_nbt['id']  # Throws an error if not set
        except:
            print item + " is an invalid item! Skipping."
            continue    # Skip to next item
        # If the Count tag exists, use it as our maxstack
        try:
            stack = item_nbt['Count'].value
        except:
            stack = 1
        _items[name] = ItemInfo(name, '', maxstack=stack, file=full_path)
        # print _items[name]
        items_count += 1
    print 'Loaded', items_count, 'items from yaml files.'


def byName(name):
    try:
        return _items[name]
    except:
        print 'Unknown item:', name
        return None

LoadItems()
LoadYAMLFiles()
