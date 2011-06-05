$(function() {
	/* copy pasted */
	jQuery.namespace = function() {
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
	
	jQuery.namespace('jQuery.booki');
	
	/* booki */
	
	jQuery.booki = function() {
	    
	    return {username:       null,

                    currentProjectID: null,
		    currentProject: null,
                    currentBookID: null,
		    currentBook:    null,
		    
		    clientID: null,

		    licenses: null, 
		    
		    subscribeToChannel: function(channelName, callback) {
			var ch = jQuery.booki.network._transport._subscribedChannels;
		    
			if(!ch[channelName]) 
			    ch[channelName] = [callback];
			else
			    ch[channelName].push(callback);
		    },
		    
		    sendToChannel: function(channelName, message, callback, errback) {
			message["channel"] = channelName;
			jQuery.booki.network._transport.sendMessage(message, callback, errback);
  		    },

		    sendToCurrentBook: function(message, callback, errback) {
			return $.booki.sendToChannel("/booki/book/"+$.booki.currentBookID+"/"+$.booki.currentVersion+"/", message, callback, errback);
		    },
		    
		    unsubscribeFromChannel: function(channelName, someID) {
		    },

		    getBookURL: function(version) {
			var u = $.booki.bookViewUrlTemplate.replace('XXX', $.booki.currentBookURL);

			if(version)  u += '_v/'+version+'/';

			return u;
		    }
	    };
	}();

	/* network */
	
	jQuery.namespace('jQuery.booki.network');
	jQuery.booki.network = function() {
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
	    
	    jQuery.extend(Sputnik.prototype, {
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
			if(_options) {
			    jQuery.extend(options, _options);
			}
			
			if(!_isInitialized) {
			    this.interval();

			    _isInitialized = true;
			}
			
			var channels = new Array(); 

			for(var key in this._subscribedChannels) {
			    // this sux
			    if(key != "isArray" && key != "contains" && key != "append")
				channels.push(key);
			}

			_messages = $.merge([{"channel": "/booki/",
					      "command": "connect",
					      "uid": _uid,
					      "channels": channels}], 
			    _messages);
			_results[_uid] = [function(result) {
			    $.booki.clientID = result.clientID;
			}, null];
			
			_uid += 1;
			
			this.sendData();
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
				
				if(_messages.length == 0) {
				    a.sendMessage({"channel": "/booki/", "command": "ping"}, function() {});
				} 
				
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
			this.sendData();
		    },
		    
		    sendData: function() {
                        if(!_isInitialized) return;
			var $this = this;
			
                        var msgs = $.toJSON(_messages);

			var s = $("<span>Sending "+_messages.length+' message(s).</span>');
			$.booki.debug.network(s.html());

                        _messages = new Array();

			
			/*
			  what to do in case of errors?!
			*/
                        var a = this;
                        $.post($.booki.sputnikDispatcherURL, {"clientID": $.booki.clientID, "messages": msgs  }, function(data, textStatus) {
			    if(data) {
				$.each(data.messages, function(i, msg) {
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

    
        /* booki.debug */
    jQuery.namespace('jQuery.booki.debug');
    jQuery.booki.debug = function() {
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

	    if(!(msg instanceof String)) {
		msg = $.toJSON(msg);
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
			$.each($("#bookidebug .content > ."+cssClass), function(i, v) {
			    $(v).css("display", "none");
			});
		    } else {
			$.each($("#bookidebug .content > ."+cssClass), function(i, v) {
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
	
	jQuery.namespace('jQuery.booki.ui');
	
	jQuery.booki.ui = function() {
	    return {"notify":  function(message) {
		    if(!message || message == "") {
			$("#notify").css("display", "none");
			return;
		    }
		    
		    $("#notify").css("display", "block");
		    $("#notify").html(message);
	    },
		    "info": function(where, message) {
			$(where).append('<span>'+message+'</span>').show().fadeOut(3000, function() {  $(where).empty().show();});

		    }
	    };
	}();


	/* booki.utils */
	
	jQuery.namespace('jQuery.booki.utils');
	
	jQuery.booki.utils = function() {
	    return {
		"linkToAttachment": function(bookURL, attachmentURL, bookVersion) {
		    var ur = $.booki.bookViewUrlTemplate.replace('XXX', bookURL);

		    ur += '_draft/';

		    if(bookVersion == undefined) 
			ur += '_v/'+$.booki.currentVersion+'/';
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

	
    });
