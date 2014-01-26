define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'underscore'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, _) {

  			return Plugin.create('extraformat', {
		        init: function () {

				   UI.adopt('removeFormat', null, {
				      click: function() {		 
						 var formats = [ 'u', 'strong', 'em', 'b', 'i', 'q', 'del', 's', 'code', 'sub', 'sup', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'quote', 'blockquote' ],
                             rangeObject = Aloha.Selection.rangeObject,
                             i;

                        // formats to be removed by the removeFormat button may now be configured using Aloha.settings.plugins.format.removeFormats = ['b', 'strong', ...]
                        // if (this.settings.removeFormats) {
                        //         formats = this.settings.removeFormats;
                        // }

                        if (rangeObject.isCollapsed()) {
                                return;
                        }

                        for (i = 0; i < formats.length; i++) {
                                GENTICS.Utils.Dom.removeMarkup(rangeObject, jQuery('<' + formats[i] + '>'), Aloha.activeEditable.obj);
                        }

                        // select the modified range
                        rangeObject.select();


	  				  }
					});

		        }
		    });

  		}
);