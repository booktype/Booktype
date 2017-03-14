#!/bin/bash
#
# MIT license
# https://github.com/MiczFlor/From-EPUB-To-Conversion
#
# USAGE EXAMPLES:
# ../ConvertEpubChapter2DOCX.sh -i ../test-booktype.epub -o ../tests/test-booktype-DOCX.zip
# ../ConvertEpubChapter2DOCX.sh --in ../test-booktype.epub --out ../tests/test-booktype-DOCX.zip

# read parameters from input
while [[ $# -gt 1 ]]
do
key="$1"

case $key in
    -i|--in)
    SOURCE="$2"
    shift # past argument
    ;;
    -o|--out)
    TARGET="$2"
    shift # past argument
    ;;
    -p)
    PANDOC="$2"
    shift # past argument
    ;;
    *)
esac
shift # past argument or value
done

filename=$(basename "$TARGET")
TARGETEXTENSION="${filename##*.}"
TARGETFILENAME="${filename%.*}"

#echo SOURCE             = $SOURCE
#echo TARGET             = $TARGET
#echo TARGETEXTENSION    = $TARGETEXTENSION
#echo TARGETFILENAME     = $TARGETFILENAME

# create temporary working directory
if [ ! -d temp ]; then
  mkdir -p temp;
fi

# create DOCX directory
if [ ! -d $TARGETFILENAME"/Chapters" ]; then
  mkdir -p $TARGETFILENAME"/Chapters";
fi

# create a DOCX version of the entire book
${PANDOC:-"pandoc"} -s --from epub --to docx -o "COMPLETE_"$TARGETFILENAME.docx $SOURCE
# move the file to the Text directory
mv "COMPLETE_"$TARGETFILENAME.docx $TARGETFILENAME

# create a copy for processing
cp $SOURCE ./temp/book.epub

# unzip epub
cd ./temp
unzip ./book.epub

# copy fonts, css and images to DOCX folder
cp -R ./OEBPS/Fonts ../$TARGETFILENAME"/"
cp -R ./OEBPS/Images ../$TARGETFILENAME"/"
cp -R ./OEBPS/Styles ../$TARGETFILENAME"/"

# move to where the HTML files are
cd ./OEBPS/Text/

for chapterxhtml in *.xhtml; do
    # new chapter name without xhtml ending
    chaptername=$(echo $chapterxhtml | cut -f 1 -d '.')
    ${PANDOC:-"pandoc"} -s --from html --to docx -o $chaptername.docx $chapterxhtml
    mv $chaptername.docx ../../../$TARGETFILENAME"/Chapters/"
done

# move back up outside temp directory
cd ../../../

# delete everything in temp folder
rm -rf ./temp

# create zip for ICML files and remove folder
zip -0r $TARGETFILENAME-DOCX.zip ./$TARGETFILENAME"/"
# delete working folder
rm -rf ./$TARGETFILENAME"/"

# move file to target
mv $TARGETFILENAME-DOCX.zip $TARGET
