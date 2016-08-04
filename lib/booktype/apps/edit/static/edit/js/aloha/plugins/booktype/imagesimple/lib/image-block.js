define(
  ['aloha/plugin', 'jquery', 'block/block'],
  function (Plugin, jQuery, block) {
    "use strict";

    var ImageBlock = block.AbstractBlock.extend({
      title: 'Image',
      isDraggable: function () {
        return false;
      },
      init: function ($element, postProcessFn) {
        var $div_caption_wrapper = null;
        var $div_caption_small = $element.find('div.caption_small');

        if ($div_caption_small.length === 0) {
          var $p_caption_small = $element.find('p.caption_small');

          // convert old formated caption_small to new format using div
          if ($p_caption_small.length && $p_caption_small.html().length) {
            $div_caption_small = jQuery('<div class="caption_small">' + $p_caption_small.html() + '</div>');
            $div_caption_small.addClass('aloha-editable');
            $div_caption_wrapper = jQuery('<div class="caption_wrapper">' + $div_caption_small.prop('outerHTML') + '</div>');
            $p_caption_small.replaceWith($div_caption_wrapper);
          }

        } else {
          // convert new style caption_small with div
          $div_caption_small.addClass('aloha-editable');
          $div_caption_wrapper = jQuery('<div class="caption_wrapper">' + $div_caption_small.prop('outerHTML') + '</div>');
          $div_caption_small.replaceWith($div_caption_wrapper);
        }

        return postProcessFn();
      },
      update: function ($element, postProcessFn) {
        return postProcessFn();
      }
    });

    return {ImageBlock: ImageBlock}
  }
);
