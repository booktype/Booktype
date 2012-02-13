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
    /* booki.group */
	
    jQuery.namespace('jQuery.booki.group');
    
    jQuery.booki.group = function() {

	return {
	    _initUI: function() {
		$("#tabs").tabs();
		$("#tabs A.butt").button();

		$("#tabgroup A.buttjoin").button().click(function() {
		    jQuery.booki.sendToChannel("/booki/group/"+$.booki.groupNameURL+"/", 
					       {"command": "join_group"
					       },
					       
					       function(message) {
						   window.location = '';
					       });
		});

		$("#tabgroup A.buttleave").button().click(function() {
		    jQuery.booki.sendToChannel("/booki/group/"+$.booki.groupNameURL+"/", 
					       {"command": "leave_group"
					       },
					       
					       function(message) {
						   window.location = '';
					       });
		});

	    },

	    /* load initial data */
	    
	    _loadInitialData: function() {
		jQuery.booki.sendToChannel("/booki/group/"+$.booki.groupNameURL+"/", 
					   {"command": "init_group",
					    "profile": $.booki.groupName
					   },

					   function(message) {
					       $.booki.ui.notify("");
					   });
	    },
	    
	    /* initialize group */
	    
	    initGroup: function() {
		jQuery.booki.subscribeToChannel("/booki/group/"+$.booki.groupNameURL+"/", function(message) {
		    var funcs = {
			
		    };

		    if(funcs[message.command]) {
			funcs[message.command]();
		    }
		    
		});
		
		$.booki.group._loadInitialData();
		$.booki.group._initUI();
	    }
	}; 
    }();
	


    });
