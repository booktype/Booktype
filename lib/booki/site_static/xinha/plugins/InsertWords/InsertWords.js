// Plugin for htmlArea to insert keywords, when a type of
// keyword is selected from a dropdown list
// By Adam Wright, for The University of Western Australia
//
// Distributed under the same terms as HTMLArea itself.
// This notice MUST stay intact for use (see license.txt).

function InsertWords(editor, params) {
	this.editor = editor;
	var cfg = editor.config;
	var self = this;

    if(params[0] && params[0].combos) {
      //if arguments where passed with registerPlugin use these
	  var combos = params[0].combos;
    } else if (cfg.InsertWords && cfg.InsertWords.combos) {
      //if combos is found in config use these
      var combos = cfg.InsertWords.combos;
    } else {
      //no combos found
      var combos = [];
    }

	// register the toolbar with the keywords dropdown
    var first = true;
    var toolbar = [];

	for (var i = combos.length; --i >= 0;) {
		var combo = combos[i];
		var id = "IW-id" + i;
		var iw_class = {
			id	: id,
			options	: combo.options,
			action	: function (editor) { self.onSelect(editor, this, combo.context); },
			refresh	: function (editor) { },
			context : combo.context
		};
        cfg.registerDropdown(iw_class);

        if (combo.label)
            toolbar.push("T[" + combo.label + "]");
        toolbar.push(id);
        toolbar.push(first ? "separator" : "space");
	}

    cfg.addToolbarElement(toolbar, "linebreak", 1);

}

InsertWords._pluginInfo = {
	name          : "InsertWords",
	version       : "1.0",
	developer     : "Adam Wright",
	developer_url : "http://blog.hipikat.org/",
	sponsor       : "The University of Western Australia",
	sponsor_url   : "http://www.uwa.edu.au/",
	license       : "htmlArea"
};

InsertWords.prototype.onSelect = function(editor, obj, context) {

	// Get the toolbar object element
	var elem = editor._toolbarObjects[obj.id].element;

	// Insert the keyword value blindly at the selection
	editor.insertHTML(elem.value);

	// Reset the dropdown to it's label
	elem.selectedIndex = 0;
};