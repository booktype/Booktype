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
ICMLFOLDER=$TEMPDIR"/"$TARGETFILENAME

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

echo '-------'CREATE ICML DIR
if [ ! -d $ICMLFOLDER"/Chapters" ]; then
  mkdir -p $ICMLFOLDER"/Chapters";
fi
echo '-------'DONE
printf '%s\n'

echo '-------'RUN PANDOC
$PANDOC -s --from epub --to icml -o $ICMLFOLDER"/COMPLETE_"$TARGETFILENAME.icml $SOURCE
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

echo '-------'COPY FONTS, CSS AND IMAGES TO ICML FOLDER
cp -R ./OEBPS/Fonts $ICMLFOLDER
cp -R ./OEBPS/Images $ICMLFOLDER
cp -R ./OEBPS/Styles $ICMLFOLDER
echo '-------'DONE
printf '%s\n'

echo '-------'RUN PANDOC FOR EACH CHAPTER
cd ./OEBPS/Text/
for chapterxhtml in *.xhtml; do
    # chapter name without xhtml ending
    chaptername=$(echo $chapterxhtml | cut -f 1 -d '.')
    $PANDOC -s --from html --to icml -o $ICMLFOLDER"/Chapters/"$chaptername.icml $chapterxhtml
done
echo '-------'DONE
printf '%s\n'

echo '-------'GENERATE HOWTO.txt FILE
echo "Tested with InDesign CC 2017

1. What is an ICML file?

ICML stands for InCopy Markup Language. It is a standard defined
by Adobe allowing the easy migration of content between InDesign
documents.

An ICML file is a text only file, similar to an HTML file, which
can be imported into and exported from InDesign. The ICML file
contains relevant information about the content and formatting
as well as relative links to media.

Using ICML file to migrate content to InDesign has the advantage
that the content can flow into an existing InDesign IDML document.
In other words: If you have a book layout in InDesign, you can
add content in chapters - or entire books - by placing ICML
content inside your project.

This is similar to placing DOCX files in InDesign with one major
advantage: the images referenced in ICML are 'raw' whereas the
DOCX images are embedded in the DOCX file - and depending on the
editor that was used to create the DOCX file, you never quite
know what conversion has been applied to the image.

If you start from scratch, follow the below step to import an
entire book into a new InDesign document.

2. Adding pages automatically when importing ICML

InDesign's 'Smart Text Reflow' functionality allows to automatically
create pages when importing a document, such as an ICML file. Here
is a simple example, assuming you start a new document:

2.1. Create new document

Make sure 'Number of pages' is set to 1.
Activate 'Primary Text Frame'.
Create document by clicking 'OK'.

2.2. Edit preferences

* Select 'Preferences > Type...' from the dropdown menu.
* Activate the 'Smart Text Reflow' section.
* Select where you want pages to be added automatically.
* Select if you want to 'Limit to primary text frames' or also
  reflow into other text frames.
* You can also select if empty pages should be deleted.
* Click 'OK' to close the preferences.

2.3. Place document

Place the ICML document in the first page of the new document.
Select 'Place' to import the ICML content.

3. Linked ICML file

The ICML file is linked to InDesign. This means that changes made
in the ICML file are reflected in InDesign. You can break this link,
if you are sure that you don't want your InDesign document to be
updated automatically as the content of the ICML file changes.

3.1. Unlink ICML file

* Select 'Links' to show all linked files.
* Locate the ICML file and simply 'unlink' it." >> $ICMLFOLDER"/HOWTO.txt"
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
