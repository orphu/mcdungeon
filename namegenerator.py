import os
import sys
import random
from utils import weighted_choice
from namegen import namegen


class namegenerator:

    def __init__(self, biomeid, theme=''):
        if theme == '':
            # Get theme from biome id
            self.theme = self.gettheme(biomeid)
        else:
            self.theme = theme
        # Choose DICT based on theme
        if (self.theme == 'egyptian'):
            dict = 'egyptian.txt'
            self.titles = ['Pharaoh', 'High Priest', 'Vizier']
        elif (self.theme == 'norse'):
            dict = 'norse.txt'
            self.titles = ['King', 'Queen', 'Jarl', 'Hojfruen']
        elif (self.theme == 'saxon'):
            dict = 'saxon.txt'
            self.titles = ['King', 'Queen', 'Elder']
        elif (self.theme == 'elven'):
            dict = 'elven.txt'
            self.titles = ['King', 'Queen', 'Lord', 'Lady']
        elif (self.theme == 'mayan'):
            dict = 'mayan.txt'
            self.titles = ['Tepal', 'Ajaw']
        elif (self.theme == 'welsh'):
            dict = 'welsh.txt'
            self.titles = ['Y Brenin', 'Y Frenhines']
        elif (self.theme == 'greek'):
            dict = 'greek.txt'
            self.titles = ['King', 'Queen', 'Strategos',
                           'Tyrant', 'Archon']
        elif (self.theme == 'pirate'):
            dict = 'pirate.txt'
            self.titles = ['Captain', 'Captain', 'Commander', 'Black', 
                           'Dread Pirate', 'Mighty Pirate' ]
        elif (self.theme == 'roman'):
            dict = 'roman.txt'
            self.titles = ['Emperor', 'Empress', 'Praetor',
                           'Prefect', 'Consul', 'Magister']

        # Find name dictionaries
        if os.path.isdir(os.path.join(sys.path[0], 'names')):
            names_path = os.path.join(sys.path[0], 'names')
        elif os.path.isdir('names'):
            names_path = 'names'
        else:
            sys.exit("Error: Could not find the names folder!")

        # Set up name generator
        self.generator = namegen.NameGen(os.path.join(names_path, dict))

    def gettheme(self, biomeid):
        # Choose DICT based on biome
        if (biomeid in (2,      # Desert
                        130,    # Desert M
                        17,     # DesertHills
                        35,     # Savanna
                        163,    # Savanna M
                        36,     # Savanna Plateau
                        164,    # Savanna Plateau M
                        37,     # Mesa
                        165,    # Mesa (Bryce)
                        38,     # Mesa Plateau F
                        166,    # Mesa Plateau F M
                        39,     # Mesa Plateau
                        167,    # Mesa Plateau M
                        )):
            theme_weights = [('egyptian', 50),
                             ('greek', 10),
                             ('roman', 10)]
        elif (biomeid in (5,    # Taiga
                          133,  # Taiga M
                          10,   # FrozenOcean
                          12,   # Ice Plains
                          140,  # Ice Plains Spikes
                          13,   # Ice Mountains
                          19,   # TaigaHills
                          26,   # Cold Beach
                          30,   # Cold Taiga
                          158,  # Cold Taiga M
                          31,   # Cold Taiga Hills
                          32,   # Mega Taiga
                          160,  # Mega Spruce Taiga
                          33,   # Mega Taiga Hills
                          161,  # Mega Spruce Taiga
                          )):
            theme_weights = [('norse', 50),
                             ('elven', 10),
                             ('saxon', 10)]
        elif (biomeid in (1,    # Plains
                          129,  # Sunflower Plains
                          3,    # Extreme Hills
                          131,  # Extreme Hills M
                          6,    # Swampland
                          134,  # Swampland M
                          20,   # Extreme Hills Edge
                          26,   # Stone Beach
                          34,   # Extreme Hills+
                          162,  # Extreme Hills+ M
                          )):
            theme_weights = [('saxon', 20),
                             ('roman', 10),
                             ('greek', 10)]
        elif (biomeid in(4,     # Forest
                         132,   # Flower Forest
                         18,    # ForestHills
                         27,    # Birch Forest
                         155,   # Birch Forest M
                         28,    # Birch Forest Hills
                         156,   # Birch Forest Hills M
                         29,    # Roofed Forest
                         157,   # Roofed Forest M
                         )):
            theme_weights = [('elven', 50),
                             ('roman', 10),
                             ('norse', 10)]
        elif (biomeid in (21,   # Jungle
                          149,  # Jungle M
                          22,   # JungleHills
                          23,   # JungleEdge
                          151,  # JungleEdge M
                          )):
            theme_weights = [('mayan', 60),
                             ('elven', 10)]
        elif (biomeid in (14,   # MushroomIsland
                          15,   # MushroomIslandShore
                          )):
            theme_weights = [('welsh', 1)]
        else:                   # The rest. Including rivers, oceans etc
            theme_weights = [('saxon', 10),
                             ('roman', 10),
                             ('greek', 10),
                             ('norse', 10),
                             ('elven', 10)]
        return weighted_choice(theme_weights)

    def genname(self):
        name = self.generator.gen_word(True)    # True indicates a unqiue name
        return name

    def genroyalname(self):
        name = random.choice(self.titles) + ' ' + self.genname()
        return name
