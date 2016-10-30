This folder contains the configuration files for villager shops. These are
generated in the SecretShops type secret rooms.

Shops have a single [shop] section and then one or more [tradeX] sections,
starting from [trade1], [trade2], etc. You can look in the existing trades
to help you create your own, and refer to the below information.

In the shop section, the following values should be set:

Name: This is the name of the shop, which will be displayed on signs.
      Maximum four words, which will appear one per line.
      Each shop keeper has a randomly generated name, you can use {{name}}
      (normal name) or {{name's}} (possessive version) to substitute this
      in to the shop name. e.g. "{{name's}} shop" becomes "Bob's shop"
     
profession_ID: ID number of the villager type. Also changes the colour
               scheme of the room.
            Farmer 0, Librarian 1, Priest 2, Blacksmith 3, Butcher 4, Nitwit 5
              
free_sample: Item to put in the shop sign. Also acts as a freebie for the
             discovering adventurer. Just use an item name, e.g. Wood Sword
            
You can have as many trade sections as you like. Trades contain the
following:

chance: Percentage chance this trade will appear. 100 will cause the trade
        to always generate
       
max_uses: The number of times this trade can be activated. This available
          trades will get refreshed when the villager levels up.
         
input: The input item. (What the player pays.) See format below.
input2: (optional) A secondary input item. Normally used for enchanting
        items etc. See format below.
output: The output item. (What the player receives) See format below.
limited: (optional) When True, this trade will never refresh. Use for
         items that should be very rare or unique.
        
Input/Output item format:

    Item Name[/Item Name/...][,Item Count][,Enchant Levels]

Examples:
    Emerald            # One Emerald
    Emerald,10         # Ten Emeralds
    Emerald/Diamond    # An Emerald or A Diamond
    Wooden Sword,1,10  # An enchanted sword

You can use anything you would normally put in a loot table.