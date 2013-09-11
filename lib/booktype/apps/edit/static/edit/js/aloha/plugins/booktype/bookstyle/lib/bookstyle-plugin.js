  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'booktype'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, Booktype) {

  			var TRANSFORMATORS = {

  				'style1': {
  					'transform': function() {
			      		var $editor = jQuery('#contenteditor');

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
  					'transform': function() {
			      		var $editor = jQuery('#contenteditor');

			      		jQuery('p', $editor).each(function(i, elem) {
			      			var $p = jQuery(elem);

			      			if(!$p.hasClass('normal')) {
			      				$p.addClass('normal');
			      			}		      			
			      		});  						
  					}
  				},

  				'style3': {
  					'transform': function() {

  					}
  				}
  			}

  			var checkContent = function() {
  				var selectedStyle = booktype.editor.data.activeStyle;
  				// This is hard coded now
  				selectedStyle = 'style1';

  				TRANSFORMATORS[selectedStyle].transform();
  			}

  			return Plugin.create('bookstyle', {
		        init: function () {
	        		  // Exclude THIS class from the content at the end
	        	      Ephemera.classes('bod-normal');
	        	      Ephemera.classes('bod-first');
	        	      Ephemera.classes('bod-word');

	                  Aloha.bind('aloha-editable-created', function(e, editable) {
	                  	checkContent();
					  });

				      Aloha.bind('aloha-smart-content-changed', function(evt) {
	                  	checkContent();				      	
				      })
		        }
		    });

  		}
);