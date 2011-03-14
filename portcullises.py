from utils import *


class Portcullis(object):
    def __init__(self):
        self.loc = Vec(0,0,0)
        self.material = None
        self.portcullises = {}
        self.size = 0
