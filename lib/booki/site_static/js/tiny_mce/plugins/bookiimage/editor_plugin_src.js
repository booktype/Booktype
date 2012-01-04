(function() {
	// Load plugin specific language pack
	//tinymce.PluginManager.requireLangPack('aco');

	tinymce.create('tinymce.plugins.BookiImagePlugin', {
		init : function(ed, url) {
  		        this.editor = ed;
			ed.addCommand('mceBookiImage', function() {
				var se = ed.selection;
				/*
				if(se.isCollapsed() && !ed.dom.getParent(se.getNode(), 'A'))
				    return;
				*/
				ed.windowManager.open({
					file : url + '/dialog.htm',
					width : 480 + parseInt(ed.getLang('aco.delta_width', 0)),
					height : 385 + parseInt(ed.getLang('aco.delta_height', 0)),
					inline : 1
				}, {
					plugin_url : url, // Plugin absolute URL
					some_custom_arg : 'custom arg' // Custom argument
				});
			});

			// Register example button
			ed.addButton('bookiimage', {
				title : 'Insert new link',
				cmd : 'mceBookiImage' ,
				image : url + '/img/example.gif' 
			});

			// Add a node change handler, selects the button in the UI when a image is selected
			
			ed.onNodeChange.add(function(ed, cm, n, co) {
				//cm.setDisabled('bookiimage', co && n.nodeName != 'A');
				//cm.setActive('bookiimage', n.nodeName == 'A' && !n.name);
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
	tinymce.PluginManager.add('bookiimage', tinymce.plugins.BookiImagePlugin);
})();
