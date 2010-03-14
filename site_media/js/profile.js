$(function() {
    /* booki.editor */
	
    jQuery.namespace('jQuery.booki.profile');
    
    jQuery.booki.profile = function() {

	return {
	    _initUI: function() {

		$("#mood INPUT").focus(function() {
		    $(this).val("");
		});


		/*
		$("#mood INPUT").blur(function() {
		    $(this).val("What's on your mind ?");
		});
                */

		$("#mood BUTTON").click(function() {
		    jQuery.booki.sendToChannel("/booki/profile/"+$.booki.profileName+"/", 
					       {
						   "command": "mood_set",
						   "value": $("#mood INPUT").val()
					       },

					       function(message) {
						   // server should send message to other clients
						   //$("#profilemood").html($("#mood INPUT").val());
						   $(this).val("What's on your mind ?");
					       });
		});
	    },

	    /* load initial data */
	    
	    _loadInitialData: function() {
		jQuery.booki.sendToChannel("/booki/profile/"+$.booki.profileName+"/", 
					   {"command": "init_profile",
					    "profile": $.booki.profileName
					   },
					   function(message) {
					       $.booki.ui.notify("");
					   });
	    },
	    
	    /* initialize profile */
	    
	    initProfile: function() {
		
		jQuery.booki.subscribeToChannel("/booki/profile/"+$.booki.profileName+"/", function(message) {
		    var funcs = {
			'user_status_changed': function() {
			    if(message.from == $.booki.profileName) {
				$("#profilemood").html(message.message);
			    }
			}
		    };

		    if(funcs[message.command]) {
			funcs[message.command]();
		    }
		    
		});
		
		$.booki.profile._loadInitialData();
		$.booki.profile._initUI();
	    }
	}; 
    }();
	


    });
