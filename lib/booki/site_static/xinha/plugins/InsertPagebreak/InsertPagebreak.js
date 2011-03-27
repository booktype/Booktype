// InsertPagebreak plugin for HTMLArea/Xinha
// Implementation by Udo Schmal & Schaffrath NeueMedien
// Original Author - Udo Schmal
//
// (c) Udo Schmal & Schaffrath NeueMedien 2004
// Distributed under the same terms as HTMLArea itself.
// This notice MUST stay intact for use (see license.txt).

function InsertPagebreak(editor, args) {
	this.editor = editor;
	var cfg = editor.config;
	var self = this;

	cfg.registerButton({
	id       : "pagebreak",
	tooltip  : this._lc("Page break"),
	image    : editor.imgURL("pagebreak.gif", "InsertPagebreak"),
	textMode : false,
	action   : function(editor) {
			self.buttonPress(editor);
		}
	});
  cfg.addToolbarElement("pagebreak", "inserthorizontalrule", 1);
}

InsertPagebreak._pluginInfo = {
	name          : "InsertPagebreak",
	version       : "1.0",
	developer     : "Udo Schmal",
	developer_url : "",
	sponsor       : "L.N.Schaffrath NeueMedien",
	sponsor_url   : "http://www.schaffrath-neuemedien.de/",
	c_owner       : "Udo Schmal & Schaffrath NeueMedien",
	license       : "htmlArea"
};

InsertPagebreak.prototype._lc = function(string) {
    return Xinha._lc(string, 'InsertPagebreak');
};

InsertPagebreak.prototype.buttonPress = function(editor, context, updatecontextclass) {
	editor.insertHTML('<div style="font-size: 1px; page-break-after: always; height: 1px; background-color: rgb(192, 192, 192);" contenteditable="false" title="Page Break">');
};