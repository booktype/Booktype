define(
  ['aloha', 'aloha/plugin', 'aloha/ephemera', 'jquery', 'jquery19', 'ui/ui', 'ui/button', 'underscore', 'PubSub'],
  function (Aloha, Plugin, Ephemera, jQuery, jQuery19, UI, Button, _, PubSub) {
    'use strict';
    var cssTag = 'font-family';

    var changeFont = function (fontName, $editable) {
      var rangeObject = Aloha.Selection.getRangeObject();
      var parents = rangeObject.getSelectionTree();
      var count = 0;
      var partialReplace = false;

      // Loop through all matching markup sections and apply the new CSS
      for (var i = 0; i < parents.length; i++) {
        if (parents[i].selection.toLowerCase() === 'full') {
          count = 0;

          jQuery(parents[i].domobj).find('span').each(function () {
            count += 1;
            jQuery(this).css(cssTag, fontName);
          });

          // If there is no elements in tree, let's check it's parent
          if (count === 0 && parents.length === 1) {
            jQuery(parents[i].domobj).parent().each(function () {
              if (this.nodeName.toLowerCase() === 'span') {
                count += 1;
                jQuery(this).css(cssTag, fontName);
              }
            });
          }

          // now is time to check the children for this parent
          if (parents[i].children.length > 0) {
            fixChildren(parents[i].children, cssTag, fontName);
            continue;
          }

          if (count === 0 || (parents[i].domobj.tagName && parents[i].domobj.tagName.toLowerCase() !== 'span')) {
            var domText = jQuery(parents[i].domobj).text();
            var spanTag = createTag('span', fontName);

            if (isValidText(domText)) {
              if (parents[i].domobj.nodeType === 3)
                jQuery(parents[i].domobj).wrap(spanTag);
              else {
                jQuery(parents[i].domobj).wrapInner(spanTag);
              }
            }
          }

        } else if (parents[i].selection.toLowerCase() === 'partial') {
          var children = parents[i].children;
          if (children.length > 0) {
            fixChildren(children, cssTag, fontName);
          } else {
            replaceItem(parents[i], cssTag, fontName, rangeObject);
          }
          partialReplace = true;
        }
      }

      if (!partialReplace)
        rangeObject.select();
    };

    // Used to apply the new font to the selected content according to the nodeType,
    // tag type and type of selection
    var replaceItem = function (item, cssTag, fontName, rangeObject) {
      if (item.domobj.nodeType === 3 && item.selection === 'partial') {
        var text = item.domobj.data.substr(item.startOffset, item.endOffset - item.startOffset);
        if (isValidText(text)) {
          text = '<span style="' + cssTag + ': ' + fontName + '">' + text + '</span>';
          text = item.domobj.data.substr(0, item.startOffset) + text;
          text = text + item.domobj.data.substr(item.endOffset, item.domobj.data.length - item.endOffset);
          jQuery(item.domobj).replaceWith(text);
        }
      } else if (item.domobj.nodeType === 3 && item.selection === 'full') {
        var text = jQuery(item.domobj).text();
        if (isValidText(text)) {
          var spanTag = createTag('span', fontName);
          jQuery(item.domobj).wrap(spanTag);
        }
      } else if (item.domobj.tagName && item.domobj.tagName.toLowerCase() === 'span' && item.selection === 'full') {
        jQuery(item.domobj).css(cssTag, fontName);
        jQuery(item.domobj).find('span').each(function () {
          jQuery(this).css(cssTag, fontName);
        });
      } else {
        if (item.selection !== 'none') {
          window.GENTICS.Utils.Dom.addMarkup(rangeObject, createTag('span', fontName), false);
        }
      }
    };

    // This checks if the given items has children to get into the
    // deep level of selection, so we can try each tag the right way
    // according to the selection type
    var fixChildren = function (items, cssTag, fontName) {
      for (var i = 0; i < items.length; i++) {
        var item = items[i];

        // this a very special case for content editable tags that aloha use
        // to handle some kind of tags like headings and tables
        if (item.children.length === 1 && item.domobj.tagName.toLowerCase() === 'div') {
          var domText = jQuery(item.domobj).text();
          var spanTag = createTag('span', fontName);

          if (isValidText(domText)) {
            if (item.selection === 'full') {
              jQuery(item.domobj).wrapInner(spanTag);
            } else {
              replaceItem(item.children[0], cssTag, fontName);
            }
          }
        } else if (item.children.length > 0) {
          fixChildren(item.children, cssTag, fontName);
        } else {
          if (item.domobj.nodeType === 3) {
            replaceItem(item, cssTag, fontName);
          }
        }
      }
    };

    // Returns true if the given text is more than just empty spaces
    var isValidText = function (text) {
      text.replace(/(\r\n|\n|\r)/gm, '');
      return (/\S/.test(text));
    };

    // Returns a new html tag with the selected font already applied as style
    var createTag = function (tagName, fontName) {
      var tag = jQuery(document.createElement(tagName));
      tag.css(cssTag, fontName);
      return tag;
    };

    return Plugin.create('font', {
      config: {
        'fontlist': ['serif', 'sans serif']
      },

      init: function () {
        var htmlListFonts = '';

        if (typeof Aloha.settings.plugins.font === 'undefined') {
          this.settings = this.config;
        }

        jQuery.each(this.settings.fontlist, function (cnt, el) {
          var fontNames = null,
            fontDescription = '';

          if (_.isArray(el)) {
            fontDescription = el[0];
            fontNames = el[1];
          } else {
            fontDescription = fontNames = el;
          }

          htmlListFonts += '<li role=\"presentation\"><a role=\"menuitem\" data-target="#"" class="action font" data-fontname="' + fontNames + '" data-placement="bottom">' + fontDescription + '</a></li>';

          Aloha.bind('aloha-editable-created', function ($event, editable) {
            // inject value to hmtl
            jQuery('.contentHeader .btn-toolbar .font-dropdown').html(htmlListFonts);

            jQuery('.contentHeader .btn-toolbar .font-dropdown a').on('click', function (event) {
              var selectedFont = jQuery(event.currentTarget).attr('data-fontname');
              changeFont(selectedFont, editable);

              // publish message notification that change-font was clicked
              PubSub.pub('toolbar.action.triggered', {'event': event});

              return true;
            });
          });

        });

      }
    });
  }
);