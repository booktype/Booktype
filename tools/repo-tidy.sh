#!/bin/bash

DIR=$1

usage() {
    echo "USAGE: $0 DIRECTORY"
}

trap usage ERR

if ! [[ "$DIR" ]]; then
    usage
    exit 1
fi

cd $DIR

#remove the twiki lease files.
find -name '*.lease' -print0 | xargs -0 rm -f

for f in  WebAtom.txt WebPreferences.txt WebChanges.txt WebRss.txt \
    WebCreateNewTopic.txt WebSearchAdvanced.txt WebHome.txt WebSearch.txt \
    WebIndex.txt WebStatistics.txt WebLeftBar.txt WebTopicList.txt WebNotify.txt; do
    rm -f */$f
done

for d in TWiki; do
    rm -rf $d
done 



