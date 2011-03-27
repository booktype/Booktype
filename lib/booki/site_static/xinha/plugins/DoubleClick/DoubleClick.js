// Double Click Plugin for Xinha
// Implementation by Marijn Kampf http://www.marijn.org
// Sponsored by http://www.smiling-faces.com
//
// (c) Marijn Kampf 2004.
// Distributed under the same terms as HTMLArea itself.
// This notice MUST stay intact for use (see license.txt).
//
// Cut-n-paste version of double click plugin.
// Almost no original code used. Based on
// Luis HTMLarea and Mihai Bazon Context Menu
//
//
//

DoubleClick._pluginInfo = {
  name          : "DoubleClick",
  version       : "1.0",
  developer     : "Marijn Kampf",
  developer_url : "http://www.marijn.org",
  c_owner       : "Marijn Kampf",
  sponsor       : "smiling-faces.com",
  sponsor_url   : "http://www.smiling-faces.com",
  license       : "htmlArea"
};

function DoubleClick(editor) {
  this.editor = editor;

  // ADDING CUSTOM DOUBLE CLICK ACTIONS
  // format of the dblClickList elements is "TAGNAME: [ ACTION ]"
  //    - TAGNAME: tagname of the tag that is double clicked
  //    - ACTION: function that gets called when the button is clicked.
  //              it has the following prototype:
  //                 function(editor, event)
  //              - editor is the Xinha object that triggered the call
  //              - target is the selected object
  this.editor.dblClickList = {
    // Edit Link dialog
    a: [ function(e) {e.config.btnList['createlink'][3](e); } ],
    // Follow link
    //a: [ function(editor, target) { window.location = target.href; properties(target); } ],

    img: [ function(e) {e.execCommand("insertimage");} ],
    td: [ function(e) {e.execCommand("inserttable");} ]
  };
}

DoubleClick.prototype.onGenerate = function() {
  var self = this;
  var doc = this.editordoc = this.editor._iframe.contentWindow.document;
  Xinha._addEvents(doc, ["dblclick"],
          function (event) {
          return self.onDoubleClick(Xinha.is_ie ? self.editor._iframe.contentWindow.event : event);
          });
  this.currentClick = null;
};

DoubleClick.prototype.onDoubleClick = function(ev) {
  var target = Xinha.is_ie ? ev.srcElement : ev.target;
  var tagName = target.tagName.toLowerCase();

  if (this.editor.dblClickList[tagName] != undefined) {
    this.editor.dblClickList[tagName][0](this.editor, target);
  }
};