/*
  This file is part of Booktype.
  Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
 
  Booktype is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
 
  Booktype is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.
 
  You should have received a copy of the GNU Affero General Public License
  along with Booktype.  If not, see <http://www.gnu.org/licenses/>.
*/

$(function() {
	/*
	  TODO: - before going into production this file should be stripped of comments and compressed
	 */

    function unescapeHtml (val) {
	    return val.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    } 

    /* booki.chat */

    jQuery.namespace('jQuery.booki.chat');

    /*
      Used for the chat.
     */

    jQuery.booki.chat = function() {
	var element = null;

	function showJoined(notice) {
	    var msg = $.booki.ui.getTemplate('joinMsg');

	    msg.find('.notice').html(notice);
	    $('.content', element).append(msg.clone());
	    $(".content", element).attr({ scrollTop: $(".content", element).attr("scrollHeight") });
	}

	function showInfo(notice) {
	    var msg = $.booki.ui.getTemplate('infoMsg');

	    msg.find('.notice').html(notice);
	    $('.content', element).append(msg.clone());
	    $(".content", element).attr({ scrollTop: $(".content", element).attr("scrollHeight") });
	}


	function formatMessage(from, message) {
	    return $("<p><b>"+from+"</b>: "+message+"</p>");
	}

	function showMessage(from, message) {
	    $(".content", element).append(formatMessage(from, message));
	    $(".content", element).attr({ scrollTop: $(".content", element).attr("scrollHeight") });
	}


	function initUI() {
	    element.html($('<form onsubmit="javascript: return false;"><div class="content" style="margin-bottom: 5px; width: 265px; height: 300px; border: 1px solid black; padding: 5px"></div><input type="text" style="width: 275px;"/></form>').submit(function() { var s = $("INPUT", element).val(); $("INPUT", element).attr("value", ""); showMessage($.booki.username, s);  $.booki.sendToChannel("/chat/"+$.booki.currentBookID+"/",{"command": "message_send", "message": s}, function() {} );
}));
	}

	
	return {
	    'initChat': function(elem) {
		element = elem;

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
	    var statuses = null;           // Holds all available statuses
	    var attachments = null;        // Holds all attachments in this book
	    var splitChapters = null; 
	    var currentlyEditing = null;   // Chapter ID of the chapter we are currently editing
	    var chapterLocks = {};         // Holds all chapter locks

	    /* local variables for lulu publish */
	    var luluUser = null;
	    var luluPassword = null;

	    // TODO
	    // should return translated status
	    // if somehow possible
	    function getStatusDescription(statusID) {
		var r = $.grep(statuses,  function(v, i) {
		    
		    return v[0] == statusID;
		});

		if(r && r.length > 0)
		    return r[0][1];

		return null;
	    }


	    /* TOC */

	    /* 
	       Creates chapter with default options.
	     */

	    function createChapter(vals) {
		var options = {
		    id: null,
		    title: '',
		    url_title: '',
		    isChapter: true,
		    isLocked: false,
		    status: null
		};

		$.extend(options, vals);

		return options;
	    }

	    /*
	      TOC holds all chapters and sections.
	     */

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

		'getItemByURLTitle': function(URLTitle) {
		    for(var i = 0; i < this.items.length; i++) {
			if(this.items[i].url_title == URLTitle) {
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

	    /*
	      HistoryPanel is used in History tab.
	     */

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
			var s = $.booki.ui.getTemplate('historyTable');
			
			$.each(data.history, function(i, entry) {
			    var kindName = $(".eventKind.template #"+entry.kind.replace(" ", "_")).html();
			    if(entry.kind == "create" || entry.kind == "rename") {
				var en = $.booki.ui.getTemplate('rowCreateRename');

				$.booki.ui.fillTemplate(en, {"entryKind": kindName,
				  	                     "entryChapter": entry.chapter,
					                     "entryUser": entry.user,
					                     "entryModified": entry.modified});

				en.find('.setChapterLink').click(function() { $this.setChapterView(entry.chapter, entry.chapter_url, entry.chapter_history); });
				s.append(en);
				
			    } else if(entry.kind == "save") {
				var en = $.booki.ui.getTemplate('rowSave');

				$.booki.ui.fillTemplate(en, {"entryKind": kindName,
					    "entryChapter": entry.chapter,
					    "entryUser": entry.user,
					    "entryModified": entry.modified});

				en.find('.setChapterLink').click(function() { $this.setChapterView(entry.chapter, entry.chapter_url, entry.chapter_history); });
				s.append(en);
			    } else if(entry.kind == "major" || entry.kind == "minor") {
				var en = $.booki.ui.getTemplate('rowVersion');

				$.booki.ui.fillTemplate(en, {"entryVersion": entry.version,
					    "entryUser": entry.user,
					    "entryModified": entry.modified});

				s.append(en);
			    } else if(entry.kind == 'attachment') {
				var en = $.booki.ui.getTemplate('rowAttachment');

				$.booki.ui.fillTemplate(en, {"entryFilename": entry.args.filename,
					    "entryUser": entry.user,
					    "entryModified": entry.modified});

				s.append(en);
			    } else if(entry.kind == 'attachment_delete') {
				var en = $.booki.ui.getTemplate('rowAttachmentDelete');

				$.booki.ui.fillTemplate(en, {"entryFilename": entry.args.filename,
					    "entryUser": entry.user,
 					    "entryModified": entry.modified});

				s.append(en);
			    } else {
				var en = $.booki.ui.getTemplate('rowGeneric');

				$.booki.ui.fillTemplate(en, {"entryKind": kindName,
					    "entryUser": entry.user,
					    "entryModified": entry.modified});

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
			his.append('<span class="hiscontainer">'+$.booki._('loading_data', 'LOADING DATA....')+'</span>');
			his.append("<br/>");
			his.append($('<a href="javascript:void(0)">&lt;&lt;previous</a>').click(function() {
			    if(_page < 2) return;

			    $.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));

			    $($this.containerName+" TABLE").css("background-color", "#f0f0f0");
			    
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
				    $.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));
				    $($this.containerName+" TABLE").css("background-color", "#f0f0f0");
				    
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

		    $.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));
		    $.booki.sendToCurrentBook({"command": "get_history",
					       "page": 1},
					      function(data) {
						  $.booki.ui.notify();
						  _drawItems(data);
					      });
		    
		    this.refresh = function() {
			$.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));
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

			var disp = $.booki.ui.getTemplate('revisionDisplay');

			disp.find('.buttonset').buttonset();
			disp.find('.button').button();
			disp.find('.backLink').click(function() { $this.setChapterView(chapterName, chapterURL, chapterHistory);});

			disp.find('.revertLink').click(function() { 
				$(".cont", his).html('<div title="'+$.booki._('revert_to_this_version', 'Revert to this revision?')+'"><p><span class="ui-icon ui-icon-alert" style="float:left; margin:0 7px 20px 0;"></span>'+$.booki._('current_chapter_reverted', 'Current chapter content will be reverted to this revision. Are you sure?')+'</p></div>');
				// TODO, Change this
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
				    $.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));
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
				$.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));
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
		    
		    $.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));
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

			var disp = $.booki.ui.getTemplate('diffDisplay');

			disp.find('.backLink').click(function() { $this.setChapterView(chapterName, chapterURL, chapterHistory);});
			disp.find('.revision1Name').html(revision1);
			disp.find('.revision2Name').html(revision2);
			disp.find('.dataOutput').html(data.output);

			disp.find("A[name=side]").button().click(function() {
				$('#newdiff').dialog('open');
				
				// TODO:
				// this has to change, so it can be localized
				$("#newdiff .diffcontent").html($.booki._('loading_data_please_wait', 'Loading data. Please wait...'));

				$.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));

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
		    
		    $.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));
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

		    $.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));

		    $($this.containerName).empty();

		    $.booki.sendToCurrentBook({"command": "get_chapter_history", "chapter": chapterURL},
					      function(data) {
						  $.booki.ui.notify();
						  
						  var his = $($this.containerName);

						  his.empty();

						  disp = $.booki.ui.getTemplate('historyDisplay');

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
							  $("#newdiff .diffcontent").html($.booki._('loading_data_please_wait', 'Loading data. Please wait...'));

							  $.booki.ui.notify($.booki._('reading_history_data', 'Reading history data...'));

							  $.booki.sendToCurrentBook({"command": "chapter_diff_parallel", 
								                     "chapter": chapterURL,
								                     "revision1": revision1,
								                     "revision2": revision2},
							                             function(data) {
								                         $.booki.ui.notify();
								  
								                         $("#newdiff .diffcontent").html(data.output);
							                              });
						      }
						  });

						  disp.find('.chapterName').html(chapterName);

						  var s = disp.find('.chapterHistoryTable');

						  var max_revision = -1;
						  $.each(data.history, function(i, entry) {
							  if(entry.revision > max_revision) max_revision = entry.revision;

							  var en = $("<tr></tr>");
							  en.append('<td><input type="radio" name="group1" value="'+entry.revision+'"/><input type="radio" name="group2" value="'+entry.revision+'"/></td>');
							  
							  en.append(
								    $('<td></td>').append(
							      $('<a href="javascript:void(0)" style="text-decoration: underline">'+entry.revision+'</a>').click(
								  function() { 
								      if(entry.user != '')
									  $this.setRevisionView(chapterName, chapterURL, chapterHistory, entry.revision);
								  })
							  )
						      );

						      en.append('<td>'+entry.user+'</td><td style="white-space: nowrap">'+entry.modified+'</td><td>'+entry.comment+"</td>");
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

	    var toc = new TOC("#chapterslist");   // Holds all chapters and sections currently in TOC 
	    var holdChapters = new TOC("#holdchapterslist"); // Holds all chapters currently on hold

	    var historyPanel = new HistoryPanel("#historycontainer");

	    /*
	      Check for notification about empty TOC.
	     */
	    function checkForEmptyTOC() {
		if(toc.items.length == 0) {
		    $("#edit-info").removeClass("template");
		} else {
		    if(!$("#edit-info").hasClass("template"))
			$("#edit-info").addClass("template");
		}
	    }

	    /*
	      Get chapter object by it's Chapter ID.
	     */
	    function getChapter(chapterID) {
		var chap = toc.getItemById(chapterID);
		if(!chap)
		    chap = holdChapters.getItemById(chapterID);
		return chap;
	    }

	    function getChapterByURLTitle(URLTitle) {
		var chap = toc.getItemByURLTitle(URLTitle);

		return chap;
	    }

	    var _isEditingSmall = false;
	    
	    /*
	      Creates HTML code for the Section line in TOC.
	     */
	    function makeSectionLine(chapterID, name) {
		var line = $.booki.ui.getTemplate('sectionLine');

		line.attr('id', 'item_'+chapterID);
		line.find('.title').text(name);
		return line;
	    }
	    
	    /*
	      Creates HTML code for the Chapter line in TOC. It also binds different events.	      
	    */
	    function makeChapterLine(chapterID, name, status) {
		var line = $.booki.ui.getTemplate('chapterLine');

		line.attr('id', 'item_'+chapterID);
		$.booki.ui.fillTemplate(line, {'title': name});

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

		// TODO, it should take care of '!+@" and other characters in status
		var statusName = $(".bookStatuses.template #"+status.replace(/\s/g, "_")).html();
		line.find('.statusName').html(statusName);

		line.dblclick(function() {
		    if(_isEditingSmall) return;
		    _isEditingSmall = true;

		    $.booki.ui.notify($.booki._('sending_data', 'Sending data...'));
		    $.booki.sendToCurrentBook({"command": "chapter_status", "status": "rename", "chapterID": chapterID}, function() {$.booki.ui.notify("");} );
		    
		    var s = $(".title", $(this)).text(); 
		    var $this = $(this);

                    $(".cont", $(this)).html($('<form  style="font-size:12px; white-space: nowrap"></form>'));

		    // Make it look nicer and look on the width of input box
		    // also use white-space: nowrap


		    $("FORM", $(this)).append($('<input type="text" style="width: 70%">').attr("value", s)); 
		    $("INPUT", $(this)).focus();

                    $("FORM", $(this)).append($('<a href="#">'+$.booki._('SAVE', 'SAVE')+'</a>').click(function() {
			var newName = $("INPUT", $this).val();
			_isEditingSmall = false; $.booki.ui.notify($.booki._('sending_data', 'Sending data...'));
			$.booki.sendToCurrentBook({"command": "chapter_rename", "chapterID": chapterID, "chapter": newName}, function() { 
			    $.booki.ui.notify("");
			    toc.refreshLocks();
			    holdChapters.refreshLocks();
			});
			$("#item_"+chapterID).replaceWith(makeChapterLine(chapterID, newName, status)); 
			toc.refreshLocks();
			holdChapters.refreshLocks();

			return false;
		    }));
		    
		    
		    $("FORM", $(this)).append($('<span> </span>').html());
                    $("FORM", $(this)).append($('<a href="#">'+$.booki._('CANCEL', 'CANCEL')+'</a>').click(function() { 
				_isEditingSmall = false; $.booki.ui.notify($.booki._('sending_data', 'Sending data...'));
				$.booki.sendToCurrentBook({"command": "chapter_status", "status": "normal", "chapterID": chapterID}, function() {$.booki.ui.notify(""); toc.refreshLocks(); holdChapters.refreshLocks(); } );
				
				// this is not god. should get info from toc
				var ch = getChapter(chapterID);
				$("#item_"+chapterID).replaceWith(makeChapterLine(chapterID, ch.title, getStatusDescription(ch.status)));  
				return false;
			    }));
		    
		    toc.refreshLocks();
		    holdChapters.refreshLocks();
		    });
		    
		return line;
	    }

	    /* 
	       Closes editor. Fades it out and refreshes all locks in TOC and hold chapters.
	     */
	    function closeEditor() {
		currentlyEditing = null;
		$("#editor").fadeOut("slow",
				     function() {
					 $("#editorcontainer").css("display", "none");
					 $("#editorcontainer TEXTAREA").tinymce().hide();
					 $("#editorcontainer").empty();
					 
					 $("#container").hide().css("display", "block"); 
					 
					 toc.refreshLocks();
					 holdChapters.refresh();
				     });
	    }

	    /* Initialize callbacks when user is leaving editor page. */
	    function _initUnsaved() {
		    /* 
		       Show warning message if user is trying to leave the page while editing chapter. 
		       Show another message
		     */
		    $(window).bind('beforeunload', function(e) {    
			    if(currentlyEditing) {
				return $.booki._('loose_changes', 'You will loose unsaved changes. You are currently editing chapter')+' - "'+getChapter(currentlyEditing).title+'".';
			    }
			    return $.booki._('leaving_editor', 'You are leaving Booki Editor.');
			});
	    }

	    /* disable unsaved */
	    function _disableUnsaved() {
		$(window).unbind('beforeunload');
	    }

	    /*
	      Analyze our URL and see if we have to preselect some option.

	      For now it can parse:
   	           _edit/#/edit/chapter_title/
   	           _edit/#/attachments/
	           _edit/#/history/
	           _edit/#/versions/
	           _edit/#/notes/
	           _edit/#/settings/
	           _edit/#/export/

	      In the future it would be nice to have:
                   _edit/#/history/chapter_name/
              but History Panel must be changed a bit to make it work.
	     */


	    function selectAccordingToSegment() {
		var url = $.url();
		var category = url.fsegment(1);
		
		switch(category) {
		case 'edit':
		    var page = url.fsegment(2);
		    
		    if(typeof page != 'undefined') {
			var chap =  getChapterByURLTitle(page);
			if(chap && !chapterLocks[chap.id]) {
			    $.booki.editor.editChapter(chap.id);
			}
		    }		    
		    break;

		case 'attachments':
		    $("#tabs").tabs("select", "tabattachments");
		    break;

		case 'history':
		    $("#tabs").tabs("select", "tabhistory");
		    break;

		case 'versions':
		    $("#tabs").tabs("select", "tabversions");
		    break;

		case 'notes':
		    $("#tabs").tabs("select", "tabnotes");
		    break;

		case 'settings':
		    $("#tabs").tabs("select", "tabsettings");
		    break;

		case 'export':
		    $("#tabs").tabs("select", "tabpublish");
		    break;
		}		
	    }
	    
	    return {
		getChaptersAll: function() {
		    var chapters = [];

		    for(var i = 0; i < toc.items.length; i++) {
			if(toc.items[i].isChapter)
			    chapters.push([toc.items[i].url_title, toc.items[i].title]);
		    }
		    
		    for(var i = 0; i < holdChapters.items.length; i++) {
			chapters.push([holdChapters.items[i].url_title, holdChapters.items[i].title]);
		    }
		    
		    return chapters;    
                },

		editStatusForChapter: function(chapterID) {
		    var chap = getChapter(chapterID);
		    var dial = $.booki.ui.getTemplate('statusChapterDialog');

		    dial.find("UL").html($.map(statuses, function(i, n) { return '<li style="list-style: none; margin-left: 0;"><input name="statchap" id="statchap'+i[0]+'" type="radio" value="'+i[0]+'" /><label for="statchap'+i[0]+'">'+i[1]+'</label></li>'}).join(''));
		    
    		    dial.find("INPUT[id=statchap"+chap.status+"]").attr('checked', 'checked');

		    dial.dialog({modal: true,
				buttons: [
					  {text: $.booki._('set_status', 'Set status'),
					   click: function() {
						  var $d = $(this);
						  var statusID = parseInt(dial.find('input[type=radio]:checked').val());
						  
						  if(statusID != -1)
						      chap.status = statusID;
						  
						  $.booki.ui.notify($.booki._('saving_data', 'Saving data...'));
						  
						  $.booki.sendToCurrentBook({"command": "change_status",
							      "chapterID": chapterID,
							      "statusID": statusID},
						      function(data) {
							  $.booki.ui.notify();
							  $d.dialog('close');
							  // this is not the nicest way to do this
							  $("#item_"+chapterID+" .status").html('<a href="javascript:void(0)" onclick="$.booki.editor.editStatusForChapter('+chapterID+')">'+getStatusDescription(chap.status)+'</a>');
						      });
					      }
					  },
					  {text: $.booki._('cancel', 'Cancel'),
						  click: function() {
						  $(this).dialog('close');
					      }
					  }
					  ]
				}
			);


		    return;
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
		    $.booki.ui.notify($.booki._('loading_chapter_data', 'Loading chapter data...'));
		    $.booki.sendToCurrentBook({"command": "get_chapter", "chapterID": chapterID, "lock": false, "revisions": true}, 
					      function(data) {
						  $.booki.ui.notify();

						  var $dialog = $('<div><div class="hdr" style="border-bottom: 1px solid #c0c0c0; padding-bottom: 5px;"></div><div class="cnt"></div></div>');

						  $dialog.find('.hdr').html('<form onsubmit="return false" action="javascript:void(0)">'+$.booki._('revision', 'Revision')+': <select>'+$.map(data['revisions'], function(i, n) { return '<option value="'+i+'">'+i+'</option>'}).join('')+'</select></form>');
						  $dialog.find('.hdr').find('OPTION[value="'+data['current_revision']+'"]').attr('selected', 'selected');

						  $dialog.find('.hdr').find('SELECT').change(function() {
							  $.booki.ui.notify($.booki._('loading_chapter_data', 'Loading chapter data...'));
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
							      title: $.booki._('booki_reader', 'Booki Reader'),
							      height: 530,
							      width:  600
							  });
						  $dialog.dialog('open');
					      });	
		},
		editChapter: function(chapterID) {
		    $.booki.ui.notify($.booki._('loading_chapter_data', 'Loading chapter data...'));
		    $.booki.sendToCurrentBook({"command": "get_chapter", "chapterID": chapterID}, function(data) {
					      $.booki.ui.notify();
					      $("#container").fadeOut("slow", function() {
						  
						  $("#container").css("display", "none");

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
						  
						  var ed = $("#editor").clone().removeClass("template");
						  
						  $("#editorcontainer").html(ed).css("display", "block").fadeIn("slow", function() {
							  $("#editorcontainer TEXTAREA").tinymce(window.EVIL_TINY_OPTIONS);
							  $("#editorcontainer TEXTAREA").html(data.content);

							  setTimeout(_sendNotification, 5000);
							      
							  currentlyEditing = chapterID;

							  $("#editorcontainer .title").html(data.title); 
						  
							  $("#editorcontainer A[name=chapter_id]").attr("value", chapterID);
							  $("#editorcontainer A[name=save]").click(function() {
								  var content = $("#editorcontainer TEXTAREA").html();
								  $.booki.ui.notify($.booki._('sending_data', 'Sending data...'));
								  
								  var minor = $("#editorcontainer INPUT[name=minor]").is(":checked");
								  var comment = $("#editorcontainer INPUT[name=comment]").val();
								  var author = $("#editorcontainer INPUT[name=author]").val();
								  var authorcomment = $("#editorcontainer INPUT[name=authorcomment]").val();

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
									  /*
									  $("#editor INPUT[name=comment]").val(""); 
									  $("#editor INPUT[name=author]").val(""); 
									  $("#editor INPUT[name=authorcomment]").val(""); 
									  */
								      } );
							      });
							  
							  $("#editorcontainer A[name=savecontinue]").click(function() {
								  $.booki.ui.notify($.booki._('sending_data', 'Sending data...'));
								  
								  var content = $("#editorcontainer TEXTAREA").html();
								  var comment = $("#editorcontainer INPUT[name=comment]").val();
							  
								  var author = $("#editorcontainer INPUT[name=author]").val();
								  var authorcomment = $("#editorcontainer INPUT[name=authorcomment]").val();
							  
								  $.booki.sendToCurrentBook({"command": "chapter_save", 
									      "chapterID": chapterID,
									      "content": content,
									      "minor": false,
									      "continue": true,
									      "comment": comment,
									      "author": author,
									      "authorcomment": authorcomment
									      },
								      function() {
									  $.booki.ui.notify(); 
									  $("#editorcontainer INPUT[name=comment]").val(""); 
									  $("#editorcontainer INPUT[name=author]").val(""); 
									  $("#editorcontainer INPUT[name=authorcomment]").val(""); 
								      });
							      });
						  
							  $("#editorcontainer A[name=view]").click(function() {
								  $.booki.ui.notify($.booki._('loading_chapter_data', 'Loading chapter data...'));
								  
								  $.booki.sendToCurrentBook({"command": "get_chapter", 
									      "chapterID": chapterID, 
									      "lock": false, 
									      "revisions": true}, 
								      function(data) {
									  $.booki.ui.notify();
									  
									  var $dialog = $('<div><div class="hdr" style="border-bottom: 1px solid #c0c0c0; padding-bottom: 5px;"></div><div class="cnt"></div></div>');
									  
									  $dialog.find('.hdr').html('<form onsubmit="return false" action="javascript:void(0)">'+$.booki._('revision', 'Revision')+': <select>'+$.map(data['revisions'], function(i, n) { return '<option value="'+i+'">'+i+'</option>'}).join('')+'</select></form>');
									  $dialog.find('.hdr').find('OPTION[value="'+data['current_revision']+'"]').attr('selected', 'selected');
									  
									  $dialog.find('.hdr').find('SELECT').change(function() {
										  $.booki.ui.notify($.booki._('loading_chapter_data', 'Loading chapter data...'));
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
										      title: $.booki._('booki_reader', 'Booki Reader'), 
										      height: 530,
										      width:  600
										      });
									  $dialog.dialog('open');
								      });	
								  
						      });

						  $("#editorcontainer A[name=cancel]").unbind('click').click(function() {
						      $.booki.sendToCurrentBook({"command": "chapter_status", 
   								                 "status": "normal", 
                                                                                 "chapterID": chapterID},
										function() {});
						      delete chapterLocks[chapterID];
						      closeEditor();
						  });  
					       });
					   });
			      	});
		},

		showSettingsTab: function() {
		    $.booki.ui.notify($.booki._('reading_settings_data', 'Reading settings data...'));

		    $("#tabsettings A[name=license]").button("option", "disabled", true);
		    $("#tabsettings A[name=language]").button("option", "disabled", true);
		    $("#tabsettings A[name=roles]").button("option", "disabled", true);
		    $("#tabsettings A[name=chapterstatus]").button("option", "disabled", true);
		    $("#tabsettings A[name=permissionbutton]").button("option", "disabled", true);

		    $.booki.sendToCurrentBook({"command": "settings_options"},
					      function(data) {
						  $.booki.ui.notify();
						  $("#tabsettings A[name=license]").button("option", "disabled", false);
						  $("#tabsettings A[name=language]").button("option", "disabled", false);
						  $("#tabsettings A[name=roles]").button("option", "disabled", false);
						  $("#tabsettings A[name=chapterstatus]").button("option", "disabled", false);
						  $("#tabsettings A[name=permissionbutton]").button("option", "disabled", false);

						  $("#tabsettings SELECT[name='permissions']").find('OPTION[value="'+data['permission']+'"]').attr('selected', 'selected');

						  var s = $.map(data['licenses'], function(i, n) { return '<option value="'+i[0]+'">'+i[1]+'</option>';}).join('');
						  $("#tabsettings SELECT[name='licen']").html(s);

						  $("#tabsettings SELECT[name='licen']").find('OPTION[value="'+data['current_licence']+'"]').attr('selected', 'selected');

						  var s2 = $.map(data['languages'], function(i, n) { return '<option value="'+i[0]+'">'+i[1]+'</option>';}).join('');
						  $("#tabsettings SELECT[name='lang']").html(s2);

						  $("#tabsettings SELECT[name='lang']").find('OPTION[value="'+data['current_language']+'"]').attr('selected', 'selected');

						  if(data['rtl'] == "RTL")
						      $("#tabsettings INPUT[name=rtl]").attr('checked', 'checked');


						  var s = $.map(statuses, function(i, n) { return '<i>'+i[1]+'</i>';}).join(', ');
						  $("#tabsettings .currentstatuses").html(s);

					      });

		},

		showAttachmentsTab: function() {
		    $.booki.ui.notify($.booki._('reading_attachments_data', 'Reading attachments data...'));
		    $.booki.sendToCurrentBook({"command": "attachments_list"},
					      function(data) {
						  $.booki.ui.notify();

						  var att_html = $("#attachmentscontainer");
						  var s = $.booki.ui.getTemplate('attachmentsTable');

						  $.each(data.attachments, function(i, entry) {
							  s.append('<tr><td width="30"><input type="checkbox" name="'+entry.id+'" value="'+entry.name+'"></td><td><a style="text-decoration: underline" href="'+$.booki.utils.linkToAttachment($.booki.currentBookURL, entry.name)+'" target="_new">'+$.booki.utils.maxStringLength(entry.name, 30)+'</a></td><td>'+$.booki.utils.formatDimension(entry.dimension)+'</td><td style="white-space: nowrap">'+$.booki.utils.formatSize(entry.size)+'</td><td style="white-space: nowrap">'+entry.created+'</td></tr>');
						  });
						  att_html.empty().append(s);
					      });

		},

		/*
		  Initialize all GUI elements on settings page and sets all callbacks.		  
		 */
		_initSettingsUI: function() {
		    // Settings - Permissions and Visibility
		    // "Set permissions" button
		   $("#tabsettings A[name=permissionbutton]").button().click(function() {
			   var newPermission = $("#tabsettings SELECT[name=permissions] OPTION:selected");

			   $.booki.sendToCurrentBook({"command": "book_permission_save",
				                      "permission": parseInt(newPermission.val())},
 			                             function(data) {
			                             });

			   return false;
		    });
		    
		   // Settings - Roles
		   // "Manage roles" button
		   $("#tabsettings A[name=roles]").button().click(function() {
			   var selectedRole = 0;
			   var dial = $.booki.ui.getTemplate('rolesDialog');

			   dial.find("SELECT[name=listroles]").change(function() {
				   var newRole = dial.find("SELECT[name=listroles] OPTION:selected");
				   if(newRole.val() != 0) {
				       selectedRole = parseInt(newRole.val());
				       
				       $.booki.sendToCurrentBook({"command": "roles_list",
						   "role": selectedRole},
					   function(data) {
					       var s = $.map(data['users'], function(i, n) { return '<option value="'+i[0]+'">'+i[1]+'</option>';}).join('');
					       dial.find("SELECT[name=users]").html(s);
					   });
				   } else {
				       dial.find("SELECT[name=users]").html("");
				   }
			       });
			   
			   dial.find("SELECT[name=users]").change(function() {
				   dial.find("A[name=removeuser]").button("option", "disabled", false);
			       });
			   
			   dial.find("A[name=adduser]").button().click(function() {
				   if(selectedRole == 0) return;
				   
				   // create new user now
				   var inp = dial.find("INPUT[name=newuser]").val();
				   if(inp.replace(/^\s+|\s+$/g, '') == '') return;
				   
				   var username = inp.split(" ")[0];
				   
				   $.booki.sendToCurrentBook({"command": "roles_add",
					       "username": username,
					       "role": selectedRole},
				       function(data) {
					   dial.find("SELECT[name=users]").append('<option value="'+username+'">'+inp+'</option>');
					   dial.find("INPUT[name=newuser]").val("")
					       });
			       });
			   
			   dial.find("A[name=removeuser]").button().click(function() {
				   var el = dial.find("SELECT[name=users] OPTION:selected");
				   if(el.html().indexOf("[owner]") == -1) {
				       $.booki.sendToCurrentBook({"command": "roles_delete",
						   "username": el.val(),
						   "role": selectedRole},
					   function(data) {
					       el.remove();
					       $(this).button("option", "disabled", true);
					   });
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
				       buttons: [
						 {text: $.booki._('close', 'Close'),
							 click:   function() {
							 $(this).dialog('close');
						     }
						 }
						 ]
				       }
			       );
		       });
		   
		   // Settings - Language
		   // "Set new language" button
		   $("#tabsettings A[name=language]").button().click(function() {
			   $.booki.sendToCurrentBook({'command': 'settings_language_save',
				                      'rtl': $("#tabsettings INPUT[name=rtl]").is(':checked'),
				                      'language': $("#tabsettings SELECT[name='lang'] OPTION:selected").val()}, 
 				                     function(data) {
				                     });
			    
		       });
		   
		   // Settings - License
		   // "Manage copyright attribution"
		   $("#tabsettings A[name=attribution]").button().click(function() {
			   var dial = $.booki.ui.getTemplate('copyrightAttribution');
			   
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
								     buttons: [
									       {text: $.booki._('save_changes', 'Save changes'), 
										       click: function() {
										       var $d = $(this);
										       var excludedUsers = dial.find("SELECT[name=excluded]").children().map(function(){return $(this).val()}).get();
										       $.booki.sendToCurrentBook({'command': 'license_attributions_save',
												   'excluded_users': excludedUsers}, 
											   function(data) {
											       $d.dialog('close');
											   });
										   }
									       },
									       {text: $.booki._('cancel', 'Cancel'),
										       click: function() {
										       $(this).dialog('close');
										   }
									       }
									       ]
								     }
							     );
						     });
			   
		       });
		   
		   // Settings - License
		   // "Set new license" button
		   $("#tabsettings A[name=license]").button().click(function() {
			    var $b = $(this);
			    $b.button("option", "disabled", true);
			    $.booki.ui.notify($.booki._('saving_data_please_wait', 'Saving data. Please wait...'));

			    $.booki.sendToCurrentBook({'command': 'license_save', 
						       'license': $("#tabsettings SELECT[name=licen]").val() },
 				                       function(data) {
 				                          $b.button("option", "disabled", false);
				                          $.booki.ui.notify();
 				                       });

		       });
		   
		   // Settings - Chapter status
		   // "Manage chapter status" button
		   $("#tabsettings A[name=chapterstatus]").button().click(function() {
			    function _createStatus(i0, i1) {
				return '<li class="ui-state-default" id="liststatus_'+i0+'"><span class="ajkon ui-icon ui-icon-arrowthick-2-n-s"></span><span class="statuslabel">'+i1+'</span><div style="float: right"><a  class="lnkdel" href="#" name="'+i0+'"><span class="ui-icon ui-icon-closethick"></span></a></div><div style="float: right"><a  class="lnkedit" href="#" name="'+i0+'"><span class="ui-icon ui-icon-pencil"></span></a></div></li>';
			    }

			    var dial = $.booki.ui.getTemplate('statusChapterSettingsDialog');

			    var s = $.map(statuses, function(i, n) { return _createStatus(i[0], i[1]); }).join('');

			    dial.find("UL").html(s);

			    function _operButtonsEdit(a) {
				a.click(function() { 
					var i = $(this).attr("name");
					var nm = getStatusDescription(i);
					var ns = prompt($.booki._('new_status_name', "New status name"), nm);
					if(ns) {
					    dial.find("#liststatus_"+i+" .statuslabel").html(ns);
					}
				    });
			    }

			    function _operButtonsDel(a) {				
				a.click(function() { 
					if(confirm($.booki._('delete_this_status', 'Delete this status?'))) {
					    var i = $(this).attr("name");

					    $.booki.sendToCurrentBook({'command': 'book_status_remove',
						    'status_id': i}, 
					    function(data) {
						if(data.result == false) {
						    alert($.booki._('cant_delete_status', "Can't delete because some chapters have this status. Change chapter status first."));
						} else {
						    // send event
						    statuses = data.statuses;
						    dial.find("#liststatus_"+i).remove();
						    dial.find("UL").sortable('refreshPositions');
						}
					    });
					}
				    });
			    }

			    _operButtonsEdit(dial.find("LI A.lnkedit"));
			    _operButtonsDel(dial.find("LI A.lnkdel"));

			    dial.find("A[name=newstatus]").button().click(function() {
				    var st = dial.find("INPUT[name=newstatus]").val();
				    if(st != '') {
					
					$.booki.sendToCurrentBook({'command': 'book_status_create',
						    'status_name': st}, 
					    function(data) {
						// send event
						statuses = data.statuses;

						var h = $(_createStatus(data.status_id, st));

						_operButtonsEdit(h.find("LI A.lnkedit"));
						_operButtonsDel(h.find("LI A.lnkdel"));


						dial.find("UL").append(h);
						dial.find("INPUT[name=newstatus]").val('')
					    });

				    }
				});



			    dial.find("UL").sortable({ containment: 'parent', 
					items: 'LI',
					update: function(event, ui) {
   					   dial.find("UL").sortable('refreshPositions');
				    }
				});
			    dial.find("UL").disableSelection();

			    dial.dialog({modal: true,
					width: 600, 
					height: 400, 
					buttons: [
						  {text: $.booki._('save_new_order', 'Save new order'),
						   click: function() {
							  var $d = $(this);
							  
							  $.booki.sendToCurrentBook({'command': 'book_status_order',
								      'order': dial.find("UL").sortable('toArray')}, 
							      function(data) {
								  // send event
								  statuses = data.statuses;
								  
								  var s = $.map(statuses, function(i, n) { return '<i>'+i[1]+'</i>';}).join(', ');
								  $("#tabsettings .currentstatuses").html(s);
								  
								  $d.dialog('close');
							      });
						      }
						  },
						  {text: $.booki._('close', 'Close'),
						   click: function() {
							  var s = $.map(statuses, function(i, n) { return '<i>'+i[1]+'</i>';}).join(', ');
							  $("#tabsettings .currentstatuses").html(s);
							  
							  $(this).dialog('close');
						      }
						  }
						  ]
					}
				);
			    
			});

		   // Settings - License
		   // "Read full text of the license" link
		    $("#tabsettings A[name=readlicense]").click(function() {

			    var $d = $('<div title="'+$("#tabsettings SELECT[name=licen]").val()+'"><iframe width="98%" height="98%"></iframe></div>').dialog({width: 800, height: 400, 
																			       modal: true,
																			       buttons: [{text: "Ok",
																					  click: function() {
						
						$( this ).dialog( "close" );
					    }
					}
																				   ]
				});

			    // This is not the way to do it :(
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

		/*
		  Initialize all GUI elements in editor and sets all callbacks.
		  Also calls _initSettingsUI.
		 */
		_initUI: function() {
		    /* Inside of dialog for inserting and uploading images */
		    $("#inserttabs").tabs();

		    
		    /* Tabs in Editor */
		    $("#tabs").tabs();
		    $('#tabs').bind('tabsselect', function(event, ui) { 
			if(ui.panel.id == "tabnotes") {
			    $.booki.ui.notify($.booki._('reading_notes_data', 'Reading notes data...'));
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
						      });

			}
			
			if(ui.panel.id == "tabattachments") {
			    $.booki.editor.showAttachmentsTab();
			}

			if(ui.panel.id == "tabsettings") {
			    $.booki.editor.showSettingsTab();
			}

			if(ui.panel.id == "tabversions") {
			    $.booki.ui.notify($.booki._('reading_version_data', 'Reading version data...'));
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

							      s += '<li><a target="_new" href="'+$.booki.getBookDraftURL(entry.major+'.'+entry.minor)+'">'+getVersionName(entry)+'   </a></li>';
							  });
							  
							  $("#tabversions .list").html("<ul>"+s+"</ul>");
								 
						      }
						      );

			}

			if(ui.panel.id == "tabhistory") {
			    historyPanel.active();
			}
		    });

		    /* TOC and hold chapters list */
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

				    $.booki.ui.info("#container .middleinfo", $.booki._('removing_chapter_from_toc', 'Removing chapter from Table of Contents.'));
				    $.booki.ui.notify($.booki._('sending_data', 'Sending data...'));
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

				    $.booki.ui.info("#container .middleinfo", $.booki._('adding_chapter_to_toc', 'Adding chapter to Table of Contents.'));
				    $.booki.ui.notify($.booki._('sending_data', 'Sending data...'));
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
			    $.booki.ui.info("#container .middleinfo", $.booki._('reordering_the_chapters', 'Reordering the chapters...'));
			    $.booki.ui.notify($.booki._('sending_data', 'Sending data...'));
			    $.booki.sendToCurrentBook({"command": "chapters_changed", 
						       "chapters": result,
						       "hold": holdResult,
						       "kind": "order",
						       "chapter_id": null
						       }, 
						      function() {$.booki.ui.notify();  toc.refreshLocks(); holdChapters.refreshLocks();} );
			}

			// $.booki.sendToCurrentBook({"command": "chapters_changed", "chapters": result}, function() {$.booki.ui.notify()} );

			checkForEmptyTOC();						
		    }, 'placeholder': 'ui-state-highlight', 'scroll': true}).disableSelection();


		    /* Initialize chat */
		    $.booki.chat.initChat($("#chat"));

		    /* Notes */
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
		    
		    /* Export tab */

		    /* Button for publishing */

		    function setWizzardOptions(frm, options) {
			var fieldsdone = [];

			$.map(options, function(i, v) {						
				if($('TEXTAREA[name='+i.name+']', frm).length > 0) {
				    $('TEXTAREA[name='+i.name+']', frm).html(i.value);
				    fieldsdone.push(i.name);
				};
				
				if($('SELECT[name='+i.name+']', frm).length > 0) {
				    $('SELECT[name='+i.name+']', frm).val(i.value);
				    fieldsdone.push(i.name);
				};

				if($('INPUT[name='+i.name+']', frm).length > 0 && $('INPUT[name='+i.name+']', frm).attr("type") != "checkbox" && $('INPUT[name='+i.name+']', frm).attr("type") != "radio") {
				    $('INPUT[name='+i.name+']', frm).val(i.value);
				    fieldsdone.push(i.name);				    
				};

				if($('INPUT[name='+i.name+']', frm).length > 0 && $('INPUT[name='+i.name+']', frm).attr("type") == "checkbox") {
				    if(i.value == 'yes' || i.value == 'on') {
					$('INPUT[name='+i.name+']', frm).attr('checked', 'checked');
					fieldsdone.push(i.name);
				    } else {
					$('INPUT[name='+i.name+']', frm).removeAttr('checked');
				    }
				};

				if($('INPUT[name='+i.name+']', frm).length > 0 && $('INPUT[name='+i.name+']', frm).attr("type") == "radio") {
				    $('INPUT[name='+i.name+'][value='+i.value+']', frm).attr('checked', 'checked');
				    fieldsdone.push(i.name);
				};

			    });			

			// this screws default options
			/*
			$.map($('INPUT', frm), function(i, v) {				
				if($.inArray($(i).attr('name'), fieldsdone) == -1) {
				    if($(i).attr('type') == 'checkbox') {
					$(i).removeAttr('checked');   
				    }
				} 
			    });
			*/
		    }

		    function createWizzard(wizzardName, wizzardType, wizzardData) {
			var t = $(wizzardData.html);

			$.booki.ui.notify();
			
			$('A[name="close"]', t).click(function() {
				$("#wizzardcontainer").html("");
				$("#wizzardcontainer").css("display", "none");
			    });
			
			$("FORM", t).formwizard({ 
				formPluginEnabled: true,
				    validationEnabled: false,
				    focusFirstInput : true,
                                    disableUIStyles: true,
				    formOptions :{
				    success: function(data) {
				    },
					beforeSubmit: function(dta) { 
					var fieldsWithValues = [];

					var data = [];

					for(var i = 0; i < dta.length; i++) {
					    if(dta[i].name == 'lulu_user' || dta[i].name == 'lulu_password') {
						if(dta[i].name == 'lulu_user')
						    luluUser = dta[i].value;
						if(dta[i].name == 'lulu_password')
						    luluPassword = dta[i].value;						
						data.push({'name': dta[i].name, 'value': ''})
					    } else {
						data.push(dta[i]);
					    }
					}
					  
					  $.map(data, function(i, v) {
					      fieldsWithValues.push(i.name);
					      });
					  
					  $.map( $('INPUT', $("FORM", t)), function(i, v) {
						  if($.inArray($(i).attr('name'), fieldsWithValues) == -1) {
						      data.push({'name': $(i).attr('name'), 'value': 'off'});
						  }
					      });
					  
					  // remove user name and password but save it in local variables
					      
					$.booki.sendToCurrentBook({"command": "set_wizzard",
						    "wizzard_type": wizzardType,
						    "wizzard_options": data}, 
					    function() {
						// ashamed of this at this point, but it will be changed soon
						setTimeout(function() {
							$("#wizzardcontainer").html("");
							$("#wizzardcontainer").css("display", "none");
						    }, 200);
					    });
				    },
					dataType: 'json',
					resetForm: true
					}	
			    });
			
			
			$("#wizzardcontainer").css("display", "block");
			$("#wizzardcontainer").html(t);

			if(luluUser != null)
			    wizzardData.options.push({"name": "lulu_user", "value": luluUser});

			if(luluPassword != null)
			    wizzardData.options.push({"name": "lulu_password", "value": luluPassword});
			
			setWizzardOptions($("FORM", t), wizzardData.options);
		    }
		    
		    
                    $('A[name="bookwizzard"]').button().click(function() {
			    $.booki.ui.notify("Loading data. Please wait...");

			    $.booki.sendToCurrentBook({"command": "get_wizzard",
 					               "wizzard_type": "book"},
			    			      function(wizzardData) {
							  createWizzard('bookwizzard', 'book', wizzardData);
						      });
			});

                    $('A[name="ebookwizzard"]').button().click(function() {
			    $.booki.ui.notify("Loading data. Please wait...");

			    $.booki.sendToCurrentBook({"command": "get_wizzard",
 					               "wizzard_type": "ebook"},
			    			      function(wizzardData) {
							  createWizzard('ebookwizzard', 'ebook', wizzardData);
						      });
			});

                    $('A[name="pdfwizzard"]').button().click(function() {
			    $.booki.ui.notify("Loading data. Please wait...");

			    $.booki.sendToCurrentBook({"command": "get_wizzard",
 					               "wizzard_type": "pdf"},
			    			      function(wizzardData) {
							  createWizzard('pdfwizzard', 'pdf', wizzardData);
						      });
			});

                    $('A[name="odtwizzard"]').button().click(function() {
			    $.booki.ui.notify("Loading data. Please wait...");

			    $.booki.sendToCurrentBook({"command": "get_wizzard",
 					               "wizzard_type": "odt"},
			    			      function(wizzardData) {
							  createWizzard('odtwizzard', 'odt', wizzardData);
						      });
			});

                    $('A[name="luluwizzard"]').button().click(function() {
			    $.booki.ui.notify("Loading data. Please wait...");

			    $.booki.sendToCurrentBook({"command": "get_wizzard",
 					               "wizzard_type": "lulu"},
			    			      function(wizzardData) {
							  createWizzard('luluwizzard', 'lulu', wizzardData);
						      });
			});


		    			
		    $('a[name=exportbutton]').button().click(function() {
			    var publishMode = $("FORM[name=formexport] INPUT[name=publish]:checked").val();

			    $('a[name=exportbutton]').button("option", "disabled", true);

			    var t = $.booki.ui.getTemplate("progress");
			    $("#tabpublish .info").html(t);

			    // if it is lulu, load local variables and pass them here
			    // if not... just ignore it...

			    commands = {"command": "publish_book2",
					"publish_mode": publishMode}

			    if(publishMode == 'lulu') {
				commands['lulu_user'] = luluUser;
				commands['lulu_password'] = luluPassword;
			    }

			    $.booki.sendToCurrentBook(commands,						  
                                                  function(data) {
						      var message = "";

						      if(typeof data.status == 'undefined' || data.status == false) {
							  var t = $.booki.ui.getTemplate("publisherror");
							  $("#tabpublish .info").html(t);
						      } else {
							  var t = $.booki.ui.getTemplate("downloadpublish");
							  $(".url", t).html('<a target="_new" href="'+data.dta+'">'+data.dta+'</a>');
							  $("#tabpublish .info").html(t);
						      }

						      $('a[name=exportbutton]').button("option", "disabled", false);

                                                      $.booki.ui.notify();
                                                  } );


			});

		    // init upload dialog

		    $.booki.editor.upload.init(function(){ return attachments } );

		    // spalato dialog
		    // not used at the moment
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
				    } 

				    splitChapters.push([chapName, ""]);

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

		    /* Book versions tab */

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
			buttons: [
				  { text: $.booki._('create_major_version', 'Create  major version'),
                                    click: function() {
					  jQuery.booki.sendToCurrentBook({"command": "create_major_version",
						      "name": $("INPUT", $(this)).val(),
						      "description": $("TEXTAREA", $(this)).val()
						      },
					      function(data) {
						  $.booki.ui.notify();
						  _disableUnsaved();

						  //window.location = $.booki.getBookURL(data.version)+'_edit/';
						  window.location = $.booki.getBookURL()+'_edit/';
					      });
					  
					  $(this).dialog('close');
				      }
				  },
				  { text: $.booki._('cancel', 'Cancel'),
				    click: function() {
					  $(this).dialog('close');
				      }
				  }
			],
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
			buttons: [
				  { text: $.booki._('create_minor_version', 'Create minor version'), 
				    click: function() {
					  jQuery.booki.sendToCurrentBook({"command": "create_minor_version",
						      "name": $("INPUT", $(this)).val(),
						      "description": $("TEXTAREA", $(this)).val()
						      },
					      function(data) {
						  $.booki.ui.notify();
						  _disableUnsaved();

						  window.location = $.booki.getBookURL()+'_edit/';
						  //window.location = $.booki.getBookURL(data.version)+'_edit/';
					      });
					  
					  $(this).dialog('close');
				      }
				  },
				  { text: $.booki._('cancel', 'Cancel'),
				    click: function() {
					  $(this).dialog('close');
				      }
				  }
			],
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

			$("#tabattachments .dialogs").html('<div id="deleteattachments" title="'+$.booki._('delete_attachments', 'Delete attachments')+'">'+$.booki._('delete_attachments', 'Delete these attachments:')+'<ul></ul></div>');

			$("#deleteattachments").dialog({
			    bgiframe: true,
			    autoOpen: true,
			    height: 200,
		            width: 400, 
			    modal: true,
			    buttons: [
				      { text: $.booki._('delete_selected_attachments', 'Delete selected attachments'),
                                        click: function() {
					      var $this = $(this);
					      $.booki.sendToCurrentBook({"command": "attachments_delete",
							  "attachments": ids},
						  function(data) {
						      $.booki.editor.showAttachmentsTab();
						      
						      $this.dialog('close');

						      if(data.result == false) {
							  alert($.booki._('delete_attachment_permission', "You don't have permission to delete attachments."));
						      }
						  });
					  }
				      },
				      { text: $.booki._('cancel', 'Cancel'),
				        click: function() {
					      $(this).dialog('close');
					  }
				      }
			    ],
			    
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
			buttons: [
				  { text: $.booki._('update', 'Update'),
				    click: function() {
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
				      }
			    },
			    { text: $.booki._('cancel', 'Cancel'),
			      click: function() {
				    $(this).dialog('close');
				}
			    }
			],
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
			buttons: [
				  { text: $.booki._('cancel', 'Cancel'),
			            click: function() {
					  $(this).dialog('close');
				      }
				  }
			],
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
			buttons: [
				  { text: $.booki._('create_chapter', 'Create chapter'),
				    click: function() {
					  if($.trim($("#newchapter INPUT").val())=='') return;
					  
					  $.booki.ui.notify($.booki._('creating_chapter', 'Creating chapter'));
				
					  $.booki.sendToChannel("/booki/book/"+$.booki.currentBookID+"/"+$.booki.currentVersion+"/", {"command": "create_chapter", "chapter": $("#newchapter INPUT").val()}, function(data) {
						  if(data.created) {
						      $.booki.ui.notify();
						  } else {
						      $.booki.ui.notify();
						      if(typeof data.silly_url != 'undefined' && data.silly_url == true) 
							  alert($.booki._('can_not_create_chapter_illegal', 'This is not a valid chapter name.'));
						      else
							  alert($.booki._('can_not_create_chapter', 'Can not create duplicate chapter name.'));
						  }
						  checkForEmptyTOC();				
					      });
				
				
					  $(this).dialog('close');
				      }
				  },
				  { text: $.booki._('cancel', 'Cancel'),
				    click: function() {
					  $(this).dialog('close');
				      }
				  }
			],
			open: function(event,ui) {
				$("INPUT", $(this)).val($.booki._('enter_new_chapter', 'Enter new Chapter title.')).select();
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
			buttons: [
				  { text: $.booki._('clone_chapter', 'Clone chapter'),
				    click: function() {
					  if($.trim($("#clonechapter INPUT[name=book]").val())=='') return;
					  if($.trim($("#clonechapter INPUT[name=chapter]").val())=='') return;

					  $.booki.ui.notify($.booki._('cloning_chapter', 'Cloning chapter'));

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
									alert($.booki._('can_not_duplicate_name', 'Can not create duplicate chapter name.'));
								    }
								});


					  $(this).dialog('close');
				      }
				  },
				  { text: $.booki._('cancel', 'Cancel'),
				    click: function() {
					  $(this).dialog('close');
				      }
				  }
                        ],
                        open: function(event,ui) {
			    $("INPUT[name=book]", $(this)).val($.booki._('enter_book', 'Enter Book id.'));
                            $("INPUT[name=book]", $(this)).autocomplete({source: "book-list.json"}).select();                            
			    $("INPUT[name=book]", $(this)).bind(
                                "autocompleteselect",
                                function (event, ui) {
                                    var book = ui.item.value;
                                    $("#clonechapter INPUT[name=chapter]").select().autocomplete("destroy").autocomplete({source: "book-list.json?book="+book});
                                });
                            $("INPUT[name=chapter]", $(this)).val($.booki._('enter_chapter', 'Enter Chapter id.'));
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
			buttons: [
				  { text: $.booki._('create_section', 'Create section'),
				    click: function() {
					  if($.trim($("#newsection INPUT").val())=='') return;
					  
					  $.booki.ui.notify($.booki._('creating_section', 'Creating section'));
					  
					  $.booki.sendToChannel("/booki/book/"+$.booki.currentBookID+"/"+$.booki.currentVersion+"/", {"command": "create_section", "chapter": $("#newsection INPUT").val()}, function(data) {
						  if(data.created) {
						      $.booki.ui.notify();
						  } else {
						      alert($.booki._('can_not_create_duplicate_name', 'Can not create duplicate section name.'));
						      $.booki.ui.notify();
						  }
						  checkForEmptyTOC();				
					      });
					  
					  $(this).dialog('close');
				      }
				      }, 
				  { text: $.booki._('cancel', 'Cancel'),
				    click: function() {
					  $(this).dialog('close');
				      }
				  }
				], 
			open: function(event,ui) {
				$("INPUT", $(this)).val($.booki._('enter_new_section', 'Enter new section title.')).select();
			},
			close: function() {
			    
			}
		    });
		    
		    
		    
		},
		
		drawAttachments: function() {
		    $("#tabattachments .files").empty().append('<tr><td width="5%"></td><td align="left"><b>'+$.booki._('filename', 'filename')+'</b></td><td align="left"><b>'+$.booki._('dimension', 'dimension')+'</b></td><td align="right" width="10%"><b>'+$.booki._('size', 'size')+'</b></td></tr>');
		    
		    $.each(attachments, function(i, elem) {
			    $("#tabattachments .files").append('<tr class="line"><td><input type="checkbox"></td><td><a class="file" href="javascript:void(0)" alt="'+elem["name"]+'">'+$.booki.utils.maxStringLength(elem["name"], 30)+'</a></td><td>'+$.booki.utils.formatDimension(elem["dimension"])+'</td><td align="right"><nobr>'+$.booki.utils.formatSize(elem.size)+'</nobr></td></tr>');
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
			    // TODO: escape imageName
			    $("#attachmentpreview").html('<img src="../_utils/thumbnail/'+imageName+'"><br/><br/><a style="font-size: 10px" href="static/'+imageName+'" target="_new">Open in new window</a>');
			}
		    });
		    
		},

		/*
		  Loads all initial data and refreshes widgets.

		  Loads: 
		   - locks
		   - licenses
		   - statuses
		   - metadata
		   - chapters
		   - hold chapters
		   - attachments
		   - online users
		 */
		_loadInitialData : function() {
		    $.booki.ui.notify($.booki._('loading', 'Loading...'));

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
							   toc.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1, status: elem[4], url_title: elem[2]}));
						   });

						   $.each(data.hold, function(i, elem) {
							   holdChapters.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1, status: elem[4], url_title: elem[2]}));
						   });


						   toc.draw();
						   holdChapters.draw();

						   attachments = data.attachments;
						   $.booki.editor.drawAttachments();
						   
						   $.each(data.onlineUsers, function(i, elem) {
						       $("#users").append('<li class="user'+elem[0]+'"><div style="background-image: url('+$.booki.profileThumbnailViewUrlTemplate.replace('XXX', elem[0])+'); width: 24px; height: 24px; float: left;  margin-right: 5px;"></div><b>'+elem[0]+'</b><br/><span>'+elem[1]+'</span></li>');
						   });

						   /* 
						      Now when everything is preloaded, try to see if some of the options has to be selected.
						    */
						   selectAccordingToSegment();
						   checkForEmptyTOC();
					       });

		},

		/* 
		   Initialize editor. 

		   Calls _initUI to initialized all GUI elements on the page (tabs, dialogs, buttons). 
		   Calls _loadInitialData to loads all data (locks, licenses,  statuses, chapters, ...).
		   Calls _initUnsaved to to bind events in case user wants to close the editor.

		   Subscribes to the book channel and defines callbacks for all the messages that might happen on that channel:
		     - user_status_changed
		     - user_add
		     - user_remove
		     - chapter_status
		     - chapters_changed
		     - chapters_create
		     - chapters_rename
		     - chapters_list
		     - change_status
		     - chapter_status_changed
		     - chapter_split
                         
		*/		
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

				    toc.refreshLocks();
				    holdChapters.refreshLocks();
				}
			    
				if(message.status == "normal") {
				    delete chapterLocks[message.chapterID];

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
				    
				    $.booki.ui.info("#container .middleinfo", $.booki._('removing_chapter_from_toc', 'Removing chapter from Table of Contents.'));
				} else {
				    if(message.kind == "add") {
					var itm = holdChapters.getItemById(message.chapter_id);
					toc.addItem(itm);
					holdChapters.delItemById(message.chapter_id);
					
					toc.update(message.ids);
					holdChapters.update(message.hold_ids);
					
					toc.draw();
					holdChapters.draw();
					
					$.booki.ui.info("#container .middleinfo", $.booki._('adding_chapter_to_toc', 'Adding chapter to Table of Contents.'));
				    } else {
					$.booki.ui.info("#container .middleinfo", $.booki._('reordering_the_chapters', 'Reordering the chapters...'));
					
					toc.update(message.ids);
					holdChapters.update(message.hold_ids);
					toc.redraw();
					holdChapters.redraw();
				    }
				}
				checkForEmptyTOC();
			    },
			    
                            "chapter_create": function() {
				// this also only works for the TOC
				if(message.chapter[3] == 1) { 
				    toc.addItem(createChapter({id: message.chapter[0], title: message.chapter[1], isChapter: true, status: message.chapter[4], url_title: message.chapter[2]}));
				    var v = toc.getItemById(message.chapter[0]);
				    makeChapterLine(v.id, v.title, getStatusDescription(v.status)).appendTo("#chapterslist");
				} else {
				    toc.addItem(createChapter({id: message.chapter[0], title: message.chapter[1], isChapter: false}));
				    var v = toc.getItemById(message.chapter[0]);
				    makeSectionLine(v.id, v.title).appendTo("#chapterslist");
				}
				checkForEmptyTOC();
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
				checkForEmptyTOC();
			    },

			    "change_status": function() {
				// message.chapterID
				// message statusID

				var item = toc.getItemById(message.chapterID);
				item.status = message.statusID;
				toc.refresh();
				holdChapters.refresh();
			    },

			    "chapter_status_changed": function() {
				statuses = message.statuses;
			    },
			    
			    "chapter_split": function()  {
				toc.items = new Array();
				holdChapters.items = new Array();
				
				$.each(message.chapters, function(i, elem) {
					toc.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1, status: elem[4], url_title: elem[2]}));
				});
				
				$.each(message.hold, function(i, elem) {
					holdChapters.addItem(createChapter({id: elem[0], title: elem[1], isChapter: elem[3] == 1, status: elem[4], url_title: elem[2]}));
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

		    _initUnsaved();
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
		    $("#insertattachment .files").append('<tr><td><b>'+$.booki._('name', 'name')+'</b></td><td><b>'+$.booki._('size', 'size')+'</b></td><td><b>'+$.booki._('dimension', 'dimension')+'</b></td><td><b>'+$.booki._('modified', 'modified')+'</b></td></tr>');

		    $.each(func(), function(i, att) {
			    $("#insertattachment .files").append('<tr><td><a class="file" style="text-decoration: underline" href="javascript:void(0)" alt="'+att.name+'">'+$.booki.utils.maxStringLength(att.name, 30)+'</a></td><td style="white-space: nowrap">'+$.booki.utils.formatSize(att.size)+'</td><td style="white-space: nowrap">'+$.booki.utils.formatDimension(att.dimension)+'</td><td>'+att.created+'</td></tr>');
		    });

		    $("#insertattachment A.file").click(function() {
			var fileName = $(this).attr("alt");
			selectedFile = fileName;
			if($.booki.utils.isImage(selectedFile))
			    $("#insertattachment .previewattachment").html('<img src="../_utils/thumbnail/'+fileName+'">');
			else
			    $("#insertattachment .previewattachment").empty();
		    });
		},

		// TODO
		// this has to be changed

		showUpload: function() {
		    var onChanged = function() {
			var entry = $(this).parent().attr("class");
			
			if(!hasChanged) {
			    $("#insertattachment .uploadsubmit").append('<input type="submit" value="'+$.booki._('upload', 'Upload')+'"/>');
			}
			
			var licenses = '';

			$.each($.booki.licenses, function(i, v) {
			    licenses += '<option value="'+v[0]+'">'+v[1]+'</option>';
			}); 

			
			$("#insertattachment .uploadattachment ."+entry).append('<br><table border="0"><tr><td>'+$.booki._("rights_holder", "Rights holder")+':</td><td> <input name="rights'+n+'" type="text" size="30"/></td></tr><tr><td>License:</td><td><select name="license'+n+'" >'+licenses+'</select></td></tr></table>');

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
    			width: 800, 
			modal: true,
			buttons: [
				  { text: $.booki._('insert_image', 'Insert image'),
				    click: function() {
				             if(selectedFile) {
				                editor.insertHTML('<img src="static/'+selectedFile+'"/>');
				                $(this).dialog('close');
				             }
			             }
                                  },
				  { text:  $.booki._('cancel', 'Cancel'),
			            click: function() {
				              $(this).dialog('close');
			                   }
                                  }
			],
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
