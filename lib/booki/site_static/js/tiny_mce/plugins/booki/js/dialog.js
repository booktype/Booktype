//tinyMCEPopup.requireLangPack();

function setAttrib(elm, attrib, value) {
	var dom = tinyMCEPopup.editor.dom;

	dom.setAttrib(elm, attrib, value);
}


var ImageDialog = {
    attachments: null,

	init : function() {
     	        var inst = tinyMCEPopup.editor;
	        var elm; // = inst.selection.getNode();
		var action = "insert";

		elm = inst.dom.getParent(elm, "IMG");
		if(elm != null && elm.nodeName == "IMG")
		    action = "update";

		if(action == "update") {
		    // also title attribute
		    var src = inst.dom.getAttrib(elm, "src");
		    var title = inst.dom.getAttrib(elm, "title");

		}
		
		parent.jQuery.booki.sendToCurrentBook({"command": "attachments_list"},
						      function(data) {
							  var s = '';
							  ImageDialog.attachments = data.attachments;

							  for(var i = 0; i < data.attachments.length; i++) {
							      var entry = data.attachments[i];
							      
							      s += '<tr><td><a href="" onclick="ImageDialog.insertWithId('+entry.id+');">'+entry.name+'</a></td><td>'+parent.jQuery.booki.utils.formatDimension(entry.dimension)+'</td><td>'+parent.jQuery.booki.utils.formatSize(entry.size)+'</td><td>'+entry.created+'</td></tr>';
							  }
							  
							  parent.jQuery("#attachmentlist", document).html('<table border="0" width="100%"><tr><td><b>name</b></td><td><b>dimension</b></td><td><b>size</b></td><td><b>date</b></td></tr>'+s+'</table>');
						      });
    },

	insertWithId: function(name) {
	for(var i = 0; i < this.attachments.length; i++) {
	    var entry = this.attachments[i];
	    if(entry.id == name) {
		var inst = tinyMCEPopup.editor;
		var elm, i;
		
		inst.execCommand('mceInsertContent', false, tinyMCEPopup.editor.dom.createHTML('img', {"src": "static/"+entry.name}), {skip_undo : 1});
		//		tinyMCEPopup.execCommand("mceInsertLink", false, document.forms[0].someurl.value, {skip_undo : 1});
		//setAttrib(inst.dom.select("a"), "title", document.forms[0].sometitle.value);
		
		tinyMCEPopup.close();
	    }
	}
    },
	
	insert : function() {
	var inst = tinyMCEPopup.editor;
	var elm, i;
	
	elm = inst.selection.getNode();
	elm = inst.dom.getParent(elm, "A");
	
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

tinyMCEPopup.onInit.add(ImageDialog.init, ImageDialog);
