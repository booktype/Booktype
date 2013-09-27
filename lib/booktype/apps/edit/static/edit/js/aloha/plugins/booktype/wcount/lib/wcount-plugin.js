define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery', 'ui/ui', 'ui/button' ],
        function(Aloha, plugin, Ephemera, jQuery, Ui, Button ){
                return plugin.create("wcount", {
                        init: function() {
                                var that = this;
                                var wcount = 0;
                                var charcount = 0;
                                var charspacecount = 0;
                                function get_text(el) {
                                        ret = "";
                                        jQuery.each(el.childNodes,function(cnt,e){
                                                if(e.nodeType != 8) {
                                                        ret += e.nodeType != 1 ? e.nodeValue+" " : get_text(e);
                                                }

                                        }); 
                                        return ret;
                                } 
                                function startCounters(){
                                                var parser = new DOMParser();
                                                var content = parser.parseFromString(Aloha.getEditableById('contenteditor').getContents(),"text/html");
                                                var words = get_text(content);
                                                var spacecount = jQuery(content).text().split(/\s+/).length-1;
                                                var wordlist = words.split(/\s+/);
                                                wcount = wordlist.length-1;
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
