import sys


class ItemInfo (object):
    def __init__(self, name, id):
        self.name = name
        self.id = int(id)

    def __str__ (self):
        print 'Item: %s, ID: %d'.format(self.name, self.id)


class ItemInfoAll (object):
    iteminfo = {}

    def __init__(self, filename = 'items.db'):
        print 'Reading items database:',filename
        try:
            with file(filename) as f:
                items_txt = f.read()
        except Exception, e:
            print "Error reading items file: ", e;

        for line in items_txt.split("\n"):
            try:
                line = line.strip()
                if len(line) == 0: continue
                if line[0] == "#": continue; # comment

                value, names = line.split('=',1);
                for name in names.split(','):
                    self.iteminfo[name.strip().lower()] = ItemInfo(name.strip(), value)
                    self.iteminfo[value] = ItemInfo(name.strip().lower(), value)

            except Exception, e:
                print "Error reading line:", e
                print "Line: ", line
                print

    def id (self, name):
            try:
                return self.iteminfo[name].id
            except:
                print 'Unknown item:', name
                sys.exit(1)

    def name (self, id):
            try:
                return self.iteminfo[str(id)].name
            except:
                print 'Unknown item ID:', id
                sys.exit(1)


items = ItemInfoAll();
