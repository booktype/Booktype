  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/console', 'aloha/ephemera', 'block/block', 'block/blockmanager'], 
        function(Aloha, Plugin, jQuery,  jQuery19, UI, Console, Ephemera, block, BlockManager) {

            var editable = null;
            var range = null;

            // Define Page Break Block
            var BreakBlock = block.AbstractBlock.extend({
                      title: 'Page Break',
                      isDraggable: function() {return false;},
                      init: function($element, postProcessFn) {             
                               // Will erase if anything is inside and insert small icon while we are
                               // editing this content.
                               $element.empty().append('<i class="icon-ellipsis-horizontal"></i>');

                               return postProcessFn();
                      },
                      update: function($element, postProcessFn) {

                        return postProcessFn();
                      }
                });                 

            return Plugin.create('pbreak', {
                init: function () {
                   // Register this block
                   BlockManager.registerBlockType('BreakBlock', BreakBlock);

                   // Every time content is fetched from Aloha will run this function which
                   // iterates over all the elements
                   var a = Ephemera.ephemera().pruneFns.push(function(node) {
                        var $node = jQuery(node);

                        // If this is Break Block element just return new node.
                        // We could have cleared the attributes and erase <i> instead
                        if($node.hasClass("aloha-block-BreakBlock")) {
                            node = jQuery('<div class="page-break"></div>')[0];
                        }

                        return node;
                    })

                   // When editor is initialised check if there is any page break in our content.
                   // If there is initiate Page Break Block for each of the elements.
                   Aloha.bind('aloha-editable-created', function($event, editable) {
                      editable.obj.find('DIV.page-break').alohaBlock({'aloha-block-type': 'BreakBlock'});
                   });

                   UI.adopt('pbreak', null, {
                      click: function() {        
                         editable = Aloha.activeEditable;
                         range = Aloha.Selection.getRangeObject();

                         // Insert div element inside with a certain class
                         // After that, create Page Break Block out of it
                         var $a = jQuery('<div class="page-break"></div>');
                         $a.alohaBlock({'aloha-block-type': 'BreakBlock'});                       

                         GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
                         
                         range.select();
                      }
                    });
                }
            });

        }
);