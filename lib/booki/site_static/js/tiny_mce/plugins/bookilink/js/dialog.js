function setAttrib(elm, attrib, value) {
	var dom = tinyMCEPopup.editor.dom;

	dom.setAttrib(elm, attrib, value);
}


var BookiLinkDialog = {
	init : function() {
     	        var inst = tinyMCEPopup.editor;
	        var elm = inst.selection.getNode();
		var action = "insert";
		var f = document.forms[0];

		elm = inst.dom.getParent(elm, "A");
		if(elm != null && elm.nodeName == "A")
		    action = "update";

		if(action == "update") {
		    // also title attribute
		    var href = inst.dom.getAttrib(elm, "href");
		    var title = inst.dom.getAttrib(elm, "title");

		    f.someurl.value =  href;		    
		    if(title != null && title != '') {
			f.sometitle.value = title;
		    } else {
			f.sometitle.value = tinyMCEPopup.editor.selection.getContent({format : 'text'});
		    }
		} else {
		    f.sometitle.value = tinyMCEPopup.editor.selection.getContent({format : 'text'});
		}

		var chapters = parent.jQuery.booki.editor.getChaptersAll();
		var select = document.getElementsByTagName('select')[0];
		for(var i=0; i < chapters.length; i++) {
		    select.options.add(new Option(chapters[i][1], chapters[i][0]));
		}
	},

	onChange: function(slct) {
    	    var s = slct.options[slct.selectedIndex];
	    var f = document.forms[0];

	    f.sometitle.value = s.text;
	    f.someurl.value = "../"+s.value+"/";
        },

	insert : function() {
	        var inst = tinyMCEPopup.editor;
	        var elm, i;

                elm = inst.selection.getNode();
                elm = inst.dom.getParent(elm, "A");

		// da li ovo sad sve titleove promjeni?
		if(elm == null) {
		    tinyMCEPopup.execCommand("mceInsertLink", false, document.forms[0].someurl.value, {skip_undo : 1});
		    setAttrib(inst.dom.select("a"), "title", document.forms[0].sometitle.value);
		} else {
		    setAttrib(elm, "href", document.forms[0].someurl.value);
		    setAttrib(elm, "title", document.forms[0].sometitle.value);
		}

		tinyMCEPopup.close();
	}
};

tinyMCEPopup.onInit.add(BookiLinkDialog.init, BookiLinkDialog);
