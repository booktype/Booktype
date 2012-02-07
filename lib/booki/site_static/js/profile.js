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
		    $("#tabs").tabs("select", "tabs-dashboard");
		    break;
		    
		case 'books':
		    $("#tabs").tabs("select", "tabs-books");
		    break;

		case 'settings':
		    $("#tabs").tabs("select", "tabs-settings");
		    break;
		}
	}

	return {
	    _initUI: function() {
                $("#tabs").tabs();

		$("FORM[name=formsettings]").submit(function() {
		    var $form = $(this);
		    var email = $("INPUT[name=email]", $form).val();
		    var fullname = $("INPUT[name=fullname]", $form).val();
		    var blurb = $("INPUT[name=aboutyourself]", $form).val();
		    var notification = $("INPUT[name=notification]", $form).val();

		    });

		$("FORM.formvisibility").submit(function() {
			var $form = $(this);
			var bookID = $("INPUT[name=book]", $form).val();
			var action = $("INPUT[name=action]", $form).val();
			
			jQuery.booki.sendToChannel("/booki/profile/"+$.booki.profileName+"/",
						   {"command":  "hide_book",
							   "bookID":   bookID,
							   "action":   action},
						   function(data) {
						       // what it does not do at the moment is refresh list of books
						       if(action == 'hide') {
							   $("BUTTON", $form).html($("SPAN.showtoothers").html());
							   $("INPUT[name=action]", $form).val("show")
							       } else {
							   $("BUTTON", $form).html($("SPAN.hidefromothers").html());
							   $("INPUT[name=action]", $form).val("hide")
							       }
						   });
						
			return false;
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
