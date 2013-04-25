#!/bin/bash
if [ -z $1 ]
then
	VERSION=""
else
	VERSION="_"$1
fi

APP_NAME=updb-explorer

STARTING_DIR=$(pwd)
SCRIPT_DIR=${0%"bundle_osx.command"}

cd $SCRIPT_DIR
rm -rf dist
rm -rf build
rm -rf $APP_NAME
echo 'Running build script...'
python setup.py py2app

echo 'Moving files around...'
# move the auto-generated programs and packages around
mv dist $APP_NAME
#rm -rf build
# move the svg and ui elements into the appropriate folders
cd $APP_NAME/$APP_NAME.app/Contents/Resources
touch qt.conf
mkdir resources
mv *.ui resources
# copy documentation and config files
cd $SCRIPT_DIR
#cp COPYING.txt $APP_NAME/
#cp COPYING.LESSER.txt $APP_NAME/
cp README.md $APP_NAME/

echo 'Bundling...'
hdiutil create -volname $APP_NAME -srcfolder $APP_NAME/ -ov -format UDZO $APP_NAME$VERSION.dmg
#rm -rf $APP_NAME
mv $APP_NAME$VERSION.dmg $STARTING_DIR