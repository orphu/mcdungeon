This folder contains the data for written books. Whenever MCDungeon creates
a written book as loot, a random text will be selected from this folder. If
there are no files, an unwritten book will be substituted.

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
	  (http://ray3k.com/site/downloads/minecraft/mbp/) Another option would
	  be to input the text in to a book in Minecraft to check what works.
	  
	* For the moment, there is currently no way to put line-returns or
	  formatting in the text.

	* For the moment, only the following characters are supported:
		0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
		!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~ 
	  Other characters will be removed.