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
						    //						    window.location = '{{ redirect }}';
						    window.location = redirectURL;
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
			    var username   = $("INPUT[name=username]", $this).val();
			    var email      = $("INPUT[name=email]", $this).val();
			    var password   = $("INPUT[name=password]", $this).val();
			    //var password2  = $("INPUT[name=password2]", $this).val();
			    var fullname   = $("INPUT[name=fullname]", $this).val();
			    
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


