STYLE_EDITOR = '''

#contenteditor {
    font-family: serif;
    line-height: 120%;
    font-size: 1em;
}

#contenteditor P {
    text-align: left;
    windows: 2;
    orphans: 2;
    margin-top:0em;
    margin-bottom:0em;
    line-height: 120%;
}

#contenteditor P, #contenteditor TD {
    line-height: 120%;
    font-family: serif;
}

#contenteditor A {
  color: red;
  text-decoration: underline;
}

/* Copyright page *************************************************************/

#contenteditor .cpytxt
{
    font-size:0.8em;
    text-align:left;
    margin-top:0em;
    margin-bottom:0em;
}

/* Basic Chapter Level Style Definitions *************************************************************/

/* Headings *******************************************************************/
/* Headings should be left aligned or centered, they do not have to contain a back link ******/

#contenteditor h1,
#contenteditor h2,
#contenteditor h3,
#contenteditor h4,
#contenteditor h5,
#contenteditor h6
{
    -webkit-hyphens:none;
    hyphens:none;
    adobe-hyphenate:none;
    page-break-after:avoid;
}

#contenteditor p
{
    widows:2;
    orphans:2;
}

#contenteditor img
{
    max-width:100%;
    max-height:100%;
    display:inline-block;
}

#contenteditor p.caption {
    font-style: italic;
}

#contenteditor .group_img {
  page-break-inside: avoid;
}

#contenteditor .image {
}

#contenteditor .center {
  text-align: center;
}

#contenteditor .caption_small {
   margin-top: 0.5em;
}

#contenteditor div.do_pagebreak
{
    page-break-before:always;
}

#contenteditor .page-break {
    page-break-after:always;
}

'''

STYLE_EPUB = '''

/* Copyright page *************************************************************/

body {
    font-family: serif;
    line-height: 120%;
    font-size: 1em;
}

p {
    text-align: left;
    windows: 2;
    orphans: 2;
    margin-top:0em;
    margin-bottom:0em;
    line-height: 120%;
}

p, td {
    line-height: 120%;
    font-family: serif;
}

a {
  color: red;
  text-decoration: underline;
}

.cpytxt
{
    font-size:0.8em;
    text-align:left;
    margin-top:0em;
    margin-bottom:0em;
}

/* Basic Chapter Level Style Definitions *************************************************************/

/* Headings *******************************************************************/
/* Headings should be left aligned or centered, they do not have to contain a back link ******/

h1,
h2,
h3,
h4,
h5,
h6
{
    -webkit-hyphens:none;
    hyphens:none;
    adobe-hyphenate:none;
    page-break-after:avoid;
}

p
{
    widows:2;
    orphans:2;
}

img
{
    max-width:100%;
    max-height:100%;
    display:inline-block;
}

p.caption {
    font-style: italic;
}

.group_img {
  page-break-inside: avoid;
}

.image {
}

.center {
  text-align: center;
}

.caption_small {
   margin-top: 0.5em;
}

div.do_pagebreak
{
    page-break-before:always;
}

.page-break {
    page-break-after:always;
}
'''
