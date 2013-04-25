echo off

set APP_NAME=updb-explorer

if "%1"=="" (set VERSION=) else set VERSION=_%1
echo %VERSION%

echo 'Cleaning...'
rd /S /Q dist
rd /S /Q build
rd /S /Q %APP_NAME%
echo 'Running build script...'
python setup.py py2exe

echo 'Moving files around...'
:: move the auto-generated programs and packages around
ren dist %APP_NAME%
rd /S /Q build

:: copy documentation and config files
:: copy COPYING.txt %APP_NAME%
:: copy COPYING.LESSER.txt %APP_NAME%
copy README.md %APP_NAME%

::echo 'Bundling...'
cd %APP_NAME%
7z.exe a ../%APP_NAME%%VERSION%.zip *
cd ..
rd /S /Q %APP_NAME%