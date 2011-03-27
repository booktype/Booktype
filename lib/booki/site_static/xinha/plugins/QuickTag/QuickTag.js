/*---------------------------------------*\
 Quick Tag Editor Plugin for HTMLArea-3.0
 -----------------------------------------
 author: Cau guanabara 
 e-mail: caugb@ibest.com.br
\*---------------------------------------*/

function QuickTag(editor) {
  var cfg = editor.config;
  var self = this;

  cfg.registerButton({
	id       : "quickeditor",
	tooltip  : this._lc("Quick Tag Editor"),
	image    : editor.imgURL("ed_quicktag.gif", "QuickTag"), 
	textMode : false,
  action   : function(editor) { 
               self.buttonPress(editor); 
             }
  });
  cfg.addToolbarElement("quickeditor", "htmlmode", 1);  
}

QuickTag.prototype.buttonPress = function(editor) { 
var self = this;
var sel = editor.getSelectedHTML().replace(/(<[^>]*>|&nbsp;|\n|\r)/g,""); 
var param = new Object();
param.editor = editor;

  if(/\w/.test(sel))
    editor._popupDialog("plugin://QuickTag/quicktag", function(p) { self.setTag(editor, p); }, param);
  else
    alert(this._lc('You have to select some text'));
};

QuickTag.prototype.setTag = function(editor, param) {
editor.surroundHTML(param.tagopen,param.tagclose);
};

QuickTag._pluginInfo = {
name          : "QuickTag",
version       : "1.0 - beta",
developer     : "Cau Guanabara",
developer_url : "mailto:caugb@ibest.com.br",
c_owner       : "Cau Guanabara",
sponsor       : "Independent production",
sponsor_url   : "http://www.netflash.com.br/gb/HA3-rc1/examples/quick-tag.html",
license       : "htmlArea"
};

QuickTag.prototype._lc = function(string) {
    return Xinha._lc(string, 'QuickTag');
};