//BK-796
define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery','jquery19', 'ui/ui', 'ui/button' ],
        function(Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button ){
                return Plugin.create("font", {                        
                        init: function() {
                                
                                var list_of_fonts = Aloha.settings.plugins.font; // get settings from aloha_header.html
                                var html_list_fonts = "";
                                jQuery.each(list_of_fonts.fontlist,function(cnt,el){
                                        html_list_fonts+="<li><a href='#' class='action font' data-tagname='"+list_of_fonts.fontpaths[el]+"' data-placement='bottom'>"+el+"</a></li>"
                                        });

                                console.log(html_list_fonts);

                                var GENTICS = window.GENTICS;

                               Aloha.bind('aloha-editable-created', function($event, editable) {
                                // inject value to hmtl
                               jQuery(".contentHeader .btn-toolbar .font-dropdown").html(html_list_fonts); 
                                jQuery(".contentHeader .btn-toolbar .font-dropdown a").on('click', function (event) {
                                    console.log('-----------------------------------');
                                    console.log('CLICKED ON FONT OPTION');
                                    console.log('-----------------------------------');
                                    console.log('event ', event);
                                    var font_selected = jQuery(event.currentTarget).text();
                                    console.log('selected font ', font_selected);
                                    console.log("editable ", editable);
                                    console.log('-----------------------------------');

                                    changeFont(font_selected, editable);
                                    return true;
                            }); 
                        });  

                        function changeFont(font_name, $editable){
                        console.log('change font');

                        var range = Aloha.Selection.getRangeObject();

                        var selection_start = range.startOffset;
                        var selection_end = range.endOffset;

                        if ((selection_end===0)||(selection_end===undefined)){ // nothing selected
                            console.log('*ERROR* Nothing was selected');
                            return;
                        }

                                    var element_selected = range.endContainer.data;

                                    console.log('ovdje prije ifova');
                                    console.log('jesu li jednaki ', range.startContainer == range.endContainer);
                                    console.log('startContainer ', range.startContainer);
                                    console.log('endContainer ', range.endContainer);
                                    console.log('node name na ', range.startContainer.nodeName);

                                    console.log('element_selected ', element_selected);
                                    console.log(element_selected.length);
                                    var $span_add;

                                    if((range.startContainer === range.endContainer) && (selection_end==element_selected.length)){
                                        console.log("one line selection");
                                        var node_name = range.splitObject.nodeName;
                                        console.log(range);
                                        $span_add = jQuery("<"+node_name+" style='font-family:"+font_name+"'>").append(element_selected);  
                                        GENTICS.Utils.Dom.removeRange(range);
                                        GENTICS.Utils.Dom.insertIntoDOM($span_add,range,range.obj);

                                    } else {
                                        console.log("multi line selection");
                                        console.log("insert span");
                                        $span_add = jQuery("<span style='font-family:"+font_name+"'>");                 
                                        GENTICS.Utils.Dom.addMarkup(range, $span_add, true); // allow nesting of other html elements                                        
                                    }
                                    range.select();                                    
                                }
                       
                }
        });
});
