(function() {
	tinymce.create('tinymce.plugins.BookiImagePlugin', {
		init : function(ed, url) {
  		        this.editor = ed;
			ed.addCommand('mceBookiImage', function() {
				var se = ed.selection;

				ed.windowManager.open({
					file : url + '/dialog.htm',
					width : 480,
					height : 385,
					inline : 1
				}, {
					plugin_url : url // Plugin absolute URL
				});
			});

			// Register example button
			ed.addButton('bookiimage', {
				title : 'Insert new image',
				cmd : 'mceBookiImage' ,
				image : url + '/img/example.gif' 
			});
		},

		getInfo : function() {
			return {
				longname : 'Booki Image Insert plugin',
				author : 'Aleksandar Erkalovic',
				authorurl : 'http://www.binarni.net/',
				infourl : 'http://wiki.moxiecode.com/index.php/TinyMCE:Plugins/example',
				version : "1.0"
			};
		}
	});

	// Register plugin
	tinymce.PluginManager.add('bookiimage', tinymce.plugins.BookiImagePlugin);
})();
