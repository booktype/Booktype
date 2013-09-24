  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'block/block', 'block/blockmanager'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, block, BlockManager) {

			 var TitleBlock = block.AbstractBlock.extend({
				      title: 'Title',
				      isDraggable: function() {return false;},
				      init: function($element, postProcessFn) {			 	
				      	//$element.append('<h3>12-09-2013</h3>');

				      	return postProcessFn();
				      },
                      update: function($element, postProcessFn) {

				      	return postProcessFn();
				 	  }
			    });  			


  			return Plugin.create('booktitle', {
  				defaultSettings: {
  					enabled: true,
  				},  				
		        init: function () {
		        	var self = this;

                    self.settings = jQuery.extend(true, self.defaultSettings, self.settings);			        	

		        	if(!self.settings.enabled) { return; }

				    Ephemera.attributes('data-aloha-block-type', 'contenteditable');
					
                    BlockManager.registerBlockType('TitleBlock', TitleBlock);

         	        var a = Ephemera.ephemera().pruneFns.push(function(node) {
         	        	var $node = jQuery(node);

         	        	if($node.hasClass("aloha-book-title")) {
         	        		$node.replaceWith('<h1>'+$node.find('h1').text()+'</h1>');
         	            }

         	        	return node;
         	        })

					Aloha.bind('aloha-editable-created', function($event, editable) {
						 editable.obj.find('span.aloha-book-title:not(.aloha-block)').alohaBlock({'aloha-block-type': 'TitleBlock'});						
						 editable.obj.find('span.aloha-book-title h1').addClass('aloha-editable');
					});

		        }
		    });

  		}
);