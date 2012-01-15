(function() {
	tinymce.create('tinymce.plugins.BookiMessagePlugin', {
		init : function(ed, url) {
  		        this.editor = ed;

			ed.addCommand('mceBookiMessage', function() {
				var se = ed.selection;

				if(se)
				    $.bookiMessage(se.getContent());
			});

			// Register example button
			ed.addButton('bookimessage', {
				title : 'Send this text as message',
				cmd : 'mceBookiMessage' ,
				image : url + '/img/example.gif' 
			});
		},

		getInfo : function() {
			return {
				longname : 'Booki plugin for messaging',
				author : 'Aleksandar Erkalovic',
				authorurl : 'http://www.binarni.net/',
				infourl : 'http://wiki.moxiecode.com/index.php/TinyMCE:Plugins/example',
				version : "1.0"
			};
		}
	});

	// Register plugin
	tinymce.PluginManager.add('bookimessage', tinymce.plugins.BookiMessagePlugin);
})();
