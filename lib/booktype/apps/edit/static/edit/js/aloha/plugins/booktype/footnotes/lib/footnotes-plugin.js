define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'underscore'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, _) {

  			var editable = null;
  			var range = null;
	        var footnotes = [];
	
            var refreshFootnotes = function() {
						           	   var $a = jQuery('sup.footnote', jQuery("#contenteditor"));

						           	   var fids = _.pluck(footnotes, 'uniqueID');
                                       var fidsNew = [];

						           	   for(var i = 0; i < $a.length; i++) {
						           	   	   fidsNew.push(jQuery($a[i]).attr('id'));

						                   jQuery($a[i]).html(i+1);
						           	   };

						           	   var deletedFootnotes = _.difference(fids, fidsNew);

						           	   _.each(deletedFootnotes, function(foot) {
						           	   	  jQuery('#content #footnotes LI[id=content_'+foot+']').remove();
						           	   	  var i = _.find(footnotes, function(item) { return item.uniqueID == foot; })

						           	   	  if(!_.isUndefined(i)) {
						           	   	      footnotes.splice(i, 1);
						           	   	  }
						           	   });

						           	   _.each(fidsNew, function(item, i) {
   									     var $e = jQuery('#content #footnotes LI').eq(i);							           	   

						           	   	 if($e.attr('id') !== 'content_'+item) {
						           	   	 	var $e2 = jQuery('#content #footnotes LI[id=content_'+item+']');
						           	   	 	var $e3 = $e2.clone();

						           	   	 	$e2.remove();

						           	   	 	if(i === 0) {
						           	   	 	 	jQuery('#content #footnotes OL').prepend($e2);
						           	   	 	} else {
						           	   	 		if(i == jQuery('#content #footnotes LI').length) {
						           	   	 			jQuery('#content #footnotes OL').append($e3);
						           	   	 		} else 
								           	   	 	jQuery('#content #footnotes LI:eq('+i+')').after($e3);
						           	   	    }
						           	   	 }
						           	   });
						            };

            var Footnote = function(uniqueID, content) {
            					this.uniqueID = uniqueID;
            					this.content = content;
				           };


  			return Plugin.create('footnotes', {
		        init: function () {

				 jQuery19("#footnoteDialog").on('show.bs.modal', function() {
				 	jQuery19("#footnoteDialog TEXTAREA").val('');
 				 });

				 jQuery19("#footnoteDialog").on('shown.bs.modal', function() {
				 	jQuery19("#footnoteDialog TEXTAREA").focus();
 				 });

				 jQuery19("#footnoteDialog BUTTON.operation-insert").on('click', function() {
						var content = jQuery19("#footnoteDialog TEXTAREA").val();
						if(jQuery.trim(content) !== '') {
							var uniqueID = _.uniqueId('footnote_');

	   				         var $a = jQuery('<sup class="footnote" id="'+uniqueID+'"></sup>');
	   				         var $l = jQuery('<li/>').attr('id', 'content_'+uniqueID).html(_.escape(content));

	   				         jQuery('#content #footnotes OL').append($l);

	   				         footnotes.push(new Footnote(uniqueID, content));

	   				         GENTICS.Utils.Dom.removeRange(range);
	 	                     GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);

							 range.select();

							 refreshFootnotes();

		                 	 jQuery19('#footnoteDialog').modal('hide');
		                }
		            });

				   UI.adopt('footnote-insert', null, {
				      click: function() {		 
				      	 editable = Aloha.activeEditable;
   				         range = Aloha.Selection.getRangeObject();

      	                 jQuery19('#footnoteDialog').modal('show');
	  				  }
					});

       			        // check if content has changed
                   Aloha.bind('aloha-smart-content-changed', function() {
                   	     refreshFootnotes();
                   });

   			       Aloha.bind('aloha-editable-created', function(e, editable) {                   
           	         var $a = jQuery('sup.footnote', jQuery("#contenteditor"));

           	         for(var i =0; i < $a.length; i++) {
           	         	var uniqueID = jQuery($a[i]).attr('id');
           	         	var content = jQuery('#content #footnotes LI[id=content_'+uniqueID+']').html();

           	         	footnotes.push(new Footnote(uniqueID, content));
           	         }

   			     });

		        }
		    });

  		}
);