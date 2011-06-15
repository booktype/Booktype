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
	    var msg = $('.joinMsg.template').clone().removeClass("template");
	    msg.find('.notice').html(notice);
	    $('.content', element).append(msg.clone());
	    $('.content', element2).append(msg.clone());
	    $(".content", element).attr({ scrollTop: $(".content", element).attr("scrollHeight") });
	    $(".content", element2).attr({ scrollTop: $(".content", element2).attr("scrollHeight") });

	}

	function showInfo(notice) {
	    var msg = $('.infoMsg.template').clone().removeClass("template");
	    msg.find('.notice').html(notice);
	    $('.content', element).append(msg.clone());
//	    $('.content', element2).append('<p><span class="icon">JOINED</span>  '+notice+'</p>');
	    $(".content", element).attr({ scrollTop: $(".content", element).attr("scrollHeight") });
	    $(".content", element2).attr({ scrollTop: $(".content", element2).attr("scrollHeight") });

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
	    element2.html($('<form onsubmit="javascript: return false;"><div class="content" style="margin-bottom: 5px; width: 500px; height: 300px; border: 1px solid gray; padding: 5px"></div><input type="text" style="width: 500px;"/></form>').submit(function() { var s = $("INPUT", element2).val(); $("INPUT", element2).attr("value", ""); showMessage($.booki.username, s);  $.booki.sendToChannel("/chat/"+$.booki.currentBookID+"/",{"command": "message_send", "message": s}, function() {} );

}));

	    element.html($('<form onsubmit="javascript: return false;"><div class="content" style="margin-bottom: 5px; width: 265px; height: 300px; border: 1px solid black; padding: 5px"></div><input type="text" style="width: 275px;"/></form>').submit(function() { var s = $("INPUT", element).val(); $("INPUT", element).attr("value", ""); showMessage($.booki.username, s);  $.booki.sendToChannel("/chat/"+$.booki.currentBookID+"/",{"command": "message_send", "message": s}, function() {} );

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
	    var chapterLocks = {};

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

		    this.refreshLocks();

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

		    this.refreshLocks();
		},

		'refresh': function() {
		    // should update status and other things also
		    $.each(this.items, function(i, v) {
			$("#item_"+v.id+"  .title").html(v.title);
			$("#item_"+v.id+" n .status").html('<a href="javascript:void(0)" onclick="$.booki.editor.editStatusForChapter('+v.id+')">'+getStatusDescription(v.status)+'</a>');
		    });

		    this.refreshLocks();
		},

		'refreshLocks': function() {
		    $.booki.debug.debug("refreshLocks");
//		    $(".extra").html("");

		    $.each(this.items, function(i, v) {
			var item = $(".edit", $("#item_"+v.id));
			item.find('.chapterLinks').show();
			item.find('.lock').hide();
		    });

		    $.each(chapterLocks, function(i, v) {
			var item = $(".edit", $("#item_"+i));
			item.find('.chapterLinks').hide();
			item.find('.lock').show();
			item.find('.lockUser').text(v);
		    });
		}
		
	    });

	    /* start of history panel */

	    function HistoryPanel(containerName) {
		this.containerName = containerName;
		this.currentView = 0;
		
		this.refresh = null;
	    }
	    
	    $.extend(HistoryPanel.prototype, {
		'_initialLoad': function() {
		    this.setHistoryView();
		},

		'setHistoryView': function() {
		    var $this = this;
		    
		    $this.currentView = 1;

		    var _page = 1;

		    function _drawItems(data) {
			var his = $($this.containerName+" SPAN.hiscontainer");
			var s = $('.historyTable.template').clone().removeClass("template");
			
			$.each(data.history, function(i, entry) {
			    var kindName = $(".eventKind.template #"+entry.kind.replace(" ", "_")).html();
			    if(entry.kind == "create" || entry.kind == "rename") {
				var en = $(".rowCreateRename.template").clone().removeClass('template');
				en.find('.entryKind').html(kindName);
				en.find('.entryChapter').html(entry.chapter);
				en.find('.entryUser').html(entry.user);
				en.find('.entryModified').html(entry.modified);
				en.find('.setChapterLink').click(function() { $this.setChapterView(entry.chapter, entry.chapter_url, entry.chapter_history); });
				s.append(en);
				
			    } else if(entry.kind == "save") {
				var en = $(".rowSave.template").clone().removeClass('template');
				en.find('.entryKind').html(kindName);
				en.find('.entryChapter').html(entry.chapter);
				en.find('.entryUser').html(entry.user);
				en.find('.entryModified').html(entry.modified);
				en.find('.setChapterLink').click(function() { $this.setChapterView(entry.chapter, entry.chapter_url, entry.chapter_history); });
				s.append(en);
			    } else if(entry.kind == "major" || entry.kind == "minor") {
				var en = $(".rowVersion.template").clone().removeClass('template');
				en.find('.entryVersion').html(entry.version);
				en.find('.entryUser').html(entry.user);
				en.find('.entryModified').html(entry.modified);
				s.append(en);
			    } else if(entry.kind == 'attachment') {
				var en = $(".rowAttachment.template").clone().removeClass('template');
				en.find('.entryFilename').html(entry.args.filename);
				en.find('.entryUser').html(entry.user);
				en.find('.entryModified').html(entry.modified);
				s.append(en);
			    } else {

				var en = $(".rowGeneric.template").clone().removeClass('template');
				en.find('.entryKind').html(kindName);
				en.find('.entryUser').html(entry.user);
				en.find('.entryModified').html(entry.modified);
				s.append(en);
			    }
			});
			his.empty();
			his.append(s);
		    }
		    
		    function _buildUI() {
			$($this.containerName).empty();
			var his = $($this.containerName);
						
			his.append("<br/>");
			his.append('<span class="hiscontainer">LOADING DATA....</span>');
			his.append("<br/>");
			his.append($('<a href="javascript:void(0)">&lt;&lt;previous</a>').click(function() {
			    if(_page < 2) return;

			    $.booki.ui.notify("Reading history data...");
			    $($this.containerName+" TABLE").css("background-color", "#f0f0f0");
			    
//			    $($this.containerName+" SPAN.hiscontainer").html("LOADING DATA...");
			    $.booki.sendToCurrentBook({"command": "get_history",
						       "page": _page-1},
						      function(data) {
							  _page = _page - 1;
							  $.booki.ui.notify();
							  _drawItems(data);
						      });
previous			    
			}));
			his.append("&nbsp;&nbsp;");
			his.append($('<a href="javascript:void(0)">next&gt;&gt;</a>').click(function() {
			    $.booki.ui.notify("Reading history data...");
			    $($this.containerName+" TABLE").css("background-color", "#f0f0f0");

//			    $($this.containerName+" SPAN.hiscontainer").html("LOADING DATA...");
			    $.booki.sendToCurrentBook({"command": "get_history",
						       "page": _page+1},
						      function(data) {
							  _page = _page + 1;
							  $.booki.ui.notify();
							  _drawItems(data);
						      });
			    
			}));


		    }

		    _buildUI();

		    $.booki.ui.notify("Reading history data...");
		    $.booki.sendToCurrentBook({"command": "get_history",
					       "page": 1},
					      function(data) {
						  $.booki.ui.notify();
						  _drawItems(data);
					      });
		    
		    this.refresh = function() {
			$.booki.ui.notify("Reading history data...");
//			$($this.containerName+" SPAN.hiscontainer").html("LOADING DATA...");
			$($this.containerName+" TABLE").css("background-color", "#f0f0f0");

			$.booki.sendToCurrentBook({"command": "get_history",
						   "page": _page},
						  function(data) {
						      $.booki.ui.notify();
						      _drawItems(data);
						  });
		    }

/*
		    $.booki.ui.notify("Reading history data...");
		    $($this.containerName).empty();

		    $.booki.sendToCurrentBook({"command": "get_history"},
					      function(data) {
						  $.booki.ui.notify();
						  
						  var his = $($this.containerName);
						  var s = $('<table width="100%"><tr><th>action</th><th></th><th>user</th><th>time</th></tr></table>')
						  
						  $.each(data.history, function(i, entry) {
						      if(entry.kind == "create" || entry.kind == "rename") {
							  var en = $("<tr></tr>");
							  en.append('<td valign="top">'+entry.kind+'</td>');
							  en.append($('<td valign="top">').append($('<a style="text-decoration: underline" href="javascript:void(0)">'+entry.chapter+"</a>").click(function() { $this.setChapterView(entry.chapter, entry.chapter_url, entry.chapter_history); })));
							  en.append('<td valign="top">'+entry.user+'</td><td valign="top" style="white-space: nowrap">'+entry.modified+"</td><td></td>");
							  s.append(en);
							  
//							  s.append($("<tr><td>"+entry.kind+'</td><td><a href="'+$.booki.getBookURL()+entry.chapter_url+'/" style="text-decoration: underline">'+entry.chapter+"</a></td><td>"+entry.user+"</td><td>"+entry.modified+"</td><td></td></tr>"));
						      } else if(entry.kind == "save") {
							  var en = $("<tr></tr>");
							  en.append('<td valign="top">'+entry.kind+"</td>");
							  en.append($('<td valign="top">').append($('<a style="text-decoration: underline" href="javascript:void(0)">'+entry.chapter+"</a>").click(function() { $this.setChapterView(entry.chapter, entry.chapter_url, entry.chapter_history); })));
							  en.append('<td valign="top">'+entry.user+'</td><td valign="top" style="white-space: nowrap">'+entry.modified+"</td><td></td>");
							  s.append(en);
						      } else if(entry.kind == "major" || entry.kind == "minor") {
							  s.append($("<tr><td>New version</td><td>Switched to "+entry.version.version+"</td><td>"+entry.user+'</td><td style="white-space: nowrap">'+entry.modified+"</td></tr>"));
						      } else if(entry.kind == 'attachment') {
							  s.append($('<tr><td>Upload</td><td valign="top">Uploaded '+entry.args.filename+".</td><td>"+entry.user+'</td><td valign="top" style="white-space: nowrap">'+entry.modified+"</td></tr>"));

						      } else {
							  s.append($("<tr><td>"+entry.kind+"</td><td></td><td>"+entry.user+'</td><td valign="top" style="white-space: nowrap">'+entry.modified+"</td></tr>"));
						      }
						  });
						  
						  his.html("<br/>");
						  his.append(s);
					      });
                    */
		},
		
		'setRevisionView': function(chapterName, chapterURL, chapterHistory, revision) {
		    var $this=this;
		    this.refresh = null;

		    function showRevision(data) {
			var his = $($this.containerName);
			
			his.empty();

			var disp = $('.revisionDisplay.template').clone().removeClass('template');
			disp.find('.buttonset').buttonset();
			disp.find('.button').button();
			disp.find('.backLink').click(function() { $this.setChapterView(chapterName, chapterURL, chapterHistory);});

			disp.find('.revertLink').click(function() { 
			    $(".cont", his).html('<div title="Revert to this revision?"><p><span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>Current chapter content will be reverted to this revision. Are you sure?</p></div>');
			    
			    cancel = $('.strings.template .cancel').text();
			    yesrevert = $('.strings.template .yesrevert').text();
			    
			    $(".cont DIV", his).dialog({
				resizable: false,
				height:160,
				modal: true,
				buttons: [
				    { text: yesrevert,
				      click: function() {
					var $dialog = $(this);
					$.booki.sendToCurrentBook({"command": "revert_revision", 
								   "chapter": chapterURL,
								   "revision": data['revision']},
								  function(data) {
								      $.booki.ui.notify();
								      $dialog.dialog('close');
								      $this.setChapterView(chapterName, chapterURL, chapterHistory);
								  });
				      }},
				    { text: cancel,
				      click: function() {
					$(this).dialog('close');
				      }},
				]
			    });
			});
		

			if(!data.chapter) {
			    disp.find('.err-no-revision').show();
			    disp.find('.revision-info').hide();
			    return;
			} else {
			    disp.find('.err-no-revision').hide();
			    disp.find('.revision-info').show();
			}
			
			$("#radio1", disp).click(function() { 
			    $('#chapterrevision', his).html(data.content);
			    
			});
			$("#radio2", disp).click(function() { 
			    $('#chapterrevision', his).html('<textarea style="width: 95%; height: 400px">'+data.content+'</textarea>');
			    
			});

			$("#radio1", disp).attr("checked", "checked");
			
			disp.find('.chapterName').html(chapterName);

			disp.find('.dataUser').html(data.user);
			disp.find('.dataModified').html(data.modified);
			disp.find('.dataVersion').html(data.version);
			disp.find('.dataRevision').html(data.revision);
			if(data.comment) {
			    disp.find('.revisiondCcomment').show();
			    disp.find('.dataComment').html(data.comment);
			} else {
			    disp.find('.revisionComment').hide();
			}

			if(data['revision'] > 1)  {
			    disp.find('.previousLinkDisplay').show();
			    disp.find('.previousLink').click(function() {
				$.booki.ui.notify("Reading history data...");
				$.booki.sendToCurrentBook({"command": "get_chapter_revision", 
							   "chapter": chapterURL,
							   "revision": data['revision']-1},
							  function(data) {
							      $.booki.ui.notify();
							      showRevision(data);
							  });
			    });
			} else {
			    disp.find('.previousLinkDisplay').hide();
			}
			
			disp.find('.nextLink').click(function() {
			    $.booki.ui.notify("Reading history data...");
			    $.booki.sendToCurrentBook({"command": "get_chapter_revision", 
						       "chapter": chapterURL,
						       "revision": data['revision']+1},
						      function(data) {
							  $.booki.ui.notify();
							  if(data.chapter)
							      showRevision(data);
						      });
			});

			disp.find('.dataContent').html(data.content);

			his.append(disp);
		    }
		    
		    $.booki.ui.notify("Reading history data...");
		    $($this.containerName).empty();

		    $.booki.sendToCurrentBook({"command": "get_chapter_revision", 
					       "chapter": chapterURL,
					       "revision": revision},
					      function(data) {
						  $.booki.ui.notify();
						  showRevision(data);
					      });

		    $this.currentView = 3;
		},

		// obsolete code for now
		'setCompareView': function(chapterName, chapterURL, chapterHistory, revision1, revision2) {
		    var $this=this;
		    this.refresh = null;


		    function showDiff(data) {
			var his = $($this.containerName);
			his.empty();

			var disp = $('.diffDisplay.template').clone().removeClass('template');

			disp.find('.backLink').click(function() { $this.setChapterView(chapterName, chapterURL, chapterHistory);});
			disp.find('.revision1Name').html(revision1);
			disp.find('.revision2Name').html(revision2);
			disp.find('.dataOutput').html(data.output);
			//disp.find('.dataOutput').html(unescapeHtml(data.output));

			disp.find("A[name=side]").button().click(function() {
				$('#newdiff').dialog('open');
				
				// TODO:
				// this has to change, so it can be localized
				$("#newdiff .diffcontent").html("Loading data. Please wait...");

				$.booki.ui.notify("Reading history data...");

				$.booki.sendToCurrentBook({"command": "chapter_diff_parallel", 
					    "chapter": chapterURL,
					    "revision1": revision1,
					    "revision2": revision2},
				    function(data) {
					$.booki.ui.notify();

					$("#newdiff .diffcontent").html(data.output);
				    });
				
			    });


			his.append(disp);
		    }
		    
		    $.booki.ui.notify("Reading history data...");
		    $($this.containerName).empty();

		    $.booki.sendToCurrentBook({"command": "chapter_diff", 
					       "chapter": chapterURL,
					       "revision1": revision1,
					       "revision2": revision2},
					      function(data) {
						  $.booki.ui.notify();
						  showDiff(data);
					      });



		    $this.currentView = 4;
		},


		'setChapterView': function(chapterName, chapterURL, chapterHistory) {
		    var $this=this;
		    this.refresh = null;

		    $.booki.ui.notify("Reading history data...");

		    $($this.containerName).empty();

		    $.booki.sendToCurrentBook({"command": "get_chapter_history", "chapter": chapterURL},
					      function(data) {
						  $.booki.ui.notify();
						  
						  var his = $($this.containerName);

						  his.empty();

						  disp = $('.historyDisplay.template').clone().removeClass('template');

						  disp.find('.backLink').click(function() { $this.setHistoryView();});
						  disp.find('.button').button();
						  disp.find('.compareLink').click(function() {
						      var revision1 = $('input[name=group1]:checked', his).val();
						      var revision2 = $('input[name=group2]:checked', his).val();

						      // new diff interface
						      if(revision1 && revision2) {
							  $('#newdiff').dialog('open');
				
							  // TODO:
							  // this has to change, so it can be localized
							  $("#newdiff .diffcontent").html("Loading data. Please wait...");

							  $.booki.ui.notify("Reading history data...");

							  $.booki.sendToCurrentBook({"command": "chapter_diff_parallel", 
								      "chapter": chapterURL,
								      "revision1": revision1,
								      "revision2": revision2},
							      function(data) {
								  $.booki.ui.notify();
								  
								  $("#newdiff .diffcontent").html(data.output);
							      });
							  
						      }
						      // old stuff
						      //$this.setCompareView(chapterName, chapterURL, chapterHistory, revision1, revision2);
						  });

						  disp.find('.chapterName').html(chapterName);

						  var s = disp.find('.chapterHistoryTable');

						  var max_revision = -1;
						  $.each(data.history, function(i, entry) {
							  if(entry.revision > max_revision) max_revision = entry.revision;

							  var en = $("<tr></tr>");
							  en.append('<td align="center" valign="top"><input type="radio" name="group1" value="'+entry.revision+'"/><input type="radio" name="group2" value="'+entry.revision+'"/></td>');
							  //						      en.append('<td align="center"><a href="" style="text-decoration: underline">'+i+'</a></td>');
							  
							  en.append(
								    $('<td align="center" valign="top"></td>').append(
							      $('<a href="javascript:void(0)" style="text-decoration: underline">'+entry.revision+'</a>').click(
								  function() { 
								      if(entry.user != '')
									  $this.setRevisionView(chapterName, chapterURL, chapterHistory, entry.revision);
								  })
							  )
						      );

						      en.append('<td align="left" valign="top">'+entry.user+'</td><td align="left" valign="top" style="white-space: nowrap">'+entry.modified+'</td><td valign="top">'+entry.comment+"</td>");
						      s.append(en);

						      s.find("[name=group1]").filter("[value="+(max_revision-1)+"]").attr("checked","checked");
						      s.find("[name=group2]").filter("[value="+(max_revision)+"]").attr("checked","checked");

						      
						  });

						  his.append(disp);
						  

						  $this.currentView = 2;
					      });
		},
		
		'active': function() {
		    if(this.currentView == 0)
			this._initialLoad();
		    
		    
		    if(this.refresh)
			this.refresh();

		},
		
		'initPanel': function() {
		    var $this = this;
		}
	    });

	    /* end of history panel */

	    var toc = new TOC("#chapterslist");
	    var holdChapters = new TOC("#holdchapterslist");

	    var historyPanel = new HistoryPanel("#historycontainer");
	    
	    function getChapter(chapterID) {
		var chap = toc.getItemById(chapterID);
		if(!chap)
		    chap = holdChapters.getItemById(chapterID);
		return chap;
	    }

	    var _isEditingSmall = false;
	    
	    function makeSectionLine(chapterID, name) {
		var line = $('.sectionLine.template').clone().removeClass('template');
		line.attr('id', 'item_'+chapterID);
		line.find('.title').text(name);
		return line;
	    }
	    
	    function makeChapterLine(chapterID, name, status) {
		var line = $('.chapterLine.template').clone().removeClass('template');
		line.attr('id', 'item_'+chapterID);
		line.find('.title').text(name);
		line.find('.editLink').click(function() {
		    $.booki.editor.editChapter(chapterID);
		});
		line.find('.viewLink').click(function() {
		    $.booki.editor.viewChapter(chapterID);
		});
		line.find('.unlockLink').click(function() {
		    $.booki.editor.unlockChapter(chapterID);
		});
		line.find('.statusLink').click(function() {
		    $.booki.editor.editStatusForChapter(chapterID);
		});
		var statusName = $(".bookStatuses.template #"+status.replace(" ", "_")).html();
		line.find('.statusName').html(statusName);

		line.dblclick(function() {
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
			    toc.refreshLocks();
			    holdChapters.refreshLocks();
			});
			$("#item_"+chapterID).replaceWith(makeChapterLine(chapterID, newName, status)); 
			toc.refreshLocks();
			holdChapters.refreshLocks();
		    }));
		    $("FORM", $(this)).append($('<span> </span>').html());
                    $("FORM", $(this)).append($('<a href="#">CANCEL</a>').click(function() { 
			_isEditingSmall = false; $.booki.ui.notify("Sending data...");
			$.booki.sendToCurrentBook({"command": "chapter_status", "status": "normal", "chapterID": chapterID}, function() {$.booki.ui.notify(""); toc.refreshLocks(); holdChapters.refreshLocks(); } );
			
			// this is not god. should get info from toc
			var ch = getChapter(chapterID);
			$("#item_"+chapterID).replaceWith(makeChapterLine(chapterID, ch.title, getStatusDescription(ch.status)));  }));
		    
		    toc.refreshLocks();
		    holdChapters.refreshLocks();
		    });
		return line;
	    }
	    
	    function closeEditor() {
		currentlyEditing = null;

		$("#editor").fadeOut("slow",
				     function() {
					 $("#editor").css("display", "none");
                                         $("#container").hide().css("display", "block"); 

					 toc.refreshLocks();
					 holdChapters.refresh();
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

			$.booki.ui.notify("Saving data...");

			$.booki.sendToCurrentBook({"command": "change_status",
						   "chapterID": chapterID,
						   "statusID": chap.status},
						  function(data) {
						      $.booki.ui.notify();
						  });
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

		unlockChapter: function(chapterID) {
		    $.booki.sendToCurrentBook({"command": "unlock_chapter", "chapterID": chapterID}, 
					      function(data) {
					      });
		},
		viewChapter: function(chapterID) {
		    $.booki.ui.notify("Loading chapter data...");
		    $.booki.sendToCurrentBook({"command": "get_chapter", "chapterID": chapterID, "lock": false, "revisions": true}, 
					      function(data) {
						  $.booki.ui.notify();

						  var $dialog = $('<div><div class="hdr" style="border-bottom: 1px solid #c0c0c0; padding-bottom: 5px;"></div><div class="cnt"></div></div>');

						  $dialog.find('.hdr').html('<form onsubmit="return false" action="javascript:void(0)">Revision: <select>'+$.map(data['revisions'], function(i, n) { return '<option value="'+i+'">'+i+'</option>'}).join('')+'</select></form>');
						  $dialog.find('.hdr').find('OPTION[value="'+data['current_revision']+'"]').attr('selected', 'selected');

						  $dialog.find('.hdr').find('SELECT').change(function() {
							  $.booki.ui.notify("Loading chapter data...");
							  rev = parseInt($(this).val());
							  $.booki.sendToCurrentBook({"command": "get_chapter", "chapterID": chapterID, "revision": rev, "lock": false, "revisions": false}, 
										    function(data2) {
											$.booki.ui.notify();
											$dialog.find('.cnt').html(data2.content);
										    });
							     
						      });

						  $dialog.find('.cnt').html(data.content);

						  $dialog.dialog({
							      autoOpen: false,
							      modal: false,
							      title: 'Booki Reader', // Must translate this
							      height: 530,
							      width:  600
							  });
						  $dialog.dialog('open');
					      });	
		},
		editChapter: function(chapterID) {
		    $.booki.ui.notify("Loading chapter data...");
		    $.booki.sendToCurrentBook({"command": "get_chapter", "chapterID": chapterID}, function(data) {
					      $.booki.ui.notify();
					      $("#container").fadeOut("slow", function() {
						  
						  $("#container").css("display", "none");
						  $("#editor").css("display", "block").fadeIn("slow");

						  /* xinha */
						  xinha_init(); 

						  function _sendNotification() {						      
						      if(currentlyEditing != null) {
							  $.booki.sendToCurrentBook({"command": "book_notification",
										     "chapterID": chapterID},
										    function(data) {
											if(data.kill == 'please') {
											    $.booki.sendToCurrentBook({"command": "chapter_status", "status": "normal", "chapterID": chapterID});
											    delete chapterLocks[chapterID];
											    closeEditor();
											}
										    });
										    
							  setTimeout(_sendNotification, 5000);
						      }
						  }
						  
						  function _tryAgain() {
						      var edi = xinha_editors.myTextArea; 
						      if(edi) {
							  edi.whenDocReady(function() {
							      edi.setEditorContent(data.content);

							      currentlyEditing = chapterID;

							      // start sending edit notifications to server
							      setTimeout(_sendNotification, 5000);
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
						  $("#editor .title").html(data.title); 
						  
   						  $("#editor A[name=chapter_id]").attr("value", chapterID);
						  $("#editor A[name=save]").unbind('click').click(function() {
						      // todo: temp remove this
						      //currentlyEditing = chapterID;
					              var edi = xinha_editors["myTextArea"]; 
                                                      var content = edi.getEditorContent();
						      
						      /*
                                                      comment out spalato

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
*/

/*
older version of spalato
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

/*
comment out spalato
						      if(chapters_n > 1) {
							  $("#spalatodialog").dialog("open");
						      } else {
*/
							  $.booki.ui.notify("Sending data...");
							  var minor = $("#editor INPUT[name=minor]").is(":checked");
							  var comment = $("#editor INPUT[name=comment]").val();
							  var author = $("#editor INPUT[name=author]").val();
							  var authorcomment = $("#editor INPUT[name=authorcomment]").val();

 							  $.booki.sendToCurrentBook({"command": "chapter_save", 
										     "chapterID": chapterID,
										     "content": content,
										     "minor": minor,
										     "continue": false,
										     "comment": comment,
										     "author": author,
										     "authorcomment": authorcomment
										    },
										    function() { 
											delete chapterLocks[chapterID];
											$.booki.ui.notify(); 
											closeEditor(); 
											$("#editor INPUT[name=comment]").val(""); 
											$("#editor INPUT[name=author]").val(""); 
											$("#editor INPUT[name=authorcomment]").val(""); } );
						   // comment out spalato   }

						  });

						  $("#editor A[name=savecontinue]").unbind('click').click(function() {
						      // todo: temp remove this
						      //currentlyEditing = chapterID;
					              var edi = xinha_editors["myTextArea"]; 
                                                      var content = edi.getEditorContent();
						      
						      $.booki.ui.notify("Sending data...");
						      var comment = $("#editor INPUT[name=comment]").val();

						      var author = $("#editor INPUT[name=author]").val();
						      var authorcomment = $("#editor INPUT[name=authorcomment]").val();
						      
 						      $.booki.sendToCurrentBook({"command": "chapter_save", 
										 "chapterID": chapterID,
										 "content": content,
										 "minor": false,
										 "continue": true,
										 "comment": comment,
										 "author": author,
										 "authorcomment": authorcomment
										},
										function() {$.booki.ui.notify(); $("#editor INPUT[name=comment]").val(""); $("#editor INPUT[name=author]").val(""); $("#editor INPUT[name=authorcomment]").val(""); } );
						  });

						  /* temporary */
						  $("#editor A[name=view]").unbind('click').click(function() {
							  $.booki.ui.notify("Loading chapter data...");
							  $.booki.sendToCurrentBook({"command": "get_chapter", "chapterID": chapterID, "lock": false, "revisions": true}, 
										    function(data) {
											$.booki.ui.notify();

											var $dialog = $('<div><div class="hdr" style="border-bottom: 1px solid #c0c0c0; padding-bottom: 5px;"></div><div class="cnt"></div></div>');
											
											$dialog.find('.hdr').html('<form onsubmit="return false" action="javascript:void(0)">Revision: <select>'+$.map(data['revisions'], function(i, n) { return '<option value="'+i+'">'+i+'</option>'}).join('')+'</select></form>');
											$dialog.find('.hdr').find('OPTION[value="'+data['current_revision']+'"]').attr('selected', 'selected');
											
											$dialog.find('.hdr').find('SELECT').change(function() {
												$.booki.ui.notify("Loading chapter data...");
												rev = parseInt($(this).val());
												$.booki.sendToCurrentBook({"command": "get_chapter", "chapterID": chapterID, "revision": rev, "lock": false, "revisions": false}, 
															  function(data2) {
															      $.booki.ui.notify();
															      $dialog.find('.cnt').html(data2.content);
															  });
												
											    });
											
											$dialog.find('.cnt').html(data.content);
											
											$dialog.dialog({
												autoOpen: false,
												    modal: false,
												    title: 'Booki Reader', // Must translate this
												    height: 530,
												    width:  600
												    });
											$dialog.dialog('open');
										    });	

						      });

						  $("#editor A[name=cancel]").unbind('click').click(function() {
						      $.booki.sendToCurrentBook({"command": "chapter_status", "status": "normal", "chapterID": chapterID},
										function() {});
						      delete chapterLocks[chapterID];
						      closeEditor();
						  });  
					      });
					  });
		},

		/* should this stay here? */

		showAdvancedPublishCSS: function(mode) {
		    // url ili custom
		    if(mode.value == "url") {
			$("#csscustom").html('URL: <input type="text" name="cssurl" size="30">');
		    }

		    if(mode.value == "custom") {



			$("#csscustom").html('Custom CSS:<br><textarea cols="50" rows="20" name="csscustom"> \
body {\n\
  font-family: "Gillius ADF";\n\
  background: #fff;\n\
  color: #000;\n\
}\n\
\n\
.unseen{\n\
  z-index: -66;\n\
  margin-left: -1000pt;\n\
}\n\
\n\
.objavi-chapter{\n\
  color: #000;\n\
}\n\
\n\
h1 .initial{\n\
  color: #000;\n\
  font-size: 2em;\n\
}\n\
\n\
.objavi-subsection{\n\
  display: block;\n\
  page-break-before: always;\n\
/*  page-break-after: always;*/\n\
  text-transform: uppercase;\n\
  font-size: 20pt;\n\
}\n\
\n\
body .objavi-subsection:first-child{\n\
  page-break-before: avoid;\n\
}\n\
\n\
.objavi-subsection .initial {\n\
  font-size: 1em;\n\
  color: #000;\n\
}\n\
\n\
.objavi-subsection-heading{\n\
  font-size: 36pt;\n\
  font-weight: bold;\n\
}\n\
\n\
h1 {\n\
  text-transform: uppercase;\n\
  page-break-before: always;\n\
  background: white;\n\
}\n\
\n\
/*h1.first-heading {\n\
  page-break-before: avoid;\n\
}*/\n\
\n\
h2 {\n\
  text-transform: uppercase;\n\
}\n\
\n\
table {\n\
  float: none;\n\
}\n\
\n\
h1.frontpage{\n\
  font-size: 64pt;\n\
  text-align: center;\n\
  page-break-after: always;\n\
  page-break-before: avoid;\n\
  max-width: 700px;\n\
}\n\
\n\
div.copyright{\n\
  padding: 1em;\n\
}\n\
\n\
table.toc {\n\
  /*border: 1px dotted #999;*/\n\
  font-size: 17pt;\n\
  width: 95%;\n\
}\n\
\n\
td.chapter {\n\
  padding-left: 2em;\n\
  text-align: right;\n\
}\n\
\n\
td.pagenumber {\n\
  text-align: right;\n\
}\n\
\n\
td.section {\n\
  font-size: 1.1em;\n\
  text-transform: uppercase;\n\
  font-weight: bold;\n\
}\n\
\n\
p, ul, ol {\n\
  page-break-inside: avoid;\n\
}\n\
\n\
pre, code, tt {\n\
  font-family: "Courier", "Courier New", monospace;\n\
  font-size: 0.8em;\n\
}\n\
\n\
pre {\n\
  max-width:700px;\n\
  overflow: hidden;\n\
}\n\
\n\
img {\n\
  max-width: 700px;\n\
  height: auto;\n\
}\n\
</textarea>');

		    }

		    if(mode.value == "default") {
			$("#csscustom").html("");
		    }
		},

		showAdvancedPublishOptions: function(flag) {
		    if(flag) {
			$("#advancedswitch").html('<a href="javascript:void(0)" onclick="$.booki.editor.showAdvancedPublishOptions(false)">Hide advanced options</a>');

			$("#advanced", $("#tabpublish")).css("display", "block");
		    } else {
			$("#advanced", $("#tabpublish")).css("display", "none");

			$("#advancedswitch").html('<a href="javascript:void(0)" onclick="$.booki.editor.showAdvancedPublishOptions(true)">Show advanced options</a>');
		    }
		},


		showSettingsTab: function() {
		    $.booki.ui.notify("Reading settings data...");

		    $("#tabsettings A[name=license]").button("option", "disabled", true);
		    $("#tabsettings A[name=language]").button("option", "disabled", true);
		    $("#tabsettings A[name=roles]").button("option", "disabled", true);

		    $.booki.sendToCurrentBook({"command": "settings_options"},
					      function(data) {
						  $.booki.ui.notify();
						  $("#tabsettings A[name=license]").button("option", "disabled", false);
						  $("#tabsettings A[name=language]").button("option", "disabled", false);
						  $("#tabsettings A[name=roles]").button("option", "disabled", false);

						  var s = $.map(data['licenses'], function(i, n) { return '<option value="'+i[0]+'">'+i[1]+'</option>';}).join('');
						  $("#tabsettings SELECT[name='licen']").html(s);

						  $("#tabsettings SELECT[name='licen']").find('OPTION[value="'+data['current_licence']+'"]').attr('selected', 'selected');


						  var s2 = $.map(data['languages'], function(i, n) { return '<option value="'+i[0]+'">'+i[1]+'</option>';}).join('');
						  $("#tabsettings SELECT[name='lang']").html(s2);

						  $("#tabsettings SELECT[name='lang']").find('OPTION[value="'+data['current_language']+'"]').attr('selected', 'selected');

						  if(data['rtl'] == "RTL")
						      $("#tabsettings INPUT[name=rtl]").attr('checked', 'checked');

					      });

		},

		showAttachmentsTab: function() {
		    $.booki.ui.notify("Reading attachments data...");
		    $.booki.sendToCurrentBook({"command": "attachments_list"},
					      function(data) {
						  $.booki.ui.notify();

						  var att_html = $("#attachmentscontainer");
						  var s = $('.attachmentsTable.template').clone().removeClass('template');
						  $.each(data.attachments, function(i, entry) {
						      s.append('<tr><td width="30"><input type="checkbox" name="'+entry.id+'" value="'+entry.name+'"></td><td><a style="text-decoration: underline" href="'+$.booki.utils.linkToAttachment($.booki.currentBookURL, entry.name)+'" target="_new">'+entry.name+'</a></td><td>'+$.booki.utils.formatDimension(entry.dimension)+'</td><td>'+$.booki.utils.formatSize(entry.size)+'</td><td>'+entry.created+'</td></tr>');
						  });
						  att_html.empty().append(s);
					      });
		},

		// INIT UI INTERFACE

		_initSettingsUI: function() {
		    $("#tabsettings A[name=roles]").button().click(function() {
			    $.booki.sendToCurrentBook({"command": "roles_init"},
						      function(data) {
							  var dial = $('.rolesDialog.template').clone().removeClass("template");
							  var s = $.map(data['users'], function(i, n) { return '<option value="'+i[0]+'">'+i[1]+'</option>';}).join('');

							  dial.find("SELECT[name=users]").html(s);
							  dial.find("SELECT[name=users]").change(function() {
								  dial.find("A[name=removeuser]").button("option", "disabled", false);
							      });

							  dial.find("A[name=adduser]").button().click(function() {
								  var inp = dial.find("INPUT[name=newuser]").val();
								  if(inp.replace(/^\s+|\s+$/g, '') == '') return;

								  var username = inp.split(" ")[0];

								  dial.find("SELECT[name=users]").append('<option value="'+username+'">'+inp+'</option>');
								  dial.find("INPUT[name=newuser]").val("")
							      });

							  dial.find("A[name=removeuser]").button().click(function() {
								  var el = dial.find("SELECT[name=users] OPTION:selected");
								  if(el.html().indexOf("[owner]") == -1) {
								      el.remove();
								      $(this).button("option", "disabled", true);
								  }
							  
							      });
							  
							  dial.find("INPUT[name=newuser]").autocomplete({
								  source: function(request, callback) {
								      $.booki.sendToCurrentBook({"command": "users_suggest",
										  "possible_user": request.term},
									  function(data) {
									      callback(data.possible_users);
									  });
								  },
								      minLength: 2,
								      select: function( event, ui ) {
								  }
							      });

							  dial.find("A[name=removeuser]").button("option", "disabled", true);

							  dial.dialog({modal: true,
								      width: 600, 
								      buttons: {
								      "Save changes": function() {
									  var $d = $(this);
									  var roleUsers = dial.find("SELECT[name=users]").children().map(function(){if($(this).html().indexOf("[owner]") == -1) return $(this).val(); return null;}).get();

									  $.booki.sendToCurrentBook({"command": "roles_save",
										      "role_name": "Administrator",
										      "users": roleUsers},
									  function(data) {
									      $d.dialog('close');
									  });
								      },
									  "Cancel": function() {
									      $(this).dialog('close');
									  }
								  }
							      });
						      });

			});
		    
		    $("#tabsettings A[name=language]").button().click(function() {
			    $.booki.sendToCurrentBook({'command': 'settings_language_save',
						       'rtl': $("#tabsettings INPUT[name=rtl]").is(':checked'),
						       'language': $("#tabsettings SELECT[name='lang'] OPTION:selected").val(),
				}, 
				function(data) {
				});
			    
  		    });

		    $("#tabsettings A[name=attribution]").button().click(function() {
			    var dial = $('.copyrightAttribution.template').clone().removeClass("template");

			    $.booki.sendToCurrentBook({'command': 'license_attributions'}, 
						      function(data) {
							  var s = $.map(data['users'], 
									function(i, n) { 
									    return '<option value="'+i[0]+'">'+i[0]+'  ('+i[1]+')</option>';
									}).join('');

							  var s2 = $.map(data['users_exclude'], 
									 function(i, n) { 
									     return '<option value="'+i[0]+'">'+i[0]+'  ('+i[1]+')</option>';
									 }).join('');

							  dial.find("SELECT[name=available]").html(s);
							  dial.find("SELECT[name=excluded]").html(s2);
							  
							  dial.find("A[name=add]").button().click(function() {
								  var el = dial.find("SELECT[name=available] OPTION:selected");
								  dial.find("SELECT[name=excluded]").append(el.clone());
								  el.remove();
							      });

							  dial.find("A[name=remove]").button().click(function() {
								  var el = dial.find("SELECT[name=excluded] OPTION:selected");
								  dial.find("SELECT[name=available]").append(el.clone());
								  el.remove();
								  });

							  dial.dialog({modal: true,
								      width: 700,
								      buttons: {
								      "Save changes": function() {
									  var $d = $(this);
									  var excludedUsers = dial.find("SELECT[name=excluded]").children().map(function(){return $(this).val()}).get();
									  $.booki.sendToCurrentBook({'command': 'license_attributions_save',
 	   									                     'excluded_users': excludedUsers}, 
												    function(data) {
													$d.dialog('close');
												    });
								      },
								      "Cancel": function() {
								          $(this).dialog('close');
								      }
								  }
							      });
						      });
			    
			});

		    $("#tabsettings A[name=license]").button().click(function() {
			    var $b = $(this);
			    $b.button("option", "disabled", true);
			    $.booki.ui.notify("Saving data. Please wait...");

			    $.booki.sendToCurrentBook({'command': 'license_save', 
						       'license': $("#tabsettings SELECT[name=licen]").val() },
				function(data) {
				    $b.button("option", "disabled", false);
				    $.booki.ui.notify();

				});

			});
		    $("#tabsettings A[name=readlicense]").click(function() {

			    var $d = $('<div title="'+$("#tabsettings SELECT[name=licen]").val()+'"><iframe width="98%" height="98%"></iframe></div>').dialog({width: 800, height: 400, 
                                          modal: true,
                                          buttons: {
              				        Ok: function() {
					             $( this ).dialog( "close" );
				                   }
				          }
				});
			    switch($("#tabsettings SELECT[name=licen]").val()) {
  			    case "CC - O":
    			       $d.find('iframe').attr("src", "http://creativecommons.org/publicdomain/zero/1.0/"); 
			       break;
  			    case "CC-BY":
    			       $d.find('iframe').attr("src", "http://creativecommons.org/licenses/by/2.0/"); 
			       break;
  			    case "CC-BY-SA":
    			       $d.find('iframe').attr("src", "http://creativecommons.org/licenses/by-sa/2.0/"); 
			       break;
  			    case "GPL":
    			       $d.find('iframe').attr("src", "http://www.gnu.org/licenses/gpl.html"); 
			       break;
  			    case "MIT":
    			       $d.find('iframe').attr("src", "http://www.opensource.org/licenses/mit-license.php"); 
			       break;
  			    case "Public Domain":
    			       $d.find('iframe').attr("src", "http://creativecommons.org/licenses/publicdomain/"); 
			       break;


			    }
			});
		    
		},
		
		_initUI: function() {
		    $("#inserttabs").tabs();
		    
		    $("#tabs").tabs();
		    $('#tabs').bind('tabsselect', function(event, ui) { 
			if(ui.panel.id == "tabnotes") {
			    $.booki.ui.notify("Reading notes data...");
			    $.booki.sendToCurrentBook({"command": "get_notes"},
						      function(data) {
							  $.booki.ui.notify();
							  $.booki.debug.debug(data.notes);

							  var notes_html = $("#tabnotes .notes");
							  var s = "";

							  $.each(data.notes, function(i, entry) {
							      $.booki.debug.debug(entry);
							      s += entry.notes;
							  });
							  notes_html.val(s);
							  //alert(s);
						      });

			}
			
			if(ui.panel.id == "tabattachments") {
			    $.booki.editor.showAttachmentsTab();
			}

			if(ui.panel.id == "tabsettings") {
			    $.booki.editor.showSettingsTab();
			}

			if(ui.panel.id == "tabversions") {
			    $.booki.ui.notify("Reading version data...");
			    $.booki.sendToCurrentBook({"command": "get_versions"},
						      function(data) {
							  $.booki.ui.notify();
							  s = '';
							  
							  $.each(data.versions, function(i, entry) {
							      function getVersionName(e) {
								  var v = e.major+'.'+e.minor;

								  if(e.name && e.name != '')
								      v += '  ('+e.name+')  ';
								  
								  return v;
							      }

							      // there should be a function for this things
							      var d = new Date(entry.created);
							      // koliko je ovo sati

							      var razlika = Math.ceil((Date.now()-d.getTime())/(1000*60));
							      $.booki.debug.debug(entry.created);
							      $.booki.debug.debug(d.toString());
							      s += '<li><a target="_new" href="'+$.booki.getBookURL(entry.major+'.'+entry.minor)+'">'+getVersionName(entry)+'   </a></li>';
							  });
							  
							  $("#tabversions .list").html("<ul>"+s+"</ul>");
								 
						      }
						      );

			}

			if(ui.panel.id == "tabhistory") {
			    historyPanel.active();
			}
		    });

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
							      function() {$.booki.ui.notify();  toc.refreshLocks(); holdChapters.refreshLocks(); } );
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
						      function() {$.booki.ui.notify();  toc.refreshLocks(); holdChapters.refreshLocks();} );
			}
/*
				$.booki.sendToCurrentBook({"command": "chapters_changed", "chapters": result}, function() {$.booki.ui.notify()} );
*/

		    }, 'placeholder': 'ui-state-highlight', 'scroll': true}).disableSelection();


		    $.booki.chat.initChat($("#chat"), $("#chat2"));

		    $("#tabnotes BUTTON").click(function() {
			var new_notes = $("#tabnotes FORM TEXTAREA[name='notes']").val();
			$("#tabnotes BUTTON").attr("disabled", "disabled");
			var message = "Saving the book notes";
			$("#tabnotes .info").html('<div style="padding-top: 20px; padding-bottom: 20px;">'+message+'</div>');

			$.booki.sendToCurrentBook({"command": "notes_save", 'notes': new_notes },
						  
                                                  function(data) {
						      var message = "Book notes saved.";

                                                      $("#tabnotes BUTTON").removeAttr("disabled");
							
                                                      $("#tabnotes .info").html('<div style="padding-top: 20px; padding-bottom: 10px">'+message+'</div>');

                                                      $.booki.debug.debug(data);
                                                      $.booki.ui.notify();
                                                  } );
                    });


                    $("#tabpublish BUTTON").click(function() {
			/* default options */
			var bookTitle = $("#tabpublish FORM INPUT[name='title']").val();
			var bookLicense = $("#tabpublish FORM SELECT[name='license']").val();
			var bookISBN = $("#tabpublish FORM INPUT[name='isbn']").val();
			var bookHeader = $("#tabpublish FORM INPUT[name='toc_header']").val();
			var bookSize = $("#tabpublish FORM SELECT[name='booksize']").val();
			var bookPageWidth = $("#tabpublish FORM INPUT[name='page_width']").val();
			var bookPageHeight = $("#tabpublish FORM INPUT[name='page_height']").val();
			var bookTopMargin = $("#tabpublish FORM INPUT[name='top_margin']").val();
			var bookSideMargin = $("#tabpublish FORM INPUT[name='side_margin']").val();
			var bookBottomMargin = $("#tabpublish FORM INPUT[name='bottom_margin']").val();
			var bookGutter = $("#tabpublish FORM INPUT[name='gutter']").val();
			var bookColumns = $("#tabpublish FORM INPUT[name='columns']").val();
			var bookColumnMargin = $("#tabpublish FORM INPUT[name='column_margin']").val();
			var bookCss = '';

			var isGreyscale = $("#tabpublish FORM INPUT[name='grey_scale']").is(":checked");
			
			var isArchive = $("#tabpublish FORM INPUT[name='archiveorg']").is(":checked");
			var publishMode = $("#tabpublish OPTION:selected").val();

			switch($("#tabpublish FORM SELECT[name='css']").val()) {
			case 'url':
			    bookCss = $("#tabpublish FORM INPUT[name='cssurl']").val();
			    break;
			case 'custom':
			    bookCss = $("#tabpublish FORM TEXTAREA[name='csscustom']").val();
			    break;
			}


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
						   "publish_mode": publishMode,
						   'title': bookTitle,
						   'license': bookLicense,
						   'isbn': bookISBN,
						   'toc_header': bookHeader,
						   'booksize': bookSize,
						   'page_width': bookPageWidth,
						   'page_height': bookPageHeight,
						   'top_margin': bookTopMargin,
						   'side_margin': bookSideMargin,
						   'gutter': bookGutter,
						   'columns': bookColumns,
						   'column_margin': bookColumnMargin,
						   'grey_scale': isGreyscale,
						   'css': bookCss
						  },
						  
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

		    $("#tabversions .version A").button();
		   
		    $("#tabversions .version A.major").click(function() {
			$("#newversionmajor").dialog('open');
		    });

		    $("#tabversions .version A.minor").click(function() {
			$("#newversionminor").dialog('open');
		    });

		    $("#newversionmajor").dialog({
			bgiframe: true,
			autoOpen: false,
			height: 350,
		        width: 400, 
			modal: true,
			buttons: {
			    'Create  major version': function() {
				jQuery.booki.sendToCurrentBook({"command": "create_major_version",
								"name": $("INPUT", $(this)).val(),
								"description": $("TEXTAREA", $(this)).val()
							       },
							       function(data) {
								   $.booki.ui.notify();
								   window.location = $.booki.getBookURL(data.version)+'_edit/';
							       });

				    $(this).dialog('close');
				},
				'Cancel': function() {
					$(this).dialog('close');
				}
			},
			open: function(event,ui) {
			    $("INPUT", $(this)).val("").select();
			},
			close: function() {
			    
			}
		    });

		    $("#newversionminor").dialog({
			bgiframe: true,
			autoOpen: false,
			height: 350,
		        width: 400, 
			modal: true,
			buttons: {
			    'Create minor version': function() {
				jQuery.booki.sendToCurrentBook({"command": "create_minor_version",
								"name": $("INPUT", $(this)).val(),
								"description": $("TEXTAREA", $(this)).val()
							       },
							       function(data) {
								   $.booki.ui.notify();
								   window.location = $.booki.getBookURL(data.version)+'_edit/';
							       });
				
				$(this).dialog('close');
				},
				'Cancel': function() {
					$(this).dialog('close');
				}
			},
			open: function(event,ui) {
			    $("INPUT", $(this)).val("").select();
			},
			close: function() {
			    
			}
		    });
		    		    
		    $("#editor A").button();

		    // init Settings UI
		    this._initSettingsUI();

		    // TAB ATTACHMENTS
		    $("#tabattachments A[name=delete]").button().click(function() {
			var ids = new Array();
			var names = '';

			$.each($("#tabattachments INPUT[type=checkbox]:checked"), function(i, entry) {
			    names += '<li>'+$(entry).val()+'</li>';
			    ids.push($(entry).attr("name"));
			});
			
			if(ids.length == 0) return;

			$("#tabattachments .dialogs").html('<div id="deleteattachments" title="Delete attachments">Delete these attachments:<ul></ul></div>');

			$("#deleteattachments").dialog({
			    bgiframe: true,
			    autoOpen: true,
			    height: 200,
		            width: 400, 
			    modal: true,
			    buttons: {
				'Delete selected attachments': function() {
				    var $this = $(this);
				    $.booki.sendToCurrentBook({"command": "attachments_delete",
							       "attachments": ids},
							      function(data) {
								  $.booki.editor.showAttachmentsTab();

								  $this.dialog('close');
							      });
				},

				'Cancel': function() {
				    $(this).dialog('close');
				}
			    },
			    
			    open: function(event,ui) {
			    },
			    close: function() {
				
			    }
			});
			
			var dl = $("#deleteattachments UL");
			dl.append(names);			
		    });

		    // edit attachments
		    $("#editattachment").dialog({
			bgiframe: true,
			autoOpen: false,
			height: 450,
    			width: 700, 
			modal: true,
			buttons: {
			    'Update': function() {
				var fields = ["f_alt", "f_border", "f_align", "f_padding", "f_margin", "f_width", "f_height", "f_bgcolor", "f_bordercolor", "f_css"];
				
				i = document.createElement("img");
				i.src = $("#editattachment INPUT[name=f_image]").val();


				$.each(fields, function(x, field) {
				    var f_value = $("#editattachment INPUT[name="+field+"]").val();
				    
				    switch(field) {
				    case "f_css":
					if(f_value.length) {
					    i.setAttribute("class", f_value);
					} else {
					    i.setAttribute("class", "");
					}
					break;
				    case "f_alt":
					i.alt = f_value;
					break;
				    case "f_border":
					if(f_value.length) {
					    i.style.borderWidth = /[^0-9]/.test(f_value) ? j : (parseInt(f_value) + "px");
					    if (i.style.borderWidth && !i.style.borderStyle) {
						i.style.borderStyle = "solid"
					    }
					} else {
					    i.style.borderWidth = "";
					    i.style.borderStyle = "";
					}
					break;
				    case "f_borderColor":
					i.style.borderColor = f_value;
					break;
				    case "f_backgroundColor":
					i.style.backgroundColor = f_value;
					break;
				    case "f_padding":
					if(f_value.length) {
					    i.style.padding = /[^0-9]/.test(f_value) ? f_value : (parseInt(f_value) + "px")
					} else {
					    i.style.padding = ""
					}
					break;
				    case "f_margin":
					if (f_value.length) {
					    i.style.margin = /[^0-9]/.test(f_value) ? f_value : (parseInt(f_value) + "px")
					} else {
					    i.style.margin = ""
					}
					break;
				    case "f_align":
					i.align = f_value;
					break;
				    case "f_width":
					if (!isNaN(parseInt(f_value))) {
					    i.width = parseInt(f_value)
					} else {
					    i.width = ""
					}
					break;
				    case "f_height":
					if (!isNaN(parseInt(f_value))) {
					    i.height = parseInt(f_value)
					} else {
					    i.height = ""
					}
					break
				    }
				});

				xinha_editors.myTextArea.insertNodeAtSelection(i);
				
				$(this).dialog('close');
			    },
			    'Cancel': function() {
				$(this).dialog('close');
			    }
			},
			open: function(event,ui) {
			},
			close: function() {
			    
			}
		    });

		    // New diff
		    
		    $("#newdiff").dialog({
			bgiframe: true,
			autoOpen: false,
			height: 500,
		        width: 700, 
			modal: true,
			buttons: {
			    'Cancel': function() {
				$(this).dialog('close');
			    }
			},
			open: function(event,ui) {
				// blah blah, set content
				// $("INPUT", $(this)).val("Enter new Chapter title.").select();
			},
			close: function() {
			    
			}
		    });


		    // CHAPTER AND SECTION
		    $("#newchapter").dialog({
			bgiframe: true,
			autoOpen: false,
			height: 200,
		        width: 400, 
			modal: true,
			buttons: {
			    'Create chapter': function() {
				if($.trim($("#newchapter INPUT").val())=='') return;

				$.booki.ui.notify("Creating chapter");
				
				$.booki.sendToChannel("/booki/book/"+$.booki.currentBookID+"/"+$.booki.currentVersion+"/", {"command": "create_chapter", "chapter": $("#newchapter INPUT").val()}, function(data) {
				    if(data.created) {
					$.booki.ui.notify();
				    } else {
					$.booki.ui.notify();
					alert("Can not create duplicate chapter name.");
				    }
				});
				
				
				$(this).dialog('close');
			    },
			    'Cancel': function() {
				$(this).dialog('close');
			    }
			},
			open: function(event,ui) {
			    $("INPUT", $(this)).val("Enter new Chapter title.").select();
			},
			close: function() {
			    
			}
		    });

                    $("#clonechapter").dialog({
                        bgiframe: true,
                        autoOpen: false,
                        height: 200,
                        width: 400,
                        modal: true,
                        buttons: {
                            'Clone chapter': function() {
                                if($.trim($("#clonechapter INPUT[name=book]").val())=='') return;
                                if($.trim($("#clonechapter INPUT[name=chapter]").val())=='') return;

                                $.booki.ui.notify("Cloning chapter");

                                $.booki.sendToChannel(
                                    "/booki/book/"+$.booki.currentBookID+"/"+$.booki.currentVersion+"/",
                                    {"command": "clone_chapter",
                                     "book": $("#clonechapter INPUT[name=book]").val(),
                                     "chapter": $("#clonechapter INPUT[name=chapter]").val(),
                                     "renameTitle": $("#clonechapter INPUT[name=rename_title]").val(),
                                    }, function(data) {
                                    if(data.created) {
                                        $.booki.ui.notify();
                                    } else {
                                        $.booki.ui.notify();
                                        alert("Can not create duplicate chapter name.");
                                    }
                                });


                                $(this).dialog('close');
                            },
                            'Cancel': function() {
                                $(this).dialog('close');
                            }
                        },
                        open: function(event,ui) {
                            $("INPUT[name=book]", $(this)).val("Enter Book id.");
                            $("INPUT[name=book]", $(this)).autocomplete({source: "book-list.json"}).select();                            
			    $("INPUT[name=book]", $(this)).bind(
                                "autocompleteselect",
                                function (event, ui) {
                                    var book = ui.item.value;
                                    $("#clonechapter INPUT[name=chapter]").select().autocomplete("destroy").autocomplete({source: "book-list.json?book="+book});
                                });
                            $("INPUT[name=chapter]", $(this)).val("Enter Chapter id.");
                        },
                        close: function() {

                        }
                    });

		    
		    
		    $("#newsection").dialog({
			bgiframe: true,
			autoOpen: false,
			height: 200,
    		        width: 400, 
			modal: true,
			buttons: {
			    'Create section': function() {
				if($.trim($("#newsection INPUT").val())=='') return;

				$.booki.ui.notify("Creating section");
				
				$.booki.sendToChannel("/booki/book/"+$.booki.currentBookID+"/"+$.booki.currentVersion+"/", {"command": "create_section", "chapter": $("#newsection INPUT").val()}, function(data) {
				    if(data.created) {
					$.booki.ui.notify();
				    } else {
					alert("Can not create duplicate section name.");
					$.booki.ui.notify();
				    }
				});
				
				$(this).dialog('close');
			    },
			    'Cancel': function() {
				$(this).dialog('close');
			    }
			},
			open: function(event,ui) {
			    $("INPUT", $(this)).val("Enter new section title.").select();
			},
			close: function() {
			    
			}
		    });
		    
		    
		    
		},
		
		drawAttachments: function() {
		    $("#tabattachments .files").empty().append('<tr><td width="5%"></td><td align="left"><b>filename</b></td><td align="left"><b>dimension</b></td><td align="right" width="10%"><b>size</b></td></tr>');
		    
		    $.each(attachments, function(i, elem) {
			$("#tabattachments .files").append('<tr class="line"><td><input type="checkbox"></td><td><a class="file" href="javascript:void(0)" alt="'+elem["name"]+'">'+elem["name"]+'</a></td><td>'+$.booki.utils.formatDimension(elem["dimension"])+'</td><td align="right"><nobr>'+$.booki.utils.formatSize(elem.size)+'</nobr></td></tr>');
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
			    $("#attachmentpreview").html('<img src="../_utils/thumbnail/'+imageName+'"><br/><br/><a style="font-size: 10px" href="static/'+imageName+'" target="_new">Open in new window</a>');
			    //			    $("#attachmentpreview").html('<img src="../_utils/thumbnail/'+imageName+'"><br/><br/><a style="font-size: 10px" href="../_draft/static/'+imageName+'" target="_new">Open in new window</a>');

			}
		    });
		    
		},
		
		_loadInitialData : function() {
		    $.booki.ui.notify("Loading...");

		    jQuery.booki.sendToCurrentBook({"command": "init_editor"},

					       function(data) {
						   $.booki.ui.notify("");

						   chapterLocks = data.locks;

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
						       $("#users").append('<li class="user'+elem[0]+'"><div style="background-image: url('+$.booki.profileThumbnailViewUrlTemplate.replace('XXX', elem[0])+'); width: 24px; height: 24px; float: left;  margin-right: 5px;"></div><b>'+elem[0]+'</b><br/><span>'+elem[1]+'</span></li>');
						   });

					       });

		},
		
		/* initialize editor */
		
		initEditor: function() {
		    
		    jQuery.booki.subscribeToChannel("/booki/book/"+$.booki.currentBookID+"/"+$.booki.currentVersion+"/", function(message) {

			var funcs = {
			    "user_status_changed": function() {
				$("#users .user"+message.from+"  SPAN").html(message.message);
				$("#users .user"+message.from).animate({backgroundColor: "yellow" }, 'fast',
								       function() {
									   $(this).animate({backgroundColor: "white"},3000);
								       });
			    },

			    "user_add": function() {
				$("#users").append('<li class="user'+message.username+'"><div style="width: 24px; height: 24px; float: left; margin-right: 5px;background-image: url('+$.booki.profileThumbnailViewUrlTemplate.replace('XXX', message.username)+');"></div><b>'+message.username+'</b><br/><span>'+message.mood+'</span></li>');
			    },

			    "user_remove": function() {
				$("#users .user"+message.username).css("background-color", "yellow").slideUp(1000, function() { $(this).remove(); });
			    },

			// ERROR
			// this does not work when you change chapter status very fast
			    "chapter_status": function() {
				$.booki.debug.debug(message);
				if(message.status == "rename" || message.status == "edit") {
				    chapterLocks[message.chapterID] = message.username;
				    // $("#item_"+message.chapterID).css("color", "red");
				    //$(".extra", $("#item_"+message.chapterID)).html('<div style="padding: 3px; background-color: red; color: white">'+message.username+'</div>');
				    toc.refreshLocks();
				    holdChapters.refreshLocks();
				}
			    
				if(message.status == "normal") {
				    delete chapterLocks[message.chapterID];
				    //$("#item_"+message.chapterID).css("color", "gray");
				    //$(".extra", $("#item_"+message.chapterID)).html("");          

				    toc.refreshLocks();
				    holdChapters.refreshLocks();
				}
			    },
			
			    "chapters_changed": function() {
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
			    },
			    
                            "chapter_create": function() {
				// this also only works for the TOC
				if(message.chapter[3] == 1) { 
				    toc.addItem(createChapter({id: message.chapter[0], title: message.chapter[1], isChapter: true, status: message.chapter[4]}));
				    var v = toc.getItemById(message.chapter[0]);
				    makeChapterLine(v.id, v.title, getStatusDescription(v.status)).appendTo("#chapterslist");
				} else {
				    toc.addItem(createChapter({id: message.chapter[0], title: message.chapter[1], isChapter: false}));
				    var v = toc.getItemById(message.chapter[0]);
				    makeSectionLine(v.id, v.title).appendTo("#chapterslist");
				}
			    },

			    "chapter_rename": function() {
				$.booki.debug.debug("[chapter_rename]");
				var item = toc.getItemById(message.chapterID);
				if(!item)
				    item = holdChapters.getItemById(message.chapterID);
				item.title = message.chapter;
				toc.refresh();
				holdChapters.refresh();
			    },
			    
			    "chapters_list": function() {
				$("#chapterslist").empty();
				$.each(message.chapters, function(i, elem) {
				    // should be makeSectionLine also
				    makeChapterLine(elem[0], elem[1], 0).prependTo("#chapterslist");
				});
			    },

			    "change_status": function() {
				// message.chapterID
				// message statusID

				var item = toc.getItemById(message.chapterID);
				item.status = message.statusID;
				toc.refresh();
				holdChapters.refresh();
			    },
			    
			    "chapter_split": function()  {
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
			};

			if(funcs[message.command]) {
			    funcs[message.command]();
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
		    $("#insertattachment .files").append('<tr><td><b>name</b></td><td><b>size</b></td><td><b>dimension</b></td><td><b>modified</b></td></tr>');

		    $.each(func(), function(i, att) {
			$("#insertattachment .files").append('<tr><td><a class="file" style="text-decoration: underline" href="javascript:void(0)" alt="'+att.name+'">'+att.name+'</a></td><td>'+$.booki.utils.formatSize(att.size)+'</td><td>'+$.booki.utils.formatDimension(att.dimension)+'</td><td>'+att.created+'</td></tr>');
		    });

		    $("#insertattachment A.file").click(function() {
			var fileName = $(this).attr("alt");
			selectedFile = fileName;
			$("#insertattachment .previewattachment").html('<img src="../_utils/thumbnail/'+fileName+'">');
			
		    });
		},

		// TODO
		// this has to be changed

		showUpload: function() {
		    var onChanged = function() {
			var entry = $(this).parent().attr("class");
			
			if(!hasChanged) {
			    $("#insertattachment .uploadsubmit").append('<input type="submit" value="Upload"/>');
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
    			width: 750, 
			modal: true,
			buttons: {
			    'Insert image': function() {
				if(selectedFile) {
				    editor.insertHTML('<img src="static/'+selectedFile+'"/>');
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
