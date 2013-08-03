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

//jQuery(function(win) {
	/* Creates namespace in global namespace. */
	jquery.namespace = function() {
	    var a=arguments, o=null, i, j, d;
	    for (i=0; i<a.length; i=i+1) {
		d=a[i].split(".");
		o=window;
		for (j=0; j<d.length; j=j+1) {
		    o[d[j]]=o[d[j]] || {};
		    o=o[d[j]];
		}
	    }
	    return o;
	};
	
	/* booki */
	
	jquery.namespace('win.booktype');
	
	/*
	  Hold some basic variables and functions that are needed on global level and almost in all situations.
	 */
	
	win.booktype = function() {

		function csrfSafeMethod(method) {
		    // these HTTP methods do not require CSRF protection
		    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
		}

		function sameOrigin(url) {
		    // test that a given url is a same-origin URL
		    // url could be relative or scheme relative or absolute
		    var host = document.location.host; // host + port
		    var protocol = document.location.protocol;
		    var sr_origin = '//' + host;
		    var origin = protocol + sr_origin;
		    // Allow absolute or scheme relative URLs to same origin
		    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
		        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
		        // or any other URL that isn't scheme relative or absolute i.e relative.
		        !(/^(\/\/|http:|https:).*/.test(url));
		}
	   
	    return {username:       null,    // username of current user 
                currentProjectID: null,   // Not used anymore. We can erase this.
		        currentProject:   null,   // Not used anymore. We can erase this.
                currentBookID:  null,   //  Book ID. 
    		    currentBook:    null,   //  Full title
		        currentBookURL: null,   //  URL title
  		        clientID: null,
  		        licenses: null, 

	            getCookie: function(name) {
	                        var cookieValue = null;
						    if (document.cookie && document.cookie != '') {
						        var cookies = document.cookie.split(';');
						        for (var i = 0; i < cookies.length; i++) {
						            var cookie = jquery.trim(cookies[i]);
						            // Does this cookie string begin with the name we want?
						            if (cookie.substring(0, name.length + 1) == (name + '=')) {
						                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
						                break;
						            }
						        }
						    }
						    return cookieValue;
						},
				initCSRF: function() {
					var csrftoken = win.booktype.getCookie('csrftoken');

					jquery.ajaxSetup({
					    beforeSend: function(xhr, settings) {
					        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
					            // Send the token to same-origin, relative URLs only.
					            // Send the token only if the method warrants CSRF protection
					            // Using the CSRFToken value acquired earlier
					            xhr.setRequestHeader("X-CSRFToken", csrftoken);
					        }
					    }
					});

				},
			    connect: function() {
			    	win.booktype.initCSRF();
	   			    win.booktype.network._transport.connect();
			    },
			    
			    subscribeToChannel: function(channelName, callback) {
				    win.booktype.network._transport.subscribeToChannel(channelName, callback);
			    },
			    
			    sendToChannel: function(channelName, message, callback, errback) {
					message["channel"] = channelName;
					win.booktype.network._transport.sendMessage(message, callback, errback);
	  		    },

			    // Just a shortcut
			    sendToCurrentBook: function(message, callback, errback) {
					return win.booktype.sendToChannel("/booktype/book/"+win.booktype.currentBookID+"/"+win.booktype.currentVersion+"/", message, callback, errback);
			    },
			    
			    // FIXME not implemented
			    unsubscribeFromChannel: function(channelName, someID) {
			    },

			    // Just a shortcut
			    "_": function(a, b) { return win.booktype.i18n.translateText(a, b); },

			    getBookURL: function(version) {
					var u = win.booktype.bookViewUrlTemplate.replace('XXX', win.booktype.currentBookURL);

					if(version)  u += '_v/'+version+'/';

					return u;
			    },

			    getBookDraftURL: function(version) {
					var u = win.booktype.bookDraftViewUrlTemplate.replace('XXX', win.booktype.currentBookURL);

					if(version)  u += '_v/'+version+'/';

					return u;
			    }
	    };
	}();

	/* network */
	
	jquery.namespace('win.booktype.network');

	/*
	  This is used for Sputnik communication. This are high level API calls we use in Booki. 
	  At the moment it uses very stupid method of making HTTP requests every now and then.
	  Other layers of network communication (like Socket.io) can easily be used for communication.
	 */

	win.booktype.network = function() {
	    var _results = null;
	    var _lastAccess = null;
	    var _isInitialized = false;
	    var _messages = null;
	    var _uid = 1;
	    var options = {'poll': true,
		'iteration': 5000
	    };
	    
	    function Sputnik() {
		this.init();
	    }
	    
	    jquery.extend(Sputnik.prototype, {
		    _subscribedChannels: null,

		    showError: function() {
			// should check if it is already open
			// temp commented
			//$('#dialog-sputnik-error').dialog('open');
                    },
		    
		    init: function() {
				var $this = this;

				_messages = new Array();
				_results  = new Array();
				this._subscribedChannels = new Array();

				$('#dialog-sputnik-qrac').ajaxError(function(event, request, opts, exc){
				    $this.showError();
				});
		    },
		    
		    connect: function(_options) {
				var $this = this;
				if(_options) {
				    // XXX requirements differ between parts of client
				    // jquery.extend(options, _options);
				}

				if (_isInitialized) return;

				this.interval();

				_isInitialized = true;
				
				var channels = new Array(); 

				for(var key in this._subscribedChannels) {
				    // this sux
				    if(key != "isArray" && key != "contains" && key != "append")
					channels.push(key);
				}

				_messages = jquery.merge([{"channel": "/booki/",
						      "command": "connect",
						      "uid": _uid,
						      "channels": channels}], 
				    _messages);
				_results[_uid] = [function(result) {
				    win.booktype.clientID = result.clientID;
				    $this.sendData();
				}, null];
				
				_uid += 1;
				
				this.sendData();
		    },
		    
		    subscribeToChannel: function(channelName, callback) {
				var ch = this._subscribedChannels;
			    
				if(!ch[channelName]) 
				    ch[channelName] = [callback];
				else
				    ch[channelName].push(callback);

				if (_isInitialized) {
				    this.sendMessage({"channel": "/booktype/", 
						      "command": "subscribe", 
						      "channels": [channelName]});
				}
		    },

		    interval: function() {
				if(!options['poll']) return;

				/* should be setTimeout and not setInterval */
				var a = this;
				
				setInterval(function() {
					var d = new Date();
					
					/*
					  if(d.getTime()-_lastAccess < 2000) {
					  }
					*/
					if (win.booktype.clientID && _messages.length == 0) {
					    a.sendMessage({"channel": "/booki/", "command": "ping"}, function() {});
					} 
					if (win.booktype.clientID)
					    a.sendData();

					_lastAccess = d;
				    }, options['iteration']);
		    },
		    
		    receiveMessage: function(message, result) {
				if(message.uid) {
				    var res = _results[message.uid];
				    
				    if(res) {
					// 0 or 1 depending of the result
					res[0](message);
					delete _results[message.uid];
				    }
				} else {
				    for(var a = 0; a<this._subscribedChannels[message.channel].length; a++) {
	                                this._subscribedChannels[message.channel][a](message);
				    }
				}
		    },
		    
		    sendMessage: function(message, callback, errback) {
				if(callback) 
				    _results[_uid] = [callback, errback];
				
				message["uid"] = _uid;
				
				_messages.push(message);
				_uid += 1;
				
				/* bash i ne bi trebao ovdje ovako ali eto */
				if (win.booktype.clientID)
				    this.sendData();
		    },
		    
		    sendData: function() {
                if(!_isInitialized) return;
                if(!_messages.length) return;
				var $this = this;
                var msgs;	

                if (_.isUndefined(JSON))	
                    msgs = jquery.toJSON(_messages);
                else
                    msgs = JSON.stringify(_messages);

				var s = $("<span>Sending "+_messages.length+' message(s).</span>');
				win.booktype.debug.network(s.html());

                _messages = new Array();

			
			/*
			  what to do in case of errors?!
			*/
                var a = this;
                jquery.post(win.booktype.sputnikDispatcherURL, {"clientID": win.booktype.clientID, "messages": msgs  }, function(data, textStatus) {
			    if(data) {
				jquery.each(data.messages, function(i, msg) {
					a.receiveMessage(msg, data.result);
				    });
			    } else {
					$this.showError();
			    }
			}, "json");
		    }
		});
	    
	    
	    return {"_transport": new Sputnik()
		    };
	    
	}();

	/* booki.i18n */
	jquery.namespace('win.booktype.i18n');

	/*
	  This is used for translating string inside of JavaScript code. 

         win.booktype.i18n.translateText("introduction", "This is default text, just in case i don't find translation");

         <span class="strings template">
          <span class="introduction">{% trans "This is introduction" %}</span>
         </span>
	 */
	
	win.booktype.i18n = function() {
	    var tmpl = $('.strings.template');

	    return {"translateText": function(translateID, defaultValue) {
		    var t = $('.'+translateID, tmpl);

		    if(t.length) {
			if(t.length > 1)
			    return $(t[0]).text();

			return t.text(); 
		    }

		    if(_.isUndefined(defaultValue)) return '';

		    return defaultValue;			  
		}};
	}();
    
        /* booki.debug */
    jquery.namespace('win.booktype.debug');

    /*
      Some basic Debug methods for JavaScript. Not to have users confused, only "booki" use can see debug window.
     */

    win.booktype.debug = function() {
	var showDebug = true;
	var showWarning = false;
	var showInfo = false;
	var showNetwork = false;

	function _msg(cssClass, msg) {
	    var d = new Date();

	    if(eval("show"+cssClass.charAt(0).toUpperCase()+cssClass.substring(1)) == false) return;

	    var h = d.getHours();
	    var m = d.getMinutes();
	    var s = d.getSeconds();

	    function frm(v) {
		if(v < 10) return "0"+v;
		return v;
	    }

	    if(!(_.isString(msg))) {
                if (_.isUndefined(JSON))
                    msg = jquery.toJSON(msg);
                else
                    msg = JSON.stringify(msg);
	    }

	    $("#bookidebug .content").append($('<div class="'+cssClass+'">['+frm(h)+':'+frm(m)+':'+frm(s)+'] '+msg+'</div>'));
	    $("#bookidebug .content").attr({ scrollTop: $("#bookidebug .content").attr("scrollHeight") });
	}

	return {
	    'init': function() {
		$("#bookidebug").dialog({"draggable": true, 
					 "autoOpen": false, 
					 "maxHeight": 350, 
					 "width": 400, 
					 "modal": false, 
					 "resizable": true, 
					 "stack": true, 
					 "title": "Booki Debug"});

		$("#bookidebug").append('<div class="header"><form style="margin: 0px"><input type="checkbox" class="checkdebug"> <span class="debug">Debug</span> <input type="checkbox" class="checkwarning"> <span class="warning">Warning</span> <input type="checkbox" class="checkwarning"> <span class="info">Info</span>  <input type="checkbox" class="checknetwork"> <span class="network">Network</span> <span style="float: right"><a class="clear" href="#">clear</a></span></form></div><div class="content">  </div>');

		$("#bookidebug INPUT.checkdebug").attr("checked", showDebug);
		$("#bookidebug INPUT.checkwarning").attr("checked", showWarning);
		$("#bookidebug INPUT.checkinfo").attr("checked", showInfo);
		$("#bookidebug INPUT.checknetwork").attr("checked", showNetwork);

		function changeOption(cssClass, value) {
		    if(!value) {
			jquery.each($("#bookidebug .content > ."+cssClass), function(i, v) {
			    $(v).css("display", "none");
			});
		    } else {
			jquery.each($("#bookidebug .content > ."+cssClass), function(i, v) {
			    $(v).css("display", "block");
			});
		    }
		}

		$("#bookidebug INPUT.checkdebug").change(function() { showDebug = !showDebug; changeOption("debug", showDebug) } );
		$("#bookidebug INPUT.checkwarning").change(function() { showWarning = !showWarning; changeOption("warning", showWarning) } );		
		$("#bookidebug INPUT.checkinfo").change(function() { showInfo = !showInfo; changeOption("info", showInfo) } );		
		$("#bookidebug INPUT.checknetwork").change(function() { showNetwork = !showNetwork; changeOption("network", showNetwork) } );

		$("#bookidebug A.clear").click(function() {
		    $("#bookidebug .content").empty();
		});
	    },


	    debug: function(msg) {
		_msg("debug", msg);
	    },

	    warning: function(msg) {
		_msg("warning", msg);
	    },
	    
	    network: function(msg) {
		_msg("network", msg);
	    },
	    
	    info: function(msg) {
		_msg("info", msg);
	    }
	}
    }();
	
	/* booki.ui */
	
	jquery.namespace('win.booktype.ui');

	/*
	  Some basic UI and templating functions.

	  var t = win.booktype.ui.getTemplate("opendialog");
	  win.booktype.ui.fillTemplate(t, {"something": "Value 1"});

	  <div class="opendialog template">
             This is our main open dialog for <span class="something"></span>!
          </div>
	 */
	
	win.booktype.ui = function() {
	    return {"notify":  function(message) {
		    if(!message || message == "") {
   			   $("DIV.notificationContainer").hide();
			return;
		    }
		    
		    $("DIV.notificationContainer").css("display", "block");
		    $("DIV.notificationContainer DIV.notification").html(message);
	            },
		    "info": function(where, message) {
 			    $(where).append('<span>'+message+'</span>').show().fadeOut(3000, function() {  $(where).empty().show();});

		    },

		    // Very simple and basic template functionality
		    "getTemplate": function(templateID) {
				var tmpl = $('.'+templateID+'.template').clone().removeClass("template");
				return tmpl;
		    },
		    "fillTemplate": function(tmpl, vars) {
				jquery.each(vars, function(varKey, varValue) {
					tmpl.find('.'+varKey).html(varValue);
				    });
		    }
	    };
	}();


	/* booki.utils */
	
	jquery.namespace('win.booktype.utils');

	/*
	  Utility functions.
	 */
	
	win.booktype.utils = function() {
		var Collection = function(itms) {
			this.items = itms || [];

			this.reset = function() {
				this.items = [];
			}

			this.length = function() {
				return this.items.length;
			}

			this.clone = function() {
				return this.items.slice(0);
			}

			this.each = function(callback) {
				jquery.each(this.items, function(i, v) {
					callback(i, v);
				})
			}
		}

	    return {
	       "Collection": Collection,
		   "unescapeHtml": function(val) {
		   					return _.unescape(val);
		   					// Old code
						   	// return val.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
						   }, 

		    "escapeJS": function(val) {
							if(val != null)
								return _.escape(val);
							   // Old code
							   // return String(val).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace("'", "&#39;").replace('"', "&quot;");

							return val;
					    }, 	    	
			"isImage": function(fileName) {
			    if(fileName.match(/\.jpg$/i) || fileName.match(/\.jpeg$/i) || fileName.match(/\.png$/i) || fileName.match(/\.tiff$/i) || fileName.match(/\.tif$/i)) 
				return true;
			    return false;
			},
			
			"maxStringLength": function(st, maxLength) {
			    if(st.length > maxLength) {
				return st.substr(0, maxLength)+'...';
			    }

			    return st;
			},
			"linkToAttachment": function(bookURL, attachmentURL, bookVersion) {
			    var ur = win.booktype.bookViewUrlTemplate.replace('XXX', bookURL);

			    ur += '_draft/';

			    if(_.isUndefined(bookVersion)) 
				ur += '_v/'+win.booktype.currentVersion+'/';
			    else 
				ur += '_v/'+bookVersion+'/';
			    
			    ur += 'static/'+attachmentURL;
			    return ur;
			},
			
			"formatSize":  function(sz) {		    
			    var kbSize = sz/1024;
			    
			    if(kbSize / 1024 > 1) {
				return Math.round(kbSize/1024, 2)+' Mb';
			    } 
			    return Math.round(kbSize, 2) + ' Kb';
		        },

			"formatDimension": function(dim) {
			    if(dim) {
				return dim[0]+'x'+dim[1];
			    }
			    
			    return '';
			}
	    };
	}();

	
})(window, jQuery);
