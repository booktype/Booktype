$(function() {
/*
 * todo: 
 *  - should send projectid and bookid and not their full names
 *
 *
 * */	
	/* booki.editor */
	
	jQuery.namespace('jQuery.booki.editor');
	
	jQuery.booki.editor = function() {
	    var chapters = null;
	    
	    function makeChapterLine(chapterID, name) {
		return $('<li class="ui-state-default" id="item_'+chapterID+'"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><div class="cont"><div class="title" style="float: left"><a href="#" onclick="$.booki.editor.editChapter('+chapterID+')">'+name+'</a></div><div class="status" style="float:right; font-size: 6pt">published</div><div class="extra" style="float: right; font-size: 6pt; clear: right"></div></div></li>').dblclick(function() {
			$.booki.ui.notify("Sending data...");
			$.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "chapter_rename", "status": "start", "chapterID": chapterID}, function() {$.booki.ui.notify("")} );
			
			
			var s = $(".title", $(this)).text(); 
                        $(".cont", $(this)).html('<form style="font-size:12px"></form>');
                        $("FORM", $(this)).append($('<input type="text" size="50" value="'+s+'" >'));
                        $("FORM", $(this)).append($('<a href="#">SAVE</a>').click(function() {alert("hej");}));
			$("FORM", $(this)).append($('<span> </span>').html());
                        $("FORM", $(this)).append($('<a href="#">CANCEL</a>').click(function() { $.booki.ui.notify("Sending data...");
				    $.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "chapter_rename", "status": "end", "chapterID": chapterID}, function() {$.booki.ui.notify("")} );$("#item_"+chapterID).replaceWith(makeChapterLine(chapterID, name));  }));
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
						      $("#editor TEXTAREA").html(data.content);
						      $("#editor INPUT").attr("value", data.title);
						      $("#editor BUTTON[class=cancel]").click(function() {
							      $("#editor").fadeOut("slow",
										   function() {
										       $("#editor").css("display", "none");                                           $("#container").hide().css("display", "block"); 
										   });
							      
							  });  
						  });
					  });
		},
		
		_initUI: function() {
		    //$("#accordion").accordion({ header: "h3" });
		    $("#chapterslist").sortable({stop: function() { 
				$.booki.ui.notify("Sending data...");
				var result = $('#chapterslist').sortable('toArray'); 
				$.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "chapters_changed", "chapters": result}, function() {$.booki.ui.notify()} );
			    }, placeholder: 'ui-state-highlight', scroll: true});
		    $("#tabs").tabs();
		    $('#tabs').bind('tabsselect', function(event, ui) {});
		},
		
		_loadInitialData : function() {
		    $.booki.ui.notify("Loading...");
		    
		    jQuery.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "get_chapters"},
					       function(data) {
						   $.booki.ui.notify("");
						   $.each(data.chapters, function(i, elem) {
							   makeChapterLine(elem[0], elem[1]).prependTo("#chapterslist");
						       });
					       });
		    
		    $.booki.sendToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", {"command": "get_users"}, function (data) {
			    $.each(data.users, function(i, elem) {
				    $("#users").append(elem+"<br/>");
				});
			});
		},
		
		/* initialize editor */
		
		initEditor: function() {
		    
		    jQuery.booki.subscribeToChannel("/booki/book/"+$.booki.currentProjectID+"/"+$.booki.currentBookID+"/", function(message) {
			    if(message.command == "chapter_rename") {
				if(message.status == "start") {
				    $("#item_"+message.chapterID).css("color", "red");
				    $(".extra", $("#item_"+message.chapterID)).html("Edited by "+message.username);
				}
				
				if(message.status == "end") {
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

