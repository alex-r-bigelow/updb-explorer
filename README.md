updb-explorer
=============
A system for exploring bite-size pieces of large pedigrees, specifically designed for the Utah Population Database

Running
-------
To visualize a file, you first need to add some statistics as extra columns (particularly the "generation" column). Use the "calculateD" program to do this. Once your file has this information, you can run the "vis" program from the same GUI. Don't get too comfortable with the intro GUI - I'm sure we'll change it extensively!

[Mac OS X v0.1.2](http://sci.utah.edu/~abigelow/Downloads/updb-explorer/Mac/updb-explorer_0.1.2.dmg)

[Linux v0.1.2](http://sci.utah.edu/~abigelow/Downloads/updb-explorer/Linux/updb-explorer_0.1.2.tar.gz)

[Windows v0.1.2](http://sci.utah.edu/~abigelow/Downloads/updb-explorer/Windows/updb-explorer_0.1.2.zip)

If you'd prefer to run from the source code, you will need to install Qt, Python 2.7, PySide, networkx and clone this repository. The same GUI can then be launched via:

	python updb-explorer.py

Or from the command line:

	python calculateD.py

or

	python vis.py

Issues
------
If you run into any problems, please use Github's "Issues" feature! Or send an email to alex dot bigelow at utah dot edu.