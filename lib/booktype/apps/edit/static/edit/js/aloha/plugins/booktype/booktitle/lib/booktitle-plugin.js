  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/ephemera', 'block/block', 'block/blockmanager', 'underscore', 'booktype', 'PubSub', 'toolbar/toolbar-plugin'], 
  		function(Aloha, Plugin, jQuery17,  jQuery, UI, Ephemera, block, BlockManager, _, booktype, PubSub, toolbar) {

  			 var switchFor = function($container, $values, tagName, textType) {
  			 	var $t = $container.find("h"+tagName);

  			 	if($t.length > 0) {
  			 		$values.find(".heading-"+textType).text($t.text());
  			 	}
  			 }  			 

  			 var getValue = function($values, textType) {
  			 	var $t = $values.find(".heading-"+textType);

  			 	if($t.length > 0)
  			 		return $t.text();

  			 	return '';
  			 }

			   var TitleBlock = block.AbstractBlock.extend({
				      title: 'Title',
				      isDraggable: function() {return false;},
				      init: function($element, postProcessFn) {			 	
                      	var style = booktype.editor.data.activeStyle;
                      	this.style = style;

          				      var $n = jQuery('<div style="display: none;"></div>');

                        if(jQuery('.heading-title', $element).length == 0) {
                                $element.append(jQuery('<span class="heading-title">'+booktype._('title_heading_content', 'Heading content')+'</span>'));
                        }

                        if(jQuery('.heading-author', $element).length == 0) {
                                $element.append(jQuery('<span class="heading-author">'+booktype.fullname+'</span>'));
                        }
//                                $element.append(jQuery('<span class="heading-2">'+booktype._('title_author_content', "Author's name")+'</span>'));

                        if(jQuery('.heading-description', $element).length == 0) {
                                $element.append(jQuery('<span class="heading-description">'+booktype._('title_sub_heading_content', 'Sub heading content')+'</span>'));
                        }

                        if(jQuery('.heading-date', $element).length == 0) {
                                var d = new Date();
                                $element.append(jQuery('<span class="heading-date">'+d.getDate()+'/'+(d.getMonth()+1)+'/'+d.getFullYear()+'</span>'));
                        }

        				      	var $children = $element.children().clone();

        				      	$element.empty();

        				      	// Add to the empty part				      	
        				      	$n.append($children);

        				      	// Find h1, h2, h3
        				      	var _title = $children.eq(0).text();
        				      	var _author = $children.eq(1).text();
        				      	var _description = $children.eq(2).text();
        				      	var _date = $children.eq(3).text();


        				      	// This depends of the style

        				      	switch(style) {
        				      		case 'style1':
        		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+_title+'</h1></div>');				      		
          				      		        break;
        				      		case 'style3':
        		    				      	$element.append('<div style=""><h3 class="aloha-editable aloha-title-date">'+_date+'</h3><h1 class="aloha-editable">'+_title+'</h1><h2 class="aloha-editable">'+_author+'</h2></div>');
        		    				      	break;
        				      		case 'style4':
        		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+_title+'</h1><h3 class="aloha-editable aloha-title-description">'+_description+'</h3><h2 class="aloha-editable">'+_author+'</h2></div>');
        		    				      	break;
        				      		case 'style6':
        		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+_title+'</h1></div>');				      		
          				      		        break;
        				      		case 'style7':
        		    				      	$element.append('<div style=""><h1 class="aloha-editable">'+_title+'</h1></div>');
        		    				      	break;
           				        }

        				      	$element.append($n);

        				      	return postProcessFn();
        				      },

                      update: function($element, postProcessFn) {
                      	var style = booktype.editor.data.activeStyle;
                      	var $container = $element.find('div').eq(0);
                      	var $values = $element.find('div').eq(1);

                      	// Depends of the previous style
                      	switch(this.style) {
                      		case 'style3':
		                      	switchFor($container, $values, '1', 'title');
		                      	switchFor($container, $values, '2', 'author');
		                      	switchFor($container, $values, '3', 'date');
	                      		break;	
                      		case 'style4':
		                      	switchFor($container, $values, '1', 'title');
		                      	switchFor($container, $values, '3', 'description');
		                      	switchFor($container, $values, '2', 'author');                      		
	                      		break;	
                      		case 'style6':
                      		case 'style7':                      		
		                      	switchFor($container, $values, '1', 'title');                      		
	                      		break;	
                      	}

                      	// Remember new style
                      	this.style = style;

                      	switch(style) {
                      		case 'style3':
		                      	  $container.empty();
        						      	  $container.append('<h3 class="aloha-editable aloha-title-date">'+getValue($values, 'date')+'</h3>');                      	  
				        		      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'title')+'</h1>');
						              	  $container.append('<h2 class="aloha-editable">'+getValue($values, 'author')+'</h2>');						      	  
						      	          break;
                      		case 'style4':
		                      	  $container.empty();
						      	          $container.append('<h1 class="aloha-editable">'+getValue($values, 'title')+'</h1>');	
        						      	  $container.append('<h3 class="aloha-editable aloha-title-description">'+getValue($values, 'description')+'</h3>');                      	  
        						      	  $container.append('<h2 class="aloha-editable">'+getValue($values, 'author')+'</h2>');						      	  
        						      	  break;
          						    case 'style6':
		                      	  $container.empty();
        						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'title')+'</h1>');
            								  break;						    
                      		case 'style7':
		                      	  $container.empty();
        						      	  $container.append('<h1 class="aloha-editable">'+getValue($values, 'title')+'</h1>');
        						      	  break;
          						    default:
                           		jQuery('h2', $container).remove();
                           		jQuery('h3', $container).remove();                      		
                        	}

          				      	return postProcessFn();
          				 	  }
          			    });  			 

        var _initHeadings = function(editable, unmodify) {
              var $h1 = editable.obj.find('h1');          
              var $headings = editable.obj.find('.bod-heading');

              var $span = jQuery('<span class="aloha-book-title"></span>');

              if($headings.length > 0) {
                var $parent = $headings.eq(0);

                $parent.addClass('aloha-book-title');

                $parent.alohaBlock({'aloha-block-type': 'TitleBlock'});             

                if(!_.isUndefined(unmodify) && unmodify==true)
                    editable.setUnmodified();

                return true;
              } 

              if($h1.length > 0) {
                 var $parent = $h1.eq(0).parent();

                   var $_h1 = $h1.eq(0);
                   var title = $_h1.text();

                   $_h1.wrap($span);

                   var $parent = $_h1.parent();

                   $parent.empty().append('<span class="heading-title">'+title+'</span>');
                   $parent.alohaBlock({'aloha-block-type': 'TitleBlock'});

                   if(!_.isUndefined(unmodify) && unmodify==true)
                      editable.setUnmodified();

                   return true;
              }          
        }


  			return Plugin.create('booktitle', {
  				defaultSettings: {
  					enabled: true
  			   	}, 
		      init: function () {
  		        	  var self = this;

                  self.settings = jQuery.extend(true, self.defaultSettings, self.settings);			        	

    		        	if(!self.settings.enabled) { return; }

      				    Ephemera.attributes('data-aloha-block-type', 'contenteditable');
    					
                  BlockManager.registerBlockType('TitleBlock', TitleBlock);

                  // User has changed style in the Style tab.
         	        jQuery(document).on('booktype-style-changed', function($event, sid) {      

                    // We need to update each block with new style information. Grab each Title block
                    // and setup new style attribute. This will make Title block refresh itself
         	        	jQuery.each(jQuery('span.aloha-book-title'), function(i, v) {
         	        		var b = BlockManager.getBlock(jQuery(v));

         	        		if(!_.isUndefined(b))
	         	        		b.attr('style', sid);
         	        	});
         	        });

                  var wasInHeading = false;

                  // Undo action will setup new html for the editable. This will destory
                  // all active blocks. We need to update them somehow. Undo will fire
                  // certain event, we bind to this event and recreate all of our blocks again.
                  Aloha.bind('aloha-my-undo', function(event, args) {
                    _initHeadings(args.editable, false);
                  });

                  PubSub.sub('aloha.selection.context-change', function(m){
                    var $block = jQuery(m.range.startContainer).closest('span.aloha-block-TitleBlock');

                    // List of buttons and menu items we want to manipulate with
                    var _buttons = ['insertImage', 'insertLink', 'table-dropdown', 'alignLeft', 'alignRight',
                                    'alignCenter', 'alignJustify', 'unorderedList', 'orderedList'];
                    var _menus = ['horizontalline', 'pbreak'];

                    if($block.length > 0) {
                      _.each(_buttons, function(btn) {
                        toolbar.disableToolbar(btn);
                      });

                      _.each(_menus, function(itm) {
                        toolbar.disableMenu(itm);
                      })

                      wasInHeading = true;
                    } else if(wasInHeading) {
                      _.each(_buttons, function(btn) {
                        toolbar.enableToolbar(btn);
                      });
                      
                      _.each(_menus, function(itm) {
                        toolbar.enableMenu(itm);
                      })

                      wasInHeading = false;
                    }

                    // Check if there is brandh new heading
                    var $blocks = Aloha.activeEditable.obj.find(".aloha-book-title");
                    var $headings = Aloha.activeEditable.obj.find("h1");

                    if($headings.length > 0 && $blocks.length == 0)
                      _initHeadings(Aloha.activeEditable, true);                    
                   });


        					Aloha.bind('aloha-editable-created', function($event, editable) {
                     _initHeadings(editable, true);
        					});

		        },		        
  				makeClean: function(obj) {
                  jQuery(obj).find('.aloha-book-title').each(function() {
                    var $this = jQuery(this);
                    var _title, _author, _description, _date;
                  	var $container = $this.find('div').eq(0);     	        		
        		        var $values = $this.find('div').eq(1);

                    var _get = function(headingNum, typeText) {
                        if($container.find("h"+headingNum).length > 0) {
                            return $container.find("h"+headingNum).text();
                        } else {
                            return $values.find(".heading-"+typeText).text();
                        }
                    }

                  	// Depends of the previous style
                  	switch(booktype.editor.data.activeStyle) {
                  		case 'style3':
                            _title = _get('1', 'title');
                            _date  = _get('3', 'date');
                            _description = _get('0', 'description');
                            _author = _get('2', 'author');
                      		break;	
                  		case 'style4':
                            _title = _get('1', 'title');
                            _date  = _get('0', 'date');
                            _description = _get('3', 'description');
                            _author = _get('2', 'author');                        
                      		break;	
                      case 'style1':
                  		case 'style6':
                  		case 'style7':                      		
                            _title = _get('1', 'title');
                            _date  = _get('0', 'date');
                            _description = _get('0', 'description');
                            _author = _get('0', 'author');                        
                      		break;	
                  	}

       	        		var $newNode = jQuery('<span class="bod-heading"><span class="heading-title">'+_title+'</span><span class="heading-author">'+_author+'</span><span class="heading-description">'+_description+'</span><span class="heading-date">'+_date+'</span></span>');
                    $this.replaceWith($newNode);
                  });
  				      }
		      });
  		}
);