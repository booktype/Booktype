  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'booktype', 'underscore'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, booktype, _, bootstrap) {
	  		var $a = null;
	  		var range = null;
	  		var editable = null;
	  		var getContainerAnchor = function(a) {
									      var el;
									      el = a;
									      while (el) {
									        if (el.nodeName.toLowerCase() === "a") {
									          return el;
									        }
									        el = el.parentNode;
									      }
									      return false;
									    };

  			return Plugin.create('linkBooktype', {
		        init: function () {
		        	var isLinkSelected = false;
		        	var isPopoverShown = false;
			  		Aloha.bind("aloha-link-selected",function(event){
			  			var range = event.target.Selection.rangeObject;
			  			var url = range.commonAncestorContainer.href;
			  			var url_value = range.endContainer.nodeValue; // which link is clicked
			  			console.log(url_value);
						isLinkSelected = true;
 					    	jQuery19('.templateAlohaContent a').each(function(cnt,e){ // go through all the links in current chapter
 					    		if(e.childNodes[0].data===url_value){
 					    			if(isPopoverShown===false){
										isPopoverShown = true;
	 					    			jQuery19(e).popover({html: true, content: "<a href='#' style='cursor:pointer;' onclick=\"window.open('"+url+"','_blank');\">"+url+"</a>"});
 					    				jQuery19(e).popover('show'); 
 					    			}
			 					    jQuery19(e).on('shown.bs.popover',function(){
 							    	jQuery19(e).popover('destroy');
 					    			isPopoverShown = false;
 					    			});
 					    		};
 					    	});
 					    	jQuery19(window).scroll (function(){ // remove popover when scrolling otherwise it shows over the toolbar
 					    		jQuery19('.templateAlohaContent a').each(function(cnt,e){ // just destroy them all
 					    			jQuery19(e).popover('destroy');
 					    			isPopoverShown = false;
 					    			console.log(e);
 					    			}); 					    		
 					    	});
	  					});

	  				Aloha.bind("aloha-link-unselected",function(event){
	  					if(isLinkSelected===true){  						
 					    	jQuery19('.templateAlohaContent a').each(function(cnt,e){ // just destroy them all
 					    		jQuery19(e).popover('destroy');
 					    		isPopoverShown = false;
 					    		console.log(e);
 					    	});
	  					}
	  					isLinkSelected = false;	 					
	  				});

			        // link to chapters
			        jQuery19('.linktochapter-header i').click(function() {
			            jQuery19(this).closest('.linktochapter').toggleClass('open');
			        });

			        jQuery19('#newLink').on('show.bs.modal', function() {
			        	var $dialog = jQuery19('#newLink');

						jQuery19('.linktochapter-content UL', $dialog).empty();

			        	_.each(booktype.editor.data.chapters.chapters, function(item) {
			        		var $link = jQuery19('<li><a href="#"><i class="icon-check-sign"></i>'+item.title+'</a></li>');

			        		jQuery19('a', $link).on('click', function() {
			        			jQuery19("#newLink INPUT[name=url]").val('../'+item.urlTitle+'/');

			        			return false;
			        		});
			        		jQuery19('.linktochapter-content UL', $dialog).append($link);
			        	});

				        jQuery19('.linktochapter .linktochapter-content li a').click(function() {
				        	console.log('KLIKNO');
				            jQuery19(this).closest('ul').find('li a').removeClass('selected');
				            jQuery19(this).addClass('selected');
				        });			        	
			        });

			        jQuery19('#newLink').on('hide.bs.modal', function () {
			            jQuery19('.linktochapter').removeClass('open');
			            jQuery19('.linktochapter .linktochapter-content ul').find('li a').removeClass('selected');
			        });		        	

				 jQuery19("#newLink BUTTON.operation-unlink").on('click', function() {
				 	  if($a !== null) {
				 	  	      var a = $a.get(0);

						      newRange = new GENTICS.Utils.RangeObject();
						      newRange.startContainer = newRange.endContainer = a.parentNode;
						      newRange.startOffset = GENTICS.Utils.Dom.getIndexInParent(a);
						      newRange.endOffset = newRange.startOffset + 1;
						      newRange.select();

						      GENTICS.Utils.Dom.removeFromDOM(a, newRange, true);

						      newRange.startContainer = newRange.endContainer;
						      newRange.startOffset = newRange.endOffset;
						      newRange.select();
						      
  		                	  jQuery19('#newLink').modal('hide');
					  }
				 });

				 jQuery19("#newLink BUTTON.operation-insert").on('click', function() {
						var title = jQuery19("#newLink INPUT[name=title]").val();
	   					var url = jQuery19("#newLink INPUT[name=url]").val();

	   					if(jQuery19.trim(title) !== '' && jQuery19.trim(url) !== '') {

						    if($a == null) {
	                          	$a = jQuery('<a/>').prop('href', url).text(title);

	                          	// A BIT DIFFERENT IF IS COLLAPSED
					//            if (range.isCollapsed()) {

	   							GENTICS.Utils.Dom.removeRange(range);
	   		                    GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
	   		                } else 
    					    	$a.prop('href', url).text(title);
		                	jQuery19('#newLink').modal('hide');
							range.select();
		            	}
		            });

				   UI.adopt('insertLink', null, {
				      click: function() {
				      	        editable = Aloha.activeEditable;
						        range = Aloha.Selection.getRangeObject();
                                var a = getContainerAnchor(range.startContainer);

                                if(a) {
                                	$a = jQuery(a);
                                	range.startContainer = range.endContainer = a;
                                	range.startOffset = 0;
                                	range.endOffset = a.childNodes.length;
                                	range.select();

									jQuery19("#newLink INPUT[name=title]").val(jQuery(a).text());
									jQuery19("#newLink INPUT[name=url]").val(a.getAttribute('href', 2));									
 					                jQuery19("#newLink .operation-unlink").prop('disabled', false); 

                                } else {
                                	if(_.isEmpty(range))
                                		return;
                                	
                                	$a = null;

						            GENTICS.Utils.Dom.extendToWord(range);

									jQuery19("#newLink INPUT[name=title]").val(range.getText()||"");
									jQuery19("#newLink INPUT[name=url]").val("");

 					                jQuery19("#newLink .operation-unlink").prop('disabled', true); 
						          }

	      	                jQuery19('#newLink').modal('show');
				      }
				  });		            
		        }
		    });

  		}
);