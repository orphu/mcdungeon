This folder contains the data for customised items. NBT files in this
folder can be referenced in loot tables as file_[filename without extension]
For example, head_notch.nbt would be referenced as file_head_notch.
See default.cfg for more details.

Each custom item is an NBT file containing the tags required to create
the inventory item. You may add your own files by editing the defaults
using an NBT editor. You can also extract the tags from a player file from
an existing Minecraft level and use that. NBTExplorer is recommended for
editing:
http://www.minecraftforum.net/topic/840677-nbtexplorer-nbt-editor-for-windows-and-mac/

Items can be very simple, or potentially a very complex tree of values.
The most simple example would be a single short tag, called id and
containing the numerical id of the item.

NOTE: The Count tag is used to determine the maximum size of a stack. This is
the tag which is normally used by minecraft to store how large the stack of
items you are holding is.

For more information on the format of the tags see:
    * http://www.minecraftwiki.net/wiki/Player.dat_Format#Item_structure

IMPORTANT: If you provide Minecraft with incorrect tags, it can potentially
crash it. Please use this feature with caution.

Packaged Items:
===============
- Items starting with "heads_" are the heads of some famous (and not so
  famous) minecrafters.
- Items starting with "firework_" are various pre-created fireworks,
  some using rare crafting materials.
- Items starting "spellbook_" are spellbooks. These are somewhat overpowered,
  so think before adding them.

Hopefully more to come!
