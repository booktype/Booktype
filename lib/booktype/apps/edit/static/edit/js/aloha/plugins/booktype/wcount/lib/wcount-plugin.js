define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery','jquery19', 'ui/ui', 'ui/button' ],
        function(Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button ){
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
                                var all_wcount = 0;
                                var charcount = 0;
                                var all_charcount = 0;
                                var charspacecount = 0;
                                var all_charspacecount = 0;
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

                                function getDataFromServer(chapter_no){
                                        //var query_string = '[{"command":"get_chapter","chapterID":3,"channel":"/booktype/book/1/1.0/","uid":2988}]';
                                        var chapter_text;
                                        jQuery.post("/_sputnik/", {
                                                "csrfmiddlewaretoken": "4fLgSZxNTOQoogmk9FC8eBp1bbZeCWnS",
                                                "clientID": 1, 
                                                "messages": '[{"command":"get_chapter","chapterID":'+chapter_no.toString()+',"channel":"/booktype/book/3/1.0/","uid":5988}]' })
                                                .done(function(data){
                                                        console.log(">>",data);
                                                        chapter_text = data.messages[0].content;                                                                                                                        
                                                        //console.log(jQuery(chapter_text).text());                                          
                                                        if (chapter_text!=undefined){
                                                                console.log(chapter_text);
                                                                console.log("-----");
                                                                var parser = new DOMParser;
                                                                var all_content = parser.parseFromString(chapter_text,"text/html");
                                                                // .........
                                                                var all_words = get_text(all_content);
                                                                var all_spacecount = jQuery(all_content).text().split(/\s+/).length-1;
                                                                var all_content_text = jQuery(all_content).text();
                                                                var all_wordlist = all_words.split(/\s+/);
                                                                console.log("-----\n",all_wordlist,"\n------");                                                                
                                                                all_wcount += all_wordlist.length-1;
                                                                //all_charcount = 0;
                                                                jQuery.each(all_wordlist,function(cnt,el){
                                                                        all_charcount+=el.length;
                                                                });
                                                                all_charspacecount = all_charcount+all_spacecount;
                                                                //...........

                                                                chapter_text = getDataFromServer(chapter_no+1);
                                                        } else {
                                                                console.log(all_wcount);
                                                                console.log(all_charcount);
                                                                console.log(all_charspacecount);
                                                                all_wcount = 0;
                                                                all_charcount = 0;
                                                                all_charspacecount = 0;
                                                        }

                                                        //console.log(data.messages[0].content);
                                                });
                                }

                                UI.adopt('wcount', null, {
                                        click: function() { 
                                                getDataFromServer(1);       
                                                //getDataFromServer('[{"command":"get_users","chapterID":3,"channel":"/booktype/book/1/1.0/","uid":2988}]');       
                                                startCounters();

                                                jQuery19("#elCount .modal-dialog .modal-content .modal-body .wcount").text(wcount);
                                                jQuery19("#elCount .modal-dialog .modal-content .modal-body .charcount").text(charcount);
                                                jQuery19("#elCount .modal-dialog .modal-content .modal-body .charspacecount").text(charspacecount);
                                                jQuery19('#elCount').modal('show');

                                                console.log(wcount);
                                                console.log(charcount);
                                                console.log(charspacecount);
                                                wcount = 0; // due to hacking of wcount need to set it to 0 again
                                        }
                                });                                
        }
        });
});
