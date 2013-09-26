define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery', 'ui/ui', 'ui/button','aloha/contenthandler' ],
        function(Aloha, plugin, Ephemera, jQuery, Ui, Button, ContentHandlerManager ){
                return plugin.create("wcount", {
                        init: function() {
                                console.log(Aloha.settings);
                                //console.log(GENTICS.Utils.trees);
                                var that = this;
                                var wcount = 0;
                                function get_text(el) {
                                        ret = "";
                                        var len = el.childNodes.length;
                                        for(var i = 0; i < len; i++) {
                                                var node = el.childNodes[i];
                                                if(node.nodeType != 8) {
                                                        ret += node.nodeType != 1 ? node.nodeValue+" " : get_text(node);
                                                }
                                        }
                                        return ret;
                                } 
                                Ephemera.classes("aloha-wcount");
                                console.log("init of the plugin wcount");
                                Aloha.bind("aloha-editable-activated",function(){ 
                                                var content = Aloha.getActiveEditable().originalObj[0];
                                                var words = get_text(content);
                                                wcount = words.split(/\s+/).length-1;
                                                console.log(wcount);
                                        });

                                Aloha.bind("aloha-smart-content-changed",function(){ 
                                                console.log(Aloha.getActiveEditable().originalObj[0]);
                                                var content = Aloha.getActiveEditable().originalObj[0];
                                                var words = get_text(content);
                                                wcount = words.split(/\s+/).length-1;
                                                console.log(wcount);
                                        }); 
        }
        });
});
