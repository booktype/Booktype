// Character Map plugin for Xinha
// Sponsored by http://www.systemconcept.de
// Implementation by Holger Hees based on HTMLArea XTD 1.5 (http://mosforge.net/projects/htmlarea3xtd/)
// Original Author - Bernhard Pfeifer novocaine@gmx.net 
//
// (c) systemconcept.de 2004
// Distributed under the same terms as Xinha itself.
// This notice MUST stay intact for use (see license.txt).

function EditTag(editor) {
  this.editor = editor;
	var cfg = editor.config;
	var self = this;
        
	cfg.registerButton({
                id       : "edittag",
                tooltip  : this._lc("Edit HTML for selected text"),
                image    : editor.imgURL("ed_edit_tag.gif", "EditTag"),
                textMode : false,
                action   : function(editor) {
                             self.buttonPress(editor);
                           }
            });

	cfg.addToolbarElement("edittag", "htmlmode",1);

}

EditTag._pluginInfo = {
	name          : "EditTag",
	version       : "1.0",
	developer     : "Pegoraro Marco",
	developer_url : "http://www.sin-italia.com/",
	c_owner       : "Marco Pegoraro",
	sponsor       : "Sin Italia",
	sponsor_url   : "http://www.sin-italia.com/",
	license       : "htmlArea"
};

EditTag.prototype._lc = function(string) {
    return Xinha._lc(string, 'EditTag');
};

EditTag.prototype.buttonPress = function(editor) {
	// Costruzione dell'oggetto parametri da passare alla dialog.
	outparam = {
		content : editor.getSelectedHTML()
	}; // Fine costruzione parametri per il passaggio alla dialog.
	editor._popupDialog( "plugin://EditTag/edit_tag", function( html ) {
		if ( !html ) {  
			//user must have pressed Cancel
			return false;
		}
		editor.insertHTML( html );
	}, outparam);
};