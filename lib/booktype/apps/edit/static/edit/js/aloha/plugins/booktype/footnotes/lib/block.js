define([
    'block/block'
], function(block) {
    var FootnotesBlock = block.AbstractBlock.extend({
    	'title': 'Footnotes',
          init: function($element, postProcessFn) {
          	console.log('INIT');
          	console.log($element);
            $element.wrapInner('<div class="title-editor"></div>');
//            $element.wrapInner('<div class="title-editor document_title aloha-editable"><h1>FOOTNOTES</h1></div>');

            return postProcessFn();
          },
          update: function($element, postProcessFn) {
            return postProcessFn();
          },
          renderBlockHandlesIfNeeded: function() {}

    });
 
    return {
        FootnotesBlock: FootnotesBlock
    };
});