updb-explorer
=============
A system for exploring bite-size pieces of large pedigrees, specifically designed for the Utah Population Database

Installation
------------
Standalone applications are coming in hopefully a few weeks! For now, you'll have to install some specific versions of stuff before it will work - feel free to send me an email if you get stuck. These are:

Version 2.7.x of [Python](http://python.org/download/)

Version 4.8 of [Qt](http://qt-project.org/downloads)

You will also need to install these python libraries:
PySide
networkx

Probably the easiest way to do this is to:
Add python to your PATH if it isn't there already:
 - On Windows 7: Go to Control Panel -> System and Security -> System, click "Advanced System Settings", "Environment Variables", find "Path" in the bottom list, click "Edit...", and add this to the end:
 
 	;C:\Python27;C:\Python27\Lib\site-packages\;C:\Python27\Scripts\;
 
 - On OS X: open ~/.bash_profile, and add this:
 
 	PATH="/Library/Frameworks/Python.framework/Versions/2.7/bin:${PATH}"
 
 - On Linux, python is probably already in your path.

Install the "distribute" package by running [this script](http://python-distribute.org/distribute_setup.py):

	python distribute_setup.py

Install [pip](https://pypi.python.org/packages/source/p/pip/pip-1.3.1.tar.gz) - on Windows you may need something to extract the .tar.gz file like [7-zip](https://pypi.python.org/packages/source/p/pip/pip-1.3.1.tar.gz):

	cd pip-1.3.1

	python setup.py install

Then run these commands:

	pip install pyside

	pip install networkx

Running
-------
Once the program has been installed, things are still pretty command-line based. Download and unzip this repository (on GitHub, click the "Zip" button).

There are two apps inside:

calculateD.py - This adds Nicki's statistic and some other columns to an egopama file. You should run this script on a file before giving it to runViz.py

runViz.py - Visualizes the egopama file.

For more instructions for each of these apps, run:

	python calculateD.py --help

or

	python runViz.py --help