  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/ephemera', 'block/block', 'block/blockmanager'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Ephemera, block, BlockManager) {


  			 var switchFor = function($container, $values, tagName) {
  			 	var $t = $container.find("h"+tagName);

  			 	if($t.length > 0) {
  			 		$values.find(".heading-"+tagName).text($t.text());
  			 	}
  			 }  			 

  			 var getValue = function($values, tagName) {
  			 	var $t = $values.find(".heading-"+tagName);

  			 	if($t.length > 0)
  			 		return $t.text();

  			 	return '';
  			 }

			 var TitleBlock = block.AbstractBlock.extend({
				      title: 'Title',
				      isDraggable: function() {return false;},
				      init: function($element, postProcessFn) {			 
//				      	$element.replaceWith('<div style="color: red">OVO JE NASLOV</div>');

//    				      	return postProcessFn();
	
                      	var style = booktype.editor.data.activeStyle;
				      	var $n = jQuery19('<div style="display: none;"></div>');

                        if(jQuery19('.heading-1', $element).length == 0) {
                                $element.append(jQuery19('<span class="heading-1">'+booktype._('title_heading_content', 'Heading content')+'</span>'));
                        }

                        if(jQuery19('.heading-2', $element).length == 0)
                                $element.append(jQuery19('<span class="heading-2">'+booktype._('title_sub_heading_content', 'Sub heading content')+'</span>'));

                        if(jQuery19('.heading-3', $element).length == 0)
                                $element.append(jQuery19('<span class="heading-3">'+booktype._('title_author_content', "Author's name")+'</span>'));

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

                      	switchFor($container, $values, '1');
                      	switchFor($container, $values, '2');
                      	switchFor($container, $values, '3');

                      	switch(style) {
                      		case 'style2':
		                      	  $container.empty();
						      	  $container.append('<h3 class="aloha-editable">'+getValue($values, '3')+'</h3>');                      	  
						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, '2')+'</h2>');
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, '1')+'</h1>');
						      	  break;
                      		case 'style3':
		                      	  $container.empty();
						      	  $container.append('<h3 class="aloha-editable">'+getValue($values, '3')+'</h3>');                      	  
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, '1')+'</h1>');
						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, '2')+'</h2>');						      	  
						      	  break;
                      		case 'style4':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, '1')+'</h1>');		                      	  
						      	  $container.append('<h3 class="aloha-editable">'+getValue($values, '3')+'</h3>');                      	  
						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, '2')+'</h2>');						      	  
						      	  break;
                      		case 'style5':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, '1')+'</h1>');
						      	  $container.append('<h3 class="aloha-editable">'+getValue($values, '3')+'</h3>');                      	  						      	  
						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, '2')+'</h2>');						      	  
						      	  break;
						    case 'style6':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, '1')+'</h1>');
								  break;						    
                      		case 'style7':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, '1')+'</h1>');
						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, '2')+'</h2>');						      	  
						      	  break;
						    case 'style8':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, '1')+'</h1>');
								  break;						    
						    case 'style9':
		                      	  $container.empty();
						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, '1')+'</h1>');
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

         	        jQuery19(document).on('booktype-style-changed', function($event, sid) {         	        			  				
         	        	jQuery19.each(jQuery('span.aloha-book-title'), function(i, v) {
         	        		var b = BlockManager.getBlock(jQuery19(v));

         	        		b.attr('style', sid);
         	        	});
         	        });

					Aloha.bind('aloha-editable-created', function($event, editable) {
		  				var $h1 = editable.obj.find('h1');  				
		  				var $headings = editable.obj.find('.bod-heading');

		  				var $span = jQuery('<span class="aloha-book-title"></span>');

		  				if($headings.length > 0) {
		  					var $parent = $headings.eq(0);

	  						$parent.addClass('aloha-book-title');

	  						$parent.alohaBlock({'aloha-block-type': 'TitleBlock'});							

 	                  	    editable.setUnmodified();
 	                  	    return true;
		  				} 

		  				if($h1.length > 0) {
		  					var $parent = $h1.eq(0).parent();

	  				        var $_h1 = $h1.eq(0);
	  				        var title = $_h1.text();
	  				        $_h1.wrap($span);
	  				        var $parent = $_h1.parent();
	  				        $parent.empty().append('<span class="heading-1">'+title+'</span>');
	  				        $parent.alohaBlock({'aloha-block-type': 'TitleBlock'});
		  				

	                  	   editable.setUnmodified();
	                  	   return true;
	                  	}
					});

		        },		        
  				makeClean: function(obj) {
                  jQuery(obj).find('.aloha-book-title').each(function() {
                    var $this = jQuery(this);

                  	var $container = $this.find('div').eq(0);     	        		
        		    var $values = $this.find('div').eq(1);

        		    var _get = function(headingNum) {
        		    	if($container.find("h"+headingNum).length > 0) {
        		    		return $container.find("h"+headingNum).text();
        		    	} else {
        		    		return $values.find(".heading-"+headingNum).text();
        		    	}
        		    }

 	        		var $newNode = jQuery('<span class="bod-heading"><span class="heading-1">'+_get('1')+'</span><span class="heading-2">'+_get('2')+'</span><span class="heading-3">'+_get('3')+'</span></span>');
                    $this.replaceWith($newNode);
                  });
  				}
		    });

  		}
);