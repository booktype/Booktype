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
		    
		    unsubscribeFromChannel: function(channelName, someID) {
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
	    
	    function Sputnik() {
		this.init();
	    }
	    
	    jQuery.extend(Sputnik.prototype, {
		    _subscribedChannels: null,
		    
		    init: function() {
			_messages = new Array();
			_results  = new Array();
			this._subscribedChannels = new Array();
			
			this.interval();
		    },
		    
		    connect: function() {
			_isInitialized = true;
			
			var channels = new Array();
			
			for(var key in this._subscribedChannels) {
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
			    }, 5000);
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
			
                        var msgs = $.toJSON(_messages);
                        _messages = new Array();
			
			/*
			  what in case of errors?!
			*/
                        var a = this;
                        $.post("/api/", {"clientID": $.booki.clientID, "messages": msgs  }, function(data, textStatus) {
				$.each(data.messages, function(i, msg) {
					a.receiveMessage(msg, data.result);
				    });
			    }, "json");
		    }
		});
	    
	    
	    return {"_transport": new Sputnik()
		    };
	    
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
		}
	    };
	}();
	
    });
