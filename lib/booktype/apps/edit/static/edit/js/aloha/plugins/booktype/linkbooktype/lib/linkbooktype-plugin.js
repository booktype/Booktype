  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera) {
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

			        // link to chapter
			        jQuery19('.linktochapter-header i').click(function() {
			            jQuery19(this).closest('.linktochapter').toggleClass('open');
			        });
			        jQuery19('.linktochapter .linktochapter-content li a').click(function() {
			            jQuery19(this).closest('ul').find('li a').removeClass('selected');
			            jQuery19(this).addClass('selected');
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

				 jQuery19("#newLink BUTTON.btn-primary").on('click', function() {
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

							range.select();
		                	jQuery19('#newLink').modal('hide');
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
									jQuery19("#newLink INPUT[name=url]").val(jQuery(a).prop("href"));
 					                jQuery19("#newLink .operation-unlink").prop('disabled', false); 

                                } else {
                                	$a = null;

						            GENTICS.Utils.Dom.extendToWord(range);

									jQuery19("#newLink INPUT[name=title]").val(range.getText()||"");
									jQuery19("#newLink INPUT[name=url]").val("");

 					                jQuery19("#newLink .operation-unlink").prop('disabled', true); 
						          }

//								console.log(range);
//								console.log(_savedRange);
	      	                jQuery19('#newLink').modal('show');

				      	console.log('insert link');
				      }
				  });		            
		        }
		    });

  		}
);