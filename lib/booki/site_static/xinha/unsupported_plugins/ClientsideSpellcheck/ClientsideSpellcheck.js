// IE Spell Implementation for XINHA
//Client-side spell check plugin
//This implements the API for ieSpell, which is owned by Red Egg Software 
//For more info about ieSpell, go to http://www.iespell.com/index.htm
// Distributed under the same terms as Xinha itself.
// This notice MUST stay intact for use (see license.txt).


function ClientsideSpellcheck(editor) {
  this.editor = editor;

  var cfg = editor.config;
  var bl = ClientsideSpellcheck.btnList;
  var self = this;

  // see if we can find the mode switch button, insert this before that
  var id = "clientsidespellcheck";
  
  
  cfg.registerButton(id, this._lc("Spell Check using ieSpell"), editor.imgURL("clientside-spellcheck.gif", "ClientsideSpellcheck"), false,
             function(editor, id) {
               // dispatch button press event
               self.buttonPress(editor, id);
             });

  if(Xinha.is_ie) {
    cfg.addToolbarElement("clientsidespellcheck", "print", 1);
}

}

ClientsideSpellcheck._pluginInfo = {
  name          : "ClientsideSpellcheck",
  version       : "1.0",
  developer     : "Michael Harris",
  developer_url : "http://www.jonesinternational.edu",
  c_owner       : "Red Egg Software",
  sponsor       : "Jones International University",
  sponsor_url   : "http://www.jonesinternational.edu",
  license       : "htmlArea"
};


ClientsideSpellcheck.prototype._lc = function(string) {
  return Xinha._lc(string, 'ClientsideSpellcheck');
};

ClientsideSpellcheck.prototype.buttonPress = function(editor) {

	try {
		var tmpis = new ActiveXObject("ieSpell.ieSpellExtension");
		tmpis.CheckAllLinkedDocuments(document);
	}
	catch(exception) {
 		if(exception.number==-2146827859) {
			if (confirm(this.lc("ieSpell not detected.  Click Ok to go to download page.")))
				window.open("http://www.iespell.com/download.php","DownLoad");
		} else {
			alert(this.lc("ieSpell can only be used in Internet Explorer"));
		}
	}
};