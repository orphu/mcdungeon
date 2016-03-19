import os
import sys
import random
import textwrap

import cfg
import mapstore
import loottable
import items
from utils import topheavy_random, converttoordinal
from pymclevel import nbt

class new:

    def __init__(self, mapstore):
        self.mapstore = mapstore
        self.flag = {'Base':0}

        # Make a list of all the txt files in the books directory
        if os.path.isdir(os.path.join(sys.path[0], cfg.dir_books)):
            self.book_path = os.path.join(sys.path[0], cfg.dir_books)
        elif os.path.isdir(cfg.dir_books):
            self.book_path = cfg.dir_books
        else:
            self.book_path = ''
        self.booklist = []
        if self.book_path != '':
            for file in os.listdir(self.book_path):
                if (str(file.lower()).endswith(".txt") and
                        file.lower() != "readme.txt"):
                    self.booklist.append(file)

        self.valid_characters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ "

        # Make a list of all paintings
        if os.path.isdir(os.path.join(sys.path[0], cfg.dir_paintings)):
            self.paint_path = os.path.join(sys.path[0], cfg.dir_paintings)
        elif os.path.isdir(cfg.dir_paintings):
            self.paint_path = cfg.dir_paintings
        else:
            self.paint_path = ''
        # Make a list of all the pairs of dat and txt files in the paintings
        # directory
        self.paintlist = []
        if self.paint_path != '':
            for file in os.listdir(self.paint_path):
                if str(file.lower()).endswith(".dat"):
                    if os.path.isfile(os.path.join(self.paint_path, file[:-3] + 'txt')):
                        self.paintlist.append(file[:-4])


    def loadrandbooktext(self):
        item = nbt.TAG_Compound()
        item['id'] = nbt.TAG_String('minecraft:written_book')
        # No books? Give a book and quill instead
        if len(self.booklist) == 0:
            item['id'] = nbt.TAG_String('minecraft:writable_book')
            return item
        # Open the book's text file
        bookfile = open(os.path.join(self.book_path, random.choice(self.booklist)))
        bookdata = bookfile.read().splitlines()
        bookfile.close()
        # Create NBT tag
        item['tag'] = nbt.TAG_Compound()
        # Prevent unusual characters from being used with filter
        item['tag']['author'] = nbt.TAG_String(
            filter(
                lambda x: x in self.valid_characters,
                bookdata.pop(0)))
        title = filter(lambda x: x in self.valid_characters,bookdata.pop(0))
        item['tag']['title'] = nbt.TAG_String(title[:32])
        item['tag']["pages"] = nbt.TAG_List()
        # Slice the pages at 50 and the page text at 256 to match minecraft
        # limits
        for p in bookdata[:50]:
            page = filter(lambda x: x in self.valid_characters, p)
            page = self.ConvertEscapeChars(page)
            # Escape quote charcaters
            page = page.replace('"','\\"')
            item['tag']["pages"].append(nbt.TAG_String('"%s"'%(page[:256])))
        # Give the book an edition
        ed = topheavy_random(0, 9)
        item['tag']['display'] = nbt.TAG_Compound()
        item['tag']['display']['Lore'] = nbt.TAG_List()
        item['tag']['display']['Lore'].append(
            nbt.TAG_String(
                converttoordinal(ed+1) +
                ' Edition'))
        if (ed == 0):
            item['tag']['generation'] = nbt.TAG_Int(0)
        elif (ed == 1):
            item['tag']['generation'] = nbt.TAG_Int(1)
        else:
            item['tag']['generation'] = nbt.TAG_Int(2)

        return item


    def loadrandpainting(self):
        # No paintings? Give a blank map (ID: 395)
        if len(self.paintlist) == 0:
            item = nbt.TAG_Compound()
            item['id'] = nbt.TAG_String('minecraft:map')
            return item

        return self.mapstore.add_painting(random.choice(self.paintlist))


    def loadrandfortune(self):
        if os.path.isfile(os.path.join(sys.path[0], cfg.file_fortunes)):
            forune_path = os.path.join(sys.path[0], cfg.file_fortunes)
        elif os.path.isfile(cfg.file_fortunes):
            forune_path = cfg.file_fortunes
        else:
            return '...in bed.'  # Fortune file not found

        # Retrieve a random line from a file, reading through the file once
        # Prevents us from having to load the whole file in to memory
        forune_file = open(forune_path)
        lineNum = 0
        while True:
            aLine = forune_file.readline()
            if not aLine:
                break
            if aLine[0] == '#' or aLine == '':
                continue
            lineNum = lineNum + 1
            # How likely is it that this is the last line of the file?
            if random.uniform(0, lineNum) < 1:
                fortune = aLine.rstrip()
        forune_file.close()
        return fortune


    # Takes item name string (and optional enchants), outputs NBT compound
    # Convenience function for frames etc.
    def buildFrameItemTag(self,i,ench=(),customname=''):
        item = items.byName(i)
        if customname == '':
            customname = item.customname
        thisloot = loottable.Loot(  None,
                                    1,
                                    item.value,
                                    item.data,
                                    ench,
                                    item.p_effect,
                                    customname,
                                    item.flag,
                                    item.flagparam,
                                    item.lore,
                                    item.file)
        return self.buildItemTag(thisloot)


    # Takes loot object, outputs NBT compound
    def buildItemTag(self,i):
        # If it's a binary NBT file, just load it
        if i.file != '':
            item_tag = nbt.load(i.file)
            # Set the slot and count
            if i.slot != None:
                item_tag['Slot'] = nbt.TAG_Byte(i.slot)
            item_tag['Count'] = nbt.TAG_Byte(i.count)
            return item_tag
        # Otherwise, we will build the compound
        item_tag = nbt.TAG_Compound()
        # Standard stuff
        item_tag['id'] = nbt.TAG_String(i.id)
        item_tag['Damage'] = nbt.TAG_Short(i.damage)
        # Enchantments
        if len(i.enchantments) > 0:
            item_tag['tag'] = nbt.TAG_Compound()
            if (i.flag == 'ENCH_BOOK'):
                item_tag['tag']['StoredEnchantments'] = nbt.TAG_List()
                elist = item_tag['tag']['StoredEnchantments']
            else:
                item_tag['tag']['ench'] = nbt.TAG_List()
                elist = item_tag['tag']['ench']
            for e in i.enchantments:
                e_tag = nbt.TAG_Compound()
                e_tag['id'] = nbt.TAG_Short(e['id'])
                e_tag['lvl'] = nbt.TAG_Short(e['lvl'])
                elist.append(e_tag)
        # Custom Potion Effects
        if i.p_effect != '':
            try:
                item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()

            # Is this a 'basic' potion i.e. no custom effects list
            if (i.p_effect.replace(',','').replace('-','').isdigit()):
                item_tag['tag']['CustomPotionEffects'] = nbt.TAG_List()
                elist = item_tag['tag']['CustomPotionEffects']
                for e in i.p_effect.split(','):
                    id, amp, dur = e.split('-')
                    e_tag = nbt.TAG_Compound()
                    e_tag['Id'] = nbt.TAG_Byte(id)
                    e_tag['Amplifier'] = nbt.TAG_Byte(amp)
                    e_tag['Duration'] = nbt.TAG_Int(dur)
                    # Flags for hiding potion particles
                    if i.flag == 'HIDE_PARTICLES' or i.flag == 'HIDE_ALL':
                        e_tag['ShowParticles'] = nbt.TAG_Byte(0)
                    elist.append(e_tag)
            else:
                item_tag['tag']['Potion'] = nbt.TAG_String(i.p_effect)
                # For basic potions there is no need for a custom name
                i.customname = ''
        # Flag for hiding additional text
        if i.flag == 'HIDE_EFFECTS' or i.flag == 'HIDE_ALL':
            try:
                item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()
            item_tag['tag']['HideFlags'] = nbt.TAG_Int(63)    # 63 = Hide everything
        # Naming
        if i.customname != '':
            try:
                item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()
            item_tag['tag']['display'] = nbt.TAG_Compound()
            item_tag['tag']['display']['Name'] = nbt.TAG_String(i.customname)
        # Lore Text
        if i.lore != '' or i.flag == 'FORTUNE':
            try:
                item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()
            try:
                item_tag['tag']['display']
            except:
                item_tag['tag']['display'] = nbt.TAG_Compound()
            item_tag['tag']['display']['Lore'] = nbt.TAG_List()
            if i.flag == 'FORTUNE':
                item_tag['tag']['display'][
                    'Name'] = nbt.TAG_String('Fortune Cookie')
                i.lore = self.loadrandfortune()
                loredata = textwrap.wrap(self.ConvertEscapeChars(i.lore), 30)
                for loretext in loredata[:10]:
                    item_tag['tag']['display']['Lore'].append(
                        nbt.TAG_String(loretext))
            else:
                loredata = i.lore.split(':')
                for loretext in loredata[:10]:
                    item_tag['tag']['display']['Lore'].append(
                        nbt.TAG_String(self.ConvertEscapeChars(loretext[:50])))
        # Dyed
        if (i.flag == 'DYED'):
            try:
                item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()
            try:
                item_tag['tag']['display']
            except:
                item_tag['tag']['display'] = nbt.TAG_Compound()
            if i.flagparam == '':
                item_tag['tag']['display']['color'] = nbt.TAG_Int(
                    random.randint(
                        0,
                        16777215))
            else:
                item_tag['tag']['display']['color'] = nbt.TAG_Int(i.flagparam)
        # special cases for written books and paintings
        elif (i.flag == 'WRITTEN'):
            item_tag = self.loadrandbooktext()
        elif (i.flag == 'PAINT'):
            item_tag = self.loadrandpainting()
        # Tags for this dungeon's flag
        elif (i.flag == 'DUNGEON_FLAG'):
            try:
                item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()
            item_tag['tag']['BlockEntityTag'] = nbt.TAG_Compound()
            item_tag['tag']['BlockEntityTag']['Base'] = nbt.TAG_Int(self.flag['Base'])
            item_tag['tag']['BlockEntityTag']['Patterns'] = nbt.TAG_List()
            for p in self.flag['Patterns']:
                q = nbt.TAG_Compound()
                q['Color'] = nbt.TAG_Int(p[0])
                q['Pattern'] = nbt.TAG_String(p[1])
                item_tag['tag']['BlockEntityTag']['Patterns'].append(q)
        elif (i.flag.startswith('ENTITYTAG:')):
            try:
                item_tag['tag']
            except:
                item_tag['tag'] = nbt.TAG_Compound()
            item_tag['tag']['EntityTag'] = nbt.TAG_Compound()
            item_tag['tag']['EntityTag']['id'] = nbt.TAG_String(i.flag.split(':')[1])

        # Set the slot and count
        if i.slot != None:
            item_tag['Slot'] = nbt.TAG_Byte(i.slot)
        item_tag['Count'] = nbt.TAG_Byte(i.count)
        return item_tag


    # Convert escape characters in a string. The following are available:
    # \n - Line Return
    # \s - Section Sign (used for formatting in minecraft)
    # \\ - Backslash
    def ConvertEscapeChars(self,input):
        out = input.replace('\\\\','<[BACKSLASH]>')
        out = out.replace('\\n','\n')
        out = out.replace('\\s',u"\u00A7".encode('utf8'))
        out = out.replace('<[BACKSLASH]>','\\')
        return out

    def SetDungeonFlag(self, flag):
        self.flag = flag
