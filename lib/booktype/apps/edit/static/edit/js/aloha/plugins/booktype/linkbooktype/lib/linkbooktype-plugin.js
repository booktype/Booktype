define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'booktype', 'underscore'], 
	function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, booktype, _) {
		var $a = null;
		var range = null;
		var editable = null;
    	var selectedLinkDomObj = null;

		var getContainerAnchor = function(a) {
            var el = a;

            while (el) {
              if (el.nodeName.toLowerCase() === "a") {
                return el;
              }
              el = el.parentNode;
            }

            return false;
        };

        var destroyPopup = function() {
            if(selectedLinkDomObj) {
                jQuery19(selectedLinkDomObj).popover('destroy');    
                selectedLinkDomObj = null;
            } 
        }

		return Plugin.create('linkBooktype', {
	        init: function () {

		  		Aloha.bind("aloha-link-selected",function(event){
		  			var range = event.target.Selection.rangeObject;
					var limit = Aloha.activeEditable.obj;
					var $lnk = getContainerAnchor(range.startContainer);
                    var linkContent = '';

					if(!$lnk) return;

                    if($lnk === selectedLinkDomObj) {
                        return;
                    } else {
                        destroyPopup();
                    }

					var url = jQuery19($lnk).attr("href");

                    if(url.indexOf('../') === 0) {
                        linkContent = url;
                    } else {
                        linkContent = "<div style='white-space: pre-wrap; word-wrap: break-word;'> \
<a href='#' rel='popover' style= 'cursor: pointer' onclick=\"window.open('"+url+"','_blank')\">"+url+"</a></div>";
                    }

					if(!selectedLinkDomObj) {
						selectedLinkDomObj = $lnk;

						jQuery19(selectedLinkDomObj).popover({html: true, 
                                                              placement: 'top',
                                                              trigger: 'manual',
                                                              content: linkContent
                                                             });
						jQuery19(selectedLinkDomObj).popover('show');
					} 
				});

				Aloha.bind("aloha-link-unselected",function(event){
                    destroyPopup();
				});

                Aloha.bind("aloha-editable-deactivated",function(event){
                    destroyPopup();
                });

		        // link to chapters
		        jQuery19('.linktochapter-header i').click(function() {
		            jQuery19(this).closest('.linktochapter').toggleClass('open');
		        });

		        jQuery19('#newLink').on('show.bs.modal', function() {
		        	var $dialog = jQuery19('#newLink');

					jQuery19('.linktochapter-content UL', $dialog).empty();

		        	_.each(booktype.editor.data.chapters.chapters, function(item) {
		        		var $link = jQuery19('<li><a href="#"><i class="icon-check-sign"></i>'+item.get('title')+'</a></li>');

		        		jQuery19('a', $link).on('click', function() {
		        			jQuery19("#newLink INPUT[name=url]").val('../'+item.get('urlTitle')+'/');

		        			return false;
		        		});
		        		jQuery19('.linktochapter-content UL', $dialog).append($link);
		        	});

			        jQuery19('.linktochapter .linktochapter-content li a').click(function() {
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
