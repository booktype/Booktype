#!/bin/bash
#
# MIT license
# https://github.com/MiczFlor/From-EPUB-To-Conversion
#

# read parameters from input
while [[ $# -gt 1 ]]
do
key="$1"

case $key in
    -i|--in)
    SOURCE="$2"
    shift
    ;;
    -o|--out)
    TARGET="$2"
    shift
    ;;
    -p)
    PANDOC="$2"
    shift
    ;;
    -t)
    TEMPDIR="$2"
    shift
    ;;
    *)
esac
shift # past argument or value
done

filename=$(basename "$TARGET")
TARGETEXTENSION="${filename##*.}"
TARGETFILENAME="${filename%.*}"
TEMPDIR="${TEMPDIR}"
PANDOC="${PANDOC:-"pandoc"}"
DOCXFOLDER=$TEMPDIR"/"$TARGETFILENAME

printf '%s\n'
echo INITIAL VARIABLES
printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
echo SOURCE === $SOURCE
echo TARGET === $TARGET
echo TARGET EXTENSION === $TARGETEXTENSION
echo TARGET FILENAME === $TARGETFILENAME
echo PANDOC EXECUTABLE === $PANDOC
echo TEMP DIR === $TEMPDIR
printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' -
printf '%s\n'

echo '-------'CREATE TEMP DIR
if [ ! -d $TEMPDIR ]; then
  mkdir -p $TEMPDIR;
fi
echo '-------'DONE
printf '%s\n'

echo '-------'CREATE DOCX DIR
if [ ! -d $DOCXFOLDER"/Chapters" ]; then
  mkdir -p $DOCXFOLDER"/Chapters";
fi
echo '-------'DONE
printf '%s\n'

echo '-------'RUN PANDOC
$PANDOC -s --from epub --to docx -o $DOCXFOLDER"/COMPLETE_"$TARGETFILENAME.docx $SOURCE
echo '-------'DONE
printf '%s\n'

echo '-------'COPY EPUB TO TEMP
cp $SOURCE $TEMPDIR"/"source.epub
echo '-------'DONE
printf '%s\n'

echo '-------'UNZIP SOURCE EPUB
cd $TEMPDIR
unzip ./source.epub
echo '-------'DONE
printf '%s\n'

echo '-------'COPY FONTS, CSS AND IMAGES TO DOCX FOLDER
cp -R ./OEBPS/Fonts $DOCXFOLDER
cp -R ./OEBPS/Images $DOCXFOLDER
cp -R ./OEBPS/Styles $DOCXFOLDER
echo '-------'DONE
printf '%s\n'

echo '-------'RUN PANDOC FOR EACH CHAPTER
cd ./OEBPS/Text/
for chapterxhtml in *.xhtml; do
    # chapter name without xhtml ending
    chaptername=$(echo $chapterxhtml | cut -f 1 -d '.')
    $PANDOC -s --from html --to docx -o $DOCXFOLDER"/Chapters/"$chaptername.docx $chapterxhtml
done
echo '-------'DONE
printf '%s\n'

echo '-------'CREATE ZIP
cd $TEMPDIR
zip -0r $TARGET ./$TARGETFILENAME"/"
echo '-------'DONE
printf '%s\n'

echo '-------'DELETE TEMP DIR
cd $TEMPDIR
cd ../
rm -rf $TEMPDIR
echo '-------'DONE
printf '%s\n'
