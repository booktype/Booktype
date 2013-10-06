  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'booktype'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, Booktype) {

  			var TRANSFORMATORS = {

  				'style1': {
  					'transform': function(editable) {
			      		var $editor = jQuery(editable.obj);

			      		jQuery('p', $editor).each(function(i, elem) {
			      			var $p = jQuery(elem);

			      			if(i == 0) {
				      			if(!$p.hasClass('bod-first')) {
				      				$p.addClass('bod-first');
				      			}

				      			if(jQuery('span.bod-word', $p).length == 0) {
				      				var content = $p.text();
				      				var words = content.split(' ');

				      				if(words.length > 2) {
					      				var newWords = words.slice(2);
					      				$p.text(newWords.join(' '));

					      				$p.prepend('<span class="bod-word">'+words.slice(0, 2).join(' ')+'</span> ');
					      			}
				      			} else {
				      				// TODO:
				      				// This part MUST be done using TextNode and not like this !
				      				// As it is now, it is just for demo and proof of concept

				      				var $span = jQuery('span:first-child', $p);
				      				var content = $span.text();
				      				var words = content.split(' ');

				      				if(words.length > 2) {
				      					var entire = $p.text();
				      					var allWords = entire.split(' ');
				      					$p.text(' '+allWords.splice(2).join(' '));
					      				$p.prepend('<span class="bod-word">'+allWords.slice(0, 2).join(' ')+'</span> ');
				      				} else {
				      					// what if it is smaller
				      				}
				      			}		      			
			      			} else {
				      			if(!$p.hasClass('bod-normal')) {
				      				$p.addClass('bod-normal');
				      			}	

				      			if($p.hasClass('bod-first')) {
				      				$p.removeClass('bod-first');

				      				var $span = jQuery('span:first-child', $p);
				      				var content = $span.text();

				      				$span.remove();
				      				$p.text(content + $p.text());
				      			}
				      		}
			      		});  					
			      	}	
  				},

  				'style2': {
  					'transform': function(editable) {
			      		var $editor = jQuery(editable.obj);

			      		jQuery('p', $editor).each(function(i, elem) {
			      			var $p = jQuery(elem);

			      			if(!$p.hasClass('bod-normal')) {
			      				$p.addClass('bod-normal');
			      			}		      			
			      		});  						
  					}
  				},

  				'style3': {
  					'transform': function(editable) {

  					}
  				}
  			}

  			var checkContent = function(editable) {
  				var selectedStyle = booktype.editor.data.activeStyle;
  				// This is hard coded now
  				selectedStyle = 'style1';

  				TRANSFORMATORS[selectedStyle].transform(editable);
  			}

  			return Plugin.create('bookstyle', {
  				defaultSettings: {
  					dynamicFormatting: false
  				},

		        init: function () {
		        	   var self = this;

		        	   // For unknown reasons this.defaults is not working as it should
                       self.settings = jQuery.extend(true, self.defaultSettings, self.settings);		        	   

	        		   if(self.settings.dynamicFormatting) {
		        	      Ephemera.classes('bod-normal');
		        	      Ephemera.classes('bod-first');
		        	      Ephemera.classes('bod-word');
	                   }

	                   Aloha.bind('aloha-editable-created', function($event, editable) {
   	                  	   if(self.settings.dynamicFormatting) {
		                  	   checkContent(editable);
		                   }

						   if(self.settings.dynamicFormatting)
		                  	   editable.setUnmodified();
					  });

				      Aloha.bind('aloha-smart-content-changed', function($event, params) {
   	                  	   if(self.settings.dynamicFormatting) {				      	
	                  	       checkContent(params.editable);				      	
	                  	   }
				      })
		        }
		    });

  		}
);