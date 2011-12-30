(function() {
	// Load plugin specific language pack
	//tinymce.PluginManager.requireLangPack('aco');

	tinymce.create('tinymce.plugins.BookiMessagePlugin', {
		init : function(ed, url) {
  		        this.editor = ed;

			ed.addCommand('mceBookiMessage', function() {
				var se = ed.selection;


				if(se)
				    $.bookiMessage(se.getContent());

				//else
				//    $.bookiMessage(editor.getHTML());
				

			});

			// Register example button
			ed.addButton('bookimessage', {
				title : 'Send this text as message',
				cmd : 'mceBookiMessage' ,
				image : url + '/img/example.gif' 
			});
		},
		    /*
		createControl : function(n, cm) {
			return null;
		},
		    */
		getInfo : function() {
			return {
				longname : 'Aco plugin',
				author : 'Aco',
				authorurl : 'http://tinymce.moxiecode.com',
				infourl : 'http://wiki.moxiecode.com/index.php/TinyMCE:Plugins/example',
				version : "1.0"
			};
		}
	});

	// Register plugin
	tinymce.PluginManager.add('bookimessage', tinymce.plugins.BookiMessagePlugin);
})();
