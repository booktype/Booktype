(function() {
        var DOM = tinymce.DOM;

	tinymce.create('tinymce.plugins.BookiCommentsPlugin', {
		init : function(ed, url) {
  		        this.editor = ed;
			ed.addCommand('mceBookiComments', function() {
				var se = ed.selection;
				var selectedText = se.getContent({format : 'html'});

				if(selectedText.search('<span id="bookicommentmarker_') != -1) {
				    tinyMCE.activeEditor.windowManager.alert('It is not advised to have comment inside of another comment.');
				    return;
				}
				
				// It would be good if we could check if you are inside of selected comment and not just if
				// you selected comment icon.								
				if(se.getNode().nodeName == 'IMG' && ed.dom.hasClass(ed.dom.getParent(se.getNode(), 'SPAN'), "bookicommentmarker")) {
				    ed.windowManager.open({
					    file : url + '/dialog.htm',
						width : 520,
						height : 500,
						inline : 1
						}, {
					    plugin_url : url // Plugin absolute URL
						});
				} else {
				    ed.windowManager.open({
					    file : url + '/dialog_new.htm',
						width : 520,
						height : 320,
						inline : 1
						}, {
					    plugin_url : url // Plugin absolute URL
						});
				}

			});

			ed.addButton('bookicomments', {
				title : 'Insert new comment',
				cmd : 'mceBookiComments' ,
				    // from http://dryicons.com/icon/coquette-icons-set/comment/
				image : url + '/img/comment.png' 
			});
		},

		getInfo : function() {
			return {
				longname : 'Booki Comment Plugin',
				author : 'Aleksandar Erkalovic',
				authorurl : 'http://www.binarni.net/',
				infourl : 'http://wiki.moxiecode.com/index.php/TinyMCE:Plugins/example',
				version : "1.0"
			};
		}
	});

	// Register plugin
	tinymce.PluginManager.add('bookicomments', tinymce.plugins.BookiCommentsPlugin);
})();
