$(function() {
/*
 * todo: 
 *  - should send projectid and bookid and not their full names
 *
 *
 * */	

function unescapeHtml (val) {
    return val.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
} 
    /* booki.chat */

    jQuery.namespace('jQuery.booki.chat');

    jQuery.booki.chat = function() {
	var element = null;
	var element2 = null;

	function showJoined(notice) {
	    $('.content', element).append('<p><span class="icon">JOINED</span>  '+notice+'</p>');
	    $('.content', element2).append('<p><span class="icon">JOINED</span>  '+notice+'</p>');
	}

	function showInfo(notice) {
	    $('.content', element).append('<p><span class="info">INFO</span>  '+notice+'</p>');
//	    $('.content', element2).append('<p><span class="icon">JOINED</span>  '+notice+'</p>');
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
	    element2.html($('<form onsubmit="javascript: return false;"><div class="content" style="margin-bottom: 5px; width: 500px; height: 300px; border: 1px solid gray; padding: 5px"></div><input type="text" style="width: 500px;"/></form>').submit(function() { var s = $("INPUT", element2).val(); $("INPUT", element2).attr("value", "");
																																	 showMessage($.booki.username, s);
  	    $.booki.sendToChannel("/chat/"+$.booki.currentBookID+"/", {"command": "message_send", "message": s}, function() {} );

}));

	    element.html($('<form onsubmit="javascript: return false;"><div class="content" style="margin-bottom: 5px; width: 200px; height: 300px; border: 1px solid black; padding: 5px"></div><input type="text" style="width: 200px;"/></form>').submit(function() { var s = $("INPUT", element).val(); $("INPUT", element).attr("value", "");
																																	 showMessage($.booki.username, s);
  	    $.booki.sendToChannel("/chat/"+$.booki.currentBookID+"/", {"command": "message_send", "message": s}, function() {} );

}));
	}

	
	return {
	    'initChat': function(elem, elem2) {
		element = elem;
		element2 = elem2;
		initUI();

		jQuery.booki.subscribeToChannel("/chat/"+$.booki.currentBookID+"/", function(message) {
		    if(message.command == "user_joined") {
			showJoined(message.user_joined);
		    }

		    if(message.command == "message_info") {
			showInfo(message.message);
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

	    /* status */
	    var statuses = null;
	    var attachments = null;
	    var splitChapters = null;
	    var currentlyEditing = null;

	    function getStatusDescription(statusID) {
		var r = $.grep(statuses,  function(v, i) {
		    
		    return v[0] == statusID;
		});

		if(r && r.length > 0)
		    return r[0][1];

		return null;
	    }


	    /* TOC */

	    function createChapter(vals) {
		var options = {
		    id: null,
		    title: '',
		    isChapter: true,
		    isLocked: false,
		    status: null
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
			    makeChapterLine(v.id, v.title, getStatusDescription(v.status)).appendTo($this.containerName);
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
			$("#item_"+v.id+"  .status").html(getStatusDescription(v.status));

		    });


		}
	    });

	    var toc = new TOC("#chapterslist");
	    var holdChapters = new TOC("#holdchapterslist");


	    function getChapter(chapterID) {
		var chap = toc.getItemById(chapterID);
		if(!chap)
		    chap = holdChapters.getItemById(chapterID);
		return chap;
	    }

	    var _isEditingSmall = false;


	    function makeSectionLine(chapterID, name) {
		return $('<li class="ui-state-default" id="item_'+chapterID+'"  style="background-color: #a0a0a0; color: white; background-image: none"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><div class="cont"><table border="0" cellspacing="0" cellpadding="0" width="100%"><tr><td width="70%"><div class="title" style="float: left">'+name+'</div></td><td width="10%"><td width="20%"><div class="extra" style="float: right; font-size: 6pt; clear: right"></div></td></tr></table></div></li>');
	    }
	    
	    function makeChapterLine(chapterID, name, status) {
		return $('<li class="ui-state-default" id="item_'+chapterID+'"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><div class="cont"><table border="0" cellspacing="0" cellpadding="0" width="100%"><tr><td width="70%"><div class="title" style="float: left">'+name+'</div></td><td width="10%"><a href="javascript:void(0)" onclick="$.booki.editor.editChapter('+chapterID+')" style="font-size: 12px">EDIT</a><td width="20%"><div class="status" style="float:right; font-size: 6pt"><a href="javascript:void(0)" onclick="$.booki.editor.editStatusForChapter('+chapterID+')">'+status+'</a></div><div class="extra" style="float: right; font-size: 6pt; clear: right"></div></td></tr></table></div></li>').dblclick(function() {
		    if(_isEditingSmall) return;
		    _isEditingSmall = true;

		    $.booki.ui.notify("Sending data...");
		    $.booki.sendToCurrentBook({"command": "chapter_status", "status": "rename", "chapterID": chapterID}, function() {$.booki.ui.notify("")} );
		    
		    var s = $(".title", $(this)).text(); 
		    var $this = $(this);

                    $(".cont", $(this)).html('<form style="font-size:12px; white-space: nowrap"></form>');

		    // Make it look nicer and look on the width of input box
		    // also use white-space: nowrap


                    $("FORM", $(this)).append($('<input type="text" style="width: 70%" value="'+s+'" >'));
                    $("FORM", $(this)).append($('<a href="#">SAVE</a>').click(function() {

			var newName = $("INPUT", $this).val();
			_isEditingSmall = false; $.booki.ui.notify("Sending data...");
			$.booki.sendToCurrentBook({"command": "chapter_rename", "chapterID": chapterID, "chapter": newName}, function() { 
			    $.booki.ui.notify("");
			});
			$("#item_"+chapterID).replaceWith(makeChapterLine(chapterID, newName, status)); 
		
		    }));
		    $("FORM", $(this)).append($('<span> </span>').html());
                    $("FORM", $(this)).append($('<a href="#">CANCEL</a>').click(function() { 
			_isEditingSmall = false; $.booki.ui.notify("Sending data...");
			$.booki.sendToCurrentBook({"command": "chapter_status", "status": "normal", "chapterID": chapterID}, function() {$.booki.ui.notify("")} );
			
			// this is not god. should get info from toc
			var ch = getChapter(chapterID);
			$("#item_"+chapterID).replaceWith(makeChapterLine(chapterID, ch.title, getStatusDescription(ch.status)));  }));
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
		editStatusForChapter: function(chapterID) {
		    var selopts = '<select><option value="-1" style="font-weight: bold; color: black">Cancel</option><option value="-1" style="font-weight: bold; color: black">--------</option>';
		    var chap = getChapter(chapterID);

		    $.each(statuses, function(i, v) {
			selopts += '<option value="'+v[0]+'"';
			if(v[0] == chap.status)
			    selopts += ' selected="selected" ';
			selopts += '">'+v[1]+'</option>';
		    });
		    selopts += '</select>';
		    
		    var s = $(selopts);

		    $("#item_"+chapterID+" .status").html(s.change(function() { 
			var chap = getChapter(chapterID);
			if(parseInt($(this).val()) != -1)
			    chap.status = parseInt($(this).val());

			$("#item_"+chapterID+" .status").html('<a href="javascript:void(0)" onclick="$.booki.editor.editStatusForChapter('+chapterID+')">'+getStatusDescription(chap.status)+'</a>');

		    }).wrap("<form></form>"));
		},

		reloadAttachments: function(func) {
		    $.booki.debug.debug("[reloadAttachments]");

		    $.booki.sendToCurrentBook({"command": "attachments_list"}, function(data) {
			attachments = data.attachments;
			$.booki.editor.drawAttachments();
			func();
		    });
		},

		editChapter: function(chapterID) {
		    $.booki.ui.notify("Loading chapter data...");
		    $.booki.sendToChannel("/booki/book/"+$.booki.currentBookID+"/",
					  {"command": "get_chapter", "chapterID": chapterID}, function(data) {
					      $.booki.ui.notify();
					      $("#container").fadeOut("slow", function() {
						  
						  $("#container").css("display", "none");
						  $("#editor").css("display", "block").fadeIn("slow");

						  /* xinha */
						  xinha_init(); 
						  
						  function _tryAgain() {
						      var edi = xinha_editors.myTextArea; 
						      if(edi) {
							  edi.whenDocReady(function() {
							      edi.setEditorContent(data.content);
							  });
						      } else {
							  setTimeout(_tryAgain, 500);
						      }
						  }

						  if(!xinha_editors.myTextArea) {
						      setTimeout(_tryAgain, 500);
						  } else {
						      _tryAgain();
						  }


						  /*
						  var edi = xinha_editors.myTextArea; 
						  if(edi)
						      edi.setEditorContent(data.content);
*/
						/*  $("#editor INPUT[name=title]").attr("value", data.title); */
						  
   						  $("#editor INPUT[name=chapter_id]").attr("value", chapterID);
						  $("#editor INPUT[name=save]").unbind('click').click(function() {
						      currentlyEditing = chapterID;
					              var edi = xinha_editors["myTextArea"]; 
                                                      var content = edi.getEditorContent();
						      
						      var c = content.substring(0);
						      var chapters_n = 0;
						      var currentPos = 0;

						      while(chapters_n < 10) {
							 var n1 = content.indexOf("</H1>", currentPos);
							 var n2 = content.indexOf("</h1>", currentPos);
 							 var n =  -1;

							if(n2 != -1 ) {
							    if (n1 > n2) 
             							n = n2;
						            else
                    					      if(n1 != -1)
								n = n1;
           						      else n = n2;
							}			
                 				        if(n == -1 && n1 == -1) {
 								break;
							} else {
 							   if(n == -1)
							        n = n1;
							}
                                                        currentPos = n+5; 
 							chapters_n += 1;
						      }

/*
						      var r = new RegExp("<h1>([^\<]+)</h1>", "ig");
						      var chapters_n = 0;

						      var c = content.substring(0);

						      while(true) {
							  $.booki.debug.debug("#"+unescapeHtml(c)+"#");
							  m = r.exec(c);
							  if(m) {
							      $.booki.debug.debug("m je pun");
							      chapters_n += 1;
							      $.booki.debug.debug("last index je ");
							      $.booki.debug.debug(r.lastIndex);
							      $.booki.debug.debug(m.length);
							      
							      c = c.substring(r.lastIndex-m[0].length);
							  } else {
							      $.booki.debug.debug("m je prazan");
							      break;
							  }
						      }
*/

						      if(chapters_n > 1) {
							  $("#spalatodialog").dialog("open");
						      } else {
							  $.booki.ui.notify("Sending data...");

 							  $.booki.sendToCurrentBook({"command": "chapter_save", "chapterID": chapterID, "content": content}, function() {$.booki.ui.notify(); closeEditor(); } );
						      }

						  });

						  $("#editor INPUT[class=cancel]").unbind('click').click(function() {
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

                    $("#tabpublish BUTTON").click(function() {
			var isArchive = $("#tabpublish FORM INPUT[type='checkbox']").is(":checked");
			var publishMode = $("#tabpublish OPTION:selected").val();

			var messageFormat = {"epub": "epub",
			    "book": "book formated pdf",
			    "openoffice": "Open Office text file",
			    "newspaper": "newspaper formatted pdf",
			    "web": "screen formatted pdf"};
			
			var message = "Your books is being sent to Objavi (Booki's publishing engine), converted to "+messageFormat[publishMode];
			if(isArchive)
			    message += " and being uploaded to Archive.org";
			message += ".";
			
			$("#tabpublish .info").html('<div style="padding-top: 20px; padding-bottom: 20px;">'+message+'</div>');
			$("#tabpublish BUTTON").attr("disabled", "disabled");
			$("#tabpublish .info").append('<div id="progressbar" style="width: 400px;"></div>');

			var currentProgress = 0;

			$("#progressbar").progressbar({
			    value: currentProgress
			});


			function _incrementProgress() {
			    if(currentProgress == -1) return;
			    if(currentProgress > 100) currentProgress = 100;

			    currentProgress += 10;

			    $("#progressbar").progressbar('value', currentProgress);
			    setTimeout(function() { _incrementProgress();}, 1000);
			}

			_incrementProgress();
			

                        $.booki.sendToCurrentBook({"command": "publish_book",
						   "is_archive": isArchive,
						   "publish_mode": publishMode},
						  
                                                  function(data) {
						      var message = "";

                                                      currentProgress = -1;

						      if(isArchive) {
							  var messageFormat = {"epub": "epub",
							      "book": "book formated pdf",
							      "openoffice": "Open Office text file",
							      "newspaper": "newspaper formatted pdf",
							      "web": "screen formatted pdf"};
							  
						      
							  message = "Your "+messageFormat[publishMode]+" has been sent to Archive.org. It will appear at the following URL in a few minutes: ";
						      }
						      
                                                      $("#tabpublish BUTTON").removeAttr("disabled");

                                                      $("#tabpublish .info").html('<div style="padding-top: 20px; padding-bottom: 10px"><a href="'+data.dta+'" target="_new">'+data.dta+'</a></div>');
                                                      $("#tabpublish .info").append('<p>'+message+'</p>');
                                                      $("#tabpublish .info").append('<p><a href="'+data.dtas3+'" target="_new">'+data.dtas3+'</a></p>');

                                                     $.booki.debug.debug(data.dtaall);
                                                      $.booki.ui.notify();
                                                  } );
                    });

		    // init upload dialog

		    $.booki.editor.upload.init(function(){ 
			return attachments } );

		    // spalato dialog

		    $("#spalatodialog").dialog({
			bgiframe: true,
			autoOpen: false,
			height: 400,
    		        width: 700, 
			modal: true,

			buttons: {
			    'Split into chapters and save changes': function() {
				var $dialog = $(this);
				$.booki.ui.notify("Saving data. Please wait...");
				// should show notify message - please wait
 				$.booki.sendToCurrentBook({"command": "chapter_split", "chapterID": currentlyEditing, "chapters": splitChapters}, function() {$dialog.dialog('close'); $.booki.ui.notify(); closeEditor(); } );
			    },

			    'Continue editing': function() {
				$(this).dialog('close');
			    }
			},

			open: function(event,ui) {

			    var edi = xinha_editors["myTextArea"]; 
                            var content = edi.getEditorContent();
			    
			    var endSplitting = false;

			    var n = 0;

			    $("#spalatodialog .chapters").empty();
			    $("#spalatodialog .content").empty();

			    splitChapters = new Array();
			    var chapName = '';
			    var chapContent = '';

			    while(!endSplitting) {
				var r = new RegExp("<h1>([^<]+)</h1>", "igm");
				var m = r.exec(content);

				if(m != null) {
				    if(n == 0) {
					if(r.lastIndex-m[0].length > 1) {
					    $("#spalatodialog .chapters").append('<li><a class="chapter" href="javascript:void(0)" title="0">Unknown chapter</a></li>');
					    var chap = content.substring(0, r.lastIndex-m[0].length);
					    $("#spalatodialog .content").append('<div style="display: none" class="chapter0">'+chap+'</div>');
					    splitChapters.push(["Unknown chapter", chap]);
					
					    n += 1;
					}
					$("#spalatodialog .chapters").append('<li><a class="chapter" href="javascript:void(0)" title="'+n+'">'+m[1]+'</a></li>');
					chapName = m[1];
					
				    } else {
					$("#spalatodialog .chapters").append('<li><a class="chapter" href="javascript:void(0)" title="'+n+'">'+m[1]+'</a></li>');
					chapName = m[1];

					if(n > 0) {
					    var chap = content.substring(0, r.lastIndex-m[0].length);
					    $("#spalatodialog .content").append('<div style="display: none" class="chapter'+(n-1)+'">'+chap+'</div>');
					    chapContent = chap;
					} 
				    }

				    if(splitChapters.length > 0) {
					if(splitChapters[splitChapters.length-1][0] != "Unknown chapter")
					    splitChapters[splitChapters.length-1][1] = chapContent;
					//splitChapters.push([chapName, ""]);
				    } //else {
					splitChapters.push([chapName, ""]);
				   // }

				    n += 1;
				    content = content.substring(r.lastIndex);
				} else {
				    endSplitting  = true;
				}

			    }
			    splitChapters[splitChapters.length-1][1] = content;

			    $("#spalatodialog .content").append('<div style="display: none" class="chapter'+(n-1)+'">'+content+'</div>');
			    $("#spalatodialog DIV.chapter0").css("display", "block");

			    $("#spalatodialog  A.chapter").click(function() {
				var chap_n = $(this).attr("title");
				$("#spalatodialog .content > DIV").css("display", "none");
				$("#spalatodialog  DIV.chapter"+chap_n).css("display", "block");

			    });

			},
    		        close: function() {
			    
			}
		    });

		    

		},

		drawAttachments: function() {
		    
		    function _getDimension(dim) {
			if(dim) {
			    return dim[0]+'x'+dim[1];
			}
			
			return '';
		    }
		    
		    function _getSize(size) {
			return (size/1024).toFixed(2)+' Kb';
		    }
		    
		    $("#tabattachments .files").empty().append('<tr><td width="5%"></td><td align="left"><b>filename</b></td><td align="left"><b>dimension</b></td><td align="right" width="10%"><b>size</b></td></tr>');
		    
		    $.each(attachments, function(i, elem) {
			$("#tabattachments .files").append('<tr class="line"><td><input type="checkbox"></td><td><a class="file" href="javascript:void(0)" alt="'+elem["name"]+'">'+elem["name"]+'</a></td><td>'+_getDimension(elem["dimension"])+'</td><td align="right"><nobr>'+_getSize(elem.size)+'</nobr></td></tr>');
		    });
		    
		    $("#tabattachments .line").hover(function() {
			$(this).css("background-color", "#f0f0f0");
		    },
						     function() {
							 $(this).css("background-color", "white");
							 
						     });
		    
		    $("#tabattachments .file").click(function() { 
			var imageName = $(this).attr("alt"); 
			if(imageName.match(/.+\.jpg$/gi)) {
			    $("#attachmentpreview").html('<img src="../_utils/thumbnail/'+imageName+'"><br/><br/><a style="font-size: 10px" href="../static/'+imageName+'" target="_new">Open in new window</a>');
			}
		    });
		    
		},
		
		_loadInitialData : function() {
		    $.booki.ui.notify("Loading...");

		    jQuery.booki.sendToCurrentBook({"command": "init_editor"},

					       function(data) {
						   $.booki.ui.notify("");

						   $.booki.licenses = data.licenses;

						   statuses = data.statuses;

						   $.each(data.metadata, function(i, elem) {
						       $("#tabinfo .metadata").append('<tr><td valign="top"><b>'+elem.name+':</b></td><td valign="top"> '+elem.value+'</td></tr>');
						   });
						   
						   $.each(data.chapters, function(i, elem) {
						       toc.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1, status: elem[4]}));
						   });

						   $.each(data.hold, function(i, elem) {
						       holdChapters.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1, status: elem[4]}));
						   });


						   toc.draw();
						   holdChapters.draw();

						   attachments = data.attachments;
						   $.booki.editor.drawAttachments();
						   
						   $.each(data.onlineUsers, function(i, elem) {
						       $("#users").append('<li class="user'+elem+'"><div style="width: 24px; height: 24px; float: left; background-color: black; margin-right: 5px;"></div><b>'+elem+'</b></li>');
						   });

					       });

		},
		
		/* initialize editor */
		
		initEditor: function() {
		    
		    jQuery.booki.subscribeToChannel("/booki/book/"+$.booki.currentBookID+"/", function(message) {

			if(message.command == "user_add") {
			    $("#users").append('<li class="user'+message.username+'"><div style="width: 24px; height: 24px; float: left; background-color: black; margin-right: 5px;"></div><b>'+message.username+'</b></li>');
			}

			if(message.command == "user_remove") {
			    $.booki.debug.debug("USER REMOVE");
			    $.booki.debug.debug(message.username);
			    $("#users .user"+message.username).css("background-color", "yellow").slideUp(1000, function() { $(this).remove(); });
			}

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
				holdChapters.addItem(createChapter({id: message.chapter[0], title: message.chapter[1], isChapter: true, status: message.chapter[4]}));
				var v = holdChapters.getItemById(message.chapter[0]);
				makeChapterLine(v.id, v.title, getStatusDescription(v.status)).appendTo("#holdchapterslist");
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
				makeChapterLine(elem[0], elem[1], 0).prependTo("#chapterslist");
			    });
			}

			if(message.command == "chapter_split") {
			    toc.items = new Array();
			    holdChapters.items = new Array();

			    $.each(message.chapters, function(i, elem) {
				toc.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1, status: elem[4]}));
			    });
			    
			    $.each(message.hold, function(i, elem) {
				holdChapters.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1, status: elem[4]}));
			    });

			    

			    toc.draw();
			    holdChapters.draw();
			}
			
		    });
		    
		    
		    $.booki.editor._initUI();
		    $.booki.editor._loadInitialData();
		}
	    }; 
	}();
	


	/* booki.editor.upload */
	
	jQuery.namespace('jQuery.booki.editor.upload');
	
	jQuery.booki.editor.upload = function() {
	    var selectedFile = null;
	    var editor = null;
	    var f = null;
	    var n = 1;
	    var hasChanged = false;

	    return {
		setEditor: function(edit) { 
		    editor = edit; 
		},

		showFiles: function(func) {
		    $("#insertattachment .files").empty();
		    
		    $("#insertattachment .files").append('<tr><td><b>name</b></td><td><b>size</b></td><td><b>image size</b></td><td><b>date modified</b></td></tr>');

		    $.each(func(), function(i, att) {
			$("#insertattachment .files").append('<tr><td><a class="file" href="javascript:void(0)" alt="'+att.name+'">'+att.name+'</a></td><td>'+att.size+'</td><td></td><td></td></tr>');
		    });

		    $("#insertattachment A.file").click(function() {
			var fileName = $(this).attr("alt");
			selectedFile = fileName;
			$("#insertattachment .previewattachment").html('<img src="../_utils/thumbnail/'+fileName+'">');
			
		    });
		},

		showUpload: function() {
		    var onChanged = function() {
			$("#insertattachment .listing").slideUp(2000);
			
			var entry = $(this).parent().attr("class");
			
			if(!hasChanged) {
			    $("#insertattachment .uploadsubmit").append('<input type="submit" value="Upload"/>');
			    $("#insertattachment .uploadattachment").css("height", "250px");
			}
			
			var licenses = '';

			$.each($.booki.licenses, function(i, v) {
			    licenses += '<option value="'+v[0]+'">'+v[1]+'</option>';
			}); 

			
			$("#insertattachment .uploadattachment ."+entry).append('<br><table border="0"><tr><td>Rights holder:</td><td> <input name="rights'+n+'" type="text" size="30"/></td></tr><tr><td>License:</td><td><select name="license'+n+'" >'+licenses+'</select></td></tr></table>');

			$('#insertattachment .'+entry+' OPTION[value="Unknown"]').attr('selected', 'selected');
			
			$("#insertattachment .uploadattachment").append('<div style="border-top: 1px solid gray; padding-top: 5px; padding-bottom: 5px" class="entry'+n+'"><input type="file" name="entry'+n+'"></div>');
			
			$("#insertattachment INPUT[type='file'][name='entry"+n+"']").change(onChanged);
			
			
			$("#insertattachment .uploadattachment").attr({ scrollTop: $("#insertattachment .uploadattachment").attr("scrollHeight") });
			n += 1;
			hasChanged = true;
		    }
		    
		    
		    $("#insertattachment .uploadsubmit").empty();
		    
		    $("#insertattachment .uploadattachment").empty();
		    $("#insertattachment .uploadattachment").css("height", "40px");

		    $("#insertattachment .uploadattachment").append('<div style="border-top: 1px solid #c0c0c0; padding-bottom: 5px" class="entry0"><input type="file" name="entry0"></div>');
		    $("#insertattachment  INPUT[type='file'][name='entry0']").change(onChanged);
		},

		redrawFiles: function() {
		    n = 1;
		    hasChanged = false;
		    $.booki.editor.upload.showFiles(f);
		    $.booki.editor.upload.showUpload();

		},
		
                init: function(func) {
		    f = func;
		    $("#insertattachment").dialog({
			bgiframe: true,
			autoOpen: false,
			height: 400,
    			width: 700, 
			modal: true,
			buttons: {
			    'Insert image': function() {
				if(selectedFile) {
				    editor.insertHTML('<img src="../static/'+selectedFile+'"/>');
				    $(this).dialog('close');
				}
			    },
			    'Cancel': function() {
				$(this).dialog('close');
			    }
			},
			open: function(event,ui) {
			    hasChanged = false;
			    n = 1;

			    $.booki.editor.upload.showUpload();
			    $.booki.editor.upload.showFiles(func);

			},
			close: function() {
			    
			}
		    });
		    
	    }
		   }
	}();

    });
