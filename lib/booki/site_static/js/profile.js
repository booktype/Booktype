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

	function _initUI() {
	    $("#tabs").tabs();
	    
	    $("FORM[name=formsettings]").submit(function() {
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
	};

	/* load initial data */
	
	function _loadInitialData() {
	    jQuery.booki.sendToChannel("/booki/profile/"+$.booki.profileName+"/", 
				       {"command": "init_profile",
					       "profile": $.booki.profileName
					       },
				       function(message) {
					   $.booki.ui.notify("");
				       });
	};
	
	
	return {
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
		
		_loadInitialData();
		_initUI();

		selectAccordingToSegment();
	    },

	    reloadProfileInfo: function() {
		$("#tabs").tabs('option', 'selected', 0);
		
		jQuery.booki.sendToChannel("/booki/profile/"+$.booki.profileName+"/",
					   {"command":  "load_info"},
					   function(data) {
					       var $dashboard = $("#tabs-dashboard");
					       $("SECTION.basic-info > P", $dashboard).html(data.info.fullname);
					       var img = $("SECTION.basic-info  IMG", $dashboard);
					       // this should be enough random for now
					       img.attr("src", img.attr("src")+"?"+Math.floor(Math.random()*100));

					       $("SECTION.profile-description > P", $dashboard).html(data.info.description);
					       console.debug(data);
					   });
		
	    }
	}; 
    }();
	


    });
