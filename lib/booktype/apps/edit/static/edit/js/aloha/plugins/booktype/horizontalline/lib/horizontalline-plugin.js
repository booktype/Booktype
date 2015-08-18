define(['aloha', 'aloha/plugin', 'jquery',  'ui/ui', 'aloha/console', 'aloha/ephemera', 'underscore'], 
  		function(Aloha, Plugin, jQuery, UI, Console, Ephemera, _) {

  			var editable = null;
  			var range = null;
	
  			return Plugin.create('horizontalline', {
		        init: function () {

				   UI.adopt('horizontalline', null, {
				      click: function() {		 
				      	 editable = Aloha.activeEditable;
   				         range = Aloha.Selection.getRangeObject();

   				         var $a = jQuery('<hr/>');

						 GENTICS.Utils.Dom.removeRange(range);
	                     GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
	  				  }
					});
		        }
		    });

  		}
);