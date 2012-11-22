import sys
import os

_items = {}
_by_id = {}

class ItemInfo (object):
    def __init__(self, name, value, data=0, maxstack=64, ench='', p_effect='',
                 customname='', flag='', flagparam='', lore=''):
        self.name = str(name)
        self.value = int(value)
        self.data = int(data)
        self.maxstack = int(maxstack)
        self.ench = ench
        self.p_effect = p_effect
        self.customname = str(customname)
        self.flag = str(flag)
        self.flagparam = str(flagparam)
        self.lore = str(lore)

    # Intentionally not printing lore
    def __str__ (self):
        return 'Item: %s, ID: %d, Data: %d, MaxStack: %d, Ench: %s, PEff: %s, Name: %s, Flag: %s, FP: %s'%(
            self.name,
            self.value,
            self.data,
            self.maxstack,
            self.ench,
            self.p_effect,
            self.customname,
            self.flag,
            self.flagparam)


def LoadItems(filename = 'items.txt'):
    # Try to load items from sys.path[0] if we can, 
    # otherwise default to the cd. 
    temp = os.path.join(sys.path[0],filename)
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
    except Exception, e:
        print "Error reading items file: ", e;
    for line in items_txt.split("\n"):
        try:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue

            if line.count(',') == 4:
                value, name, data, maxstack, flag = line.split(',')
            else:
                value, name, data, maxstack = line.split(',')
                flag = ''
            name = name.lower()
            _items[name] = ItemInfo(name, value, data, maxstack, flag=flag)
            _by_id[int(value)] = ItemInfo(name, value, data, maxstack, flag=flag)
            items += 1
        except Exception, e:
            print "Error reading line:", e
            print "Line: ", line
    print 'Loaded', items, 'items.'
    #We need to prevent written books being generated if the books folder is empty
    #Substitute written books for plain book here to ensure they never get genetated
    if (BooksReady() == False):
        print 'Notice: There are no texts in the books folder. Written Books will be generated as Books instead.'
        _items['written book'] = _items['book']

def LoadMagicItems(filename = 'magic_items.txt'):
    # Try to load items from sys.path[0] if we can, 
    # otherwise default to the cd. 
    temp = os.path.join(sys.path[0],filename)
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
    except Exception, e:
        print "Error reading items file: ", e;
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
            value = _items[item].value
            data = _items[item].data
            flag = _items[item].flag
            flagparam = _items[item].flagparam

            _items[name] = ItemInfo(name, value, data=data, maxstack=1, ench=ench,
                                    customname=customname, flag=flag,
                                    flagparam=flagparam, lore=lore)
            #print _items[name]
            items += 1
        except Exception, e:
            print "Error reading line:", e
            print "Line: ", line
    print 'Loaded', items, 'magic items.'


def LoadPotions(filename = 'potions.txt'):
    # Try to load items from sys.path[0] if we can, 
    # otherwise default to the cd. 
    temp = os.path.join(sys.path[0],filename)
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
    except Exception, e:
        print "Error reading custom potions file: ", e;
    for line in items_txt.split("\n"):
        try:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue

            name, stuff = line.split(':')
            data, p_effect = stuff.split(',', 1)
            customname = name
            name = (name.lower())
            value = _items['water bottle'].value

            _items[name] = ItemInfo(name, value, data=data, maxstack=1,
                                    p_effect=p_effect, customname=customname)
            #print _items[name]
            items += 1
        except Exception, e:
            print "Error reading line:", e
            print "Line: ", line
    print 'Loaded', items, 'custom potions.'


def LoadDyedArmour(filename = 'dye_colors.txt'):
    # Try to load items from sys.path[0] if we can, 
    # otherwise default to the cd. 
    temp = os.path.join(sys.path[0],filename)
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
    except Exception, e:
        print "Error reading dyes file: ", e;
    #leather armour types
    arms = ['leather helmet','leather chestplate','leather leggings','leather boots']
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
                value = _items[arm].value
                name = '%s %s' % (colorname.lower(),_items[arm].name)
                _items[name] = ItemInfo(name, value, data=0, maxstack=1,
                                        flag=flag, flagparam=flagparam)
            #print _items[name]
            items += 1
        except Exception, e:
            print "Error reading line:", e
            print "Line: ", line
    print 'Loaded', items, 'dye colors.'


def LoadHeads(filename = 'heads.txt'):
    # Try to load items from sys.path[0] if we can, 
    # otherwise default to the cd. 
    temp = os.path.join(sys.path[0],filename)
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
    except Exception, e:
        print "Error reading heads file: ", e;
    for line in color_txt.split("\n"):
        try:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue

            flag = 'HEAD'
            flagparam = line
            value = _items['head'].value
            data = _items['head'].data

            name = '%s\'s head' % (line.lower())
            _items[name] = ItemInfo(name, value, data=data, maxstack=1,
                                    flag=flag, flagparam=flagparam)
            #print _items[name]
            items += 1
        except Exception, e:
            print "Error reading line:", e
            print "Line: ", line
    print 'Loaded', items, 'heads.'


def BooksReady():
    #Book directory existance
    if os.path.isdir(os.path.join(sys.path[0],'books')):
        book_path = os.path.join(sys.path[0],'books')
    elif os.path.isdir('books'):
        book_path = 'books'
    else:
        return False

    #Check for at least one book
    for file in os.listdir(book_path):
        if (file.endswith(".txt")):
            return True
    return False


def byName (name):
        try:
            return _items[name]
        except:
            print 'Unknown item:', name
            sys.exit(1)


def byID (id):
        try:
            return _by_id[id]
        except:
            print 'Unknown item ID:', id
            sys.exit(1)

LoadItems()
LoadDyedArmour()
LoadPotions()
LoadHeads()
LoadMagicItems()
