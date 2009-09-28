// DefinitionList plugin for Xinha
// Distributed under the same terms as Xinha itself.
// This notice MUST stay intact for use (see license.txt).


function DefinitionList(editor) {
  this.editor = editor;
  var cfg = editor.config;
  var bl = DefinitionList.btnList;
  var self = this;
  // register the toolbar buttons provided by this plugin
  var toolbar = ["linebreak"];
  for (var i = 0; i < bl.length; ++i) {
    var btn = bl[i];
    if (!btn) {
      toolbar.push("separator");
    } else {
      var id = btn[0];
      cfg.registerButton(id, this._lc(btn[1]), editor.imgURL("ed_" + btn[0] + ".gif", "DefinitionList"), false,
             function(editor, id) {
               // dispatch button press event
               self.buttonPress(editor, id);
             });
      toolbar.push(id);
    }
  }
  // add a new line in the toolbar
  cfg.toolbar.push(toolbar);
}

DefinitionList._pluginInfo = {
  name          : "DefinitionList",
  version       : "1.0",
  developer     : "Udo Schmal",
  developer_url : "",
  c_owner       : "Udo Schmal",
  license       : "htmlArea"
};

// the list of buttons added by this plugin
DefinitionList.btnList = [
  ["dl", "definition list"],
  ["dt", "definition term"],
  ["dd", "definition description"]
  ];

DefinitionList.prototype._lc = function(string) {
  return Xinha._lc(string, 'DefinitionList');
};

DefinitionList.prototype.onGenerate = function() {
  this.editor.addEditorStylesheet(Xinha.getPluginDir('DefinitionList') + '/definition-list.css');
};

DefinitionList.prototype.buttonPress = function(editor,button_id) {
  if (button_id=='dl') { //definition list
    var pe = editor.getParentElement();
    while (pe.parentNode.tagName.toLowerCase() != 'body') {
      pe = pe.parentNode;
    }
    var dx = editor._doc.createElement(button_id);
    dx.innerHTML = '&nbsp;';
    if(pe.parentNode.lastChild==pe) {
      pe.parentNode.appendChild(dx);
    }else{
      pe.parentNode.insertBefore(dx,pe.nextSibling);
    }
  } else if ((button_id=='dt')||(button_id=='dd')) { //definition term or description
    var pe = editor.getParentElement();
    while (pe && (pe.nodeType == 1) && (pe.tagName.toLowerCase() != 'body')) {
      if(pe.tagName.toLowerCase() == 'dl') {
        var dx = editor._doc.createElement(button_id);
        dx.innerHTML = '&nbsp;';
        pe.appendChild(dx);
        break;
      }else if((pe.tagName.toLowerCase() == 'dt')||(pe.tagName.toLowerCase() == 'dd')){
        var dx = editor._doc.createElement(button_id)
        dx.innerHTML = '&nbsp;';
        if(pe.parentNode.lastChild==pe) {
        pe.parentNode.appendChild(dx);
        }else{
          pe.parentNode.insertBefore(dx,pe.nextSibling);
        }
        break;
      }
      pe = pe.parentNode;
    }
    if(pe.tagName.toLowerCase() == 'body')
  alert('You can insert a definition term or description only in a definition list!');
  }
};