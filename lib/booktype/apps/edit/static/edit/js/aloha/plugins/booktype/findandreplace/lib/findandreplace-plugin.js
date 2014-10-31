define(['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui' ],
function (Aloha, plugin, jquery, jquery19, UI) {
    'use strict';

    var GENTICS = window.GENTICS;
    var nextSiblingStack;
    var selectedPos;
    var $content;
    var startPos;
    var isStart;
    var nextCounter;
    var offsetTopPrev;
    var $dialog;
    var search;
    var replace;

    var closeSearchDialog = function () {
      $dialog.find('.msg-report').removeClass('hide');
      window.setTimeout(function () {
        $dialog.modal('hide');
        $dialog.find('INPUT[name=find]').val('');
        $dialog.find('INPUT[name=replace]').val('');
      }, 1000);
    };

    var scrollToSelection = function (direction, range) {
      range.getCommonAncestorContainer();
      var currentWindowHeight = jquery(window).height();
      var currentOffsetTop = range.commonAncestorContainer.offsetTop;
      var position =  currentOffsetTop - offsetTopPrev;

      if ((offsetTopPrev !== currentOffsetTop) || (currentWindowHeight >= position)) {
        if (direction === 1) {
          window.scrollBy(0, position);
        } else {
          if (position < 0) {
            window.scrollBy(0, position);
          }
        }
      }
      offsetTopPrev = range.commonAncestorContainer.offsetTop;
    };

    var markFound = function ($content, direction, textToMark, position) {
      var range = new GENTICS.Utils.RangeObject({
        startContainer : $content,
        startOffset : position,
        endContainer : $content,
        endOffset : position + textToMark.length,
      });
      range.select();
      Aloha.Selection.updateSelection();
      scrollToSelection(direction, range);
    };


    var traverse = function ($incontent) {
      if ($incontent === undefined) {
        return;
      }
      if ($incontent.nextSibling !== null) {
        nextSiblingStack.push($incontent.nextSibling);
      }
      if ($incontent.nodeName === '#text') {
        $content = $incontent;
        return false;
      }
      if ($incontent.nodeName === 'BR') {
        return false;
      }
      if ($incontent.childNodes.length > 0) {
        return traverse($incontent.childNodes[0]);
      }
      return traverse(nextSiblingStack.pop());
    };

    var traverseToCurrentRange = function (currentRange) {
      var prevContent;
      var currentCursorPos = currentRange.startOffset;
      search = $dialog.find('INPUT[name=find]').val();
      nextCounter = 0;
      startPos = 0;
      $content = jquery('#contenteditor')[0].childNodes[0];
      if (currentRange.markupEffectiveAtStart.length === 0) { // at the title - no markup so far
        startPos = currentRange.endOffset;
        return;
      }
      var isSelected = -1;
      selectedPos = 0;
      while (isSelected === -1) {
        isSelected = currentRange.markupEffectiveAtStart.indexOf($content);
        prevContent = $content;
        traverse($content);
        innerSearch($content);
        if (selectedPos !== -1) {
          if ($content !== currentRange.startContainer) {
            nextCounter ++;
            startPos = selectedPos + search.length;
          } else {
            if (selectedPos < currentCursorPos) {
              nextCounter ++;
              startPos = selectedPos + search.length;
            } else {
              break;
            }
          }
        } else {
          if (nextSiblingStack.length > 0) {
            $content = nextSiblingStack.pop();
            isSelected = -1;
            startPos = 0;
          } else {
            return;
          }
        }
      }
      $content = prevContent;
      selectedPos = 0;
    };

    var countOccurances = function (search) {
      var innerText = jquery(jquery('#contenteditor').html().split('</').join('\n</')).text().toLowerCase();
      var counter = 0;
      var fromPos = 0;
      var foundPos = 0;
      while (foundPos !== -1) {
        foundPos = innerText.indexOf(search.toLowerCase(), fromPos);
        fromPos = foundPos + search.length;
        if (foundPos !== -1) {
          counter ++;
        }
      }
      return counter;
    };

    var innerSearch = function (textToSearch) {
      search = $dialog.find('INPUT[name=find]').val();
      selectedPos = jquery(textToSearch).text().toLowerCase().indexOf(search.toLowerCase(), startPos);
    };

    var initData = function () {
      selectedPos = -1;
      startPos = 0;
      nextCounter = 0;
      nextSiblingStack = [];
    };

    return plugin.create('findandreplace', {
        defaults: {
        },
        init: function () {
            $dialog = jquery19('#find-replace');
            search = '';
            replace = '';
            offsetTopPrev = 0;
            var newSearch = true;

            Aloha.bind('aloha-editable-created', function (event, $editable) {
              if ($editable.obj && $editable.obj.attr('id') === 'contenteditor') {
                jquery('#contenteditor').on('click', function () { // clicked - might as well be editing???
                  jquery('#contenteditor').off('click');
                  isStart = false;
                });
                initData();
                isStart = true;
                $dialog.find('INPUT[name=find]').val('');
                $dialog.find('INPUT[name=replace]').val('');
                $dialog.find('.next-button').attr('disabled', true);
                $dialog.find('.prev-button').attr('disabled', true);
                $dialog.find('.replace-button').attr('disabled', true);
              }
            });

            $dialog.find('INPUT[name=replace]').focus(function () {
              $dialog.find('.replace-button').attr('disabled', false);
            });

            $dialog.find('BUTTON.prev-button').on('click', function () {
              var numberOfOccurances = countOccurances(search);
              if ((numberOfOccurances === 1) || (nextCounter === 1)) {
                return;
              }
              $content = jquery('#contenteditor')[0].childNodes[0];
              selectedPos = -1;
              nextSiblingStack = [];
              nextCounter--;
              startPos = 0;
              var i = 0;

              traverse($content);

              while (i < numberOfOccurances) {
                while (selectedPos === -1) {
                  innerSearch($content);
                  if (selectedPos === -1) {
                    if (nextSiblingStack.length > 0) {
                      $content = nextSiblingStack.pop();
                    } else {
                      break;
                    }
                    startPos = 0;
                    traverse($content);
                  }
                }

                if (selectedPos !== -1) {
                  i++;
                  if (i < nextCounter) {
                    startPos = selectedPos + search.length;
                    selectedPos = -1;
                  }
                }
              }
              if (nextCounter !== 0) {
                markFound($content, -1, search, selectedPos);
              }
              startPos = selectedPos + search.length;
              selectedPos = -1;
            });

            $dialog.on('shown.bs.modal', function () {
              $dialog.find('INPUT[name=replace]').val('');
              jquery19($dialog).draggable();
              $dialog.find('.msg-report').addClass('hide');
              $dialog.find('INPUT[name=find]').focus();
            });

            $dialog.find('INPUT[name=find]').on('keyup', function () {
              if ($dialog.find('INPUT[name=find]').val().length === 0) {
                $dialog.find('.next-button').attr('disabled', true);
              } else {
                $dialog.find('.next-button').attr('disabled', false);
              }
              $dialog.find('.prev-button').attr('disabled', true);
              selectedPos = -1;
              newSearch = true;
            });
                 
            $dialog.find('BUTTON.next-button').on('click', function () {
              var currentRange = Aloha.Selection.getRangeObject();
              var currentCursorPos = currentRange.startOffset;
              if ((newSearch) && (!isStart)) {
                if (startPos < currentRange.startOffset) {
                  startPos = currentRange.startOffset;
                }
                traverseToCurrentRange(currentRange);
              }
              newSearch = false;
              search = $dialog.find('INPUT[name=find]').val();
              var numberOfOccurances = countOccurances(search);
              if (nextCounter === numberOfOccurances) { // already at the end
                return;
              }
              $dialog.find('.replace-button').attr('disabled', true);
              if (numberOfOccurances > 1) {
                $dialog.find('.prev-button').attr('disabled', false);
              }

              if (isStart) {
                initData(); // needed to get search in the title
                $content = jquery('#contenteditor')[0].childNodes[0];
                isStart = false;
                traverse($content);
              } else {
                if ($content !== currentRange.startContainer) {
                  traverseToCurrentRange(currentRange);
                  selectedPos = -1;
                  isStart = false;
                  traverse($content);
                }
              }
              selectedPos = -1;
              while (selectedPos === -1) {
                innerSearch($content);
                startPos = selectedPos + search.length;
                if (selectedPos === -1) {
                  if (nextSiblingStack.length > 0) {
                    $content = nextSiblingStack.pop();
                    startPos = 0;
                  } else {
                    return;
                  }
                  traverse($content);
                }
                if ((startPos < currentCursorPos) && ($content === currentRange.startContainer)) {
                  selectedPos = -1;
                  nextCounter++;
                }
              }
              if (selectedPos !== -1) {
                offsetTopPrev = currentRange.commonAncestorContainer.offsetTop;
                markFound($content, 1, search, selectedPos);
                nextCounter++;
                startPos = selectedPos + search.length;
                selectedPos = -1;
              }
            });

            $dialog.find('BUTTON.replace-button').on('click', function () {
              $dialog.find('.next-button').attr('disabled', true);
              $dialog.find('.prev-button').attr('disabled', true);
              search = $dialog.find('INPUT[name=find]').val();
              replace = $dialog.find('INPUT[name=replace]').val();
              var newValue;

              $content = jquery('#contenteditor')[0].childNodes[0];
              while (1) {
                traverse($content);

                var range = new GENTICS.Utils.RangeObject({
                  startContainer : $content,
                  startOffset : 0,
                  endContainer : $content,
                  endOffset : $content.length,
                });
                  
                var prevValue = range.startContainer;
                selectedPos = 0;
                startPos = 0;
                while (selectedPos !== -1) {
                  innerSearch(prevValue);
                  startPos = selectedPos + search.length;
                  if (selectedPos !== -1) {
                    newValue = prevValue;
                    prevValue.textContent = prevValue.textContent.substring(0, selectedPos) +  replace + prevValue.textContent.substring(startPos);
                    markFound($content, 1, replace, selectedPos);
                  }
                }

                if (nextSiblingStack.length > 0) {
                  $content = nextSiblingStack.pop();
                } else {
                  $dialog.find('.replace-button').attr('disabled', true);
                  closeSearchDialog();
                  return;
                }
              }
            });

            UI.adopt('findandreplace', null, { // search & replace
                click: function () {
                    $dialog.modal(
                        {'backdrop': 'static',
                         'show': true,
                       });
                  }
              });
          }
      });
  });