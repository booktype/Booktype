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

// booksparkSignin
// booksparkRegister

(function( $ ){
    var postURL;
    var redirectURL;
    var redirectRegisterURL;

    function showNotification(whr, msg) {
	$(whr).find("*").addClass('template');
	$(whr).find(msg).removeClass('template');
    }

    var methodsSignin = {
	init : function( options ) {
	    if(options) {
		postURL = options.url || '';
		redirectURL = options.redirect || '';
	    }

	    return this.each(function(){
		    var $this = $(this);

		    $('INPUT[type=submit]', $this).button().click(function() {
			    var username = $("INPUT[name=username]", $this).val();
			    var password = $("INPUT[name=password]", $this).val();

			    $.post(postURL, {'ajax': '1',
					     'method': 'signin',
					     'username': username,
					     'password': password},

        		                    function(data) {
						var whr = $('.notify', $this);

						switch(data.result) {
						case 1: // Everything is ok
						    if(redirectURL != '')
							window.location = redirectURL;
						    else {
							if(typeof data.redirect != 'undefined')
							    window.location = data.redirect;
							else
							    window.location = '';
						    }
						    return;
						case 2:  // User does not exist
						    showNotification(whr, '.no-such-user');
						    $("INPUT[name=username]", $this).focus().select();
						    break;
						case 3: // Wrong password 
						    showNotification(whr, '.wrong-password');
						    $("INPUT[name=password]", $this).focus().select();
						    break;
						    
						default: // Unknown error
						    showNotification(whr, '.unknown-error');
						}
						
					    }, 'json');
			});
		    return true;
		})}
    };

    var methodsRegister = {
	init : function( options ) {
	    if(options) {
		postURL = options.url || '';
		redirectRegisterURL = options.redirect || '';
	    }

	    return this.each(function(){
		    var $this = $(this);

		    $('INPUT[type=submit]', $this).button().click(function() {
			    var username   = $.trim($("INPUT[name=username]", $this).val());
			    var email      = $.trim($("INPUT[name=email]", $this).val());
			    var password   = $.trim($("INPUT[name=password]", $this).val());
			    //var password2  = $("INPUT[name=password2]", $this).val();
			    var fullname   = $.trim($("INPUT[name=fullname]", $this).val());

			    var whr = $('.notify', $this);
			    showNotification(whr, '#clear');

			    $.post(postURL, {'ajax': '1',
					     'method': 'register',
					     'username':  username,
					     'password':  password,
					     'password2': password,
					     'email':     email,
   					     'fullname':  fullname,
					      'groups': '[]'
					},
					//'groups':    $.toJSON(groupsToJoin)},

				function(data) {
				    switch(data.result) {
				    case 1: // Everything is ok
					window.location = redirectRegisterURL.replace('XXX', username);
					return;

				    case 2: // Missing username
					showNotification(whr, '.missing-username');
					$("INPUT[name=username]", $this).focus().select();
					break;
					
				    case 3: // Missing email
					showNotification(whr, '.missing-email');
					$("INPUT[name=email]", $this).focus().select();
					break;
					
				    case 4: // Missing password
					showNotification(whr, '.missing-password');
					$("INPUT[name=password]", $this).focus().select();
					break;
					
				    case 5: // Missing fullname
					showNotification(whr, '.missing-fullname');
					$("INPUT[name=fullname]", $this).focus().select();
					break;
					
				    case 6: // Wrong username
					showNotification(whr, '.invalid-username');
					$("INPUT[name=username]", $this).focus().select();
					break;
					
				    case 7: // Wrong email
					showNotification(whr, '.invalid-email');
					$("INPUT[name=email]", $this).focus().select();
					break;
					
				    case 8: // Password does not match
					showNotification(whr, '.password-mismatch');
					$("INPUT[name=password]", $this).focus().select();
					break;
					
				    case 9: // Password too small
					showNotification(whr, '.invalid-password');
					$("INPUT[name=password]", $this).focus().select();
					break;

				    case 10: // Username exists
					showNotification(whr, '.username-taken');
					$("INPUT[name=username]", $this).focus().select();
					break;
					
				    case 11: // Full name too long
					showNotification(whr, '.fullname-toolong');
					$("INPUT[name=fullname]", $this).focus().select();
			   break;

			   
		       default: // Unknown error
			   showNotification(whr, '.unknown-error');
		       }
		   }, 'json');

			});
		    return true;
		})}
    };
    
    
    $.fn.booksparkSignin = function( method ) {       
	if ( methodsSignin[method] ) {
	    return methodsSignin[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
	} else if ( typeof method === 'object' || ! method ) {
	    return methodsSignin.init.apply( this, arguments );
	} 
    };

    $.fn.booksparkRegister = function( method ) {	
	if ( methodsRegister[method] ) {
	    return methodsRegister[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
	} else if ( typeof method === 'object' || ! method ) {
	    return methodsRegister.init.apply( this, arguments );
	} 
    };

    
})( jQuery );

// booksparkCreateBook

(function( $ ){
    var postURL;
    var rootURL;

    var methods = {
	init : function( options ) {
	    if(options) {
		postURL = options.url || '';
		rootURL = options.rooturl || '';
	    }

	    return this.each(function(){
		    var $this = $(this);
		    var steps;

		    function showStep(d, stepID) {
			$(steps).css("display", "none");				    
			$(steps[stepID]).css("display", "block");
			
			/*
			if(stepID == 1) {
			    $("TEXTAREA", d).tinymce({script_url : rootURL+'/site_static/js/tiny_mce/tiny_mce.js',
					theme : "simple"});							    
			}
			*/
		    }

		    $this.click(function() {
			    var stepIndex = 0;
			    var buttons;

			    $(".createbookClass").remove();

			    var $d = $("<span/>").load(postURL, function() {				    
				    steps = $(".step", $d);

				    showStep($d, 0);
				    
				    var dialog = $("DIV.dialog", $d);

				    //$("TEXTAREA", dialog).tinymce({script_url : rootURL+'/site_static/js/tiny_mce/tiny_mce.js',
				    //		theme : "simple"});

				    // MUST CHECK IF IT ONLY HAS name filled

				    $(".dialog", $d).dialog({"modal":    true,
						"dialogClass": "createbookClass",
						"width":   600,
						"height":  400,
						"autoOpen": true,
						"open": function(event, ui) {
						    stepIndex = 0;

						    buttons = $('.createbookClass .ui-dialog-buttonpane button');
						    $(buttons[0]).attr('disabled', 'disabled');
						    $(buttons[1]).attr('disabled', 'disabled');
						    $(buttons[2]).attr('disabled', '');
						    $(buttons[3]).attr('disabled', '');

						    $("INPUT[name=title]", dialog).keyup(function() {
							    $.getJSON(postURL, {"q": "check", "bookname": $(this).val()}, function(data) {
								    if(data.available) {
									$(".bookexists", dialog).css("display", "none");
									$(buttons[1]).attr('disabled', '');								
								    } else {
									$(".bookexists", dialog).css("display", "block");
									$(buttons[1]).attr('disabled', 'disabled'); 
								    }
								});

							});

					         },
						"close": function(event, ui) {
						},
						"buttons": [{"text": "Back",
							     "click": function() { 
							                 stepIndex -= 1;
					                                 showStep(dialog, stepIndex);

									 $(buttons[3]).attr('disabled', '');
									 if(stepIndex == 0)
									     $(buttons[0]).attr('disabled', 'disabled');
						              }
  						            },

						            {"text": "Create",
							     "click": function() { 
								    var $dialog = $(this);
								    var frm = $("FORM", dialog);

								    $(frm).submit();
						              }
  						            },

						            {"text": "Cancel",
							     "click": function() { 
								    $(this).dialog('close');
						              }
  						            },

						            {"text": "Next",
							     "click": function() { 
							                 stepIndex += 1;
					                                 showStep(dialog, stepIndex);

									 $(buttons[0]).attr('disabled', '');
									 if(stepIndex == steps.length-1)
									     $(buttons[3]).attr('disabled', 'disabled');
						              }
  						            }
						    ]
						});
				});

			    return false;
			});
		});
	    return true;
	}
    };

        
    $.fn.booksparkCreateBook = function( method ) {       
	if ( methods[method] ) {
	    return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
	} else if ( typeof method === 'object' || ! method ) {
	    return methods.init.apply( this, arguments );
	} 
    };

})( jQuery );


// booksparkCreateGroup

(function( $ ){
    var postURL;
    var rootURL;

    var methods = {
	init : function( options ) {
	    if(options) {
		postURL = options.url || '';
		rootURL = options.rooturl || '';
	    }

	    return this.each(function(){
		    var $this = $(this);

		    $this.click(function() {
			    var stepIndex = 0;

			    $(".creategroupClass").remove();

			    var $d = $("<span/>").load(postURL, function() {				    
				    var dialog = $("DIV.dialog", $d);

				    $(".dialog", $d).dialog({"modal":    true,
						"dialogClass": "creategroupClass",
						"width":   600,
						"height":  400,
						"autoOpen": true,
						"open": function(event, ui) {
						    $("INPUT[name=title]", dialog).keyup(function() {
							    $.getJSON(postURL, {"q": "check", "groupname": $(this).val()}, function(data) {
								    if(data.available) {
									$(".groupexists", dialog).css("display", "none");
								    } else {
									$(".groupexists", dialog).css("display", "block");
								    }
								});
							});
					         },
						"close": function(event, ui) {
						},
						"buttons": [
						            {"text": "Cancel",
							     "click": function() { 
								    var $dialog = $(this);
								    $dialog.dialog('close');
						              }
  						            },

						            {"text": "Create",
							     "click": function() { 
								    var $dialog = $(this);
								    var frm = $("FORM", $dialog);

								    $.getJSON(postURL, {"q": "create", 
										        "name": $("INPUT[name=title]", frm).val(),
										        "description": $("TEXTAREA", frm).val()}, 
									       function(data) {
										   if(data.created == true) {
										       window.location='';
										   } else {
										       // this has to be translated and etc...
										       alert("Couldn't create a group!");
										   }
									       });
						              }
  						            }
						    ]
						});
				});
			    
			    return false;
			});
		});
	    return true;
	}
    };

        
    $.fn.booksparkCreateGroup = function( method ) {       
	if ( methods[method] ) {
	    return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
	} else if ( typeof method === 'object' || ! method ) {
	    return methods.init.apply( this, arguments );
	} 
    };

})( jQuery );



// booksparkImportBook

(function( $ ){
    var postURL;
    var rootURL;

    var methods = {
	init : function( options ) {
	    if(options) {
		postURL = options.url || '';
		rootURL = options.rooturl || '';
	    }

	    return this.each(function(){
		    var $this = $(this);

		    $this.click(function() {
			    var buttons;

			    $(".importbookClass").remove();

			    var $d = $("<span/>").load(postURL, function() {				    
				    var dialog = $("DIV.dialog", $d);

				    $(".dialog", $d).dialog({"modal":    true,
						"dialogClass": "importbookClass",
						"width":   600,
						"height":  400,
						"autoOpen": true,
						"open": function(event, ui) {
						    buttons = $('.importbookClass .ui-dialog-buttonpane button');

						    $(buttons[1]).attr('disabled', 'disabled');

						    // must translate this
						    var values = {"epub": "enter epub URL",
								  "flossmanuals": "enter FLOSS Manuals ID",
								  "archive": "enter Archive.org ID",
								  "wikibooks": "enter Wikibooks URL",
								  "booki": "enter Booktype URL"                                                                
						    };

						    $("SELECT", dialog).change(function() {
							    $("INPUT[name=source]", dialog).val(values[$(this).val()]).select();
							    if(typeof values[$(this).val()] != 'undefined')
								$(buttons[1]).attr('disabled', '');								
						    });
					         },
						"close": function(event, ui) {
						},
						"buttons": [
						            {"text": "Cancel",
							     "click": function() { 
								    var $dialog = $(this);
								    $dialog.dialog('close');
						              }
  						            },

						            {"text": "Import",
							     "click": function() { 
								    var $dialog = $(this);
								    var isHidden = '';

								    $(buttons[0]).attr('disabled', 'disabled');
								    $(buttons[1]).attr('disabled', 'disabled');

								    if($("INPUT[name=hidden]", dialog).is(':checked'))
									isHidden = 'on';

								    var dta = {"q": "import", 
										"source": $("INPUT[name=source]", dialog).val(),
										"title": $("INPUT[name=title]", dialog).val(), 
										"hidden": isHidden,
										"importtype": $("SELECT[name=importtype]", dialog).val()};

								    $('.forms', dialog).css("display", "none");
								    $('.importmessage', dialog).css("display", "block");

								    $.getJSON(postURL, dta,
									       function(data) {
										   $dialog.dialog('close');

										   if(typeof data.info_url != 'undefined')
										       window.location = data.info_url;
								               });
						              }
  						            }
						    ]
						});
				});

			    return false;
			});
		});
	    return true;
	}
    };

        
    $.fn.booksparkImportBook = function( method ) {       
	if ( methods[method] ) {
	    return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
	} else if ( typeof method === 'object' || ! method ) {
	    return methods.init.apply( this, arguments );
	} 
    };

})( jQuery );


// booksparkEditBookInfo

(function( $ ){
    var postURL;
    var rootURL;

    var methods = {
	init : function( options ) {
	    if(options) {
		postURL = options.url || '';
		rootURL = options.rooturl || '';
	    }

	    return this.each(function(){
		    var $this = $(this);

		    $this.click(function() {

			    var $d = $("<span/>").load(postURL, function() {				    
				    var dialog = $("DIV.dialog", $d);

				    $(".dialog", $d).dialog({"modal":    true,
						"dialogClass": "editinfoClass",
						"width":   600,
						"height":  450,
						"autoOpen": true,
						"open": function(event, ui) {
						    stepIndex = 0;
					         },
						"close": function(event, ui) {
						},
						"buttons": [{"text": "Cancel",
							     "click": function() { 
							    $(this).dialog('close');
							      }
							     },
         
						            {"text": "Save changes",
							     "click": function() { 
								    var $dialog = $(this);
								    var frm = $("FORM", dialog);

								    $(frm).submit();
						              }
  						            }
						    ]
						});
				});


			});
		});
	    return true;
	}
    };

        
    $.fn.booksparkEditBookInfo = function( method ) {       
	if ( methods[method] ) {
	    return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
	} else if ( typeof method === 'object' || ! method ) {
	    return methods.init.apply( this, arguments );
	} 
    };

})( jQuery );
