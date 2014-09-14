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
                'cre','sku','moj','bri'] # 'gra','gru' (removed)
                
    # Prevent this item, or clashing items from being selected    
    def removeclash(item,list,clashlist):
        list.remove(item)
        for c in clashlist:
            try:
                if c[0] == item:
                    list.remove(c[1])
                elif c[1] == item:
                    list.remove(c[0])
            except: pass

    # Base color of banner
    basecol = random.choice(colors)
    # Prevent this colour, or clashing colours from being selected
    removeclash(basecol,colors,clash)

    # Select first pattern and colour
    patt1 = random.choice(patterns)
    col1 = random.choice(colors)
    # Prevent this color or pattern from clashing with the last layer
    removeclash(patt1,patterns,pattern_clash)
    removeclash(col1,colors,clash)
    
    # Special case, remove bricks pattern. (Looks bad as the last layer)
    patterns.remove('bri')

    # Select last pattern and colour
    patt2 = random.choice(patterns)
    col2 = random.choice(colors)
    
    flag = {'Base':basecol,
            'Patterns':([col1,patt1],[col2,patt2])}
    return flag
    #print '/give @p minecraft:banner 1 0 {BlockEntityTag:{Base:'+
    #      str(basecol)+',Patterns:[{Pattern:'+patt1+',Color:'+str(col1)+
    #      '},{Pattern:'+patt2+',Color:'+str(col2)+'}]}}
