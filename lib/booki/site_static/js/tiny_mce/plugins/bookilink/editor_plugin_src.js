(function() {
	tinymce.create('tinymce.plugins.BookiLinkPlugin', {
		init : function(ed, url) {
  		        this.editor = ed;
			ed.addCommand('mceBookiLink', function() {
				var se = ed.selection;
				
				if(se.isCollapsed() && !ed.dom.getParent(se.getNode(), 'A'))
				    return;

				ed.windowManager.open({
					file : url + '/dialog.htm',
					width : 320 + parseInt(ed.getLang('aco.delta_width', 0)),
					height : 300 + parseInt(ed.getLang('aco.delta_height', 0)),
					inline : 1
				}, {
					plugin_url : url, // Plugin absolute URL
					some_custom_arg : 'custom arg' // Custom argument
				});
			});

			// Register example button
			ed.addButton('bookilink', {
				title : 'Insert new link',
				cmd : 'mceBookiLink' ,
				image : url + '/img/example.gif' 
			});

			// Add a node change handler, selects the button in the UI when a image is selected
			ed.onNodeChange.add(function(ed, cm, n, co) {
				cm.setDisabled('bookilink', co && n.nodeName != 'A');
				cm.setActive('bookilink', n.nodeName == 'A' && !n.name);
			});
		},

		createControl : function(n, cm) {
			return null;
		},

		getInfo : function() {
			return {
				longname : 'Booki Link Insert plugin',
				author : 'Aleksandar Erkalovic',
				authorurl : 'http://www.binarni.net/',
				infourl : 'http://wiki.moxiecode.com/index.php/TinyMCE:Plugins/example',
				version : "1.0"
			};
		}
	});

	// Register plugin
	tinymce.PluginManager.add('bookilink', tinymce.plugins.BookiLinkPlugin);
})();
