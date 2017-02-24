import sys
import os
import hashlib
import shutil

print "Quick and dirty tool to update paintings in an existing world."

if (len(sys.argv) != 2):
    print 'Usage: update_paintings.py <path to world folder>'
    print 'When using a multiverse setup remember to provide the primary world'
    print "Always make a backup."
    sys.exit()

oldhash = {'\xee\xb5E\x94\xd0B7%j\xd1\x9a]\xd4\x9dT\x8e': 'Chess_King.dat',
            "\xe9'\xf4!\xab@\xe1\xfe\x8dA\xd9o\xf4\xb1\x19,": 'the_scream.dat',
            'i)~t\xddf\xaf\xf0\xec/\xefR\x83:A\xc9': 'circle_guide.dat',
            'cz\x1eY\xda\xa9\xce\x1as\xd0\x1d\xcfk\x7f\xd64': 'american_gothic.dat',
            ';^d _\x93\xab\xab \x1f\x90\x8d]|\x8f\x94': 'moulin_galette.dat',
            '\xf5\x13\xfb\x0bl\x92q\x04s\x9dU\xf3\x12X\xa5\x87': 'mona_lisa.dat',
            'pS\x06>H\x16Gh\xc2\xe5\x12s\x0b\xd5\xfd\x03': 'cruchon_compotier.dat',
            '\xa9P\xcd \x80\xe2\x1a\xfa\xaf\xe61\xe5\xc8)\x82\xe0': 'water_lily_pond.dat',
            '[\xce\xfc\xf6)\xaa\x13$\xa5\xbfh\xe9\xa0\x06^\x03': 'sunday_afternoon.dat',
            '*\xc3\xe4\xcb\x17\x9a6\x1f\x95V\x7fL\xc3\xab\xc5n': 'Chess_Bishop.dat',
            'K\xd5\x9e\xe9b\x97O\x02rS\xbdh"\xd7\x17\xa3': 'adele_bloch_bauer.dat',
            '\x00h\x88\x96P)\xb8\xd7\xa5\xb6\x04\x91mw\x93Q': 'pearl_earring.dat',
            '\xb2"\xf2\xccC\xb8\xbe\x92\xb2\xad\xaa\xa8\xd9\x07I\xac': 'Chess_Rook.dat',
            '\x11.\xbeubQKX\xdbz\xb4,@qa\xdb': 'tower_of_babel.dat',
            '\x0f\r\x15<\xdd\xc4w\xb9WB\x91\xc2\x9d\xac\xb5a': 'brewing_guide.dat',
            'V\xed\x18\xad\xb5\xbe.\x8dKc\xcf`\x18\x1a\xa2\x83': 'dr_gachet.dat',
            '\x9er\x88#\\s\xec \x80\xcc\xef\x99\xeb\xc5\x81\xbc': 'Chess_Pawn.dat',
            '\xaa3\x1b\xc9\x9f\xcd\x08\xd4\xd7\xe33\xc9@\rn\x1b': 'Chess_Kight.dat',
            '\xb3\xca\x9f{@6\xf0\xb0\xf0\x04:\x16k\xd6\xaf9': 'sunflowers.dat',
            'Pu\x8d\xe9%\xfd\xe4\x89\x0f\xb4u\xc0V\xd3\x9d^': 'friend_in_need.dat',
            'z\x98\xf0\xaaK`\x17\xc2\xe7\xa6E\xb2J2\xf5!': 'diana_actaeon.dat',
            '\x117\x06h\x9aP"\x18\xbf\x11H0\x85*2H': 'card_players.dat',
            "'\xf9\xce\x81w\x94\x14?\x0e\x1f-\x12[\x08\xdf\x18": 'Chess_Queen.dat',
            '-\x9b\x92od\xa3\xc2U\x9e\xd0y qE\n\xcb': 'birth_of_venus.dat'}
          
dir = os.path.join(sys.argv[1],'data')
paint_dir = os.path.join('..','paintings')

for file in os.listdir(dir):
    if (str(file.lower()).endswith(".dat")):
        #Gen hash and extract map ID
        hash = hashlib.md5(open(os.path.join(dir,file), 'r').read()).digest()
        if (hash in oldhash):
            src = os.path.join(paint_dir,oldhash[hash])
            dst = os.path.join(dir,file)
            shutil.copyfile(src, dst)
            print file + " identified as " + oldhash[hash] + " and updated."
            
print "All done!"
