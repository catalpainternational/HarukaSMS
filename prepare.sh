#!/bin/bash

if [ "$1" = "" ];then
    echo "Please give the directory that contains a skeleton Windows HarukaSMS chromeless app, without the python source code. e.g.: ~/projects/chromeless/builds/HarukaSMS "
    exit
else
    export CLEAN_APP=$1
fi

if [ "$2" = "" ];then
    echo "Please give the directory that will contain the final clean HarukaSMS directory and zip - e.g. : ~/tmp/"
    exit
else
    export DEST=$2
fi

export HARU=$DEST/HarukaSMS-`date '+%Y%M%d'`
mkdir -p $HARU
echo "- Copying the clean HarukaSMS"
cp -r $CLEAN_APP/* $HARU/

export SRC_DEST=$HARU/haruka_lib
echo "- Copying the pyhon sources to $SRC_DEST"
mkdir -p $SRC_DEST
cp -r * $SRC_DEST/

echo "- Copying site-packages"
cp -r ../lib/python2.7/site-packages $SRC_DEST/

echo '- Going into into $SRC_DEST'
cd $SRC_DEST/
echo "- removing pyc, .so and .ds_store files"
find . -name '*.pyc' -exec rm '{}' ';'
find . -type f -name '.DS_Store' -exec rm '{}' ';'
find . -name '*.so' -exec rm '{}' ';'

echo " removing the .git and .edd-info directories"
find . -type d -name '*egg-info' -exec rm -rf '{}' ';'
find . -type d -name '.git' -exec rm -rf '{}' ';'
echo "- removing ipython directory"
rm -rf site-packages/IPython

echo '- Going two levels up'

cd ../../
echo " You should have a look through the directory structure and then run this command:"
echo "zip -r HarukaSMS-`date '+%Y%M%d'`.zip $HARU"
