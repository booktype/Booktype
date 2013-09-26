define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery', 'ui/ui', 'ui/button' ],
        function(Aloha, plugin, Ephemera, jQuery, Ui, Button ){
                return plugin.create("wcount", {
                        init: function() {
                                console.log(Aloha.settings);
                                console.log(GENTICS.Utils);
                                var that = this;
                                var wcount = 0;
                                var charcount = 0;
                                var charspacecount = 0;
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
                                function startCounters(){
                                                var content = Aloha.getActiveEditable().originalObj[0];
                                                var words = get_text(content);
                                                var spacecount = jQuery(content).text().split(/\s+/).length-1;
                                                console.log(spacecount);
                                                var wordlist = words.split(/\s+/);
                                                wcount = wordlist.length-1;
                                                console.log(wcount);
                                                charcount = 0;
                                                jQuery.each(wordlist,function(cnt,el){
                                                        charcount+=el.length;
                                                });
                                                charspacecount = charcount+spacecount;                                                
                                }
                                Ephemera.classes("aloha-wcount");
                                Aloha.bind("aloha-editable-activated",function(){ 
                                                startCounters();
                                                console.log(charcount);
                                                console.log(charspacecount);
                                        });

                                Aloha.bind("aloha-smart-content-changed",function(){ 
                                                startCounters();
                                                console.log(charcount);
                                                console.log(charspacecount);
                                        }); 
        }
        });
});
