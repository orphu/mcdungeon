This set of configurations requires the Minecraft Forge module "Lucky Blocks" to be installed.

This popular module creates a new block type, 850 == lucky:lucky_block, which has a number of random outcomes when mined.

Information about the Lucky Blocks module is here:
http://www.planetminecraft.com/mod/lucky-block/

Under early versions of Minecraft, the lucky block ID is 850

Under Minecraft 1.7, the ID changes as new modules are loaded.  
If no other modules creating blocks are installed before it, it will get ID 165.
These examples are set up using 165 but if your system is different, you
will need to modify the ID setting in items.txt, materials.cfg, and the items/*.nbt

Under Minecraft 1.8, the ID is lucky:lucky_block

Under Minecraft 1.9, Forge is not yet available, but it is anticipated that Lucky Blocks will be named as under 1.8.

Lucky blocks are configured in the .minecraft/config/lucky/LuckyBlockProperties.txt file;
you may well want to disable various potential effects that do not work well underground.

The sample NBT files in the items/ directory explicitly specify only drop effects that
are practical underground, removing the need to use a customised LuckyBlockProperties.txt
file.