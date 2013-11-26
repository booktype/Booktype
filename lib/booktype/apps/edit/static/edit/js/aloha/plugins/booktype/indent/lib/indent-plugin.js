define(['aloha', 'aloha/plugin','aloha/ephemera', 'jquery','jquery19', 'ui/ui', 'ui/button', 'booktype' ],
        function(Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button, booktype ){
                function increase_indent(data_to_add, current_margin){
                    console.log("inc");
                    var new_margin_value = current_margin+48;
                    jQuery(data_to_add).css("margin-left",new_margin_value+"px");
                }

                function decrease_indent(data_to_add, current_margin){
                    console.log("dec");
                    if(current_margin>=48){
                    var new_margin_value = current_margin-48;
                    jQuery(data_to_add).css("margin-left",new_margin_value+"px");
                    }
                }

                return Plugin.create("indent", {
                        init: function() {
                            console.log("indent plugin");
                            UI.adopt('indent-right',event,{ // increase indent
                                click: function(){
                                    var range = Aloha.Selection.getRangeObject();
                                    var range_object = range.getSelectionTree();
                                    var start_container = range.startContainer.parentElement;
                                    var end_container = range.endContainer.parentElement;

                                    var $data_to_add=jQuery();
                                    var margin_left_value;
                                    var clicked_value;
                                    if(start_container===end_container){
                                        $data_to_add = range_object[0].domobj.parentNode;
                                        margin_left_value = parseInt(jQuery($data_to_add).css("margin-left"),10);
                                        if(isNaN(margin_left_value)){
                                            margin_left_value=0;
                                        }
                                        increase_indent($data_to_add,margin_left_value);
                                    } else {
                                        var full_content = jQuery(Aloha.getEditableById('contenteditor').getContents());
                                        var are_we_in_range = false;
                                        jQuery.each(range_object,function(cnt,el){
                                            if (el.selection!=="none"){
                                                $data_to_add = el.domobj;
                                                margin_left_value = parseInt(jQuery($data_to_add).css("margin-left"),10);
                                                if(isNaN(margin_left_value)){
                                                    margin_left_value=0;
                                                }
                                                increase_indent($data_to_add,margin_left_value);
                                            }
                                        });

                                    }
                                }
                            });
                            UI.adopt('indent-left',event,{ // decrease indent
                                click: function(){
                                    var range = Aloha.Selection.getRangeObject();
                                    var range_object = range.getSelectionTree();
                                    var start_container = range.startContainer.parentElement;
                                    var end_container = range.endContainer.parentElement;

                                    var $data_to_add=jQuery();
                                    var margin_left_value;
                                    var clicked_value;
                                    if(start_container===end_container){
                                        $data_to_add = range_object[0].domobj.parentNode;
                                        margin_left_value = parseInt(jQuery($data_to_add).css("margin-left"),10);
                                        if(isNaN(margin_left_value)){
                                            margin_left_value=0;
                                        }
                                        clicked_value = jQuery(event.target).text().replace(/^\s+|\s+$/g,'');
                                        decrease_indent($data_to_add,margin_left_value);
                                    } else {
                                        var full_content = jQuery(Aloha.getEditableById('contenteditor').getContents());
                                        var are_we_in_range = false;
                                        jQuery.each(range_object,function(cnt,el){
                                            if (el.selection!=="none"){
                                                $data_to_add = el.domobj;
                                                margin_left_value = parseInt(jQuery($data_to_add).css("margin-left"),10);
                                                if(isNaN(margin_left_value)){
                                                    margin_left_value=0;
                                                }
                                                clicked_value = jQuery(event.target).text().replace(/^\s+|\s+$/g,'');
                                                decrease_indent($data_to_add,margin_left_value);
                                            }
                                        });

                                    }
                                }
                            });
        }
        });
});
