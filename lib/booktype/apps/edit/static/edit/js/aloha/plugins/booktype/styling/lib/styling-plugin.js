//styling
define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery','jquery19', 'ui/ui', 'ui/button' ],
        function(Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button ){
                return Plugin.create("styling", {                        
                        init: function() {
                            var GENTICS = window.GENTICS;

                            UI.adopt('styling', null, {
                                click: function() {        
                                    var rangeObject = Aloha.Selection.getRangeObject();
                                    var common = rangeObject.getCommonAncestorContainer();
                                    var limit = Aloha.activeEditable.obj;
                                    var markup = jQuery("<p>");
                                    var nodeName = markup.get(0).nodeName;
                                    var highestObject, root, rangeTree;

                                    function partial_styleRemover(in_rangeTree){
                                        var new_in_rangeTree = in_rangeTree.children;
                                        if(new_in_rangeTree.length>1){
                                            jQuery.each(new_in_rangeTree, function(cnt,el) {
                                                if(el.type=="partial"){
                                                    partial_styleRemover(el);
                                                }
                                                if(el.type=="full"){
                                                    full_styleRemover(el);
                                                }
                                            });
                                        }

                                    }
                                    function full_styleRemover(in_rangeTree){
                                        var new_in_rangeTree = in_rangeTree.children;
                                        jQuery(in_rangeTree.domobj).removeAttr("style"); // remove if style at the top of the dom tree                                                
                                        if(new_in_rangeTree.length>0){
                                            jQuery.each(new_in_rangeTree,function(cnt,el) {
                                                full_styleRemover(el);
                                            });
                                        } else {
                                            jQuery(in_rangeTree.domobj).removeAttr("style");
                                        }                                        
                                    }

                                    function removeEmptySpans(invalue){
                                        var rt;
                                        jQuery.each(invalue,function(cnt,el){
                                            if(el.type!="none"){
                                                if(el.children.length>1){
                                                    if(el.type=="full"){
                                                        rt = Aloha.Selection.getRangeObject();
                                                        GENTICS.Utils.Dom.removeMarkup( rangeObject, jQuery("<span>"), limit );
                                                    }
                                                    removeEmptySpans(el.children);
                                                } else {
                                                    if(el.type=="full"){
                                                        var html_markup_name = el.domobj.nodeName;
                                                        var jq_html_markup = jQuery(el.domobj);
                                                        if((html_markup_name=="SPAN")&&(jq_html_markup.attr("class")==undefined)&&(jq_html_markup.attr("style")==undefined)){
                                                            rt = Aloha.Selection.getRangeObject();
                                                            GENTICS.Utils.Dom.recursiveRemoveMarkup( rt.getRangeTree("SPAN"), jQuery("<span>") );
                                                        }  

                                                    }

                                                }
                                            }
                                        });
                                    }
                                    highestObject = GENTICS.Utils.Dom.findHighestElement(common, nodeName, limit);
                                    root = highestObject ? highestObject.parentNode : common;
                                    if (root) {
                                        rangeTree = rangeObject.getRangeTree(root);
                                        var i, rangeLength, content;
                                        jQuery.each(rangeTree,function(cnt,el){
                                            if(el.type=="full"){
                                                full_styleRemover(el);
                                            }
                                            if(el.type=="partial"){
                                                partial_styleRemover(el);
                                            }
                                        });
                                    removeEmptySpans(rangeTree);                                                                                    
                            }
                        }                                    
                    });
                }
            }); 
    }); 