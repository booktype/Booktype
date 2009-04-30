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

# remove the twiki directory
for d in TWiki; do
    rm -rf $d
done

#remove the twiki lease files.
find -name '*.lease' -print0 | xargs -0 rm -f

#remove magic twiki boilerplate
for f in  WebAtom WebPreferences WebChanges WebRss \
    WebCreateNewTopic WebSearchAdvanced WebHome WebSearch \
    WebIndex WebStatistics WebLeftBar WebTopicList WebNotify \
    WebTopicCreator WebTopicEditTemplate ; do
    rm -f */$f.txt
    rm -f */$f.txt,v
    rm -f */${f}Talk.txt
    rm -f */${f}Talk.txt,v
done




