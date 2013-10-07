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

/*                                // select font dialog
                               var html_list_fonts = "";
                                jQuery.each(list_of_fonts.fontlist,function(cnt,el){
                                        html_list_fonts+="<li><a href='#' class='action font' data-tagname='"+list_of_fonts.fontpaths[el]+"' data-placement='bottom'>"+el+"</a></li>"
                                        });

                                console.log(html_list_fonts);
                                // inject value to hmtl
                                jQuery(".btn-toolbar .font-dropdown").html(html_list_fonts); 
                                //jQuery(".templateAlohaToolbar .btn-toolbar .font-dropdown").html(html_list_fonts);  */ 

                                function changeFont(font_name){
                                        var selection_start = Aloha.Selection.rangeObject.startOffset;
                                        var selection_end = Aloha.Selection.rangeObject.endOffset;
                                        if ((selection_end===0)||(selection_end===undefined)){ // nothing selected
                                                return;
                                        }
                                        var editable = Aloha.Selection.rangeObject;                                        
                                        var element_selected = editable.endContainer.data;
                                        console.log("======");
                                        console.log(Aloha.Selection.rangeObject.splitObject);
                                        console.log(selection_start);
                                        console.log(selection_end);
                                        console.log("======");
                                        if((selection_start===0)&&(selection_start===jQuery(element_selected).text().length)){
                                                console.log("change whole css");
                                                var node_name_editable = editable.commonAncestorContainer.nodeName;
                                                console.log(node_name_editable);
                                                var node_attributes_list = editable.commonAncestorContainer.attributes;
                                                var new_values_node_attributes = "<"+node_name_editable+" ";
                                                jQuery.each(node_attributes_list,function(cnt,el){
                                                        if(el.name!='style'){
                                                                new_values_node_attributes+=el.name+"='"+el.value+"' ";
                                                        } else {
                                                                new_values_node_attributes+="style='font-family:"+font_name+";"+el.value+"'";
                                                        }
                                                }); 
                                                // adding style if there is style already added
                                                if (new_values_node_attributes.indexOf("style")==-1){
                                                    new_values_node_attributes+="style='font-family:"+font_name+"'";
                                                }
                                                new_values_node_attributes +=">";
                                                console.log(new_values_node_attributes);
                                                var $span_add = jQuery(new_values_node_attributes).append(element_selected);                          
                                        } else {
                                                console.log("insert span");
                                                var value_selected = element_selected.substring(selection_start,selection_end);
                                                var $span_add = jQuery("<span style='font-family:"+font_name+"'>").append(value_selected);
                                        }                                   
                                        GENTICS.Utils.Dom.removeRange(editable);
                                        GENTICS.Utils.Dom.insertIntoDOM($span_add,editable,editable.obj);
                                }
                                UI.adopt('font', null, {
                                        click: function() {  
                                                console.log("ui adopt font");
                                                console.log(jQuery("#contentHeader"));
                                                // inject value to hmtl
                                                jQuery(".contentHeader .btn-toolbar .font-dropdown").html(html_list_fonts); 
                                                jQuery(".contentHeader .btn-toolbar .font-dropdown").menu({
                                                    select: function(event,ui){
                                                        console.log(event);
                                                        var font_selected = jQuery(event.currentTarget).text();
                                                        changeFont(font_selected);
                                                    }
                                                }); 
                                                //jQuery(".templateAlohaToolbar .btn-toolbar .font-dropdown").html(html_list_fonts);                                   

/*                                                var font_selected = jQuery(e.currentTarget).text();
                                                console.log(font_selected);
                                                changeFont(font_selected);  */
                                        }
                                });                                
        }
        });
});
