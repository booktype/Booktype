define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'underscore'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, _) {

  			var editable = null;
  			var range = null;
	        var footnotes = [];
	
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