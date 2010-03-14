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
						   $("#profilemood").html($("#mood INPUT").val());
						   $(this).val("What's on your mind ?");
					       });
		});
	    },
	    
	    /* initialize profile */
	    
	    initProfile: function() {
		
		jQuery.booki.subscribeToChannel("/booki/profile/"+$.booki.profileName+"/", function(message) {
		    
		});
		
		
		$.booki.profile._initUI();
	    }
	}; 
    }();
	


    });
