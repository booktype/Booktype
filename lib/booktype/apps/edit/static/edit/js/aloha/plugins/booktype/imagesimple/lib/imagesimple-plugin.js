define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'booktype', 'underscore'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, booktype, _) {
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

  			return Plugin.create('imagesimple', {
		        init: function () {

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

                   	    var $d = jQuery('<div class="group"></div>');
                   	    $d.append($a);

                   	    if(description !== '')
	                   	    $d.append(jQuery('<p class="caption">'+description+'</p>'));

	                    GENTICS.Utils.Dom.insertIntoDOM($d, range, editable.obj);			        	

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
				   	   if($imageInFocus.parent().hasClass('group')) {
                           $imageInFocus.closest("div.group").remove();
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

				   // When Aloha editor is initialized just hook on every image in the editor 
                   Aloha.bind('aloha-editable-created', function($event, editable) {
                   	 jQuery19('img', editable.obj).on('click', function($e) {
                   	 	var $img = jQuery19($e.target);
                   	 	selectImage($img);

                   	 	return true;
                   	 });
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