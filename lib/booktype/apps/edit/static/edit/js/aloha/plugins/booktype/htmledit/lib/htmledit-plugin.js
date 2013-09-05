  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera) {
  		    var myCodeMirror = null;

  			return Plugin.create('htmledit', {
		        init: function () {

				 jQuery19("#htmleditDialog").on('shown', function() {
			          var content = Aloha.getEditableById('contenteditor').getContents();
	

	   				  myCodeMirror = myCodeMirror || CodeMirror.fromTextArea(jQuery19("#htmleditDialog TEXTAREA")[0], 
				   				  	                                          {'mode': 'text/html',
				   				  	                                          'autofocus': true,
				   				  	                                          'lineNumbers': true,
				   				  	                                          'lineWrapping': true});
	   				  console.log('aloha vraca ', content);
	   				  myCodeMirror.getDoc().setValue(content);
	   				  myCodeMirror.setSize("100%", "100%");
	   				  jQuery19("#htmleditDialog .CodeMirror-scroll").scrollTop(0);
				 });	

				 jQuery19("#htmleditDialog BUTTON.btn-primary").on('click', function() {
	   					var content = myCodeMirror.getDoc().getValue();

	   					console.log('code mirror vraca ', content);

			            Aloha.getEditableById('contenteditor').setContents(content);
                	    jQuery19('#htmleditDialog').modal('hide');
		            });

				   UI.adopt('htmledit', null, {
				      click: function() {
	      	                jQuery19('#htmleditDialog').modal('show');
				      }
				  });		            
		        }
		    });

  		}
);