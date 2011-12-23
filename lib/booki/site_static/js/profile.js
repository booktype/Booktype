$(function() {
    /* booki.editor */

	/* not used at the profile page */
	
    jQuery.namespace('jQuery.booki.profile');
    
    jQuery.booki.profile = function() {

	return {
	    _initUI: function() {

/*		$("#mood INPUT[type='text']").focus(function() {
		    if ($.booki.profileName == $.booki.username)
			$(this).val("");
		});*/


		/*
		$("#mood INPUT").blur(function() {
		    $(this).val("What's on your mind ?");
		});
                */
/*
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
*/
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

		$.booki.sendToChannel("/booki/profile/"+$.booki.profileName+"/",
				      {"command": "get_status_messages",
				       "profile": $.booki.profileName},
				      function(message) {
					  var con = $("#status_messages").empty();
					  $.each(message.list, function(i, v) {
					      con.append($('<p>'+v[0]+'</p>'));
					  });
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
	    }
	}; 
    }();
	


    });
