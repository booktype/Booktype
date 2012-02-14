(function() {
        var DOM = tinymce.DOM;

	tinymce.create('tinymce.plugins.BookiFootnotesPlugin', {
		init : function(ed, url) {
  		        this.editor = ed;
			ed.addCommand('mceBookiFootnotes', function() {
				var se = ed.selection;
				
				ed.windowManager.open({
					file : url + '/dialog.htm',
					width : 520,
					height : 250,
					inline : 1
				}, {
					plugin_url : url // Plugin absolute URL
				});
			});

			// Register example button
			ed.addButton('bookifootnotes', {
				title : 'Insert new footnote',
				cmd : 'mceBookiFootnotes' ,
				image : url + '/img/example.gif' 
			});
		},

		getInfo : function() {
			return {
				longname : 'Booki footnote plugin',
				author : 'Aleksandar Erkalovic',
				authorurl : 'http://www.binarni.net/',
				infourl : 'http://wiki.moxiecode.com/index.php/TinyMCE:Plugins/example',
				version : "1.0"
			};
		}
	});

	// Register plugin
	tinymce.PluginManager.add('bookifootnotes', tinymce.plugins.BookiFootnotesPlugin);
})();
