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

(function(win, jquery) {

	jquery.namespace('win.booktype.editor');
	
	/*
	  Hold some basic variables and functions that are needed on global level and almost in all situations.
	 */
	
	win.booktype.editor = function() {				

		var DEFAULTS = {
						panels: {'edit': 'win.booktype.editor.edit',
			    			     'toc' : 'win.booktype.editor.toc',					  
					             'media' : 'win.booktype.editor.media',
  								},
		               };
		// Panels
		var activePanel = null;
		var panels = null;

		var data = {'chapters': null,
		            'holdChapters': null,
		            'statuses': null,

		            'settings': {}
					};

		var currentEdit = null;

		// TABS

		var tabs = [];

		var Tab = function(tabID, iconID) {
					this.tabID = tabID;
					this.iconID = iconID;
					this.domID = '';
                    this.isLeft = false;
                    this.isOnTop = false;
				  }

		Tab.prototype.onActivate = function() {};
		Tab.prototype.onDeactivate = function() {};


		var hideAllTabs = function() {
          jquery('.right-tabpane').removeClass('open hold'); 
          jquery('body').removeClass('opentabpane-right');
          jquery('.right-tablist li').removeClass('active');

          jquery('.left-tabpane').removeClass('open hold'); 
          jquery('body').removeClass('opentabpane-left');
          jquery('.left-tablist li').removeClass('active');          			
		}
	   
		var createRightTab = function(tab_id, iconID) {
			     var tb = new Tab(tab_id, iconID);
			     tb.isLeft = false;
			     tb.domID = '.right-tablist li #'+tab_id;

	       		 return tb;		
		}
		// leftTab
		var createLeftTab = function(tab_id, iconID) {
			     var tb = new Tab(tab_id, iconID);
			     tb.isLeft = true;
			     tb.domID = '.left-tablist li #'+tab_id;

				return tb;
		}	   

		var activateTabs = function(tabList) {
			jquery.each(tabList, function(i, v) {
				if(!v.isLeft) {
					if(v.isOnTop)
	   	                jquery('DIV.right-tablist UL.navigation-tabs li:eq(0)').before('<li><a href="#" id="'+v.tabID+'"><i class="'+v.iconID+'"></i></a></li>');
   	            	else
	   	                jquery('DIV.right-tablist UL.navigation-tabs').append('<li><a href="#" id="'+v.tabID+'"><i class="'+v.iconID+'"></i></a></li>');

                    jquery(v.domID).click(function() {
		 		            //close left side
				            jquery('.left-tabpane').removeClass('open hold');
				            jquery('body').removeClass('opentabpane-left');
				            jquery('.left-tablist li').removeClass('active');
				            // check if the tab is open
				            if (jquery('#right-tabpane').hasClass('open')) {
				                // if clicked on active tab, close tab
				                if(jquery(this).closest('li').hasClass('active')) {
				                    jquery('.right-tabpane').toggleClass('open');
				                    jquery('.right-tabpane').removeClass('hold');
				                    jquery('.right-tabpane section').hide();
				                    jquery('body').toggleClass('opentabpane-right');
				                    jquery(this).closest('li').toggleClass('active');
				                }
				                // open but not active, switching content
				                else {
				                    jquery(this).closest('ul').find('li').removeClass('active');
				                    jquery(this).parent().toggleClass('active');
				                    jquery('.right-tabpane').removeClass('hold');
				                    var target = jquery(this).attr('id');
				                    jquery('.right-tabpane section').hide();
				                    jquery('.right-tabpane section[source_id="'+target+'"]').show();
				                    var is_hold = jquery(this).attr('id')
				                    if (is_hold == 'hold-tab') {
				                        jquery('.right-tabpane').addClass('hold');
				                    }

				                    v.onActivate();
				                }
				            }   
				            // if closed, open tab
				            else {
				                jquery('body').toggleClass('opentabpane-right');
				                jquery(this).parent().toggleClass('active');
				                jquery('.right-tabpane').toggleClass('open');
				                var target = jquery(this).attr('id');
				                jquery('.right-tabpane section').hide();
				                jquery('.right-tabpane section[source_id="'+target+'"]').show();
				                var is_hold = jquery(this).attr('id')
				                if (is_hold == 'hold-tab') {
				                    jquery('.right-tabpane').addClass('hold');
				                }

				                v.onActivate();
				            }
			       		 });	   	                
				} else {
					if(v.isOnTop)
	   	                jquery('DIV.left-tablist UL.navigation-tabs li:eq(0)').before('<li><a href="#" id="'+v.tabID+'"><i class="'+v.iconID+'"></i></a></li>');
   	            	else
	   	                jquery('DIV.left-tablist UL.navigation-tabs').append('<li><a href="#" id="'+v.tabID+'"><i class="'+v.iconID+'"></i></a></li>');   	            	

	   		        jquery(v.domID).click(function() {
			            //close right side
			            jquery('.right-tabpane').removeClass('open hold'); 
			            jquery('body').removeClass('opentabpane-right');
			            jquery('.right-tablist li').removeClass('active');
			            // check if the tab is open
			            if (jquery('#left-tabpane').hasClass('open')) {
			                // if clicked on active tab, close tab
			                if(jquery(this).closest('li').hasClass('active')) {
			                    jquery('.left-tabpane').toggleClass('open');
			                    jquery('.left-tabpane').removeClass('hold');
			                    jquery('.left-tabpane section').hide();
			                    jquery('body').toggleClass('opentabpane-left');
			                    jquery(this).closest('li').toggleClass('active');
			                }
			                // open but not active, switching content
			                else {
			                    jquery(this).closest('ul').find('li').removeClass('active');
			                    jquery(this).parent().toggleClass('active');
			                    jquery('.left-tabpane').removeClass('hold');
			                    var target = jquery(this).attr('id');
			                    jquery('.left-tabpane section').hide();
			                    jquery('.left-tabpane section[source_id="'+target+'"]').show();
			                    var is_hold = jquery(this).attr('id')
			                    if (is_hold == 'hold-tab') {
			                        jquery('.left-tabpane').addClass('hold');
			                    }
			                    v.onActivate();
			                }
			            }   
			            // if closed, open tab
			            else {
			                jquery('body').toggleClass('opentabpane-left');
			                jquery(this).parent().toggleClass('active');
			                jquery('.left-tabpane').toggleClass('open');
			                //jquery('.right-tabpane').removeClass('open');
			                var target = jquery(this).attr('id');
			                jquery('.left-tabpane section').hide();
			                jquery('.left-tabpane section[source_id="'+target+'"]').show();
			                var is_hold = jquery(this).attr('id')
			                if (is_hold == 'hold-tab') {
			                    jquery('.left-tabpane').addClass('hold');
			                }
			                v.onActivate();
			            }
    		        });

				}
            });

		}

		var deactivateTabs = function(tabList) {
			jquery.each(tabList, function(i, v) {
					if(v.isLeft)
				      jquery('DIV.left-tablist UL.navigation-tabs #'+v.tabID).remove();
					else						
				      jquery('DIV.right-tablist UL.navigation-tabs #'+v.tabID).remove();
			});
		}

		// UTIL FUNCTIONS

		function showTOC() {
	   	  activePanel.hide();
	   	  activePanel = panels['toc'];
	   	  activePanel.show();
       	}

		function showMedia() {
	   	  activePanel.hide();
	   	  activePanel = panels['media'];
	   	  activePanel.show();
       	}
				
		var _editChapter = function(id) {
             win.booktype.ui.notify('Loading chapter.');

			 win.booktype.sendToCurrentBook({"command": "get_chapter",
            										"chapterID": id},
												       function(data) {
												       	  currentEdit = id;
												       	  activePanel.hide();
												       	  activePanel = panels['edit'];
												       	  activePanel.setChapterID(id);

												       	  jquery('#content').html(data.content);
												       	  activePanel.show();
   									       	              win.booktype.ui.notify();
												       });
		}


		var _initUI = function() {
            win.booktype.ui.notify();

			activePanel = panels['toc'];
			activePanel.show();

            // This should be initialized somewhere else
            jquery("UL.hold-chapters A").on('click', function(e) {
            	_editChapter(jquery(e.target).attr('title'));

            	return false;
            });


            // ONLINE USERS TAB
	        var t1 = createLeftTab('online-users-tab','big-icon-online-users');
	        t1.onActivate = function() {
	            console.log('* activate online users *');

	        };

	        // CHAT TAB
	        var t2 = createLeftTab('chat-tab', 'big-icon-chat');
	        t2.draw = function() {
	        	var $this = this;
	        	var $container = jquery("section[source_id=chat-tab]");

	        	var scrollBottom = function() {
								     var scrollHeight = jquery(".content", $container)[0].scrollHeight; 
								     $(".content", $container).scrollTop(scrollHeight);
						        	}		

				$this.formatString = function(frm, args) {
									    return frm.replace(/\{\{|\}\}|\{(\d+)\}/g, 
									    				   function (m, n) {
																if (m == "{{") { return "{"; }
																if (m == "}}") { return "}"; }
																return win.booktype.utils.escapeJS(args[n]);
														    });
							  		  };

				$this.showJoined = function(notice) {
									    var msg = win.booktype.ui.getTemplate('joinMsg');
									    msg.find('.notice').html(win.booktype.utils.escapeJS(notice));

							    	    jquery('.content', $container).append(msg.clone());
									    scrollBottom();
									}

				$this.showInfo = function(notice) {
									    var msg = win.booktype.ui.getTemplate('infoMsg');

									    if(typeof notice.message_id !== 'undefined') {
  										    msg.find('.notice').html($this.formatString(win.booktype._('message_info_'+notice.message_id, ''), notice.message_args));
									    }

									    jquery('.content', $container).append(msg.clone());
									    scrollBottom();
							 	}	        	

	        	$this.formatMessage = function(from, message) {
									    return $("<p><b>"+from+"</b>: "+win.booktype.utils.unescapeHtml(message)+"</p>");
								 	 }								 	 

	            $this.showMessage = function(from, message) {
								     $(".content", $container).append($this.formatMessage(from, message));
								     scrollBottom();
							  	   };

	        	jquery("FORM", $container).submit(function() {
		        	var msg = jquery.trim(jquery("INPUT[name=message]", $container).val());
		        	if(msg !== '') {
	           		   $this.showMessage(win.booktype.username, msg);
		   		  	   jquery("INPUT", $container).val('');

				   	   win.booktype.sendToChannel("/chat/"+win.booktype.currentBookID+"/",
				   	   							 {"command": "message_send", 
				   	   							  "message": msg}, function() {
				   	   							  } );
		        	}
		        	return false;
	        	});
	        }
	        t2.onActivate = function() {
	            console.log('* activate chat *');
	        };
	        t2.draw();

	        // Activate tabs
	        tabs = [t1, t2];
	        activateTabs(tabs);

	        jquery(document).trigger('booktype-ui-finished');
		}

		var _loadInitialData = function() {
            win.booktype.ui.notify('Loading data.');

		    booktype.sendToCurrentBook({"command": "init_editor"},
									       function(dta) {
									       		// Put this in the TOC

									       		data.chapters.loadFromArray(dta.chapters);
									       		data.holdChapters = dta.hold;
									       		attachments = dta.attachments;
									       		data.statuses = dta.statuses;

	    				       				   	// Initislize rest of the interface
		    									_initUI();
											});	
		}

		var _disableUnsaved = function() {
							       jquery(win).bind('beforeunload', function(e) {   
							       		// CHECK TO SEE IF WE ARE CURRENTLY EDITING SOMETHING
							       		return 'nesto;'
							       });

							    }

		var _initEditor = function(settings) {
			// Settings
			data.settings = _.defaults(settings, DEFAULTS)

			// Initialize Panels
			panels = {};

			_.each(settings.panels, function(pan, name){
				panels[name] = eval(pan);				
			});

			jquery.each(panels, function(i, v) { v.init(); });

			// initialize chapters
			data.chapters = new win.booktype.editor.toc.TOC();
			data.holdChapters = new win.booktype.editor.toc.TOC();

			//_disableUnsaved();

			// Subscribe to the book channel
		    win.booktype.subscribeToChannel("/booktype/book/"+win.booktype.currentBookID+"/"+win.booktype.currentVersion+"/", function(message) {
				var funcs = {
				    "user_status_changed": function() {
				    	console.log('*user status changed*');
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
				};

					if(funcs[message.command]) {
					    funcs[message.command]();
					}

		    });

			win.booktype.subscribeToChannel("/chat/"+win.booktype.currentBookID+"/", function(message) {
				console.log('* chat message *');
				console.log(message);
			    if(message.command == "user_joined") {
					tabs[1].showJoined(message.user_joined);
			    }

			    if(message.command == "message_info") {
					tabs[1].showInfo(message);
			    }


			    if(message.command == "message_received") {
					tabs[1].showMessage(message.from, message.message);
			    }
			});


		    _loadInitialData();		   
		}



	    return {
	    	data: data,
	        // statuses: statuses,

	    	showTOC: showTOC,
	    	showMedia: showMedia,
	    	editChapter: function(id) { _editChapter(id);},
	    	getCurrentChapterID: function() { return currentEdit; },

            initEditor: _initEditor,

            getActivePanel: function() { return activePanel; },

            hideAllTabs: hideAllTabs,
            activateTabs: activateTabs,
            deactivateTabs: deactivateTabs,
            createLeftTab: createLeftTab,
            createRightTab: createRightTab
	    };
	}();

	
})(window, jQuery);
