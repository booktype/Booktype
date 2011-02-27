function SetId(editor) {
  this.editor = editor;
  var cfg = editor.config;
  var self = this;

  // register the toolbar buttons provided by this plugin
  cfg.registerButton({
    id       : "setid",
    tooltip  : this._lc("Set Id and Name"),
    image    : editor.imgURL("set-id.gif", "SetId"),
    textMode : false,
    action   : function(editor) {
                 self.buttonPress(editor);
               }
  });
  cfg.addToolbarElement("setid", "createlink", 1);
}

SetId._pluginInfo = {
  name          : "SetId",
  version       : "2.0",
  developer     : "Udo Schmal",
  developer_url : "http://www.schaffrath-neuemedien.de",
  c_owner       : "Udo Schmal",
  sponsor       : "L.N.Schaffrath NeueMedien",
  sponsor_url   : "http://www.schaffrath-neuemedien.de",
  license       : "htmlArea"
};

SetId.prototype._lc = function(string) {
  return Xinha._lc(string, 'SetId');
};


SetId.prototype.onGenerate = function() {
  this.editor.addEditorStylesheet(Xinha.getPluginDir("SetId") + '/set-id.css');
};

SetId.prototype.buttonPress = function(editor) {
  var outparam = null;
  var html = editor.getSelectedHTML();
  var sel  = editor._getSelection();
  var range  = editor._createRange(sel);
  var node = editor._activeElement(sel);
  if (node)
    outparam = { name : node.id };
  else
    outparam = { name : '' };

  editor._popupDialog( "plugin://SetId/set_id", function( param ) {
    if ( param ) {
      var name = param["name"];
      if (name == "" || name == null) {
        if (node) {
          node.removeAttribute("name");
          node.removeAttribute("id");
          node.removeAttribute("title");
          if (node.className == "hasid") {
            node.removeAttribute("class");
          }
        }
        return;
      }
      try {
        var doc = editor._doc;
        if (!node) {
          node = doc.createElement("span");
          node.id = name;
          node.name = name;
          node.title = name;
          node.className = "hasid";
          node.innerHTML = html;
          if (Xinha.is_ie) {
            range.pasteHTML(node.outerHTML);
          } else {
            editor.insertNodeAtSelection(node);
          }
        } else {
          node.id = name;
          node.name = name;
          node.title = name;
          node.className = "hasid";
        }
      }
      catch (e) { }
    }
  }, outparam);
};
