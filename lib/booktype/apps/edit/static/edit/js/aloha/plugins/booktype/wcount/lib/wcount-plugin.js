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
                                console.log("testing dialog");
                                showModalDialog("/accounts");
                                console.log("is the dialog shown?");
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
                                                content = editable.getContents();
                                                console.log(content);
                                        }); 
                                // var wcount = content.search(" "); <- count spaces to get word count
        }
        });
});
