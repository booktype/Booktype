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

    var closeSearchDialog = function () {
      var $dialog =   jquery19('#find-replace');
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
      var currentClientHeight = range.commonAncestorContainer.clientHeight;

      if (offsetTopPrev !== 0) {
        var position =  currentOffsetTop - offsetTopPrev;

        if (((offsetTopPrev !== currentOffsetTop) && (currentClientHeight !== 0)) || (currentWindowHeight >= position)) {
          if (direction === 1) {
            window.scrollBy(0, position);
          } else {
            if (position < 0) {
              window.scrollBy(0, position);
            }
          }
        }
      }
      offsetTopPrev = range.commonAncestorContainer.offsetTop;
    };

    var markFound = function ($content, direction) {
      var $dialog =   jquery19('#find-replace');
      var search = $dialog.find('INPUT[name=find]').val();

      var range = new GENTICS.Utils.RangeObject({
        startContainer : $content,
        startOffset : selectedPos,
        endContainer : $content,
        endOffset : selectedPos + search.length,
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
      var $dialog =   jquery19('#find-replace');
      var search = $dialog.find('INPUT[name=find]').val();
      nextCounter = 0;
      startPos = 0;
      $content = jquery('#contenteditor')[0].childNodes[0];
      if (currentRange.markupEffectiveAtStart.length === 0) { // at the title - no markup so far
        startPos = currentRange.endOffset;
        return;
      }
      var isSelected = -1;
      while (isSelected === -1) {
        isSelected = currentRange.markupEffectiveAtStart.indexOf($content);
        prevContent = $content;
        traverse($content);
        var rangeChildren = currentRange.commonAncestorContainer.childNodes;
        if (rangeChildren[0].nodeName === '#text') {
          if (rangeChildren[0] === $content) {
            isSelected = 0;
          }
        }
        selectedPos = 0;
        while (selectedPos !== -1) {
          innerSearch($content);
          if (selectedPos !== -1) {
            nextCounter ++;
          }
          startPos = selectedPos + search.length;
        }
        if (nextSiblingStack.length > 0) {
          $content = nextSiblingStack.pop();
        } else {
          return;
        }
      }
      $content = prevContent;
    };

    var countOccurances = function (search) {
      var innerText = jquery(jquery('#contenteditor')[0]).text().toLowerCase();
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
      var $dialog =   jquery19('#find-replace');
      var search = $dialog.find('INPUT[name=find]').val();
      selectedPos = jquery(textToSearch).text().toLowerCase().indexOf(search.toLowerCase(), startPos);
    };

    var initData = function () {
      selectedPos = -1;
      startPos = 0;
      nextCounter = 0;
      nextSiblingStack = [];
      offsetTopPrev = 0;
    };

    return plugin.create('findandreplace', {
        defaults: {
        },
        init: function () {
            var $dialog = jquery19('#find-replace');
            var search = $dialog.find('INPUT[name=find]').val();
            var replace = $dialog.find('INPUT[name=replace]').val();
            var newSearch = true;


            Aloha.bind('aloha-ready', function () {
              initData();
              isStart = true;
              jquery(window).scrollTop(0);
            });

            Aloha.bind('aloha-editable-activated', function () {
              jquery('#contenteditor').on('click', function () { // clicked - might as well be editing???
                isStart = false;
              });
            });

            Aloha.bind('aloha-editable-destroyed', function () {
              jquery(window).scrollTop(0);
              initData();
              isStart = true;
              $dialog = jquery19('#find-replace');
              $dialog.find('INPUT[name=find]').val('');
              $dialog.find('INPUT[name=replace]').val('');
              $dialog.find('.next-button').attr('disabled', true);
              $dialog.find('.prev-button').attr('disabled', true);
              $dialog.find('.replace-button').attr('disabled', true);
            });

            $dialog.find('.next-button').attr('disabled', true);
            $dialog.find('.prev-button').attr('disabled', true);
            $dialog.find('.replace-button').attr('disabled', true);

            $dialog.find('INPUT[name=find]').focus(function () {
              $dialog = jquery19('#find-replace');
              $dialog.find('.next-button').attr('disabled', false);
            });

            $dialog.find('INPUT[name=replace]').focus(function () {
              $dialog = jquery19('#find-replace');
              $dialog.find('.replace-button').attr('disabled', false);
            });

            if (replace.length === 0) {
              $dialog.find('.replace-button').attr('disabled', true);
            }

            $dialog.find('BUTTON.prev-button').on('click', function () {
              var $dialog =   jquery19('#find-replace');
              var search = $dialog.find('INPUT[name=find]').val();
              var numberOfOccurances = countOccurances(search);
              if (numberOfOccurances === 1) {
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
                markFound($content, -1);
              }
              startPos = selectedPos + search.length;
              selectedPos = -1;
            });

            $dialog.on('hide.bs.modal', function () {
              $dialog.find('INPUT[name=replace]').val('');
            });

            $dialog.find('INPUT[name=find]').on('keyup', function () {
              $dialog.find('.prev-button').attr('disabled', true);
              selectedPos = -1;
              newSearch = true;
            });
                 
            $dialog.find('BUTTON.next-button').on('click', function () {
              var currentRange;
              if ((newSearch) && (!isStart)) {
                currentRange = Aloha.Selection.getRangeObject();
                traverseToCurrentRange(currentRange);
              }
              newSearch = false;

              $dialog =   jquery19('#find-replace');
              search = $dialog.find('INPUT[name=find]').val();
              var numberOfOccurances = countOccurances(search);
              if (numberOfOccurances === nextCounter) { // already at the end
                return;
              }

              $dialog.find('.replace-button').attr('disabled', true);
              if (numberOfOccurances > 1) {
                $dialog.find('.prev-button').attr('disabled', false);
              }

              currentRange = Aloha.Selection.getRangeObject();

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

              while (selectedPos === -1) {
                innerSearch($content);
                if (selectedPos === -1) {
                  if (nextSiblingStack.length > 0) {
                    $content = nextSiblingStack.pop();
                    startPos = 0;
                  } else {
                    return;
                  }
                  traverse($content);
                }
              }

              if (selectedPos !== -1) {
                offsetTopPrev = currentRange.commonAncestorContainer.offsetTop;
                markFound($content, 1);
                nextCounter++;
                startPos = selectedPos + search.length;
                selectedPos = -1;
              }
            });

            $dialog.find('BUTTON.replace-button').on('click', function () {
              var $dialog =   jquery19('#find-replace');
              $dialog.find('.next-button').attr('disabled', true);
              $dialog.find('.prev-button').attr('disabled', true);
              var search = $dialog.find('INPUT[name=find]').val();
              var replace = $dialog.find('INPUT[name=replace]').val();
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
                range.select();
                  
                var prevValue = range.startContainer;
                selectedPos = 0;
                startPos = 0;
                while (selectedPos !== -1) {
                  innerSearch(prevValue);
                  startPos = selectedPos + search.length;
                  if (selectedPos !== -1) {
                    newValue = prevValue;
                    prevValue.textContent = prevValue.textContent.substring(0, selectedPos) +  replace + prevValue.textContent.substring(startPos);
                  }
                }

                if (nextSiblingStack.length > 0) {
                  $content = nextSiblingStack.pop();
                } else {
                  closeSearchDialog();
                  initData();
                  isStart = true;
                  jquery(window).scrollTop(0);
                  return;
                }

                range.startOffset = 0;
                range.endOffset = 0;
                range.select();
                Aloha.Selection.updateSelection();
              }
            });

            UI.adopt('findandreplace', null, { // search & replace
                click: function () {

                    $dialog.find('.modal-dialog .modal-content .modal-body');
                    jquery19($dialog).draggable();
                    $dialog.find('.msg-report').addClass('hide');
                    $dialog.modal(
                        {'backdrop': 'static',
                         'show': true,
                       });
                  }
              });
          }
      });
  });