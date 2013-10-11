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

                                    console.log(' common je ', common);
                                    console.log(' common je ', jQuery(common)); 

                                    console.log("=======");
                                    console.log("test");
                                    console.log(rangeObject);
                                    console.log(rangeObject.endContainer.nodeValue);
                                    console.log("=======");
                                    
                                    var limit = Aloha.activeEditable.obj;
                                    var markup = jQuery("<p>");
                                    var nodeName = markup.get(0).nodeName;
                                    var highestObject, root, rangeTree;
                                    highestObject = GENTICS.Utils.Dom.findHighestElement(common, nodeName, limit);
                                    root = highestObject ? highestObject.parentNode : common;
                                    if (root) {
                                        rangeTree = rangeObject.getRangeTree(root);
                                        var i, rangeLength, content;
                                        for (i = 0, rangeLength = rangeTree.length; i < rangeLength; ++i) {
                                            console.log(rangeTree[i].type,rangeTree[i].domobj.nodeName);
                                            if (rangeTree[i].type == 'full') {
                                                if(rangeTree[i].domobj.nodeName == markup.get(0).nodeName) {
                                                        console.log(rangeTree[i].domobj);
                                                        jQuery(rangeTree[i].domobj).removeAttr("style");                                                
                                                }                                                  
                                                markup = jQuery("<span>");
                                                jQuery.each(rangeTree[i],function(cnt,el){
                                                    if(el.length>0){
                                                        for(j=0;j<el.length;j++){
                                                            if((el[j].type=="full")&&(el[j].domobj.nodeName == markup.get(0).nodeName)) {                                                                                                               
                                                                    jQuery(el[j].domobj).removeAttr("style");                                                
                                                                }  
                                                        }
                                                    };
                                                });
                                            }
                                        }   
                                    }
                                    console.log("finish");
                                    rangeObject.select();
                            }
                        });                                    
                    }
                });
            }); 