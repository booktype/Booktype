$(function() {
/*
 * todo: 
 *  - should send projectid and bookid and not their full names
 *
 *
 * */	


    /* booki.chat */

    jQuery.namespace('jQuery.booki.chat');

    jQuery.booki.chat = function() {
	var element = null;
	var element2 = null;

	function showJoined(notice) {
	    $('.content', element).append('<p><span class="icon">JOINED</span>  '+notice+'</p>');
	    $('.content', element2).append('<p><span class="icon">JOINED</span>  '+notice+'</p>');
	}

	function formatMessage(from, message) {
	    return $("<p><b>"+from+"</b>: "+message+"</p>");
	}

	function showMessage(from, message) {
	    $(".content", element).append(formatMessage(from, message));
	    $(".content", element2).append(formatMessage(from, message));

	    
	    $(".content", element).attr({ scrollTop: $(".content", element).attr("scrollHeight") });
	    $(".content", element2).attr({ scrollTop: $(".content", element2).attr("scrollHeight") });
	}


	function initUI() {
	    element2.html($('<form onsubmit="javascript: return false;"><div class="content" style="margin-bottom: 5px; width: 500px; height: 400px; border: 1px solid gray; padding: 5px"></div><input type="text" style="width: 500px;"/></form>').submit(function() { var s = $("INPUT", element2).val(); $("INPUT", element2).attr("value", "");
																																	 showMessage($.booki.username, s);
  	    $.booki.sendToChannel("/chat/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "message_send", "message": s}, function() {} );

}));

	    element.html($('<form onsubmit="javascript: return false;"><div class="content" style="margin-bottom: 5px; width: 200px; height: 400px; border: 1px solid black; padding: 5px"></div><input type="text" style="width: 200px;"/></form>').submit(function() { var s = $("INPUT", element).val(); $("INPUT", element).attr("value", "");
																																	 showMessage($.booki.username, s);
  	    $.booki.sendToChannel("/chat/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "message_send", "message": s}, function() {} );

}));
	}

	
	return {
	    'initChat': function(elem, elem2) {
		element = elem;
		element2 = elem2;
		initUI();

		jQuery.booki.subscribeToChannel("/chat/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", function(message) {
		    if(message.command == "user_joined") {
			showJoined(message.user_joined);
		    }

		    if(message.command == "message_received") {
			showMessage(message.from, message.message);
		    }
		});
		
	    }
	};
    }();
	/* booki.editor */
	
	jQuery.namespace('jQuery.booki.editor');
	
	jQuery.booki.editor = function() {

	    /* TOC */

	    function createChapter(vals) {
		var options = {
		    id: null,
		    title: '',
		    isChapter: true,
		    isLocked: false
		};

		$.extend(options, vals);

		return options;
	    }

	    function TOC() {
		this.items = new Array();
	    }

	    $.extend(TOC.prototype, {
		'addItem': function(item) {
		    this.items.push(item);
		},
		
		'delItemById': function(id) {
		    for(var i = 0; i < this.items.length; i++) {
			if(this.items[i].id == id) {
			    return this.items.slice(i, i+1);
			}
		    }
		},
		
		'getItemById': function(id) {
		    for(var i = 0; i < this.items.length; i++) {
			if(this.items[i].id == id) {
			    return this.items[i];
			}
		    }

		    return null;
		},

		'update': function(order) {
		    var newOrder = new Array();

		    for(var i = 0; i < order.length; i++) {
			var item = this.getItemById(order[i])
			newOrder.push(item);
		    }
		    this.items = newOrder;
		},

		'draw': function() {
		    $("#chapterslist").empty();
		    $.each(this.items, function(i, v) {
			if(v.isChapter)
			    makeChapterLine(v.id, v.title).appendTo("#chapterslist");
			else
			    makeSectionLine(v.id, v.title).appendTo("#chapterslist");

		    });
		},

		'redraw': function() {
		    var chldrn = $("#chapterslist").contents().clone(true);

		    $("#chapterslist").empty();

		    $.each(this.items, function(i, v) {
			for(var n = 0; n < chldrn.length; n++) {
			    if( $(chldrn[n]).attr("id") == "item_"+v.id) {
				$(chldrn[n]).appendTo("#chapterslist");
				break;
			    }
			}
		    });
		},

		'refresh': function() {
		    // should update status and other things also
		    $.each(this.items, function(i, v) {
			$("#item_"+v.id+"  .title").html(v.title);
		    });


		}
	    });

	    var toc = new TOC();

	    var _isEditingSmall = false;

	  function _f(data) {
	    function _edi() {
//	      xinha_init(); 
	      
	      var edi = xinha_editors.myTextArea; 
	      if(edi) {
		edi.setEditorContent(data.content);
	      } 
	    }
	    return _edi;
	  }


	    function makeSectionLine(chapterID, name) {
		return $('<li class="ui-state-default" id="item_'+chapterID+'"  style="background-color: #a0a0a0; color: white; background-image: none"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><div class="cont"><table border="0" cellspacing="0" cellpadding="0" width="100%"><tr><td width="70%"><div class="title" style="float: left">'+name+'</div></td><td width="10%"><td width="20%"><div class="extra" style="float: right; font-size: 6pt; clear: right"></div></td></tr></table></div></li>');
	    }
	    
	    function makeChapterLine(chapterID, name) {
		return $('<li class="ui-state-default" id="item_'+chapterID+'"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><div class="cont"><table border="0" cellspacing="0" cellpadding="0" width="100%"><tr><td width="70%"><div class="title" style="float: left">'+name+'</div></td><td width="10%"><a href="javascript:void(0)" onclick="$.booki.editor.editChapter('+chapterID+')" style="font-size: 12px">EDIT</a><td width="20%"><div class="status" style="float:right; font-size: 6pt">published</div><div class="extra" style="float: right; font-size: 6pt; clear: right"></div></td></tr></table></div></li>').dblclick(function() {
		    if(_isEditingSmall) return;
		    _isEditingSmall = true;

		    $.booki.ui.notify("Sending data...");
		    $.booki.sendToCurrentBook({"command": "chapter_status", "status": "rename", "chapterID": chapterID}, function() {$.booki.ui.notify("")} );
		    
		    var s = $(".title", $(this)).text(); 
		    var $this = $(this);

                    $(".cont", $(this)).html('<form style="font-size:12px"></form>');
                    $("FORM", $(this)).append($('<input type="text" size="50" value="'+s+'" >'));
                    $("FORM", $(this)).append($('<a href="#">SAVE</a>').click(function() {

			var newName = $("INPUT", $this).val();
			_isEditingSmall = false; $.booki.ui.notify("Sending data...");
			$.booki.sendToCurrentBook({"command": "chapter_rename", "chapterID": chapterID, "chapter": newName}, function() { 
			    $.booki.ui.notify("");
			});
			$("#item_"+chapterID).replaceWith(makeChapterLine(chapterID, newName)); 
		
		    }));
		    $("FORM", $(this)).append($('<span> </span>').html());
                    $("FORM", $(this)).append($('<a href="#">CANCEL</a>').click(function() { 
			_isEditingSmall = false; $.booki.ui.notify("Sending data...");
			$.booki.sendToCurrentBook({"command": "chapter_status", "status": "normal", "chapterID": chapterID}, function() {$.booki.ui.notify("")} );
			
			$("#item_"+chapterID).replaceWith(makeChapterLine(chapterID, name));  }));
		    });
	    }
	    
	    function closeEditor() {
		$("#editor").fadeOut("slow",
				     function() {
					 $("#editor").css("display", "none");
                                         $("#container").hide().css("display", "block"); 
				     });
	    }
	    
	    return {
		editChapter: function(chapterID) {
		    $.booki.ui.notify("Loading chapter data...");
		    $.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/",
	{"command": "get_chapter", "chapterID": chapterID}, function(data) {
					      $.booki.ui.notify();
					      $("#container").fadeOut("slow", function() {

						      $("#container").css("display", "none");
						      $("#editor").css("display", "block").fadeIn("slow");
//  						      $("#editor TEXTAREA").html(data.content);
    						      
                                                      
						     /* xinha */
						  setTimeout(xinha_init,  0);
  						  setTimeout(_f(data), 100);

						      $("#editor INPUT[name=title]").attr("value", data.title);

   						  $("#editor INPUT[name=chapter_id]").attr("value", chapterID);
						  $("#editor INPUT[name=save]").unbind('click').click(function() {
					              var edi = xinha_editors["myTextArea"]; 
                                                      var content = edi.getEditorContent();

						      $.booki.ui.notify("Sending data...");

						      $.booki.sendToCurrentBook({"command": "chapter_save", "chapterID": chapterID, "content": content}, function() {$.booki.ui.notify(); closeEditor(); } );

						  });

						  $("#editor BUTTON[class=cancel]").unbind('click').click(function() {
							  $.booki.sendToCurrentBook({"command": "chapter_status", "status": "normal", "chapterID": chapterID});
							  closeEditor();
						      });  
						  });



					  });
		},
		
		_initUI: function() {
		    $("#tabs").tabs();
		    $('#tabs').bind('tabsselect', function(event, ui) {});

		    /* $("#accordion").accordion({ header: "h3" }); */
		    $("#chapterslist").sortable({'cursor': 'crosshair', 'stop': function() { 
				$.booki.ui.notify("Sending data...");
				var result = $('#chapterslist').sortable('toArray'); 
				$.booki.sendToCurrentBook({"command": "chapters_changed", "chapters": result}, function() {$.booki.ui.notify()} );
			    }, 'placeholder': 'ui-state-highlight', 'scroll': true});


		    $.booki.chat.initChat($("#chat"), $("#chat2"));
		},
		
		_loadInitialData : function() {
		    $.booki.ui.notify("Loading...");

		    jQuery.booki.sendToCurrentBook({"command": "init_editor"},

					       function(data) {
						   $.booki.ui.notify("");

						   $.each(data.chapters, function(i, elem) {
						       toc.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1}));
						      // makeChapterLine(elem[0], elem[1]).appendTo("#chapterslist");
						   });

						   toc.draw();
						   
						   $.each(data.users, function(i, elem) {
						       $("#users").append(elem+"<br/>");
						   });

					       });

		},
		
		/* initialize editor */
		
		initEditor: function() {
		    
		    jQuery.booki.subscribeToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", function(message) {

			// ERROR
			// this does not work when you change chapter status very fast
			if(message.command == "chapter_status") {
			    if(message.status == "rename" || message.status == "edit") {
				// $("#item_"+message.chapterID).css("color", "red");
				$(".extra", $("#item_"+message.chapterID)).html('<div style="padding: 3px; background-color: red; color: white">'+message.username+'</div>');
			    }
			    
			    if(message.status == "normal") {
				//$("#item_"+message.chapterID).css("color", "gray");
				$(".extra", $("#item_"+message.chapterID)).html("");          
			    }
			}
			
			if(message.command == "chapters_changed") {
			    toc.update(message.ids);
			    toc.redraw();
			}
			
                        if(message.command == "chapter_create") {
			    $.booki.debug.debug("[chapter_create]");
			    $.booki.debug.debug(message.chapter);
			    if(message.chapter[3] == 1) { 
				toc.addItem(createChapter({id: message.chapter[0], title: message.chapter[1], isChapter: true}));
				var v = toc.getItemById(message.chapter[0]);
				makeChapterLine(v.id, v.title).appendTo("#chapterslist");
			    } else {
				toc.addItem(createChapter({id: message.chapter[0], title: message.chapter[1], isChapter: false}));
				var v = toc.getItemById(message.chapter[0]);
				makeSectionLine(v.id, v.title).appendTo("#chapterslist");

			    }
			}

			if(message.command == "chapter_rename") {
			    $.booki.debug.debug("[chapter_rename]");
			    var item = toc.getItemById(message.chapterID);
			    item.title = message.chapter;
			    toc.refresh();
			}
			
			if(message.command == "chapters_list") {
			    $("#chapterslist").empty();
			    $.each(message.chapters, function(i, elem) {
				// should be makeSectionLine also
					makeChapterLine(elem[0], elem[1]).prependTo("#chapterslist");
			    });
			}
			
		    });
		    
		    
		    $.booki.editor._initUI();
		    $.booki.editor._loadInitialData();
		}
	    }; 
	}();
	
    });

