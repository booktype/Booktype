$(function() {
    /* booki.group */
	
    jQuery.namespace('jQuery.booki.group');
    
    jQuery.booki.group = function() {

	return {
	    _initUI: function() {
		$("#tabs").tabs();
		$("#tabs A.butt").button();

		$("#tabgroup A.buttjoin").button().click(function() {
		    jQuery.booki.sendToChannel("/booki/group/"+$.booki.groupNameURL+"/", 
					       {"command": "join_group"
					       },
					       
					       function(message) {
						   window.location = '';
					       });
		});

		$("#tabgroup A.buttleave").button().click(function() {
		    jQuery.booki.sendToChannel("/booki/group/"+$.booki.groupNameURL+"/", 
					       {"command": "leave_group"
					       },
					       
					       function(message) {
						   window.location = '';
					       });
		});

	    },

	    /* load initial data */
	    
	    _loadInitialData: function() {
		jQuery.booki.sendToChannel("/booki/group/"+$.booki.groupNameURL+"/", 
					   {"command": "init_group",
					    "profile": $.booki.groupName
					   },

					   function(message) {
					       $.booki.ui.notify("");
					   });
	    },
	    
	    /* initialize group */
	    
	    initGroup: function() {
		jQuery.booki.subscribeToChannel("/booki/group/"+$.booki.groupNameURL+"/", function(message) {
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
