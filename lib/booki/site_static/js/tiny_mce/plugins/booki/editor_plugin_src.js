(function() {
        var DOM = tinymce.DOM;

	tinymce.create('tinymce.plugins.BookiPlugin', {
		init : function(ed, url) {
                        var t = this, tbId = ed.getParam('bookiadv_toolbar', 'toolbar2');

                        ed.onPostRender.add(function() {
                                var adv_toolbar = ed.controlManager.get(tbId);

                                if ( ed.getParam('bookiadv_hidden', 1) && adv_toolbar ) {
                                        DOM.hide(adv_toolbar.id);

					var adv_toolbar = ed.controlManager.get("toolbar3");
                                        DOM.hide(adv_toolbar.id);

                                        t._resizeIframe(ed, tbId, 28);
                                        t._resizeIframe(ed, "toolbar3", 28);
                                }
                        });


                        ed.addCommand('mceBookiAdvanced', function() {
                                var cm = ed.controlManager, id = cm.get(tbId).id;

                                if ( 'undefined' == id )
                                        return;

                                if ( DOM.isHidden(id) ) {
                                        cm.setActive('bookiadv', 1);
                                        DOM.show(id);

					id = cm.get("toolbar3").id;
                                        DOM.show(id);

                                        t._resizeIframe(ed, tbId, -28);
                                        t._resizeIframe(ed, "toolbar3", -28);

                                        ed.settings.bookiadv_hidden = 0;
                                } else {
                                        cm.setActive('bookiadv', 0);
                                        DOM.hide(id);
					id = cm.get("toolbar3").id;
                                        DOM.hide(id);

                                        t._resizeIframe(ed, tbId, 28);
                                        t._resizeIframe(ed, "toolbar3", 28);

                                        ed.settings.bookiadv_hidden = 1;
                                }
                        });

			ed.addButton('bookiadv', {
				title : 'Toogle advanced toolbar',
				cmd : 'mceBookiAdvanced' ,
				image : url + '/img/example.gif' 
			});
		},

                _resizeIframe : function(ed, tb_id, dy) {
                        var ifr = ed.getContentAreaContainer().firstChild;

                        DOM.setStyle(ifr, 'height', ifr.clientHeight + dy); // Resize iframe
                        ed.theme.deltaHeight += dy; // For resize cookie
                },


		getInfo : function() {
			return {
				longname : 'Booki plugin for advanced/simple toolbar',
				author : 'Aleksandar Erkalovic',
				authorurl : 'http://www.binarni.net/',
				infourl : 'http://wiki.moxiecode.com/index.php/TinyMCE:Plugins/example',
				version : "1.0"
			};
		}
	});

	// Register plugin
	tinymce.PluginManager.add('booki', tinymce.plugins.BookiPlugin);
})();
