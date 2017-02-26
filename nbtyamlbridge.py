from pymclevel import nbt
from nbt2yaml import parse_yaml, parse
from numpy import fromstring

# Get pymclevel tags from YAML file
def tagsfromfile(filename):
    return convert(loadyaml(filename))

# Load structure from YAML
def loadyaml(filename):
    yamlfile = open(filename, 'rb')
    nbt_structure = parse_yaml(yamlfile)
    yamlfile.close()
    return nbt_structure

# This allows us to process lists in the same way as compounds
class dummyNBTyaml:
    def __init__(self, type, data):
        self.type = type
        self.data = data
        self.name = None

# Convert structure parsed from YAML to pymclevel NBT tags
def convert(tag):
    out = None
    if (tag.type is parse.TAG_Byte):
        out = nbt.TAG_Byte(value=tag.data, name=tag.name)
    elif (tag.type is parse.TAG_Byte_Array):
        out = nbt.TAG_Byte_Array(value=fromstring(tag.data), name=tag.name)
    elif (tag.type is parse.TAG_Double):
        out = nbt.TAG_Double(value=tag.data, name=tag.name)
    elif (tag.type is parse.TAG_Float):
        out = nbt.TAG_Float(value=tag.data, name=tag.name)
    elif (tag.type is parse.TAG_Int):
        out = nbt.TAG_Int(value=tag.data, name=tag.name)
    elif (tag.type is parse.TAG_Int_Array):
        out = nbt.TAG_Int_Array(value=tag.data, name=tag.name)
    elif (tag.type is parse.TAG_Long):
        out = nbt.TAG_Long(value=tag.data, name=tag.name)
    elif (tag.type is parse.TAG_Short):
        out = nbt.TAG_Short(value=tag.data, name=tag.name)
    elif (tag.type is parse.TAG_String):
        out = nbt.TAG_String(value=tag.data, name=tag.name)
    # Recursives
    elif (tag.type is parse.TAG_Compound):
        out = nbt.TAG_Compound(name=tag.name)
        for item in tag.data:
            temp = convert(item)
            if (temp is not None):
                out[temp.name] = temp
    elif (tag.type is parse.TAG_List):
        out = nbt.TAG_List(name=tag.name)
        for item in tag.data[1]:
            temp = convert(dummyNBTyaml(tag.data[0], item))
            if (temp is not None):
                out.append(temp)

    return out