$(function() {
    /* booki.editor */
	
    jQuery.namespace('jQuery.booki.profile');
    
    jQuery.booki.profile = function() {

	return {
	    _initUI: function() {

		$("#mood INPUT[type='text']").focus(function() {
		    if ($.booki.profileName == $.booki.username)
			$(this).val("");
		});


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
							   alert("ERROR. DID NOT CREATE NEW GROUP.");
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
/*
{
'origin': u'', 
'summary_detail': {'base': u'http://status.flossmanuals.net/agfa/rss', 'type': 'text/html', 'value': u"agfa's status on Saturday, 15-Jan-11 17:20:47 UTC", 'language': None}, 'foaf_maker': u'', 
'updated_parsed': time.struct_time(tm_year=2011, tm_mon=1, tm_mday=15, tm_hour=17, tm_min=20, tm_sec=47, tm_wday=5, tm_yday=15, tm_isdst=0), 
'links': [{'href': u'http://status.flossmanuals.net/notice/26', 'type': 'text/html', 'rel': 'alternate'}], 
'title': u'agfa: @agfa eto ti ga na!', 
'has_creator': u'', 
'author': u'agfa', 
'updated': u'2011-01-15T17:20:47+00:00', 
'summary': u"agfa's status on Saturday, 15-Jan-11 17:20:47 UTC", 
'content': [{'base': u'http://status.flossmanuals.net/agfa/rss', 'type': 'text/html', 'value': u'@<span class="vcard"><a href="http://status.flossmanuals.net/user/9" class="url"><span class="fn nickname">agfa</span></a></span> eto ti ga na!', 'language': None}], 'title_detail': {'base': u'http://status.flossmanuals.net/agfa/rss', 'type': 'text/plain', 'value': u'agfa: @agfa eto ti ga na!', 'language': None}, 'link': u'http://status.flossmanuals.net/notice/26', 'has_discussion': u'', 'licence': u'', 'id': u'http://status.flossmanuals.net/notice/26', 'posticon': u''}
*/
					  
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
