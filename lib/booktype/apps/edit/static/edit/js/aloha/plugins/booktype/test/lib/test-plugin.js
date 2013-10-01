define(
['aloha', 'aloha/plugin', 'jquery', 'ui/ui', 'ui/button' ],
function(Aloha, plugin, jQuery, Ui, Button ) {
    "use strict";

	var GENTICS = window.GENTICS;
    return plugin.create('test', {
        defaults: {
        },
        init: function(){
            var that = this;

  //          Aloha.require(['undo/undo-plugin'], function(UndoPlugin) {
                that._undoButton = Ui.adopt("test", Button, {
                    tooltip: "Ovo je neki test",
                    icon: "aloha-icon aloha-icon-undo",
                    scope: 'Aloha.continuoustext',
                    click: function(e){
                        console.debug('klikno sam');
                    }
                });
//            });
        }
    });

});
