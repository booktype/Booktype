$(function() {
    /* booki.editor */

	/* not used at the profile page */
	
    jQuery.namespace('jQuery.booki.profile');
    
    jQuery.booki.profile = function() {


	function selectAccordingToSegment() {
		var url = $.url();
		var category = url.fsegment(1);

		switch(category) {
		case 'dashboard':
		    $("#tabs").tabs("select", "tabs-1");
		    break;
		    
		case 'books':
		    $("#tabs").tabs("select", "tabs-3");
		    break;

		case 'settings':
		    $("#tabs").tabs("select", "tabs-2");
		    break;
		}
	}

	return {
	    _initUI: function() {
                $("#tabs").tabs();

		$("#newgroup BUTTON").click(function() {
		    var groupName = $("#newgroup INPUT").val();
		    var groupDescription = $("#newgroup TEXTAREA").val();

		    if(groupName.length > 0 && groupDescription.length > 0) {

			jQuery.booki.sendToChannel("/booki/profile/"+$.booki.profileName+"/", 
						   {
						       "command":          "group_create",
						       "groupName":        groupName,
						       "groupDescription": groupDescription
						   },
						   
						   function(message) {
						       if(!message.created) {
							   alert("There is already group with this name.");
						       } else {
							   window.location = '.';
						       }
						   });
		    } else {
			alert("Please fill all the fields.");
		    }
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
				//$("#profilemood").html(message.message);
			    }
			}
		    };

		    if(funcs[message.command]) {
			funcs[message.command]();
		    }
		    
		});
		
		$.booki.profile._loadInitialData();
		$.booki.profile._initUI();

		selectAccordingToSegment();
	    }
	}; 
    }();
	


    });
