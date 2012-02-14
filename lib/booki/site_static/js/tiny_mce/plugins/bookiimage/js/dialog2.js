var FileBrowserDialogue = {
    attachments: null,
    win: null,
    selectedAttachment: null,

    init : function () {
        this.win = tinyMCEPopup.getWindowArg("window");

	var j = this.win.parent.jQuery;

        j("#filesframe", document).ready(function() {
            FileBrowserDialogue.loadAttachments();
        });

	j('#frameupload2', document).ready(function() {
		FileBrowserDialogue.showUpload();
	});
    },

    showUpload: function() {
	var j = this.win.parent.jQuery;
	var frm = j(frames['frameupload2'].document).contents();		
	
	var s =  '<html><body><form method="POST" action="/_upload/" enctype="multipart/form-data"><input type="file" name="entry0"><br/><br/>';
	s += '<input type="hidden" name="attachmenttab" value="2"/><input type="submit" value="Upload" /></form></body></html>';
        
	j(frm).html(s);
	j('FORM', frm).attr("action", '/'+j.booki.currentBookURL+'/_upload/');
    },

    loadAttachments: function() {
	var j = this.win.parent.jQuery;

        j.booki.sendToCurrentBook({"command": "attachments_list"},
				  function(data) {
				      var s = '';
				      FileBrowserDialogue.attachments = data.attachments;
				      for(var i = 0; i < data.attachments.length; i++) {
					  var entry = data.attachments[i];
					  
					  s += '<tr><td><a href="" onclick="parent.FileBrowserDialogue.selectAttachment(this, '+entry.id+'); return false;">'+entry.name+'</a></td><td>'+j.booki.utils.formatDimension(entry.dimension)+'</td><td>'+j.booki.utils.formatSize(entry.size)+'</td><td>'+entry.created+'</td></tr>';
				      }
                                      
				      var frm = j(frames['filesframe'].document).contents();		
				      j("BODY", frm).html('<table border="0" width="100%"><tr><td><b>name</b></td><td><b>dimension</b></td><td><b>size</b></td><td><b>date</b></td></tr>'+s+'</table>');
				  });
	
    },
    
    selectAttachment: function(fl, attachmentID) {
	var j = this.win.parent.jQuery;

	FileBrowserDialogue.selectedAttachment = FileBrowserDialogue.getAttachmentByID(attachmentID);
	
	var u = FileBrowserDialogue.win.parent.jQuery.booki.currentBookURL;									     
	var s = '<img src="/'+u+'/_utils/thumbnail/'+FileBrowserDialogue.selectedAttachment.name+'">';									     

	FileBrowserDialogue.win.parent.jQuery('#previewdiv', document).html(s);
	
	var frm = j(frames['filesframe'].document).contents();		
	
	j("TR", frm).css("background-color", "");
	j(fl).parent().parent().css("background-color", "#2B6FB6");
	
	j("TR", frm).css("color", "black");
	j("TD > A", frm).css("color", "black");
	j(fl).css("color", "white");
	j(fl).parent().parent().css("color", "white");
    },

    getAttachmentByID: function(attachmentID) {
	var inst = tinyMCEPopup.editor;
	
	for(var i = 0; i < FileBrowserDialogue.attachments.length; i++) {
	    var entry = FileBrowserDialogue.attachments[i];
	    if(entry.id == attachmentID) {
		return entry;
	    }
	}
	
	return null;
    },

    insert: function() {
	var entry = FileBrowserDialogue.selectedAttachment;
	
	if(!entry) return;			   
	
	FileBrowserDialogue.win.document.getElementById(tinyMCEPopup.getWindowArg("input")).value = 'static/'+entry.name;		
	FileBrowserDialogue.win.ImageDialog.showPreviewImage();	   
	
	tinyMCEPopup.close();
    }
    
};

tinyMCEPopup.onInit.add(FileBrowserDialogue.init, FileBrowserDialogue);
