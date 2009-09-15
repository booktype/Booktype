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
	    var chapters = null;

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
	    
	    function makeChapterLine(chapterID, name) {
/*		return $('<li class="ui-state-default" id="item_'+chapterID+'"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><div class="cont"><div class="title" style="float: left"><a href="javascript:void(0)" onclick="$.booki.editor.editChapter('+chapterID+')">'+name+'</a></div><div class="status" style="float:right; font-size: 6pt">published</div><div class="extra" style="float: right; font-size: 6pt; clear: right"></div></div></li>').dblclick(function() { */

		return $('<li class="ui-state-default" id="item_'+chapterID+'"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><div class="cont"><table border="0" cellspacing="0" cellpadding="0" width="100%"><tr><td width="70%"><div class="title" style="float: left">'+name+'</div></td><td width="10%"><a href="javascript:void(0)" onclick="$.booki.editor.editChapter('+chapterID+')" style="font-size: 12px">EDIT</a><td width="20%"><div class="status" style="float:right; font-size: 6pt">published</div><div class="extra" style="float: right; font-size: 6pt; clear: right"></div></td></tr></table></div></li>').dblclick(function() {
			$.booki.ui.notify("Sending data...");
			$.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "chapter_status", "status": "rename", "chapterID": chapterID}, function() {$.booki.ui.notify("")} );
			
			
			var s = $(".title", $(this)).text(); 
                        $(".cont", $(this)).html('<form style="font-size:12px"></form>');
                        $("FORM", $(this)).append($('<input type="text" size="50" value="'+s+'" >'));
                        $("FORM", $(this)).append($('<a href="#">SAVE</a>').click(function() {alert("hej");}));
			$("FORM", $(this)).append($('<span> </span>').html());
                        $("FORM", $(this)).append($('<a href="#">CANCEL</a>').click(function() { $.booki.ui.notify("Sending data...");
				    $.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "chapter_status", "status": "normal", "chapterID": chapterID}, function() {$.booki.ui.notify("")} );$("#item_"+chapterID).replaceWith(makeChapterLine(chapterID, name));  }));
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
//						      var content = $("#editor TEXTAREA").val();
					              var edi = xinha_editors["myTextArea"]; 
                                                      var content = edi.getEditorContent();

						      $.booki.ui.notify("Sending data...");
						      $.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "chapter_save", "chapterID": chapterID, "content": content}, function() {$.booki.ui.notify(); closeEditor(); } );
						  });

						  $("#editor BUTTON[class=cancel]").unbind('click').click(function() {
							  $.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "chapter_status", "status": "normal", "chapterID": chapterID});
							  closeEditor();
						      });  
						  });



					  });
		},
		
		_initUI: function() {
		    $("#tabs").tabs();
		    $('#tabs').bind('tabsselect', function(event, ui) {});

		    /* $("#accordion").accordion({ header: "h3" }); */
		    $("#chapterslist").sortable({stop: function() { 
				$.booki.ui.notify("Sending data...");
				var result = $('#chapterslist').sortable('toArray'); 
				$.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "chapters_changed", "chapters": result}, function() {$.booki.ui.notify()} );
			    }, placeholder: 'ui-state-highlight', scroll: true});


		    $.booki.chat.initChat($("#chat"), $("#chat2"));
		},
		
		_loadInitialData : function() {
		    $.booki.ui.notify("Loading...");

		    jQuery.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "init_editor"},
					       function(data) {
						   $.booki.ui.notify("");

						   $.each(data.chapters, function(i, elem) {
							   makeChapterLine(elem[0], elem[1]).prependTo("#chapterslist");
						   });
						   
						   $.each(data.users, function(i, elem) {
						       $("#users").append(elem+"<br/>");
						   });

					       });

		},
		
		/* initialize editor */
		
		initEditor: function() {
		    
		    jQuery.booki.subscribeToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", function(message) {
			    if(message.command == "chapter_status") {
				if(message.status == "rename" || message.status == "edit") {
				    $("#item_"+message.chapterID).css("color", "red");
				    $(".extra", $("#item_"+message.chapterID)).html("Edited by "+message.username);
				}
				
				if(message.status == "normal") {
				    $("#item_"+message.chapterID).css("color", "gray");
				    $(".extra", $("#item_"+message.chapterID)).html("");          }
			    }
			    
			    if(message.command == "chapters_changed") {
				
				$("#chapterslist").empty();
				$.each(message.chapters, function(i, elem) {
					makeChapterLine(elem[0], elem[1]).prependTo("#chapterslist");
				    });
				
				
			    }
			    
			    if(message.command == "chapters_list") {
				$("#chapterslist").empty();
				$.each(message.chapters, function(i, elem) {
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

