#!/bin/bash
#
# Simple script to package the required bits for python versions of MCDungeon
#
# Copy this script into a new folder, then run this script with
# desired tag. Passing no options will build the current master HEAD rev,
# which should be the current release version.

FILES="README.md LICENSE.txt CHANGELOG.txt fortunes.txt materials.cfg items.txt magic_items.txt dye_colors.txt potions.txt configs example_configs books shops spawners items paintings names overviewer_icons d"

function error {
	echo -e "\nFATAL: $1"
	exit $2
}

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

NAME="mcdungeon-${VERSION}"
echo "Build name will be: $NAME"

if [ -d $NAME ]; then
	echo "Removing old distro directory..."
	rm -rf $NAME
fi

# Create distro directory
mkdir $NAME

# Copy over support files
for SUBDIR in $FILES; do
	echo "Copying $SUBDIR..."
	cp -r mcdungeon/$SUBDIR $NAME/
done

# Copy over the python code
for SUBDIR in \*.py pymclevel overviewer_core namegen yaml; do
	echo "Copying $SUBDIR..."
	cp -r mcdungeon/$SUBDIR $NAME/
done

# Remove cruft
rm $NAME/cave_demo.py
rm $NAME/dungeon_name_test.py
rm $NAME/perlin_test.py
rm -rf $NAME/pymclevel/regression_test $NAME/pymclevel/schematics $NAME/pymclevel/test $NAME/pymclevel/testfiles

echo -e "\nDone!"
echo "Look in $NAME"
