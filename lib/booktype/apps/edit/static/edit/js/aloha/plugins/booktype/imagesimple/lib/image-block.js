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
        var $divCaptionWrapper = null;
        var $divCaptionSmall = $element.find('div.caption_small');

        if ($divCaptionSmall.length === 0) {
          var $pCaptionSmall = $element.find('p.caption_small');

          // convert old formated caption_small to new format using div
          if ($pCaptionSmall.length && $pCaptionSmall.html().length) {
            $divCaptionSmall = jQuery('<div class="caption_small">' + $pCaptionSmall.html() + '</div>');
            $divCaptionSmall.addClass('aloha-editable');
            $divCaptionWrapper = jQuery('<div class="caption_wrapper">' + $divCaptionSmall.prop('outerHTML') + '</div>');
            $pCaptionSmall.replaceWith($divCaptionWrapper);
          } else if ($pCaptionSmall.length && $pCaptionSmall.html().trim() === '') {
            $pCaptionSmall.remove();
          }

        } else {
          // convert new style caption_small with div
          $divCaptionSmall.addClass('aloha-editable');
          $divCaptionWrapper = jQuery('<div class="caption_wrapper">' + $divCaptionSmall.prop('outerHTML') + '</div>');
          $divCaptionSmall.replaceWith($divCaptionWrapper);
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
