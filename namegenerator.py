import os
import sys
import random
from utils import weighted_choice
from namegen import namegen

class namegenerator:
    def __init__(self, biomeid):
        # Get theme from biome id
        theme = self.gettheme(biomeid)
        print theme
        # Choose DICT based on theme
        if (theme == 'egyptian'):
            dict = 'egyptian.txt'
            self.titles = ['Pharaoh','High Priest','Vizier']
        elif (theme == 'norse'):
            dict = 'norse.txt'
            self.titles = ['King','Queen','Jarl','Hojfruen']
        elif (theme == 'saxon'):
            dict = 'saxon.txt'
            self.titles = ['King','Queen', 'Elder']
        elif (theme == 'elven'):
            dict = 'elven.txt'
            self.titles = ['King','Queen','Lord','Lady']
        elif (theme == 'mayan'):
            dict = 'mayan.txt'
            self.titles = ['Tepal','Ajaw']
        elif (theme == 'welsh'):
            dict = 'welsh.txt'
            self.titles = ['Y Brenin','Y Frenhines']
        elif (theme == 'greek'):
            dict = 'greek.txt'
            self.titles = ['King','Queen','Strategos',
                           'Tyrant','Archon']
        elif (theme == 'roman'):
            dict = 'roman.txt'
            self.titles = ['Emperor','Empress', 'Praetor',
                           'Prefect', 'Consul', 'Magister']

        # Find name dictionaries
        if os.path.isdir(os.path.join(sys.path[0],'names')):
            names_path = os.path.join(sys.path[0],'names')
        elif os.path.isdir('names'):
            names_path = 'names'
        else:
            sys.exit("Error: Could not find the names folder!")

        # Set up name generator
        self.generator = namegen.NameGen(os.path.join(names_path,dict))

    def gettheme(self, biomeid):
        # Choose DICT based on biome
        if (biomeid == 2 or     # Desert
            biomeid == 17):     # DesertHills
            theme_weights = [('egyptian', 50),
                             ('greek', 10),
                             ('roman', 10)]
        elif (biomeid == 5 or   # Taiga
              biomeid == 10 or  # FrozenOcean
              biomeid == 12 or  # Ice Plains
              biomeid == 13 or  # Ice Mountains
              biomeid == 19):   # TaigaHills
            theme_weights = [('norse', 50),
                             ('elven', 10),
                             ('saxon', 10)]
        elif (biomeid == 6 or   # Swampland
              biomeid == 3 or   # ExtremeHills
              biomeid == 20 or  # ExteremeHillsEdge
              biomeid == 1):    # Plains
            theme_weights = [('saxon', 20),
                             ('roman', 10),
                             ('greek', 10)]
        elif (biomeid == 4 or   # Forest
              biomeid == 18):   # ForestHills
            theme_weights = [('elven', 50),
                             ('roman', 10),
                             ('norse', 10)]
        elif (biomeid == 21 or  # Jungle
              biomeid == 22):   # Jungle Hills
            theme_weights = [('mayan', 60),
                             ('elven', 10)]
        elif (biomeid == 14 or  # MushroomIsland
              biomeid == 15):   # MushroomIslandShore
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