define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'block/block', 'block/blockmanager', 'booktype', 'underscore'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, block, BlockManager, booktype, _) {
         	var editable;
         	var range;

  			// Image Manager Dialog
         	var $manager = jQuery19('#imageManager');

         	// Popup window when image is selected in the editor
       	 	var $popup = jQuery19('#imagePopup');

         	// Loaded attachments for this book
         	var attachments = null;

         	// Image selected in the dialog
         	var selectedImage = null;

         	// This is just one big dirty hack
         	// Should really figure out how to avoid this situation
       	 	var doNothing = false;

       	 	// Reference to image selected in the editor
       	 	var $imageInFocus = null;

       	 	// Define Image Block
		    var ImageBlock = block.AbstractBlock.extend({
			      title: 'Image',
			      isDraggable: function() {return false;},
			      init: function($element, postProcessFn) {	
			      		var $desc = $element.find('p');
			      		var $n = jQuery('<div class="caption_small center aloha-editable">'+$desc.html()+'</div>');
			      		
			      		$desc.replaceWith($n);

      				    return postProcessFn();	 
			      },
                  update: function($element, postProcessFn) {
                  	    return postProcessFn();
                  }
            });

       	 	// Get attachment
         	var getAttachment = function(media_id) {
         		return _.find(attachments, function(a) { return a.id == media_id; });
         	}

         	// Image is selected in the editor
         	var selectImage = function($img) {
           	 	var pos = $img.offset();
                var y = pos.top;

           	 	$popup.css('top', y-40);
           	 	$popup.css('left', pos.left);
           	 	$popup.show();

         		$imageInFocus = $img;
         	}

         	var reloadAttachments = function(callback) {
					    booktype.sendToCurrentBook({"command": "attachments_list"}, 
					                               function(data) {
					                               	 attachments = data.attachments;
					                               	 showImages(data.attachments);

					                               	 if(!_.isUndefined(callback))
						                               	 callback();	
   			                                       });	         		
         	}

         	// Show images in the Image Manager Dialog
  			var showImages = function(attachments) {
              	 var $t = _.template(jQuery19('#templateImageThumbnail').html());

 	        	 jQuery19('.uploads-grid', $manager).empty();

                 _.each(attachments, function(att, i) {
                 	var $i = $t({'name': att.name, 'media_id': att.id});
                 	jQuery19('.uploads-grid', $manager).append($i);
                 });

                 jQuery19('.uploads-grid li a.delete-attachment').on('click', function() {
                 	var $this = jQuery19(this);
                 	var media_id = $this.parent().parent().parent().attr('data-media-id');

                    jQuery19('#removeMedia INPUT[name=attachments]').val(media_id);                                 

                    jQuery19('#removeMedia').modal('show');

                 	return false;
                 });

		        jQuery19('.uploads-grid li').click(function(){
		        	var media_id = jQuery19(this).attr('data-media-id');		        	

		        	if(_.isUndefined(media_id)) return;

		        	var att = getAttachment(media_id);

		        	selectedImage = att;

		            jQuery19(this).closest('.tab-pane').addClass('open-info');
		            jQuery19(this).parent().parent().find('ul li').removeClass('active');
		            jQuery19(this).toggleClass('active');
		            jQuery19('.image-info-container', $manager).removeClass('metadata-switch');
		            var imgsrc = jQuery19(this).find('img').attr('src');
		            jQuery19('.image-preview img', $manager).attr('src',imgsrc);
		            
		            var imgHeight = jQuery19('.image-preview img', $manager).height();
		            var imgMargin = Math.round((226 - imgHeight)/2) + 'px';        

		            jQuery19('.image-preview img', $manager).css('margin-top', imgMargin);     

                 	 var $t2 = _.template(jQuery19('#templateImageInfo').html());
                 	 var d = '';

			         if(att && att.dimension !== null)
			             d = att.dimension[0]+'x'+att.dimension[1]+'px';                 	 

                 	 var info = {'filesize': booktype.utils.formatSize(att.size),
                 	             'name': att.name,
                                 'dimension': d,
                                 'timestamp': att.created };

                 	 jQuery19('.image-info').html($t2(info));

                 	 // Resize the grid
                 	 var uplGridWidth = jQuery19('.tab-pane.active', $manager).width();
					 var newGridWidth = Math.round(uplGridWidth - 320) + 'px';
				     jQuery19('.open-info .uploads-grid', $manager).css('width', newGridWidth);
		        });

		        jQuery19('.uploads-grid > li').hover(
		            function() {
		                jQuery19(this).addClass('open-image-menu');  
		            },
		            function() {
		                jQuery19(this).removeClass('open-image-menu');
		                jQuery19(this).removeClass('open');
		            }
	    	    );
  			}

  			/* Initialise all images */
  			/* Create Aloha Block if image has caption. Bind click event to all images */
  			var _initImages = function(editable) {
               	 jQuery('img', editable.obj).each(function() {
               	 	var $img = jQuery(this);

               	 	var $g = $img.closest('div.group_img');

               	 	if($g.length > 0) {
	               	 	var $p = $g.find('p.caption_small');

	               	 	if($p.length > 0) {
	               	 		$g.alohaBlock({'aloha-block-type': 'ImageBlock'});
	               	 	}
					}
               	 });

               	 jQuery19('img', editable.obj).on('click', function($e) {
               	 	var $img = jQuery19($e.target);
               	 	selectImage($img);

               	 	return true;
               	 });  				
  			}

  			return Plugin.create('imagesimple', {
  				
  				makeClean: function(obj) {
  					jQuery(obj).find('DIV.group_img').each(function() {
  						var $div = jQuery(this);
  						var $d = jQuery('<div class="group_img"></div>');

//  						$d.append($div.find('img'));
  						$d.append($div.find('div.image'));

  						var $desc = $div.find('div.caption_small');
  						if($desc.length > 0) {
  							var $d0 = jQuery('<p class="caption_small center">'+$desc.html()+'</p>');
  							$d.append($d0);
  						}
  						$div.replaceWith($d);
  					});
  				}, 

		        init: function () {

                    BlockManager.registerBlockType('ImageBlock', ImageBlock);

			        jQuery19('.upload-file', $manager).fileupload({
                        dataType: 'json',
                        sequentialUploads: true,                        
                        done: function (e, data) {
                        	reloadAttachments(function() {
		                           jQuery19('a.medialibrary', $manager).tab('show');
		                           // select that file now
							 });

                             jQuery19('.upload-file', $manager).prop('disabled', false);
		                     jQuery19(document).trigger('booktype-attachment-uploaded', [data.files]);   
                        },
                        add: function (e, data) {
                          jQuery19('.upload-file', $manager).prop('disabled', true);

                          fileUpload = data.submit();
                        },
                        progressall: function (e, data) {
                                var progress = parseInt(data.loaded / data.total * 100, 10);
                            }
                    });

			        jQuery19('.image-dropdown-button', $manager).click(function(){
			            jQuery19(this).parent().toggleClass('open');
			            return false;
			        });

			        jQuery19('a.closeinfo', $manager).click(function(){
			            jQuery19(this).closest('.tab-pane').removeClass('open-info');
			            jQuery19(this).parent().removeClass('metadata-switch');
			            jQuery19('.uploads-grid').css('width', ''); 
			        });


			        jQuery19('a.metadata-btn', $manager).click(function(){
			            jQuery19(this).parent().toggleClass('metadata-switch');
			        });

			        jQuery19('a.cancel-metadata-btn', $manager).click(function(){
			            jQuery19(this).parent().toggleClass('metadata-switch');
			        });

			        jQuery19('.coverInfoButton', $manager).click(function(){
			            jQuery19('.coverInfo').toggleClass('open');
			        });

			        jQuery19('.insert-image', $manager).on('click', function() {
			        	var title = jQuery19.trim(jQuery19("input.image-title", $manager).val());
			        	var description = jQuery19.trim(jQuery19("textarea.image-description", $manager).val());

				     	$a = jQuery('<img alt="" src=""/>').prop('src', 'static/'+selectedImage.name);				     	
				     	$a.prop('alt', title);

                   	    $a.on('click', function($e) {
                   	 	    var $img = jQuery19($e.target);
                   	     	selectImage($img);
                   	 	
                   	 	    return true;
                   	     });

                   	    var $d = jQuery('<div class="group_img"></div>');
                   	    var $d2 = jQuery('<div class="image"></div>');
                   	    $d2.append($a);
                   	    $d.append($d2);

                   	    if(description !== '') {
	                   	    $d.append(jQuery('<p class="caption_small center">'+description+'</p>'));
                   	    }

                 	    $d.alohaBlock({'aloha-block-type': 'ImageBlock'});	                   	    

                 	    // Sometimes IE has issues with focus. In case when IE looses focus, this should
                 	    // probably to the work
						var $editable = Aloha.getEditableById('contenteditor');
	                    GENTICS.Utils.Dom.insertIntoDOM($d, range, $editable.obj);			        	

			        	$manager.modal('hide');
			        });

			        $manager.on('hide.bs.modal', function() {
						jQuery19("#removeMedia .btn-primary").unbind('click.simpleimage');

			        });

			        $manager.on('show.bs.modal', function() {
			        	selectedImage = null;
			        	jQuery19("input.image-title", $manager).val("");
			        	jQuery19("textarea.image-description", $manager).val("");
  		                jQuery19('.image-info-container', $manager).removeClass('metadata-switch');
			            jQuery19('#medialibrary').removeClass('open-info');
						jQuery19('a.medialibrary', $manager).tab('show');			            

			        	reloadAttachments();

  				        jQuery19("#removeMedia .btn-primary").bind('click.simpleimage', function() {
				          if(jQuery19("#removeMedia INPUT[name=understand]:checked").val() == 'on') {
				            var lst = jQuery19("#removeMedia INPUT[name=attachments]").attr("value").split(",");
				            
				            if(lst.length == 0) return;

				            booktype.ui.notify('Removing media files');

				            booktype.sendToCurrentBook({"command": "attachments_delete",
				                                            "attachments": lst},
				                                            function(data) {
				                                                booktype.ui.notify();
				                                                jQuery19("#removeMedia").modal('hide');
				                                                reloadAttachments();

                                        			            jQuery19('#medialibrary').removeClass('open-info');

				                                                // Trigger event
				                                                jQuery19(document).trigger('booktype-attachment-deleted'); 
				                                            });
				          }

				        });

					});

			       // Remove image
				   jQuery19('a.remove', $popup).on('click', function($e) {
				   	   // Is this image in a div ?
				   	   if($imageInFocus.parent().hasClass('group_img')) {
                           $imageInFocus.closest("div.group_img").remove();
				   	   } else {
                       	   $imageInFocus.remove();
				   	   }

                       $e.stopPropagation();
                       $e.preventDefault();
				   	   $popup.hide();

                       doNothing = true;

                       // This is so stupid
                       setTimeout(function() { doNothing = false; }, 100);
                       return false;
				   });

				   Aloha.bind('aloha-selection-changed', function (event, rangeObject, originalEvent) {
				   	if(doNothing) return;

				   	 if($popup.is(":visible"))
 				   	     $popup.hide();
				   });

	 			   // This is triggered after undo operation
                   Aloha.bind('aloha-my-undo', function(event, args) {
                    _initImages(args.editable);
                   });

				   // When Aloha editor is initialized just hook on every image in the editor 
                   Aloha.bind('aloha-editable-created', function($event, editable) {
                   	 _initImages(editable);
                   });	

                   Aloha.bind('aloha-editable-destroyed', function($event, editable) {
                   	$popup.hide();
                   });



				   UI.adopt('insertImage', null, {
				      click: function() {
		      	           editable = Aloha.activeEditable;
						   range = Aloha.Selection.getRangeObject();

	      	               $manager.modal('show');
				      }
				  });		            
		        }
		    });

  		}
);