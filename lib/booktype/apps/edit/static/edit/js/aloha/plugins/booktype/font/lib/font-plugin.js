//BK-796
define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery','jquery19', 'ui/ui', 'ui/button', 'underscore' ],
        function(Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button, _){
                var GENTICS = window.GENTICS;

                var changeFont = function (font_name, $editable) {
                                    var range = Aloha.Selection.getRangeObject();

                                    var selection_start = range.startOffset;
                                    var selection_end = range.endOffset;

                                    if ((selection_end===0)||(selection_end===undefined)){ // nothing selected
                                        return;
                                    }

                                    var element_selected = range.endContainer.data;
                                    var $span_add;

                                    if((range.startContainer === range.endContainer) && (selection_end==element_selected.length) && (selection_start===selection_end)){
                                        var node_name = range.splitObject.nodeName;

                                        $span_add = jQuery("<"+node_name+" style='font-family:"+font_name+"'>").append(element_selected);  

                                        GENTICS.Utils.Dom.removeRange(range);
                                        GENTICS.Utils.Dom.insertIntoDOM($span_add,range,range.obj);
                                    } else {
                                        $span_add = jQuery("<span style='font-family:"+font_name+"'>");

                                        GENTICS.Utils.Dom.addMarkup(range, $span_add, false);
                                    }
                                    range.select();                                    
                                }

                return Plugin.create("font", {                        
                        // Default 
                        config: {'fontlist': ['serif', 'sans serif']},
                        init: function() {
                                var html_list_fonts = "";

                                if(typeof Aloha.settings.plugins.font === 'undefined') {
                                    this.settings = this.config;
                                }

                                jQuery.each(this.settings.fontlist,function(cnt,el){
                                    var fontNames = null, fontDescription = '';

                                    if(_.isArray(el)) {
                                        fontDescription = el[0];
                                        fontNames = el[1];
                                    } else {
                                        fontDescription = fontNames = el;
                                    }

                                    html_list_fonts+="<li role=\"presentation\"><a role=\"menuitem\"data-target='#' class='action font' data-fontname='"+fontNames+"' data-placement='bottom'>"+fontDescription+"</a></li>"
                                });

                               Aloha.bind('aloha-editable-created', function($event, editable) {
                                    // inject value to hmtl
                                   jQuery(".contentHeader .btn-toolbar .font-dropdown").html(html_list_fonts);
                                   jQuery(".contentHeader .btn-toolbar .font-dropdown a").on('click', function (event) {
                                        var font_selected = jQuery(event.currentTarget).attr('data-fontname'); // what about other font names ???

                                        changeFont(font_selected, editable);
                                        return true;
                                   }); 
                               });  

                       
                }
        });
});
