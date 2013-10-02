define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery','jquery19', 'ui/ui', 'ui/button' ],
        function(Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button ){
                return Plugin.create("font", {                        
                        init: function() {
                                var GENTICS = window.GENTICS;
                                var list_of_fonts = ["Arial","Swiss"];
                                function changeFont(){
                                        var selection_start = Aloha.Selection.rangeObject.startOffset;
                                        var selection_end = Aloha.Selection.rangeObject.endOffset;
                                        if (selection_end===0){ // nothing selected
                                                return;
                                        }
                                        var element_selected = Aloha.Selection.rangeObject.splitObject;
                                        console.log(Aloha.Selection.rangeObject.splitObject);
                                        console.log(selection_start);
                                        console.log(selection_end);
                                        if((selection_start===0)&&(selection_start===jQuery(element_selected).text().length)){
                                                console.log("change whole css");
                                        } else {
                                                console.log("insert span");
                                                var editable = Aloha.Selection.rangeObject;
                                                //var $span_add = jQuery("<span class='something'>");
                                                var value_selected = jQuery(element_selected).text().substring(selection_start,selection_end);
                                                var $span_add = jQuery("<span class='something'>").append(value_selected);
                                                GENTICS.Utils.Dom.removeRange(editable);
                                                GENTICS.Utils.Dom.insertIntoDOM($span_add,editable,editable.obj);
                                                //GENTICS.Utils.Dom.insertIntoDOM($span_start, selection_start, editable.obj);
                                                //GENTICS.Utils.Dom.insertIntoDOM($span_end, selection_end, editable.obj);
                                        }                                   
                                }
                                //Ephemera.classes("aloha-wcount");
                                UI.adopt('font', null, {
                                        click: function() {        
                                                changeFont();

/*                                                jQuery19("#elCount .modal-dialog .modal-content .modal-body .wcount").text(wcount);
                                                jQuery19("#elCount .modal-dialog .modal-content .modal-body .charcount").text(charcount);
                                                jQuery19("#elCount .modal-dialog .modal-content .modal-body .charspacecount").text(charspacecount);
                                                jQuery19('#elCount').modal('show'); */

                                        }
                                });                                
        }
        });
});
