define(
['aloha', 'aloha/plugin', 'jquery'],
function (Aloha, plugin, jquery) {
    'use strict';
    var GENTICS = window.GENTICS;
    var textUnit = 'px';
    var cssStyle = [];

    var sizeToShow = function (value) {
        var screenValue = ('' + value).trim();
        if (screenValue.length === 1) {
          screenValue = '&nbsp;&nbsp;' + value;
        }
        return screenValue;
      };


    var traverseTree = function (range, tree, fontSize, level, startPos, endPos, inTree) {
      var cssValue;
      var nodePos = level;
      var startPosition = startPos;
      var endPosition = endPos;
      var nodeOrText = 'T';
      var positionInTree = inTree.slice();

      jquery.each(tree, function (cnt, el) {
        if ((el.type !== 'none') && (jquery(el.domobj).text().trim().length !== 0)) {
          if (el.domobj.nodeName === '#text') {
            endPosition = el.domobj.length;
          } else {
            if (el.domobj.nodeName !== 'SPAN') {
              positionInTree.push(cnt);
            }
          }
          if (el.domobj.parentNode.nodeName === 'DIV') {
            positionInTree = [cnt];
          }
          if (el.domobj.parentNode.nodeName !== 'SPAN') {
            startPosition = 0;
            if (jquery(el.domobj.parentNode).text() === jquery(el.domobj).text()) {
              startPosition = 0;
              endPosition = 0;
            }
          } else {
            if (el.type === 'partial') {
              startPosition = startPosition - (el.endOffset - el.startOffset);
              endPosition = endPosition - (el.endOffset - el.startOffset);
            }
          }

          var fullCssValue = jquery(el.domobj).prop('style');
          var cssTextValue = '';
          if (fullCssValue !== undefined) {
            cssValue = fullCssValue;
            if (fullCssValue.length > 1) {
              var elements = fullCssValue.cssText.split(';');
              jquery.each(elements, function (cnt1, el1) {
                if ((el1.indexOf('font-size') === -1) && (el1.length > 0)) {
                  cssTextValue = el1.trim();
                }
              });
            } else {
              cssTextValue = cssValue.cssText;
            }
            if ((cssTextValue.indexOf('font-size') === -1) && (cssTextValue.length !== 0)) {
              if (el.children.length > 1) {
                startPosition = el.children.length - 1;
                endPosition = el.children.length - 1;
                nodeOrText = 'N';
              } else {
                nodeOrText = 'T';
                startPosition = endPosition;
                endPosition = startPosition + el.children[0].domobj.length;
              }
              if (el.type !== 'none') {
                if ((el.domobj.parentNode.nodeName !== 'P') && (el.domobj.parentNode.nodeName !== 'SPAN')) {
                  nodePos ++;
                }
                cssStyle.push([cssTextValue, nodePos, startPosition, endPosition, nodeOrText, positionInTree]);
                positionInTree = [];
              }
            }
          }
          if (el.children.length > 0) {
            nodePos++;
            return traverseTree(range, el.children, fontSize, nodePos, startPosition, endPosition, positionInTree);
          }
        }
      });
      return true;
    };

    var removeColorMarkup = function (range) {
      var tree = range.getRangeTree();
      var $span = jquery('<span>');
      if ((range.commonAncestorContainer.nodeName === 'P') || (range.commonAncestorContainer.nodeName === 'SPAN') || (range.commonAncestorContainer.nodeName === 'DIV')) {
        GENTICS.Utils.Dom.removeMarkup(range, $span);
      } else {
        jquery.each(tree, function (cnt, el) {
          if (el.type !== 'none') {
            var nr = new GENTICS.Utils.RangeObject();
            nr.startContainer = el.domobj;
            nr.endContainer = el.domobj;
            nr.startOffset = 0;
            nr.endOffset = el.domobj.length;
            nr.select();
            GENTICS.Utils.Dom.removeMarkup(nr, $span);
          }
        });
      }
    };


    var getFontSize = function (fontDataSize) {
        var range = Aloha.Selection.getRangeObject();
        var tree = range.getRangeTree();
        var level = 0;
        var $span = jquery('<span>');
        traverseTree(range, tree, fontDataSize, level, 0, 0, []);
        removeColorMarkup(range, fontDataSize);
        GENTICS.Utils.Dom.addMarkup(range, $span.css('font-size', fontDataSize + textUnit));
        Aloha.Selection.updateSelection();

        var moveStart = 0;
        var moveTree = 0;
        jquery.each(tree, function (cnt, el) {
          if (el.type === 'full') {
            return false;
          }

          if (el.type === 'partial') {
            if (el.domobj.nodeName === '#text') {
              moveStart = el.domobj.length;
              moveTree = 1;
            }
            return false;
          }
        });

        var newTree = range.getRangeTree();
        var newRange = range;
        jquery.each(newTree, function (cnt, el) {
          if (el.children.length > 0) {
            newRange.startContainer = newRange.endContainer = el.children[0].domobj;
          }
        });
        jquery.each(cssStyle, function (cnt, el) {
          var cssSetting = el[0].split(':');
          if (el[1] === 0) {
            newRange.startOffset = el[2] - moveStart;
            newRange.endOffset = el[3] - moveStart;
            newRange.select();
            GENTICS.Utils.Dom.addMarkup(newRange, $span.css(cssSetting[0], cssSetting[1]));
          } else {
            if (el[5].length > 0) {
              jquery.each(el[5], function (cnt1, el1) {
                newTree = newTree[el1 + moveTree].children;
              });
            } else {
              jquery.each(newTree, function (cnt2, el2) {
                if (el2.type === 'full') {
                  newTree = newTree[cnt2].children;
                  return false;
                }
              });
            }
            var nr = new GENTICS.Utils.RangeObject();
            var textToMark;
            if (el[4] === 'T') {
              if (el[5].length > 0) {
                textToMark = newTree[0].children[0].domobj;
              } else {
                textToMark = newTree[0].domobj;
              }
              nr.startContainer = nr.endContainer = textToMark;
            } else {
              textToMark = newTree[0].children;
              nr.startContainer = textToMark[0].domobj;
              nr.endContainer = textToMark[textToMark.length - 1].domobj;
            }
            nr.startOffset = el[2];
            nr.endOffset = el[3];
            nr.select();
            Aloha.Selection.updateSelection();
            GENTICS.Utils.Dom.addMarkup(nr, $span.css(cssSetting[0], cssSetting[1]));
          }
        });
        cssStyle = [];

        jquery('button.btn.btn-default.btn-sm.fontSize').attr('data-fontsize', fontDataSize);
        jquery('button.btn.btn-default.btn-sm.fontSize').html(sizeToShow(fontDataSize));
      };

    return plugin.create('fontsize', {
        init: function () {
            var defaultSizeValue = parseInt(jquery(jquery('#contenteditor')[0]).css('font-size'), 10);
            var fontList;
            textUnit = jquery(jquery('#contenteditor')[0]).css('font-size').replace(defaultSizeValue, '');
            if (typeof Aloha.settings.plugins.fontsize === 'undefined') {
              fontList = [defaultSizeValue];
            } else {
              fontList = Aloha.settings.plugins.fontsize.fontsize;
              if (typeof Aloha.settings.plugins.fontsize.unit !== 'undefined') {
                textUnit = Aloha.settings.plugins.fontsize.unit;
              }
            }

            var htmlFontsizes = '';
            jquery.each(fontList, function (cnt, el) {
                var fontsizes;
                if (_.isArray(el)) {
                  fontsizes = el[0];
                } else {
                  fontsizes = el;
                }
                htmlFontsizes += '<li><a data-target="#" class="action changeFontsize" data-fontsize="' + fontsizes + '" data-placement="bottom">' + fontsizes + '</a></li>';
              });
            Aloha.bind('aloha-editable-created', function ($event, $editable) {
              if ($editable.obj && $editable.obj.attr('id') === 'contenteditor') {
                var fontDataSize;
                jquery('.contentHeader .btn-toolbar .fontsize-dropdown').html(htmlFontsizes);
                jquery('.contentHeader .btn-toolbar .fontsize-dropdown a').on('click', function ($event) {
                    fontDataSize = $event.currentTarget.text;
                    getFontSize(fontDataSize);
                  });
                jquery('button.btn.btn-default.btn-sm.fontSize').on('click', function () {
                    fontDataSize = jquery('button.btn.btn-default.btn-sm.fontSize').html();
                    getFontSize(fontDataSize);
                  });
              }
            });
            
            Aloha.bind('aloha-selection-changed', function () {
                var range = Aloha.Selection.getRangeObject();
                var styleValue;
                var attribute;
                var allMarkups = range.markupEffectiveAtStart;
                jquery.each(allMarkups, function (cnt, el) {
                  attribute = jquery(el).attr('style');
                  if (attribute !== undefined) {
                    if (attribute.indexOf('font-size') !== -1) {
                      styleValue = jquery(el).attr('style');
                      return false;
                    }
                  }
                });
                var sizeValue = defaultSizeValue;
                if (styleValue !== undefined) {
                  if (styleValue.indexOf('font-size') !== -1) {
                    sizeValue = parseInt(styleValue.split(':')[1], 10);
                  }
                }
                jquery('button.btn.btn-default.btn-sm.fontSize').attr('data-fontsize', sizeValue);
                jquery('button.btn.btn-default.btn-sm.fontSize').html(sizeToShow(sizeValue));
              });
          }
      });
  });