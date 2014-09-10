define(
['aloha', 'aloha/plugin', 'jquery', 'booktype'],
function (Aloha, plugin, jquery, booktype) {
    'use strict';
    var GENTICS = window.GENTICS;

    var fontUnit = 'px';

    var sizeToShow = function (value) {
        var screenValue = ('' + value).trim();
        if (screenValue.length === 1) {
          screenValue = '&nbsp;&nbsp;' + value;
        }
        return screenValue;
      };

    var clearContent = function (node) {
      if (node.type === 'full') {
        if (node.domobj.nodeName.toLowerCase() === 'span') {
          jquery(node.domobj).css('font-size', '');

          var _style = jquery(node.domobj).attr('style');

          if (typeof _style === 'undefined') {
            var nr = new GENTICS.Utils.RangeObject();
            nr.startContainer = node.domobj;
            nr.endContainer = node.domobj;
            nr.startOffset = 0;
            nr.endOffset = 1;
            nr.select();

            var $a = jquery(node.domobj);
            $a.replaceWith($a.html());
          }
        }
      }

      jquery.each(node.children, function (idx, nd) {
        clearContent(nd);
      });
    };

    var setDefaultSize = function () {
      /* This does not set proper default size in many situations. */
      var rangeObject = Aloha.Selection.getRangeObject();

      jquery.each(rangeObject.getRangeTree(), function (idx, node) {
        clearContent(node);
      });

      rangeObject.select();
      Aloha.Selection.updateSelection();
    };

    var changeFontSize = function (fontDataSize) {
      var markup = jquery('<span></span>'),
        rangeObject = Aloha.Selection.getRangeObject();

      jquery.each(rangeObject.getRangeTree(), function (idx, node) {
        clearContent(node);
      });

      /*
      if (rangeObject.startContainer.nodeName !== '#text' && rangeObject.endContainer.nodeName !== '#text' && rangeObject.startContainer === rangeObject.endContainer) {
        jquery(rangeObject.startContainer).css('font-size', fontDataSize + fontUnit);
      } else {
        */
      jquery(markup).css('font-size', fontDataSize + fontUnit);
      window.GENTICS.Utils.Dom.addMarkup(rangeObject, markup, false);
      //}

      rangeObject.select();
      Aloha.Selection.updateSelection();
    };

    return plugin.create('fontsize', {
      defaultSettings: {
        sizes: [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30],
        unit: 'px'
      },
      init: function () {
        var htmlFontsizes = '';

        this.settings = jQuery.extend(false, this.defaultSettings, this.settings);
        fontUnit = this.settings.unit;

        jquery.each(this.settings.sizes, function (cnt, fs) {
            htmlFontsizes += '<li><a data-target="#" class="action changeFontsize" data-fontsize="' + fs + '" data-placement="bottom">' + fs + '</a></li>';
          });

        htmlFontsizes += '<li role="presentation" class="divider"></li>';
        htmlFontsizes += '<li><a data-target="#" class="action changeFontsize" data-fontsize="" data-placement="bottom">' +  booktype._('font_set_default_size', 'Set default size') + '</a></li>';

        Aloha.bind('aloha-editable-created', function ($event, $editable) {
          if ($editable.obj && $editable.obj.attr('id') === 'contenteditor') {
            var fontDataSize;
            jquery('.contentHeader .btn-toolbar .fontsize-dropdown').html(htmlFontsizes);

            jquery('.contentHeader .btn-toolbar .fontsize-dropdown a').on('click', function ($event) {
              fontDataSize = jquery($event.currentTarget).attr('data-fontsize');

              if (fontDataSize === '') {
                setDefaultSize();
              } else {
                changeFontSize(fontDataSize);

                jquery('button.btn.btn-default.btn-sm.fontSize').attr('data-fontsize', fontDataSize);
                jquery('button.btn.btn-default.btn-sm.fontSize').html(fontDataSize);
              }
            });

            jquery('button.btn.btn-default.btn-sm.fontSize').on('click', function () {
                fontDataSize = jquery('button.btn.btn-default.btn-sm.fontSize').attr('data-fontsize');
                changeFontSize(fontDataSize);
              });
          }
        });

        Aloha.bind('aloha-selection-changed', function (evt, range) {
          var $parent = null;

          if (range.markupEffectiveAtStart.length === 0) {
            $parent = range.commonAncestorContainer;
          } else {
            $parent = range.markupEffectiveAtStart[0];
          }
          // DPI = px*72/96
          var sizeValue = parseInt(jquery($parent).css('font-size'));

          if (!isNaN(sizeValue)) {
            jquery('button.btn.btn-default.btn-sm.fontSize').attr('data-fontsize', sizeValue);
            jquery('button.btn.btn-default.btn-sm.fontSize').html(sizeToShow(sizeValue));
          }
        });

      }
    });
  });

