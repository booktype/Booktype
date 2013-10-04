  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/ephemera', 'block/block', 'block/blockmanager'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Ephemera, block, BlockManager) {


  			 var switchFor = function($container, $values, tagName) {
  			 	var $t = $container.find(tagName);

  			 	if($t.length > 0) {
  			 		$values.find(tagName).text($t.text());
  			 	}
  			 }  			 

  			 var getValue = function($values, tagName) {
  			 	var $t = $values.find(tagName);

  			 	if($t.length > 0)
  			 		return $t.text();

  			 	return '';
  			 }

			 var TitleBlock = block.AbstractBlock.extend({
				      title: 'Title',
				      isDraggable: function() {return false;},
				      init: function($element, postProcessFn) {			 	
				      	console.log('=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-');
				      	console.log('INIT BLOCK');

                      	var style = booktype.editor.data.activeStyle;			      	
				      	var $n = jQuery19('<div style="display: none;"></div>');

				      	if(jQuery19('h1', $element).length == 0) {
				      		$element.append(jQuery19('<h1>Heading</h1>'));
				      	}

				      	if(jQuery19('h2', $element).length == 0)
				      		$element.append(jQuery19('<h2>Sub heading</h2>'));

				      	if(jQuery19('h3', $element).length == 0)
				      		$element.append(jQuery19('<h3>Author</h3>'));

				      	var $children = $element.children().clone();

				      	// Find h1, h2, h3
				      	var h1 = $children.eq(0).text();
				      	var h2 = $children.eq(1).text();
				      	var h3 = $children.eq(2).text();

				      	$element.empty();

				      	// Add to the empty part				      	
				      	$n.append($children);

				      	// This depends of the style

				      	switch(style) {
				      		case 'style1':
		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+h1+'</h1></div>');				      		
  				      		        break;
				      		case 'style2':
		    				      	$element.append('<div style=""><h3 class="aloha-editable">'+h3+'</h3><h2 class="aloha-editable">'+h2+'</h2><h1 class="aloha-editable">'+h1+'</h1></div>');
		    				      	break;
				      		case 'style3':
		    				      	$element.append('<div style=""><h3 class="aloha-editable">'+h3+'</h3><h1 class="aloha-editable">'+h1+'</h1><h2 class="aloha-editable">'+h2+'</h2></div>');
		    				      	break;
				      		case 'style4':
		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+h1+'</h1><h3 class="aloha-editable">'+h3+'</h3><h2 class="aloha-editable">'+h2+'</h2></div>');
		    				      	break;
				      		case 'style5':
		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+h1+'</h1><h3 class="aloha-editable">'+h3+'</h3><h2 class="aloha-editable">'+h2+'</h2></div>');
		    				      	break;
				      		case 'style6':
		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+h1+'</h1></div>');				      		
  				      		        break;
				      		case 'style7':
		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+h1+'</h1><h2 class="aloha-editable">'+h2+'</h2></div>');
		    				      	break;
				      		case 'style8':
		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+h1+'</h1></div>');				      		
  				      		        break;
				      		case 'style9':
		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+h1+'</h1></div>');				      		
  				      		        break;


   				        }

				      	$element.append($n);

				      	return postProcessFn();
				      },
                      update: function($element, postProcessFn) {
                      	var style = booktype.editor.data.activeStyle;
                      	var $container = $element.find('div').eq(0);
                      	var $values = $element.find('div').eq(1);

                      	switchFor($container, $values, 'h1');
                      	switchFor($container, $values, 'h2');
                      	switchFor($container, $values, 'h3');

                      	switch(style) {
                      		case 'style2':
		                      	  $container.empty();
						      	  $container.append('<h3 class="aloha-editable">'+getValue($values, 'h3')+'</h3>');                      	  
						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, 'h2')+'</h2>');
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'h1')+'</h1>');
						      	  break;
                      		case 'style3':
		                      	  $container.empty();
						      	  $container.append('<h3 class="aloha-editable">'+getValue($values, 'h3')+'</h3>');                      	  
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'h1')+'</h1>');
						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, 'h2')+'</h2>');						      	  
						      	  break;
                      		case 'style4':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'h1')+'</h1>');		                      	  
						      	  $container.append('<h3 class="aloha-editable">'+getValue($values, 'h3')+'</h3>');                      	  
						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, 'h2')+'</h2>');						      	  
						      	  break;
                      		case 'style5':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'h1')+'</h1>');
						      	  $container.append('<h3 class="aloha-editable">'+getValue($values, 'h3')+'</h3>');                      	  						      	  
						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, 'h2')+'</h2>');						      	  
						      	  break;
						    case 'style6':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'h1')+'</h1>');
								  break;						    
                      		case 'style7':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'h1')+'</h1>');
						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, 'h2')+'</h2>');						      	  
						      	  break;
						    case 'style8':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'h1')+'</h1>');
								  break;						    
						    case 'style9':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'h1')+'</h1>');
								  break;						    

						    default:
                         		jQuery19('h2', $container).remove();
                         		jQuery19('h3', $container).remove();                      		
                      	}

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
         	        		console.log($node);
	                      	var $container = $node.find('div').eq(0);     	        		
       	        		    var $values = $node.find('div').eq(1);

       	        		    var _get = function(tagName) {
       	        		    	if($container.find(tagName).length > 0) {
       	        		    		return $container.find(tagName).text();
       	        		    	} else {
       	        		    		return $values.find(tagName).text();
       	        		    	}
       	        		    }
	      	        		// first get from container and then values

         	        		var $newNode = jQuery19('<span class="bod-heading"><h1>'+_get('h1')+'</h1><h2>'+_get('h2')+'</h2><h3>'+_get('h3')+'</h3></span>');
         	        		$node.replaceWith($newNode);
         	            }

         	        	return node;
         	        })

         	        jQuery19(document).on('booktype-style-changed', function($event, sid) {
         	        	jQuery19.each(jQuery('span.aloha-book-title'), function(i, v) {
         	        		var b = BlockManager.getBlock(jQuery19(v));

         	        		b.attr('style', sid);
         	        	});
         	        });

					Aloha.bind('aloha-editable-created', function($event, editable) {
						editable.obj.find('span.aloha-book-title:not(.aloha-block)').alohaBlock({'aloha-block-type': 'TitleBlock'});						
					});

		        }
		    });

  		}
);