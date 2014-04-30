This folder contains the data for written books. Whenever MCDungeon creates
a written book as loot, a random text will be selected from this folder. If
there are no files, a book and quill will be substituted.

The default books provided are public domain works sourced from Project
Gutenberg (http://www.gutenberg.org/)

You may add your own books using the following guide:

    * Books are simple text files. The file should use the ".txt" extension.

    * The first line is the author, The second the book title and then one
      line per page of the book.

    * As in Minecraft, Books are limited to 256 characters per page and 50
      pages per book. Any excess will not be loaded.

    * IMPORTANT: It is not enough to just split the text every 256
      characters. It is still possible for the text on a page to be too
      long which will make it look funny in Minecraft. The default texts
      were split using the help of the Multiplayer Book Paster tool.
      (http://ray3k.com/site/?page_id=13) Another option would be to input
      the text in to a book in Minecraft to check what works.

    * The following escape characters can be used:
        \n - Produces a new line
        \s - Produces the section sign
        \\ - Produces a backslash
      For information about using the section sign for formatting, see:
      http://www.minecraftwiki.net/wiki/Formatting_Codes

    * For the moment, only the following characters are supported:
        0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
        !"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~ 
      Other characters will be removed.
