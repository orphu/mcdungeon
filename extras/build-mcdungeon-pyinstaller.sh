#!/bin/bash
#
# Simple script to build stand alone versions of MCDungeon with
# PyInstaller.
#
# Tested configurations:
#
# Pyinstaller 2.1 dev - 5804133658
#
# Windows 7 / Python 2.7.3 64 bit
# Windows 7 / Python 2.7.3 32 bit
# Linux / Python 2.7.3 64 bit (Ubuntu)
# OS X 10.8 / Python 2.7.2 64 bit 
#
# Requirements:
# 	Python 2.7.x
#	numpy
#	pywin32 (for windows)
#	Pyinstaller 
#	git 
#	Gitbash from Git for Windows if Windows
#
# Copy this script into the pyinstaller folder, then run this script with
# desired tag. Passing no options will build the current master HEAD rev,
# which should be the current release version.

FILES="fortunes.txt items.txt magic_items.txt dye_colors.txt potions.txt configs books spawners items"

function error {
	echo -e "\nFATAL: $1"
	exit $2
}

# Figure out the platform
case `python -c 'import platform;print platform.system()'` in
	Windows)
		PLATFORM="win"
		EXE="mcdungeon.exe"
		OPTS=" --icon=mcdungeon/extras/favicon.ico "
		;;
	Darwin)
		PLATFORM="macosx"
		EXE="mcdungeon"
		OPTS=""
		;;
	Linux)
		PLATFORM="linux"
		EXE="mcdungeon"
		OPTS=""
		;;
	*)
		error 'Unable to determine platform! Aborting!' 1
		;;
esac
echo "Platform is $PLATFORM"
	
# Clean up the build environment
if [ -d mcdungeon ]; then
	echo "Removing old git repo..."
	rm -rf mcdungeon
fi
if [ -d mcdungeon-build ]; then
	echo "Removing old build directory..."
	rm -rf mcdungeon-build
fi

# Grab a fresh copy of the repo
git clone --recursive https://github.com/orphu/mcdungeon || error 'Failed to pull MCDungeon repo.' $?
# Pick a rev and update pymclevel if we need to
if [ ${1:+1} ]; then
	echo "Checking out $1..."
	cd mcdungeon 
	git checkout --quiet $1 || error 'Failed to checkout branch/tag.' $?
	git submodule update || error 'Failed to updade pymclevel submodule.' $?
	cd ..
fi

# Figure out the version, or use the tag
if [ ${1:+1} ]; then
	VERSION=$1
else
	# FIXME - boy this is ugly
	VERSION=`grep ^__version__ mcdungeon/mcdungeon.py | cut -d\' -f2`
	VERSION="v${VERSION}"
fi
echo "MCDungeon Version is $VERSION"

# Figure out the machine		
case `python -c 'import platform;print platform.machine()'` in
	x86_64|AMD64)
		MACH="64"
		;;
	x86)
		MACH="32"
		;;
	*)
		MACH=""
		;;
esac

NAME="mcdungeon-${VERSION}-${PLATFORM}${MACH}"
echo "Build name will be: $NAME"

if [ -d $NAME ]; then
	echo "Removing old distro directory..."
	rm -rf $NAME
fi

# Make a spec file.
python utils/Makespec.py -o mcdungeon-build --onefile $OPTS mcdungeon/mcdungeon.py || error 'Makespec step failed.' $?
# Add additional data files.
sed -i -e '/^pyz/ i\
a.datas += [ \
	("pymclevel/minecraft.yaml", "mcdungeon/pymclevel/minecraft.yaml", "DATA"), \
	("pymclevel/classic.yaml", "mcdungeon/pymclevel/classic.yaml", "DATA"), \
	("pymclevel/indev.yaml", "mcdungeon/pymclevel/indev.yaml", "DATA"), \
	("pymclevel/pocket.yaml", "mcdungeon/pymclevel/pocket.yaml", "DATA"), \
]
' mcdungeon-build/mcdungeon.spec
# Build it!
python utils/Build.py -y mcdungeon-build/mcdungeon.spec || error 'Pyinstaller build failed.' $?

# Copy over support files
mkdir $NAME
for SUBDIR in d $FILES; do
	cp -r mcdungeon/$SUBDIR $NAME/
done
for FILE in `find . -name README`; do mv $FILE $FILE.txt; done
cp mcdungeon/CHANGELOG $NAME/CHANGELOG.txt
cp mcdungeon/README $NAME/README.txt
cp mcdungeon/LICENSE $NAME/LICENSE.txt
case $PLATFORM in
	win)
		cp mcdungeon/extras/launcher.bat $NAME/lancher.bat
		;;
	macosx)
		cp mcdungeon/extras/launcher.command $NAME/launcher.command
		;;
esac

# Copy over the executable
cp mcdungeon-build/dist/$EXE $NAME/

echo -e "\nDone!"
echo "Look in $NAME"
