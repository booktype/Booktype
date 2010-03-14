$(function() {
    /* booki.group */
	
    jQuery.namespace('jQuery.booki.group');
    
    jQuery.booki.group = function() {

	return {
	    _initUI: function() {
	    },

	    /* load initial data */
	    
	    _loadInitialData: function() {
		jQuery.booki.sendToChannel("/booki/group/"+$.booki.groupName+"/", 
					   {"command": "init_group",
					    "profile": $.booki.groupName
					   },
					   function(message) {
					       $.booki.ui.notify("");
					   });
	    },
	    
	    /* initialize group */
	    
	    initGroup: function() {
		jQuery.booki.subscribeToChannel("/booki/group/"+$.booki.groupName+"/", function(message) {
		    var funcs = {
			
		    };

		    if(funcs[message.command]) {
			funcs[message.command]();
		    }
		    
		});
		
		$.booki.group._loadInitialData();
		$.booki.group._initUI();
	    }
	}; 
    }();
	


    });
