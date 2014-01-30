define(['aloha', 'aloha/plugin','aloha/ephemera', 'jquery','jquery19', 'ui/ui', 'ui/button', 'booktype' ],
        function(Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button, booktype ){
                var current_margin;
                var changeNumber = function(fromUnit,toUnit){
                    // no centimeters - I have no idea how to convert them
                    // the source for the values is http://reeddesign.co.uk/test/points-pixels.html
                    var conversion = 1.0;
                    if(fromUnit==="px"){
                        switch(toUnit) {
                            case "pt":
                                conversion = 0.8571; // 6/7
                                break;
                            case "em":
                                conversion = 0.0625; // 1/16
                                break;
                            case "%":
                                conversion = 6.25; // 50/8
                                break;
                        }

                    }
                    if(fromUnit==="pt"){
                        switch(toUnit) {
                            case "px":
                                conversion = 1.3333; // 8/6
                                break;
                            case "em":
                                conversion = 0.08333; // 1/12
                                break;
                        case "%":
                                conversion = 8.12; // 6/50
                                break;
                        }
                    }
                    if(fromUnit==="%"){
                        switch(toUnit) {
                            case "pt":
                                conversion = 8.3333; // 50/6
                                break;
                            case "em":
                                conversion = 0.01; // 1/100
                                break;
                            case "px":
                                conversion = 0.16; // 8/50
                                break;
                        }
                    }
                    if(fromUnit==="em"){
                        switch(toUnit) {
                            case "pt":
                                conversion = 12;
                                break;
                            case "%":
                                conversion = 100;
                                break;
                            case "px":
                                conversion = 16;
                                break;
                        }
                    }
                    return conversion;
                };

                function get_unit(invalue){
                    var unitValue = invalue.replace(/[\d\.,]/g,''); // remove numbers
                    if((unitValue!=="em")&&(unitValue!=="%")&&(unitValue!=="px")&&(unitValue!=="pt")) {
                        unitValue = "px"; // if unit value is missing or is wrong - return px
                    }
                    return unitValue;
                }
                function increase_indent(data_to_add){
                    var user_margin_text = "48px"; // default left margin value
                    if (typeof Aloha.settings.plugins.indent !== 'undefined'){
                        if (typeof Aloha.settings.plugins.indent.marginLeft !== 'undefined'){
                            user_margin_text = Aloha.settings.plugins.indent.marginLeft;
                        }
                    }
                    var margin_type = get_unit(user_margin_text);
                    var margin_text = jQuery(data_to_add).prop("style").marginLeft;
                    var current_margin = parseFloat(margin_text);
                    if(isNaN(current_margin)){
                        current_margin=0.0;
                    }
                    var page_unit_value = get_unit(margin_text);
                    if(current_margin===0){
                        page_unit_value = margin_type; // if left-margin of the page is 0 use unit from settings
                    }
                    var new_margin_value = current_margin*changeNumber(page_unit_value,margin_type)+parseFloat(user_margin_text);
                    jQuery(data_to_add).css("margin-left",new_margin_value+margin_type);
                }

                function decrease_indent(data_to_add){
                    var user_margin_text = "48px"; // default left margin value                    
                    if (typeof Aloha.settings.plugins.indent !== 'undefined'){
                        if (typeof Aloha.settings.plugins.indent.marginLeft !== 'undefined'){
                            user_margin_text = Aloha.settings.plugins.indent.marginLeft;
                        }
                    }
                    var margin_text = jQuery(data_to_add).prop("style").marginLeft;
                    var current_margin = parseFloat(margin_text);
                    var margin_type = get_unit(margin_text);
                    if(isNaN(current_margin)){
                        current_margin=0.0;
                    }
                    var page_unit_value = get_unit(margin_text);
                    if(current_margin===0){
                        page_unit_value = margin_type; // if left-margin of the page is 0 use unit from settings
                    }
                    if(current_margin*changeNumber(page_unit_value,margin_type)>=parseFloat(user_margin_text)){
                    var new_margin_value = current_margin*changeNumber(page_unit_value,margin_type)-parseFloat(user_margin_text);
                    jQuery(data_to_add).css("margin-left",new_margin_value+margin_type);
                    }
                }

                return Plugin.create("indent", {
                        init: function() {
                            UI.adopt('indent-right', null, { // increase indent
                                click: function(){
                                    var range = Aloha.Selection.getRangeObject();
                                    var range_object = range.getSelectionTree();
                                    var start_container = range.startContainer.parentElement;
                                    var end_container = range.endContainer.parentElement;

                                    var $data_to_add=jQuery();

                                    if(start_container===end_container){
                                        $data_to_add = range_object[0].domobj.parentNode;
                                        increase_indent($data_to_add);
                                    } else {
                                        var are_we_in_range = false;
                                        jQuery.each(range_object,function(cnt,el){
                                            if (el.selection!=="none"){
                                                $data_to_add = el.domobj;
                                                increase_indent($data_to_add);
                                            }
                                        });

                                    }
                                }
                            });
                            UI.adopt('indent-left', null, { // decrease indent
                                click: function(){
                                    var range = Aloha.Selection.getRangeObject();
                                    var range_object = range.getSelectionTree();
                                    var start_container = range.startContainer.parentElement;
                                    var end_container = range.endContainer.parentElement;

                                    var $data_to_add=jQuery();
                                    var margin_left_value;

                                    if(start_container===end_container){
                                        $data_to_add = range_object[0].domobj.parentNode;
                                        decrease_indent($data_to_add);
                                    } else {
                                        var are_we_in_range = false;
                                        jQuery.each(range_object,function(cnt,el){
                                            if (el.selection!=="none"){
                                                $data_to_add = el.domobj;
                                                decrease_indent($data_to_add);
                                            }
                                        });

                                    }
                                }
                            });
        }
        });
});
