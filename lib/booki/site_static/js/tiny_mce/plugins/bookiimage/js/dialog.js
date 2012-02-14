var j = parent.jQuery;

 function myFileBrowser (field_name, url, type, win) {

    var cmsURL = window.location.toString();    // script URL - use an absolute path!

    if (cmsURL.indexOf("?") < 0) {
        cmsURL = cmsURL + "?type=" + type;
    } else {
        cmsURL = cmsURL + "&type=" + type;
    }

    cmsURL = window.location.toString().replace("dialog.htm", "dialog2.htm");

    tinyMCE.activeEditor.windowManager.open({
        file : cmsURL,
        title : 'Browse images',
        width : 700,  
        height : 400,
        resizable : "yes",
        inline : "yes",  // This parameter only has an effect if you use the inlinepopups plugin!
        close_previous : "no"
    }, {
        window : win,
        input : field_name
    });
    return false;
  }

function setAttrib(elm, attrib, value) {
	var dom = tinyMCEPopup.editor.dom;

	dom.setAttrib(elm, attrib, value);
}


var ImageDialog = {
	init : function() {

	    var f = document.forms[0];
	    var inst = tinyMCEPopup.editor;
	    var elm = inst.selection.getNode();
	    var action = "insert";

	    ImageDialog.editor = inst;
	    
	    
	    tinyMCEPopup.resizeToInnerSize();

	    elm = inst.dom.getParent(elm, "IMG");
	    
	    if(elm != null && elm.nodeName == "IMG")
		action = "update";

	    if(action == "update") {
		f.imageurl.value = inst.dom.getAttrib(elm, "src");
		f.imagetitle.value = inst.dom.getAttrib(elm, "alt");
		f.width.value = inst.dom.getAttrib(elm, "width");
		f.height.value = inst.dom.getAttrib(elm, "height");
		f.hspace.value = inst.dom.getAttrib(elm, "hspace");
		f.vspace.value = inst.dom.getAttrib(elm, "vspace");
		f.border.value = inst.dom.getAttrib(elm, "border");

		f.cssid.value = inst.dom.getAttrib(elm, "id");
		f.cssclass.value = inst.dom.getAttrib(elm, "class");

		j('#align OPTION[value="'+inst.dom.getAttrib(elm, "align")+'"]', document).attr("selected", "selected");
	    }

	    j("input[name='imageurl']", document).keyup(function() {
		    ImageDialog.showPreviewImage();    		    
	    });

	    j("BUTTON.browse", document).click(function() {
		    myFileBrowser("imageurl", "", "image", window);
		    return false;
		});
	    
	    this.updateStyle();
	    this.showPreviewImage();
	    
	    return;
        },

	updateStyle: function(styleType) {
	   var f = document.forms[0];
	   var align = j('#align OPTION:selected', document).val();
	   var border = tinymce.trim(f.border.value);
	   var hspace = tinymce.trim(f.hspace.value);
	   var vspace = tinymce.trim(f.vspace.value);
	   
	   var img = j('#alignSampleImg', document);

	   img.attr("align", align);
	   img.attr("border", border);
	   img.attr("hspace", hspace);
	   img.attr("vspace", vspace);
        },

	showPreviewImage: function() {
	    var src = document.forms[0].imageurl.value;
	    if(src == '') return;

	    var imageURL = j.booki.utils.linkToAttachment(j.booki.currentBookURL, src);;

	    if(src.search("http") === 0) imageURL = src;
	    

	    j("#prev", j(document)).html('<img src="'+imageURL+'" alt="Neki opis" onerror="ImageDialog.resetPreview();" onload="ImageDialog.updateImageData(this);"/>');	
            return false;
         },

        resetPreview: function() {
	    j("#prev", document).html("");
        },

	updateImageData : function(img, st) {
		var f = document.forms[0];

		if (!st) {
			f.elements.width.value = img.width;
			f.elements.height.value = img.height;
		}

		this.preloadImg = img;
	},

	changeHeight : function() {
		var f = document.forms[0], tp, t = this;

		if (!f.constrain.checked || !t.preloadImg) {
			return;
		}

		if (f.width.value == "" || f.height.value == "")
			return;

		tp = (parseInt(f.width.value) / parseInt(t.preloadImg.width)) * t.preloadImg.height;
		f.height.value = tp.toFixed(0);
	},

	changeWidth : function() {
		var f = document.forms[0], tp, t = this;

		if (!f.constrain.checked || !t.preloadImg) {
			return;
		}

		if (f.width.value == "" || f.height.value == "")
			return;

		tp = (parseInt(f.height.value) / parseInt(t.preloadImg.height)) * t.preloadImg.width;
		f.width.value = tp.toFixed(0);
	},


	insert : function() {
 	    var inst = tinyMCEPopup.editor;
	    var f = document.forms[0];

	    var align = j('#align OPTION:selected', document).val();
	    var alt = tinymce.trim(f.imagetitle.value);
	    var border = tinymce.trim(f.border.value);
	    var hspace = tinymce.trim(f.hspace.value);
	    var vspace = tinymce.trim(f.vspace.value);
	    var width = tinymce.trim(f.width.value);
	    var height = tinymce.trim(f.height.value);
	    var cssid = tinymce.trim(f.cssid.value);
	    var cssclass = tinymce.trim(f.cssclass.value);
	    
 	    var elm, i;
	
	    elm = inst.selection.getNode();
	    elm = inst.dom.getParent(elm, "IMG");

	    if(elm == null) {
		var raw = '';

		if(alt != '') raw += ' alt="'+alt+'" ';
		if(align != '') raw += ' align="'+align+'" ';
		if(border != '') raw += ' border="'+border+'" ';
		if(hspace != '') raw += ' hspace="'+hspace+'" ';
		if(vspace != '') raw += ' vspace="'+vspace+'" ';
		if(width != '') raw += ' width="'+width+'" ';
		if(height != '') raw += ' height="'+height+'" ';
		if(cssid != '') raw += ' id="'+cssid+'" ';
		if(cssclass != '') raw += ' class="'+cssclass+'" ';

		tinyMCEPopup.execCommand("mceInsertRawHTML", false, '<img src="'+f.imageurl.value+'" '+raw+'>', {skip_undo : 1});
	    } else {
		setAttrib(elm, "src", f.imageurl.value);

		setAttrib(elm, "id", cssid);
		setAttrib(elm, "class", cssclass);
		setAttrib(elm, "alt", alt);
		setAttrib(elm, "align", align);
		setAttrib(elm, "border", border);
		setAttrib(elm, "hspace", hspace);
		setAttrib(elm, "vspace", vspace);
		setAttrib(elm, "width", width);
		setAttrib(elm, "height", height);
	    }
	
	    tinyMCEPopup.close();
       }
};

tinyMCEPopup.onInit.add(ImageDialog.init, ImageDialog);
