//styling
define(
['aloha', 'aloha/plugin','aloha/ephemera', 'jquery','jquery19', 'ui/ui', 'ui/button' ],
        function(Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button ){
                return Plugin.create("styling", {                        
                        init: function() {
                            var GENTICS = window.GENTICS;
                            console.log("styling");
                            UI.adopt('styling', null, {
                                click: function() {        
                                    console.log("clicked styling");
                                    var rangeObject = Aloha.Selection.getRangeObject();
                                    var common = rangeObject.getCommonAncestorContainer();

                                    function getTreeSetting(invalue){
                                        GENTICS.Utils.RangeObject.clearCaches; // clearing cache before new tree
                                        return rangeObject.getRangeTree(invalue);
                                    }

                                    function partial_styleRemover(in_rangeTree){

                                    }
                                    function full_styleRemover(in_rangeTree){
                                        
                                    }

                                    function styleRemover(in_rangeTree,in_type){
                                        //console.log(in_rangeTree);
                                        console.log("styleRemover");
                                        console.log(in_type);
                                        console.log("in**",in_rangeTree.type);                                        

                                        //jQuery(in_rangeTree.domobj).removeAttr("style");
                                        console.log("loop");
                                        /*if(in_rangeTree.type=="none"){
                                            jQuery(in_rangeTree.domobj).removeAttr("style");                                            
                                        } */
                                        jQuery.each(getTreeSetting(in_rangeTree.domobj),function(cnt,el){
                                            //if(el.type=="full"){
                                            if(in_type=="full"){
                                                jQuery(el.domobj).removeAttr("style");
                                            }
                                            var part_rangeTree = getTreeSetting(el.domobj);
                                            if((part_rangeTree.length)>1){
                                                //styleRemover(el,part_rangeTree.type);
                                                styleRemover(el,in_type);
                                            } else { // dom object not proper or is it? check domobj in the full if statement - the look
                                                console.log("dom**",el.domobj);
                                                jQuery(el.domobj).removeAttr("style");
                                            }
                                          /*  if(el.type!="none"){
                                                var part_rangeTree = getTreeSetting(el.domobj);
                                                //console.log(el, part_rangeTree.length);
                                                if(el.type=="full"){
                                                    console.log("removing first");
                                                    console.log(el);
                                                    jQuery(el.domobj).removeAttr("style");
                                                    console.log("removing first end");
                                                } else {
                                                    styleRemover(el);
                                                }
                                                if(part_rangeTree.length>1){
                                                    styleRemover(el);
                                                } else {
                                                    if(el.type=="full"){
                                                        console.log(el.domobj);
                                                        jQuery(el.domobj).removeAttr("style");
                                                    }
                                                }
                                            } */
                                        });
                                        console.log("end loop");
                                        console.log("end styleRemover");
                                    }
                                    
                                    var limit = Aloha.activeEditable.obj;
                                    var markup = jQuery("<p>");
                                    var nodeName = markup.get(0).nodeName;
                                    var highestObject, root, rangeTree;
                                    highestObject = GENTICS.Utils.Dom.findHighestElement(common, nodeName, limit);
                                    root = highestObject ? highestObject.parentNode : common;
                                    if (root) {
                                        rangeTree = getTreeSetting(root);
                                        var i, rangeLength, content;
                                        for (i = 0, rangeLength = rangeTree.length; i < rangeLength; ++i) {
                                            if(rangeTree[i].type=="partial"){
                                                jQuery.each(rangeTree[i],function(cnt,el){
                                                    console.log("RT**",el);
                                                    if(el.type=="full"){
                                                        jQuery(el.domobj).removeAttr("style");
                                                    }
                                                });
                                            }
                                            //console.log(rangeTree[i].domobj,rangeTree[i].type);
                                            //console.log("**",rangeTree[i].type);
                                            if(rangeTree[i].type!="none"){
                                                var new_rangeTree = getTreeSetting(rangeTree[i].domobj);
                                                console.log("each**",rangeTree[i].type,rangeTree[i].domobj);
                                                //console.log("new**",rangeTree[i].type,rangeTree[i].domobj);
                                                if(new_rangeTree.length>1){
                                                    jQuery.each(new_rangeTree,function(cnt,el){
                                                        console.log("each**",el);
                                                        styleRemover(el,rangeTree[i].type); 
                                                    }); 
                                                } else {
                                                    //console.log("1->",new_rangeTree[0]);
                                                    if(new_rangeTree[0].type=="full"){
                                                        console.log("removing object->",new_rangeTree[0].domobj);
                                                        jQuery(new_rangeTree[0].domobj).removeAttr("style");
                                                    }
                                                }
                                            }
                                        }   
                                    }
                                    console.log("finish");
                                    //rangeObject.select();
                            }
                        });                                    
                    }
                });
            }); 