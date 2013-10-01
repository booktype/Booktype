// I should break dependancy on jQuery. But jQuery is so niiiicccce.
var j = parent.jQuery;

var CommentsDialog = {
    init : function() {
	CommentsDialog.editor = tinyMCEPopup.editor;
		
	tinyMCEPopup.resizeToInnerSize();
	
	CommentsDialog.initWith();
    },

    initWith: function() {
	var se = this.editor.selection;

	if(se.getNode().nodeName == 'IMG' && this.editor.dom.hasClass(this.editor.dom.getParent(se.getNode(), 'SPAN'), "bookicommentmarker")) {
	    var commentID = j(this.editor.dom.getParent(se.getNode(), 'SPAN')).attr("id").substr(19);

	    this.commentID = commentID;
	    this.loadCommentsForID(commentID);
        };
    },

    loadCommentsForID: function(commentID) {	
	var doc = this.editor.getDoc();
	var s = '';
	
	j('#bookicomment_'+commentID+' .bookicommententry', doc).each(function(i, v) {
		var content = j('.bookicommentcontent', v).html();
		var author = j('.bookicommentuser', v).html();
		var tme = j('.bookicommentdate', v).html();
		var d = new Date();
		d.setTime(parseInt(tme));
		
		s += '<div class="entry"><div class="header"><b>'+author+'</b> - <i>'+d.toLocaleString()+'</i></div>'+content+'</div>';
	    });

	j("DIV.scroll", document).html(s);

	return s;
    },

    getNewID: function() {
	var newID = '';

	for(var i = 0; i < 10; i++) 
	    newID += Math.floor(Math.random()*10);

	return newID;
    },

    removeComment: function() {
	tinyMCE.activeEditor.windowManager.confirm("Do you want to remove all the comments?", function(s) {
		if(s) {
		    var sel = tinyMCEPopup.editor.selection.getNode();
		    var span = tinyMCEPopup.editor.dom.getParent(sel, 'SPAN');
		    
		    var text = j(span).clone();
		    var commentID = j(span).attr("id").substr(19);
		    
		    if(j(span).attr("class") == 'bookicommentmarker') {
			// remove the marker
			j('IMG.markerimage', text).remove();
			j(span).replaceWith(text.html());

			// remove the comment
			j("#bookicomment_"+commentID, CommentsDialog.editor.getDoc()).remove();
		    }
		    
		    tinyMCEPopup.close();
		}
	    });

	return false;	
    },

    append: function() {
	var l = j("#bookicomment_"+CommentsDialog.commentID, j(CommentsDialog.editor.getDoc())); 

	if(tinymce.trim(document.forms[0].commentContent.value) == '') return false;

	l.append(CommentsDialog.createComment(CommentsDialog.commentID));

	tinyMCEPopup.close();
    },

    insert : function() {
	var f = document.forms[0];

	if(tinymce.trim(f.commentContent.value) == '') return false;

	var sel = tinyMCEPopup.editor.selection.getContent({format : 'html'});

	var newID = CommentsDialog.getNewID();
	// this is just stupid
	var imageURL = window.location.href.replace("dialog_new.htm", "img/comment.png");

	// background-color: #ffffcc
	var raw = '<span id="bookicommentmarker_'+newID+'" class="bookicommentmarker"><img class="markerimage" alt="comment" src="'+imageURL+'"/>'+sel+'</span>';

	tinyMCEPopup.execCommand("mceInsertRawHTML", false, raw, {skip_undo : 1});

	if(j("#BookiComments_CommentsList",CommentsDialog.editor.getDoc()).length == 0) {
	    j(CommentsDialog.editor.getDoc().body).append('<ol id="BookiComments_CommentsList"><li class="dummy">test</li></ol>');
	}

	CommentsDialog.insertComment(newID, f.commentContent.value);

	tinyMCEPopup.close();

	return false;
    },

    insertComment: function(commentID, content) {

	var l = j("#BookiComments_CommentsList", j(CommentsDialog.editor.getDoc())); 

	l.append('<li id="bookicomment_'+commentID+'">'+CommentsDialog.createComment(commentID)+'</li>');
	j("LI.dummy", l).remove();
    },

    createComment: function(commentID) {
	var f = document.forms[0];
	var content = f.commentContent.value.replace(/\n/g, "<br/>");

	return '<span class="bookicommententry"><span class="bookicommentcontent">'+content+'</span><span class="bookicommentuser">'+j.booki.username+'</span><span class="bookicommentdate">'+(new Date()).getTime()+'</span></span>';
    }

};

tinyMCEPopup.onInit.add(CommentsDialog.init, CommentsDialog);
