define(['aloha', 'aloha/plugin','aloha/ephemera', 'jquery','jquery19', 'ui/ui', 'ui/button', 'booktype' ],
        function(Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button, booktype ){
                return Plugin.create("wcount", {                        
                        init: function() {
//==============
                        (function(DOMParser) {
                                "use strict";   
                        

                                var DOMParser_proto = DOMParser.prototype, real_parseFromString = DOMParser_proto.parseFromString;              

                                // Firefox/Opera/IE throw errors on unsupported types
                                try {
                                        // WebKit returns null on unsupported types
                                        if ((new DOMParser).parseFromString("", "text/html")) {
                                                // text/html parsing is natively supported
                                                return;
                                        }
                                } catch (ex) {}         

                                DOMParser_proto.parseFromString = function(markup, type) {
                                        if (/^\s*text\/html\s*(?:;|$)/i.test(type)) {
                                                var doc = document.implementation.createHTMLDocument("");
                                                if (markup.toLowerCase().indexOf('<!doctype') > -1) {
                                                        doc.documentElement.innerHTML = markup;
                                                }
                                                else {
                                                        doc.body.innerHTML = markup;
                                                }
                                                return doc;
                                        } else {
                                                return real_parseFromString.apply(this, arguments);
                                        }
                                };
                        }(DOMParser));
//================
                                var that = this;
                                var wcount = 0;
                                var charcount = 0;
                                var charspacecount = 0;
                                function get_text(el) {
                                        var ret_value = "";
                                        jQuery.each(el.childNodes,function(cnt,e){
                                                if(e.nodeType==10){ // if the DOMParsers is not working we are using the above DOMParser and have to remove nodeType 10
                                                        wcount = -1;
                                                }
                                                if((e.nodeType!=8)&&(e.nodeType!=10)) {
                                                        var node_value = e.nodeValue;
                                                        if(node_value!==null){
                                                        }
                                                        if (e.nodeType!=1){
                                                                ret_value+= node_value+ " ";
                                                        } else {
                                                                ret_value += get_text(e);
                                                        } 
                                                } 
                                        }); 
                                        return ret_value;
                                } 

                                function startCounters(){
                                                var parser = new DOMParser;
                                                var in_editor_data = Aloha.getEditableById('contenteditor').getContents();
                                                var content = parser.parseFromString(Aloha.getEditableById('contenteditor').getContents(),"text/html");
                                                var words = get_text(content);
                                                var spacecount = jQuery(content).text().split(/\s+/).length-1;
                                                var content_text = jQuery(content).text();
                                                var wordlist = words.split(/\s+/);                      
                                                wcount += wordlist.length-1;
                                                charcount = 0;
                                                jQuery.each(wordlist,function(cnt,el){
                                                        charcount+=el.length;
                                                });
                                                charspacecount = charcount+spacecount;
                                }

                                function getDataFromServer(){
                                        var get_wordcount = function(callback) {
                                                var current_chapter_id = booktype.editor.getCurrentChapterID();
                                                booktype.sendToCurrentBook({"command": "word_count", "current_chapter_id": current_chapter_id}, 
                                                        function(data) {
                                                            //outing the data
                                                            jQuery19("#elCount .modal-dialog .modal-content .modal-body .all_wcount").text(data.wcount+wcount);
                                                            jQuery19("#elCount .modal-dialog .modal-content .modal-body .all_charcount").text(data.charcount+charcount);
                                                            jQuery19("#elCount .modal-dialog .modal-content .modal-body .all_charspacecount").text(data.charspacecount+charspacecount);
                                                            wcount = 0; // due to hacking of wcount need to set it to 0 again                                                            
                                                            if(!_.isUndefined(callback)) {
                                                                callback();
                                                            }
                                                        });
                                                };
                                        get_wordcount();
                                        };

                                UI.adopt('wcount', null, {
                                        click: function() { 
                                                startCounters();                                            
                                                getDataFromServer();       

                                                jQuery19("#elCount .modal-dialog .modal-content .modal-body .wcount").text(wcount);
                                                jQuery19("#elCount .modal-dialog .modal-content .modal-body .charcount").text(charcount);
                                                jQuery19("#elCount .modal-dialog .modal-content .modal-body .charspacecount").text(charspacecount);
                                                jQuery19('#elCount').modal('show');
                                        }
                                });                                
        }
        });
});
