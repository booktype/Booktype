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

	    function TOC(containerName) {
		this.containerName = containerName;
		this.items = new Array();

	    }

	    $.extend(TOC.prototype, {
		'addItem': function(item) {
		    this.items.push(item);
		},
		
		'delItemById': function(id) {
		    for(var i = 0; i < this.items.length; i++) {
			if(this.items[i].id == id) {
			    return this.items.splice(i, 1);
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
		    var $this = this;

		    $($this.containerName).empty();
		    $.each(this.items, function(i, v) {
			if(v.isChapter)
			    makeChapterLine(v.id, v.title).appendTo($this.containerName);
			else
			    makeSectionLine(v.id, v.title).appendTo($this.containerName);

		    });
		},

		'redraw': function() {
		    var $this = this;
		    var chldrn = $($this.containerName).contents().clone(true);

		    $($this.containerName).empty();

		    $.each(this.items, function(i, v) {
			for(var n = 0; n < chldrn.length; n++) {
			    if( $(chldrn[n]).attr("id") == "item_"+v.id) {
				$(chldrn[n]).appendTo($this.containerName);
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

	    var toc = new TOC("#chapterslist");
	    var holdChapters = new TOC("#holdchapterslist");

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
		    $("#chapterslist, #holdchapterslist").sortable({'connectWith': ['.connectedSortable'], 'dropOnEmpty': true,  'stop': function(event, ui) { 

			var result     = $('#chapterslist').sortable('toArray'); 
			var holdResult = $('#holdchapterslist').sortable('toArray'); 

			// too much copy+paste here. should organise it in better way.

			if(toc.items.length > result.length) {
			    for(var i = 0; i < toc.items.length; i++) {
				var wasFound = false;
				for(var n = 0; n < result.length; n++) {
				    if(toc.items[i].id == result[n].substr(5)) {
					wasFound = true;
				    }
				}

				if(!wasFound) {
				    var itm = toc.getItemById(toc.items[i].id);
				    if((""+itm.id).substring(0,1) != 's') {
					holdChapters.addItem(itm);
				    } else {
					$("#item_"+toc.items[i].id).remove();
				    }
				    $.booki.debug.debug(itm.id);
				    toc.delItemById(toc.items[i].id);

				    $.booki.ui.info("#container .middleinfo", "Removing chapter from Table of Contents.");
				    $.booki.ui.notify("Sending data...");
				    $.booki.sendToCurrentBook({"command": "chapters_changed", 
							       "chapters": result,
							       "hold": holdResult,
							       "kind": "remove",
							       "chapter_id": itm.id}, 
							      function() {$.booki.ui.notify()} );
                                    
				    break;
				}
			    }
			}  else if(toc.items.length < result.length) {
			    for(var i = 0; i < holdChapters.items.length; i++) {
				var wasFound = false;
				for(var n = 0; n < holdResult.length; n++) {
				    if(holdChapters.items[i].id == holdResult[n].substr(5)) {
					wasFound = true;
				    }
				}

				if(!wasFound) {
				    var itm = holdChapters.getItemById(holdChapters.items[i].id);
				    toc.addItem(itm);
				    holdChapters.delItemById(itm.id);

				    $.booki.ui.info("#container .middleinfo", "Adding chapter to Table of Contents.");
				    $.booki.ui.notify("Sending data...");
				    $.booki.sendToCurrentBook({"command": "chapters_changed", 
							       "chapters": result,
							       "hold": holdResult,
							       "kind": "add",
							       "chapter_id": itm.id}, 
							      function() {$.booki.ui.notify()} );
				    break;
				} 
			    }

			} else if (toc.items.length == result.length) {
			    $.booki.ui.info("#container .middleinfo", "Reordering the chapters...");
			    $.booki.ui.notify("Sending data...");
			    $.booki.sendToCurrentBook({"command": "chapters_changed", 
						       "chapters": result,
						       "hold": holdResult,
						       "kind": "order",
						       "chapter_id": null
						       }, 
							      function() {$.booki.ui.notify()} );
			}
/*
				$.booki.sendToCurrentBook({"command": "chapters_changed", "chapters": result}, function() {$.booki.ui.notify()} );
*/

		    }, 'placeholder': 'ui-state-highlight', 'scroll': true}).disableSelection();


		    $.booki.chat.initChat($("#chat"), $("#chat2"));
		},
		
		_loadInitialData : function() {
		    $.booki.ui.notify("Loading...");

		    jQuery.booki.sendToCurrentBook({"command": "init_editor"},

					       function(data) {
						   $.booki.ui.notify("");

						   $.each(data.chapters, function(i, elem) {
						       toc.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1}));
						   });

						   $.each(data.hold, function(i, elem) {
						       holdChapters.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1}));
						   });


						   toc.draw();
						   holdChapters.draw();
						   
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
			    if(message.kind == "remove") {

				var itm = toc.getItemById(message.chapter_id);

				if((""+message.chapter_id).substring(0,1) != 's')
				    holdChapters.addItem(itm);

				toc.delItemById(message.chapter_id);

				toc.update(message.ids);
				holdChapters.update(message.hold_ids);

				toc.draw();
				holdChapters.draw();

				$.booki.ui.info("#container .middleinfo", "Removing chapter from Table of Contents.");
			    } else {
				if(message.kind == "add") {
				    var itm = holdChapters.getItemById(message.chapter_id);
				    toc.addItem(itm);
				    holdChapters.delItemById(message.chapter_id);

				    toc.update(message.ids);
				    holdChapters.update(message.hold_ids);

				    toc.draw();
				    holdChapters.draw();

				    $.booki.ui.info("#container .middleinfo", "Adding chapter to Table of Contents.");
				} else {
				    $.booki.ui.info("#container .middleinfo", "Reordering the chapters...");

				    toc.update(message.ids);
				    holdChapters.update(message.hold_ids);
				    toc.redraw();
				    holdChapters.redraw();
				}
			    }
			}
			
                        if(message.command == "chapter_create") {
			    // this also only works for the TOC
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
			    if(!item)
				item = holdChapters.getItemById(message.chapterID);
			    item.title = message.chapter;
			    toc.refresh();
			    holdChapters.refresh();
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

