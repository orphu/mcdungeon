import os
import sys
import random
from namegen import namegen

class namegenerator:
    def __init__(self, biomeid):
        # Choose DICT based on biome
        if (biomeid == 2 or     # Desert
            biomeid == 17):     # DesertHills
            dict = 'egyptian.txt'
            self.titles = ['Pharaoh']
        elif (biomeid == 5 or   # Taiga
              biomeid == 10 or  # FrozenOcean
              biomeid == 12 or  # Ice Plains
              biomeid == 13 or  # Ice Mountains
              biomeid == 19):   # TaigaHills
            dict = 'norse.txt'
            self.titles = ['King','Queen']
        elif (biomeid == 6):    # Swampland
            dict = 'saxon.txt'
            self.titles = ['King','Queen']
        elif (biomeid == 4 or   # Forest
              biomeid == 18):   # ForestHills
            dict = 'elven.txt'
            self.titles = ['King','Queen']
        elif (biomeid == 21 or  # Jungle
              biomeid == 22):   # Jungle Hills
            dict = 'mayan.txt'
            self.titles = ['Tepal']
        elif (biomeid == 14 or  # MushroomIsland
              biomeid == 15):   # MushroomIslandShore
            dict = 'welsh.txt'
            self.titles = ['Y Brenin','Y Frenhines']
        elif (biomeid == 3 or   # ExtremeHills
              biomeid == 20):   # ExteremeHillsEdge
            dict = 'greek.txt'
            self.titles = ['King','Queen']
        else:                   # The rest. Including plains, rivers,
            dict = 'roman.txt'  # oceans and any misc biomes
            self.titles = ['Emperor','Empress']

        # Find name dictionaries
        if os.path.isdir(os.path.join(sys.path[0],'names')):
            names_path = os.path.join(sys.path[0],'names')
        elif os.path.isdir('names'):
            names_path = 'names'
        else:
            sys.exit("Error: Could not find the names folder!")

        # Set up name generator
        self.generator = namegen.NameGen(os.path.join(names_path,dict))

    def genname(self):
        name = self.generator.gen_word(True)    # True indicates a unqiue name
        return name

    def genroyalname(self):
        name = random.choice(self.titles) + ' ' + self.genname()
        return name