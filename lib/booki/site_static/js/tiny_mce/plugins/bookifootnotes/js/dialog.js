// Should not depend on jQuery. But jQuery is sooo niiiccce....

var j = parent.jQuery;

var FootnotesDialog = {
    notes: [],

    init : function() {
	FootnotesDialog.editor = tinyMCEPopup.editor;
	
	var f = document.forms[0];
	
	// when user selects different footnote
	j(f.noteMenu).change(function() {
		var _sel =  j(":selected", j(this));
		
		if(_sel.val() == "new") {
		    f.noteContent.value = "";
		    j(f.noteContent).removeAttr('disabled');
		} else {
		    f.noteContent.value = FootnotesDialog.notes[_sel.val()];
		    j(f.noteContent).attr('disabled', 'disabled');
		}
	    });
	
	FootnotesDialog.loadNotes();
	
	tinyMCEPopup.resizeToInnerSize();
    },
    
    // load all footnotes
    loadNotes: function() {
	var a = FootnotesDialog.editor.getDoc().getElementById("InsertNote_NoteList");
	var f = document.forms[0];

	j("LI", j(a)).each(function(i, v) {
		var _id = j(v).attr("id");
		var _value = j(v).text();
		
		FootnotesDialog.notes[_id] = _value;
		
		// do it in a nicer way
		j(f.noteMenu).append(j('<OPTION value="'+_id+'">'+(1+i)+'. ' +_value+'</OPTION>'));
	    });
    },
    
    getNewID: function() {
	var newId = 0;
	var doc = FootnotesDialog.editor.getDoc().getElementById("InsertNote_NoteList");

	j("LI:not(.dummy)", j(doc)).each(function(i, v) {
		var _id = j(this).attr("id");
		var n = parseInt(_id.substr(13));
		if(n > newId)  newId = n;
	    });

	return newId+1;
    },

    getNewMarkerID: function() {
	var newId = 0;
	var doc = FootnotesDialog.editor.getDoc();

	j("SPAN.InsertNoteMarker", j(doc)).each(function(i, v) {
		var _id = j(this).attr("id");
		var m = _id.match(/.+marker(\d+)$/i);
		var n;

		if(m) {
		    n = parseInt(m[1]);
		    if(n > newId)  newId = n;
		}
	    });

	return newId+1;
    },
		
    insert : function() {
	var f = document.forms[0];

	var _sel =  j(":selected", j(f.noteMenu));

	var _id = _sel.val();
	var _value = _sel.text();
	
	// check if content is empty, then show warning

	if(_id == "new" && f.noteContent.value == "") {
	    tinyMCEPopup.alert("Empty footnote", function() {});
	    return false;
	}

	if(j("#InsertNote_NoteList",FootnotesDialog.editor.getDoc()).length == 0) {
	    j(FootnotesDialog.editor.getDoc().body).append('<ol id="InsertNote_NoteList"><li class="dummy">test</li></ol>');
	}
	
	myid = FootnotesDialog.insertMarker(_id);

	if(_id == "new") {
	    FootnotesDialog.insertNote(myid, f.noteContent.value);
	}

	FootnotesDialog.insertMarkersForNote(myid);

	FootnotesDialog.fixNotes();
       
	tinyMCEPopup.close();
	return false;
    },

    insertMarker: function(_id) {
	var f = document.forms[0];

	var markerID = FootnotesDialog.getNewMarkerID();
	var num;
	var myid;

	if(_id == "new") {
	    myid = "InsertNoteID_"+FootnotesDialog.getNewID();
	    var ls = j("#InsertNote_NoteList", j(FootnotesDialog.editor.getDoc())); 
	    num = j("LI:not(.dummy)", ls).length+1;
	} else {
	    myid = _id;
	    num = f.noteMenu.selectedIndex-1;
	}
	
	var raw = '<span id="'+myid+'_marker'+markerID+'" class="InsertNoteMarker"><sup><a href="#'+myid+'">'+num+'</a></sup><span>';
	tinyMCEPopup.execCommand("mceInsertRawHTML", false, raw, {skip_undo : 1});

	return myid;
    },
    
    insertNote: function(noteID, content) {
	var l = j("#InsertNote_NoteList", j(FootnotesDialog.editor.getDoc())); 

	l.append('<li id="'+noteID+'">'+content+' <span id="'+noteID+'_LinkBacks">&nbsp;</span>');
	j("LI.dummy", l).remove();
    },

    insertMarkersForNote: function(noteID) {
	var selMarkers = j('SPAN[id*="'+noteID+'_marker"].InsertNoteMarker', this.editor.getDoc());
	var numMarkers = selMarkers.length;

	j('#'+noteID+'_LinkBacks', j(FootnotesDialog.editor.getDoc())).empty();

	selMarkers.each(function(i, v) {
		var com = '';
		var mark = '^';

		if(i>0) com = '<sup>, </sup>';

		if(numMarkers > 1) {
		    mark = String.fromCharCode('a'.charCodeAt(0)+i);
		}

		j('#'+noteID+'_LinkBacks', j(FootnotesDialog.editor.getDoc())).append(com+'<sup><a href="#'+j(v).attr("id")+'">'+mark+'</a></sup>');
	    });
    },

    fixNotes: function() {
	var selMarkers = j('SPAN.InsertNoteMarker', this.editor.getDoc());
	var l = j("#InsertNote_NoteList", j(FootnotesDialog.editor.getDoc())); 

	var toDelete = [];
	var newOrder = [];

	selMarkers.each(function(i, v) {
		var _id = j("A", j(v)).attr("href").substr(1);

		if( j('#'+_id, l).length == 0) {
		    toDelete.push(_id);
		} else {
		    if(j.inArray(_id, newOrder) == -1) {
			newOrder.push(_id);
		    }

		    var pos = j.inArray(_id, newOrder)+1;
		    j("A", j(v)).html(pos);
		}
	    });

	for(var k = 0; k < toDelete.length; k++) {
	    j('SPAN[id*="'+toDelete[k]+'_marker"].InsertNoteMarker', this.editor.getDoc()).remove();
	}

	var newList = j("<p/>");

	for(var i = 0; i < newOrder.length; i++) {
	    var elem = newOrder[i];

	    var c = j('#'+elem, l).clone();
	    newList.append(c);
	}

	l.empty().append(newList.children());
	
	j("LI", j("#InsertNote_NoteList", j(FootnotesDialog.editor.getDoc()))).each(function(i, v) {
		FootnotesDialog.insertMarkersForNote(j(v).attr("id"));
	    });

    }
};

tinyMCEPopup.onInit.add(FootnotesDialog.init, FootnotesDialog);
