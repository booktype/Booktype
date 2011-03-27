/*---------------------------------------*\
 Insert Smiley Plugin for Xinha
 -----------------------------------------
 author: Ki Master George
 e-mail: kimastergeorge@gmail.com
\*---------------------------------------*/

function InsertSmiley(editor) {
  this.editor = editor;
  var cfg = editor.config;
  var self = this;

  // register the toolbar buttons provided by this plugin
  cfg.registerButton({
    id       : "insertsmiley",
    tooltip  : this._lc("Insert Smiley"),
    image    : editor.imgURL("ed_smiley.gif", "InsertSmiley"),
    textMode : false,
    action   : function(editor) {
                 self.buttonPress(editor);
               }
  });
  cfg.addToolbarElement("insertsmiley", "inserthorizontalrule", 1);
}

InsertSmiley._pluginInfo = {
  name          : "InsertSmiley",
  version       : "1.0",
  developer     : "Ki Master George",
  developer_url : "http://kimastergeorge.i4host.com/",
  c_owner       : "Ki Master George",
  sponsor       : "Ki Master George",
  sponsor_url   : "http://kimastergeorge.i4host.com/",
  license       : "htmlArea"
};

InsertSmiley.prototype._lc = function(string) {
  return Xinha._lc(string, 'InsertSmiley');
};
Xinha.Config.prototype.InsertSmiley=  {
  smileyURL : "http://www.x-webservice.net/storage/xinha/plugins/InsertSmiley/"
};

InsertSmiley.prototype.buttonPress = function(editor) {
  var self = this;
  var sel = editor.getSelectedHTML().replace(/(<[^>]*>|&nbsp;|\n|\r)/g,"");
  var param = {};
  param.editor = editor;
  editor._popupDialog("plugin://InsertSmiley/insertsmiley", function(param) {
    editor.insertHTML("<img src=\"" + editor.config.InsertSmiley.smileyURL + param.smileyfile + "\" alt=\"Smiley\" />");
  }, param);
};