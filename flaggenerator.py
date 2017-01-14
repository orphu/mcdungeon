import random

BLACK = 0
RED = 1
GREEN = 2
BROWN = 3
BLUE = 4
PURPLE = 5
CYAN = 6
LGRAY = 7
GRAY = 8
PINK = 9
LIME = 10
YELLOW = 11
LBLUE = 12
MAGENTA = 13
ORANGE = 14
WHITE = 15

clash = ([PINK,BLUE],
         [PINK,CYAN],
         [PINK,LBLUE],
         [PINK,GREEN],
         [PINK,LIME],
         [PINK,ORANGE],
         [PINK,BROWN],
         [MAGENTA,CYAN],
         [MAGENTA,LBLUE],
         [MAGENTA,GREEN],
         [MAGENTA,LIME],
         [MAGENTA,ORANGE],
         [CYAN,GREEN],
         [CYAN,LIME],
         [CYAN,ORANGE],
         [CYAN,PURPLE],
         [BROWN,RED],
         [YELLOW,PURPLE],
         [PURPLE,GREEN],
         [PURPLE,LIME],
         [PURPLE,RED],
         [LBLUE,LIME],
         [BROWN,GRAY],
         [BROWN,LGRAY])

pattern_clash = (['hh','hhb'],
                 ['vh','vhr'],
                 ['ld','rd'],
                 ['rud','lud'],
                 ['flo','cre'],
                 ['flo','sku'],
                 ['flo','moj'],
                 ['cre','sku'],
                 ['cre','moj'],
                 ['sku','moj'],
                 ['sc','cs'],
                 ['sc','ms'],
                 ['cr','dls'],
                 ['cr','drs'],
                 ['ls','tl'],
                 ['ls','bl'],
                 ['rs','tr'],
                 ['rs','br'])

def generateflag():
    colors = [BLACK,RED,GREEN,BROWN,BLUE,PURPLE,CYAN,LGRAY,
              GRAY,PINK,LIME,YELLOW,LBLUE,MAGENTA,ORANGE,WHITE]
              
    patterns = ['hh','hhb','vh','vhr','ts','bs','ls','rs','ld','rud','lud',
                'rd','cr','dls','drs','sc','cs','ms','tl','bl','tr','br',
                'tt','bt','mr','mc','bts','tts','ss','bo','cbo','flo',
                'cre','sku','moj','bri'] #,'gra','gru' (removed)

    def saferemove(list,item):
        if item in list:
            list.remove(item)

    # Prevent this item, or clashing items from being selected    
    def removeclash(item,list,clashlist,remove_self=True):
        if remove_self:
            saferemove(list,item)
        for c in clashlist:
            if c[0] == item:
                saferemove(list,c[1])
            elif c[1] == item:
                saferemove(list,c[0])

    # Base color of banner
    basecol = random.choice(colors)
    # Prevent this colour, or clashing colours from being selected
    removeclash(basecol,colors,clash)

    # Select first pattern and colour
    patt1 = random.choice(patterns)
    col1 = random.choice(colors)
    # Prevent the next color or pattern from clashing with the last layer
    removeclash(patt1,patterns,pattern_clash)
    removeclash(col1,colors,clash,False)
    # Special case, remove bricks pattern. (Looks bad as upper layers)
    saferemove(patterns,'bri')
    
    # Select second pattern and colour
    patt2 = random.choice(patterns)
    col2 = random.choice(colors)
    
    # 33% chance of a 3rd patten
    if random.randint(0,2) == 0:
        # Remove clashes from layer 2
        removeclash(patt2,patterns,pattern_clash)
        removeclash(col2,colors,clash,False)
        patt3 = random.choice(patterns)
        col3 = random.choice(colors)
        # Create setttings for pattern flag
        patterns = ([col1,patt1],[col2,patt2],[col3,patt3])
    else:
        patterns = ([col1,patt1],[col2,patt2])
    
    flag = {'Base':basecol,
            'Patterns':patterns}
    return flag

#for _ in range(0,50):
#    f = generateflag()
#    out = '/give @p minecraft:banner 1 %d {BlockEntityTag:{Base:%d,Patterns:[' %(f['Base'],f['Base'])
#    for p in f['Patterns']:
#        out = out + '{Pattern:%s,Color:%d},' %(p[1],p[0])
#    print out[:-1]+']}}'