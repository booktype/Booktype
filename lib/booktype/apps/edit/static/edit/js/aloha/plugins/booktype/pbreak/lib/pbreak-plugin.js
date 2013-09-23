define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery', 'ui/ui', 'ui/button' ],
        function(Aloha, plugin, Ephemera, jQuery, Ui, Button ){
                //var GENTICS = window.GENTICS;
                return plugin.create("pbreak", {
                        defaults: {
                                value: 10
                        },
                        init: function() {
                                var that = this;
                                Ephemera.classes("aloha-pbreak");
                                //console.log("init of the plugin");
                                Aloha.bind("aloha-smart-content-changed",function()
                                        { 
                                                var content = jQuery("#contenteditor").html();
                                                console.log(content);
                                        });


            Aloha.require(['pbreak/pbreak-plugin'], function(UndoPlugin) {
                that._undoButton = Ui.adopt("pbreak", Button, {
                    tooltip: "hello",
                    icon: "aloha-icon aloha-icon-undo",
                    scope: 'Aloha.continuoustext',
                    click: function(e){
                        var valueToInsert = "(*)";
                        var content = jQuery("#contenteditor").html();
                        var cursorPosition = Aloha.Selection.rangeObject.endOffset;                        
                        /*console.log("-------");
                        console.log(GENTICS.Utils.Dom.removeRange(Aloha.Selection.rangeObject));
                        console.log("-------"); */
                        var textInLine = Aloha.Selection.rangeObject.endContainer.data;
                        /*console.log(textInLine);
                        console.log(cursorPosition); */
                        var startPos = content.search(textInLine);
                        var contentSize = content.length;
                        var newValue = content.substring(0,startPos+cursorPosition)+valueToInsert+content.substring(startPos+cursorPosition,contentSize);
                        jQuery("#contenteditor").html(newValue);
                    }
                });
            });

        }
        });
});
