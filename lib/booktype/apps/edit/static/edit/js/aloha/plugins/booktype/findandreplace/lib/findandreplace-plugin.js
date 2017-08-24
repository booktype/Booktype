define(['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui', 'underscore', 'PubSub', 'booktype', 'icejs/icejs-plugin'],
function (Aloha, Plugin, jquery, jquery19, UI, _, PubSub, booktype, icejsPlugin) {
    'use strict';

    var GENTICS = window.GENTICS;
    var $dialog;

    var cursorPosition = -1;
    var numberOfSearch = -1;

    var doSearch = function (what, caseMatch) {
      var escapeRegExp = function (string) {
        return string.replace(/([.*+?^${}()|\[\]\/\\])/g, "\\$1");
      };

      findAndReplaceDOMText(document.getElementById('contenteditor'), {
        find: new RegExp(escapeRegExp(what), "g"+(caseMatch ? "" : "i")),
        replace: function (portion, match) {
          var node = document.createElement('span');
          node.className = 'aloha-search-marker';
          node.style.backgroundColor = 'yellow';
          var txt = document.createTextNode(portion.text);
          node.appendChild(txt);
          if (portion.index !== 0) {
            node.className += ' aloha-secondary-match';
          }
          return node;
        }
      });
    };

    var doReplace = function (replace, selection) {
      var $content = jquery("#contenteditor");
      selection = selection || $content.find('span.aloha-search-marker');
      selection.filter('.aloha-secondary-match').remove();
      selection.parent().next('.aloha-secondary-match').remove();

      selection.each(function () {
        var $node = jquery(this);

        if (!_.isUndefined(booktype.tracker) && booktype.tracker.isTracking) {
          return icejsPlugin.trackAndReplace($node, replace);
        } else {
          $node.replaceWith(replace)
        }
      });
    };

    var moveToMarker = function (num) {
      var $markers = jquery("#contenteditor").find('span.aloha-search-marker').not('.aloha-secondary-match');
      $markers.removeClass('current');
      var $e = $markers.eq(num);
      $e.addClass('current');

      var range = new GENTICS.Utils.RangeObject({
        startContainer: $e.get(0),
        endContainer: $e.get(0),
        startOffset : 0,
        endOffset : 1,
      });

      range.select();
      Aloha.Selection.updateSelection();

      return range;
    };

    var scrollToElement = function (elem) {
      if (!elem) return;
      var _top = jquery(elem).offset().top - jquery("#contenteditor").offset().top;
      jquery(window).scrollTop(_top-100);
    };

    var checkButtons = function () {
      $dialog.find('.prev-button').attr('disabled', cursorPosition === 0?true:false);
      $dialog.find('.next-button').attr('disabled', cursorPosition === (numberOfSearch-1)?true:false);
    };

    var hideResults = function () {
      var $content = jquery("#contenteditor");

      var range = new GENTICS.Utils.RangeObject({
        startContainer: $content.find('h1').get(0),
        endContainer: $content.find('h1').get(0),
        startOffset : 0,
        endOffset : 1,
      });

      range.select();
      range.update();
      Aloha.Selection.updateSelection();

      $content.find('span.aloha-search-marker').each(function () {
        var $node = jquery(this);
        $node.replaceWith($node.text());
      });
    };

    var init = function () {
      cursorPosition = -1;
      numberOfSearch = -1;
    };

    return Plugin.create('findandreplace', {
      defaults: {
      },

      makeClean: function(obj){
          jquery(obj).find('.aloha-search-marker, .aloha-secondary-match').each(function () {
            var $elem = jquery(this);
            $elem.replaceWith($elem.text());
          });
      },

      init: function () {
        $dialog = jquery19('#find-replace');

        jquery19($dialog).draggable();

        Aloha.bind('aloha-editable-created', function (event, $editable) {
          if ($editable.obj && $editable.obj.attr('id') === 'contenteditor') {
            init();

            $dialog.find('INPUT[name=find]').val('');
            $dialog.find('INPUT[name=replace]').val('');
          }
        });

        $dialog.on('show.bs.modal', function () {
          jquery19('body').addClass('aloha-search-plugin-loaded');
        });

        $dialog.on('shown.bs.modal', function () {
          init();

          $dialog.removeClass('fade');

          $dialog.find('INPUT[name=find]').val('');
          $dialog.find('INPUT[name=replace]').val('');
          $dialog.find('.msg-report').addClass('hide');
          $dialog.find('INPUT[name=find]').focus().select();

          if($dialog.find('INPUT[name=find]').val() === '') {
            $dialog.find('.next-button').attr('disabled', true);
          }

          $dialog.find('.prev-button').attr('disabled', true);
          $dialog.find('.replace-all-button').attr('disabled', true);
          $dialog.find('.replace-button').attr('disabled', true);

          $dialog.find('.next-button').empty().append(booktype._('find_button'));
        });

        $dialog.on('hide.bs.modal', function () {
          jquery19('body').removeClass('aloha-search-plugin-loaded');
          hideResults();
        });

        $dialog.on('hidden.bs.modal', function () {
          $dialog.addClass('fade');
        });

        var restartSearch = function () {
          if (numberOfSearch > 0) {
            hideResults();
            $dialog.find('.next-button').empty().append(booktype._('find_button'));
          }

          init();

          if ($dialog.find('INPUT[name=find]').val().length === 0) {
            $dialog.find('.next-button').attr('disabled', true);
          } else {
            $dialog.find('.next-button').attr('disabled', false);
          }

          $dialog.find('.prev-button').attr('disabled', true);
          $dialog.find('INPUT[name=find]').focus();
        };

        $dialog.find('INPUT[name=find]').on('keyup',restartSearch);
        $dialog.find('INPUT[name=match-case]').on('change',restartSearch);

        $dialog.find('INPUT[name=replace]').focus(function () {
          $dialog.find('.replace-all-button').attr('disabled', false);
          $dialog.find('.replace-button').attr('disabled', false);
        });

        $dialog.find('BUTTON.next-button').on('click', function () {
          var caseMatch = $dialog.find('INPUT[name=match-case]').is(':checked');
          var $content = jquery("#contenteditor");
          var search = $dialog.find('INPUT[name=find]').val();
          if(!caseMatch){
            search = search.toLowerCase();
          }

          if (cursorPosition == -1) {

            doSearch(search, caseMatch);

            numberOfSearch = jquery("#contenteditor").find('span.aloha-search-marker').not('.aloha-secondary-match').length;
            cursorPosition = 0;

            if (numberOfSearch > 0)
              $dialog.find('.next-button').empty().append(booktype._('find_next_button'));
          } else {
            if (cursorPosition < numberOfSearch) {
                cursorPosition += 1;
            }
          }

          checkButtons();

          if (numberOfSearch > 0) {
            var range = moveToMarker(cursorPosition);
            scrollToElement(range.startContainer);
          }
        });

        $dialog.find('BUTTON.prev-button').on('click', function () {
          var $content = jquery("#contenteditor");

          if (cursorPosition > 0) {
            cursorPosition -= 1;
          }

          checkButtons();

          if (numberOfSearch > 0) {
            var range = moveToMarker(cursorPosition);
            scrollToElement(range.startContainer);
          }
        });

        $dialog.find('BUTTON.replace-all-button, BUTTON.replace-button').on('click', function (event) {
          var caseMatch = $dialog.find('INPUT[name=match-case]').is(':checked');
          var $content = jquery("#contenteditor");
          var replace = $dialog.find('INPUT[name=replace]').val();

          if (numberOfSearch == -1) {
            var search = $dialog.find('INPUT[name=find]').val();
            if (!caseMatch) {
              search = search.toLowerCase();
            }
            doSearch(search, caseMatch);
          }

          if ($(this).is('.replace-all-button')) {
            doReplace(replace);
            $dialog.modal('hide');
          } else {
            doReplace(replace, $content.find('span.aloha-search-marker.current'));
            cursorPosition -= 1;
            $dialog.find('BUTTON.next-button').trigger('click');
          }

          // publish message notification that replace button was clicked
          PubSub.pub('toolbar.action.triggered', {'event': event});
        });

        $dialog.find('BUTTON.cancel-button').on('click', function () {
            $dialog.modal('hide');
        });

        UI.adopt('findandreplace', null, { // search & replace
            click: function () {
              $dialog.modal({'backdrop': 'static', 'show': true});
            }
          });
      }
    });
  });
