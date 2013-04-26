#!/bin/bash
if [ -z $1 ]
then
	VERSION=""
else
	VERSION="_"$1
fi

APP_NAME=updb-explorer

STARTING_DIR=$(pwd)

SCRIPT_DIR=$(readlink -f $0)
SCRIPT_DIR=${SCRIPT_DIR%"bundle_linux.sh"}
cd $SCRIPT_DIR
rm -rf dist
rm -rf build
rm -rf $APP_NAME
echo 'Running build script...'
python setup.py build

echo 'Moving files around...'
# move the auto-generated programs and packages around
mv dist $APP_NAME
# copy the svg and ui elements manually
mkdir $APP_NAME/resources
cp -r resources/*.ui $APP_NAME/resources
cd build/exe*
mv * ../../$APP_NAME
cd ../..
rm -rf build
# copy documentation and config files
#cp COPYING.txt $APP_NAME
#cp COPYING.LESSER.txt $APP_NAME
cp README.md $APP_NAME

echo 'Bundling...'
tar -czf $APP_NAME$VERSION.tar.gz $APP_NAME
mv $APP_NAME$VERSION.tar.gz $STARTING_DIR
