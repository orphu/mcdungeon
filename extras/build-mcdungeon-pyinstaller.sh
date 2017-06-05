#!/bin/bash
#
# Simple script to build stand alone versions of MCDungeon with
# PyInstaller.
#
# Tested configurations:
#
# Pyinstaller 3.2.1 stable
#
# Windows 10 (64 bit) / Python 2.7.13 / numpy-1.12.0 (pip) / pipywin32 219 (pip)
# OS X 10.11.3 (El Capitan) / Python 2.7.13 (pyenv) / numpy-1.13.0 (pip) *
#
# * See this note for numpy and pyenv 20150310 on OS X:
#
# https://github.com/yyuu/pyenv/issues/518#issuecomment-199827456
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

FILES="README.md LICENSE.txt CHANGELOG.txt fortunes.txt materials.cfg items.txt magic_items.txt dye_colors.txt potions.txt recipes.txt configs example_configs books shops spawners items paintings names overviewer_icons d"

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

# Grab a fresh copy of the repo
git clone --recursive https://github.com/orphu/mcdungeon || error 'Failed to pull MCDungeon repo.' $?
# Pick a rev and update pymclevel if we need to
if [ ${1:+1} ]; then
	echo "Checking out $1..."
	cd mcdungeon 
	git checkout --quiet $1 || error 'Failed to checkout branch/tag.' $?
	git submodule sync || error 'Failed to sync submodules.' $?
	git submodule update || error 'Failed to update submodules.' $?
	cd ..
fi

# Figure out the version, or use the tag
if [ ${1:+1} ]; then
	VERSION=$1
else
	# FIXME - boy this is ugly
	VERSION=$(grep ^__version__ mcdungeon/mcdungeon.py | cut -d\' -f2)
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
python makespec.py -F -c $OPTS mcdungeon/mcdungeon.py || error 'Makespec step failed.' $?

# Add additional data files.
sed -i -e '/^pyz/ i\
a.datas += [ \
        ("pymclevel/minecraft.yaml", "mcdungeon/pymclevel/minecraft.yaml", "DATA"), \
        ("pymclevel/classic.yaml", "mcdungeon/pymclevel/classic.yaml", "DATA"), \
        ("pymclevel/indev.yaml", "mcdungeon/pymclevel/indev.yaml", "DATA"), \
        ("pymclevel/pocket.yaml", "mcdungeon/pymclevel/pocket.yaml", "DATA"), \
]
' mcdungeon/mcdungeon.spec

# Build it!
python pyinstaller.py --clean mcdungeon/mcdungeon.spec || error 'Pyinstaller build failed.' $?

# Copy over support files
mkdir -p $NAME/bin
for SUBDIR in $FILES; do
	echo "Copying $SUBDIR..."
	cp -r mcdungeon/$SUBDIR $NAME/bin/
done

case $PLATFORM in
	win)
		cp -v mcdungeon/extras/launcher.bat $NAME/launcher.bat
		;;
	macosx)
		cp -v mcdungeon/extras/launcher.command $NAME/launcher.command
		;;
esac

# Move a few things out of the bin directory
for F in README.md CHANGELOG.txt LICENSE.txt; do
	mv -v $NAME/bin/$F $NAME/$F
done

# Copy over the executable
cp -v mcdungeon/dist/$EXE $NAME/bin/

echo -e "\nDone!"
echo "Look in $NAME"
