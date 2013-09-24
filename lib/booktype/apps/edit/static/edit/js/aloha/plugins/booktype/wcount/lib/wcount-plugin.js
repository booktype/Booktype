define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery', 'ui/ui', 'ui/button' ],
        function(Aloha, plugin, Ephemera, jQuery, Ui, Button ){
                //var GENTICS = window.GENTICS;
                return plugin.create("wcount", {
                        defaults: {
                                //value: 10
                        },
                        init: function() {
                                var that = this;
                                var content;
                                //var content = jQuery("#contenteditor").html();
                                //console.log(content);                                
                                Ephemera.classes("aloha-wcount");
                                console.log("init of the plugin wcount");
                                Aloha.bind("aloha-editable-activated",function()
                                        { 
                                                content = jQuery("#contenteditor").text();
                                                console.log(content);
                                        });

                                Aloha.bind("aloha-smart-content-changed",function()
                                        { 
                                                content = jQuery("#contenteditor").text();
                                                console.log(content);
                                        }); 
                                // var wcount = content.search(" "); <- count spaces to get word count

/*
            Aloha.require(['wcount/wcount-plugin'], function(WcountPlugin) {
                that._undoButton = Ui.adopt("word count", Button, {
                    tooltip: "word count",
                    icon: "aloha-icon aloha-icon-undo",
                    scope: 'Aloha.continuoustext',
                    click: function(e){
                        var valueToInsert = "(*)";
                        var content = jQuery("#contenteditor").html();
                        var cursorPosition = Aloha.Selection.rangeObject.endOffset;                        
                        var textInLine = Aloha.Selection.rangeObject.endContainer.data;
                        var startPos = content.search(textInLine);
                        var contentSize = content.length;
                        var newValue = content.substring(0,startPos+cursorPosition)+valueToInsert+content.substring(startPos+cursorPosition,contentSize);
                        jQuery("#contenteditor").html(newValue);
                    }
                });
            }); */

        }
        });
});
