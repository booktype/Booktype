/*
  This file is part of Booktype.
  Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
 
  Booktype is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
 
  Booktype is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.
 
  You should have received a copy of the GNU Affero General Public License
  along with Booktype.  If not, see <http://www.gnu.org/licenses/>.
*/

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

	    $("FORM[name=formpassword]").submit(function() {
		    var $frm = $("FORM[name=formpassword]");
		    $('DIV.notificationpassword').html('');

		    var password0 = $.trim($("INPUT[name=password0]", $frm).val());
		    var password1 = $.trim($("INPUT[name=password1]", $frm).val());
		    var password2 = $.trim($("INPUT[name=password2]", $frm).val());

		    $("INPUT[name=password0]", $frm).css('border', '');
		    $("INPUT[name=password1]", $frm).css('border', '');
		    $("INPUT[name=password2]", $frm).css('border', '');

		    if(password0 == '') {
			var txt = $.booki._('passwordmissingold', '');
			$('DIV.notificationpassword').html('<p class="alert-box">'+txt+'</p>');
			$("INPUT[name=password0]", $frm).css('border', '1px solid red');
			return false;
		    }

		    if(password1 != password2) {
			var txt = $.booki._('passwordnotequal', '');
			$('DIV.notificationpassword').html('<p class="alert-box">'+txt+'</p>');
			$("INPUT[name=password1]", $frm).css('border', '1px solid red');
			$("INPUT[name=password2]", $frm).css('border', '1px solid red');
			return false;
		    }

		    if(password1.length < 6) {
			var txt = $.booki._('passwordshort', '');
			$('DIV.notificationpassword').html('<p class="alert-box">'+txt+'</p>');
			$("INPUT[name=password1]", $frm).css('border', '1px solid red');
			$("INPUT[name=password2]", $frm).css('border', '1px solid red');
			return false;
		    }

		    jQuery.booki.sendToChannel("/booki/profile/"+$.booki.profileName+"/", 
					       {"command": "change_password",
						       "profile": $.booki.profileName,
						       "password0": password0,
						       "password1": password1,
						       "password2": password2
						       },
					       function(message) {
						   if(message.result == true) {
						       if(message.status == 1) {
							   var txt = $.booki._('passwordchanged', '');
							   $('DIV.notificationpassword').html('<p class="alert-box">'+txt+'</p>');
							    $("INPUT[name=password0]", $frm).val("");
							    $("INPUT[name=password1]", $frm).val("");
							    $("INPUT[name=password2]", $frm).val("");
						       }
						       if(message.status == 2) {
							   var txt = $.booki._('passwordwrongold', '');
							   $('DIV.notificationpassword').html('<p class="alert-box">'+txt+'</p>');
							   $("INPUT[name=password0]", $frm).css('border', '1px solid red');
						       }
						       if(message.status == 3) {
							   var txt = $.booki._('passwordnotequal', '');
							   $('DIV.notificationpassword').html('<p class="alert-box">'+txt+'</p>');
							   $("INPUT[name=password1]", $frm).css('border', '1px solid red');
							   $("INPUT[name=password2]", $frm).css('border', '1px solid red');
						       }
						   }
						   
						   $.booki.ui.notify("");
					       });
		    return false;
		});

	    
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
					       if(data.result == true) {
						   var $dashboard = $("#tabs-dashboard");
						   $("SECTION.basic-info > P", $dashboard).html(data.info.fullname);
						   var img = $("SECTION.basic-info  FIGURE", $dashboard);
						   img.html(data.info.image);
						   
						   // this should be enough random for now
						   //img.attr("src", img.attr("src")+"?"+Math.floor(Math.random()*100));
						   
						   $("SECTION.profile-description > P.des-text", $dashboard).html(data.info.description);
					       }
					   });
		
	    }
	}; 
    }();
	


    });
