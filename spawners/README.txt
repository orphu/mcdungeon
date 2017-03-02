This folder contains the data for custom spawners. YAML files in this folder
can be referenced as spawner types in dungeon config files. See default.cfg
for more details.

Each custom spawner is an YAML file containing the nbt tags required to create
the spawner object. You may add your own files by editing the defaults
using a text editor, taking care to match nbt2yaml's format.
https://pypi.python.org/pypi/nbt2yaml

Spawners can be very simple, or potentially a very complex tree of values.
The most simple example would be a single string tag, called EntityId and
containing the EntityId of the mob you want to spawn. The Id, x, y and z
tags are unnecessary as they are added by MCDungeon.

For more information on the format of the tags see:
    * http://www.minecraftwiki.net/wiki/Chunk_format#Tile_Entity_Format
    * http://www.minecraftwiki.net/wiki/Chunk_format#Mobs

YAML files in this folder can be referenced in mob tables as
"file_[filename without extension]" For example, "Angrypig.yaml" would be
referenced as "file_Angrypig". See default.cfg for more details.

IMPORTANT: If you provide Minecraft with incorrect tags, it can potentially
crash it. Please use this feature with caution.

Packaged Spawners:
==================
Angrypig: A zombie pigman that has already been aggroed.
Catling: Skeletons with ocelot masks wielding tipped arrows
         with postive effects.
Chargedcreeper: Creeper with the lightning strike charge effect.
CustomKnight: Zombie with full suit of armour and strength.
Herobrine: You really don't want to meet this guy.
Husk: Husk zombie mob varient.
Multi_creeper: Spawns charged creepers 20% of the time. Normal creepers
               the rest of the time.
Multi_monster: Equal random chance of Zombie, Skeleton, Creeper or spider.
Multi_skeleton: Spawns wither skeletons 20% of the time. Normal skeletons
                the rest of the time.
Multi_zombie: Spawns zombie with strength and speed skeletons 20% of the time.
              Normal skeletons the rest of the time.
Silverfish_Swarm: A swarm of 5 silverfish.
Skeleton_Armored_Axe_Iron: Skeleton with an iron axe.
Skeleton_Armored_Sword_Iron: Skeleton with an iron sword.
Skeleton_Armored_Sword_Leather: Skeleton with an iron sword and leather armour.
Skeleton_Pumpkin: A tough skeleton with a pumpkin on his head so
                  that he can be in the sun.
Skeleton_Tipped_Arrow: Skeletons wielding various tipped arrows.
Stray: Stray skeleton mob varient.
Zombie_Fast: Zombie with speed potion effect.
Zombie_Pumpkin: A strengthened zombie wearing a pumpkin on his head so
                that he can be in the sun.
Zombie_Strong: Zombie with strength potion effect.
Zombie_Sword_Helmet: A zombie with a sword and helmet.
Zombie_Villager: Zombie villiager mob varient(like in a siege.)
