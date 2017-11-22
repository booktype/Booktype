define(
  ['aloha/plugin', 'jquery', 'block/block', 'imageeditor/bk-image-editor'],
  function (Plugin, jQuery, block, BkImageEditor) {
    "use strict";

    var ImageBlock = block.AbstractBlock.extend({
      title: 'Image',
      isDraggable: function () {
        return false;
      },
      init: function ($element, postProcessFn) {
        var layout = BkImageEditor.getImageLayout($element);
        var $divCaptionSmall = null;

        if (layout === 'image-layout-2images_2captions_bottom') {
          $divCaptionSmall = $element.find('div.caption_small');
          $divCaptionSmall.addClass('aloha-editable');
          $divCaptionSmall.wrap('<div class="caption_wrapper"/>');
        } else {
          var $divCaptionWrapper = null;
          $divCaptionSmall = $element.find('div.caption_small');

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
            if (!$divCaptionSmall.parent().hasClass('caption_wrapper')) {
              $divCaptionWrapper = jQuery('<div class="caption_wrapper">' + $divCaptionSmall.prop('outerHTML') + '</div>');
              $divCaptionSmall.replaceWith($divCaptionWrapper);
            }

          }
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
