AsciiMathML Formula Editor for Xinha
 _______________________
 
Based on AsciiMathML by Peter Jipsen (http://www.chapman.edu/~jipsen).
Plugin by Raimund Meyer (ray) xinha@raimundmeyer.de

AsciiMathML is a JavaScript library for translating ASCII math notation to Presentation MathML.

Usage
 The formmulae are stored in their ASCII representation, so you have to include the 
 ASCIIMathML library which can be found in the plugin folder in order to render the MathML output in your pages. 
 
 Example (also see example.html):
  var mathcolor = "black"; //  You may change the color of the formulae (default: red)
  var mathfontfamily = "Arial"; //and the font (default: serif, which is good I think)
  var showasciiformulaonhover = false; // if true helps students learn ASCIIMath (default:true)
  <script type="text/javascript" src="/xinha/plugins/AsciiMath/ASCIIMathML.js"></script>

 The recommended browser for using this plugin is Mozilla/Firefox. At the moment showing the MathML output
 inside the editor is not supported in Internet Explorer.
 
 
License information

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License as published by
 the Free Software Foundation; either version 2.1 of the License, or (at
 your option) any later version.

 This program is distributed in the hope that it will be useful, 
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 Lesser General Public License (at http://www.gnu.org/licenses/lgpl.html) 
 for more details.
 
 NOTE: I have changed the license of AsciiMathML from GPL to LGPL according to a permission 
 from the author (see http://xinha.gogo.co.nz/punbb/viewtopic.php?pid=4150#p4150)
 Raimund Meyer 11-29-2006