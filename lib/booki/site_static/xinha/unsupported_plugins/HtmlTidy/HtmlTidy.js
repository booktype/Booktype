// Plugin for htmlArea to run code through the server's HTML Tidy
// By Adam Wright, for The University of Western Australia
//
// Distributed under the same terms as HTMLArea itself.
// This notice MUST stay intact for use (see license.txt).

function HtmlTidy(editor) {
	this.editor = editor;

	var cfg = editor.config;
	var bl = HtmlTidy.btnList;
	var self = this;

	this.onMode = this.__onMode;

	// register the toolbar buttons provided by this plugin
	var toolbar = [];
	for (var i = 0; i < bl.length; ++i) {
		var btn = bl[i];
		if (btn == "html-tidy") {
			var id = "HT-html-tidy";
			cfg.registerButton(id, this._lc("HTML Tidy"), editor.imgURL(btn[0] + ".gif", "HtmlTidy"), true,
					   function(editor, id) {
						   // dispatch button press event
						   self.buttonPress(editor, id);
					   }, btn[1]);
			toolbar.push(id);
		} else if (btn == "html-auto-tidy") {
            var btnTxt = [this._lc("Auto-Tidy"), this._lc("Don't Tidy")];
            var optionItems = new Object();
            optionItems[btnTxt[0]] = "auto";
            optionItems[btnTxt[1]] = "noauto";
			var ht_class = {
				id	: "HT-auto-tidy",
				options	: optionItems,
				action	: function (editor) { self.__onSelect(editor, this); },
				refresh	: function (editor) { },
				context	: "body"
			};
			cfg.registerDropdown(ht_class);
		}
	}

	for (var i in toolbar) {
		cfg.toolbar[0].push(toolbar[i]);
	}
}

HtmlTidy._pluginInfo = {
	name          : "HtmlTidy",
	version       : "1.0",
	developer     : "Adam Wright",
	developer_url : "http://blog.hipikat.org/",
	sponsor       : "The University of Western Australia",
	sponsor_url   : "http://www.uwa.edu.au/",
	license       : "htmlArea"
};

HtmlTidy.prototype._lc = function(string) {
    return Xinha._lc(string, 'HtmlTidy');
};

HtmlTidy.prototype.__onSelect = function(editor, obj) {
	// Get the toolbar element object
	var elem = editor._toolbarObjects[obj.id].element;

	// Set our onMode event appropriately
	if (elem.value == "auto")
		this.onMode = this.__onMode;
	else
		this.onMode = null;
};

HtmlTidy.prototype.__onMode = function(mode) {
	if ( mode == "textmode" ) {
		this.buttonPress(this.editor, "HT-html-tidy");
	}
};

HtmlTidy.btnList = [
		    null, // separator
		    ["html-tidy"],
		    ["html-auto-tidy"]
];

HtmlTidy.prototype.buttonPress = function(editor, id) {

	switch (id)
  {
    case "HT-html-tidy":
    {
      var oldhtml = editor.getHTML();
      if(oldhtml=="") break; //don't clean empty text
      // Ask the server for some nice new html, based on the old...
      Xinha._postback(Xinha.getPluginDir("HtmlTidy") + '/html-tidy-logic.php', {'htisource_name' : oldhtml},
                            function(javascriptResponse) { eval(javascriptResponse) });
    }
		break;
	}
};

HtmlTidy.prototype.processTidied = function(newSrc) {
	editor = this.editor;
	editor.setHTML(newSrc);
};