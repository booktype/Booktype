define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'booktype', 'underscore', 'PubSub', 'ui/scopes'],
  function (Aloha, Plugin, jQuery,  jQuery19, UI, booktype, _, PubSub, Scopes) {
    'use strict';

    var $a = null,
      range = null,
      selectedLinkDomObj = null;

    var getContainerAnchor = function (a) {
      var el = a;

      while (el) {
        if (el.nodeName.toLowerCase() === 'a') {
          return el;
        }

        el = el.parentNode;
      }

      return false;
    };

    var destroyPopup = function () {
      if (selectedLinkDomObj) {
        jQuery19(selectedLinkDomObj).popover('destroy');
        selectedLinkDomObj = null;
      }
    };

    var selectionChangeHandler = function (that, rangeObject) {
      var foundMarkup,
        enteredLinkScope = false;

      // Check if we need to ignore this selection changed event for
      // now and check whether the selection was placed within a
      // editable area.
      if (!that.ignoreNextSelectionChangedEvent &&
        Aloha.Selection.isSelectionEditable() &&
        Aloha.activeEditable != null) {

        foundMarkup = that.findLinkMarkup(rangeObject);

        if (foundMarkup) {
          that.toggleLinkScope(true);

          Aloha.trigger('aloha-link-selected');
          enteredLinkScope = true;

          // PubSub.pub('aloha.link.selected', {
          //   input: that.hrefField.getInputElem(),
          //   href: that.hrefField.getValue(),
          //   element: that.hrefField.getTargetObject()
          // });
        } else {
          that.toggleLinkScope(false);
          Aloha.trigger('aloha-link-unselected');
        }
      } else {
        that.toggleLinkScope(false);
      }

      that.ignoreNextSelectionChangedEvent = false;
      return enteredLinkScope;
    };

    return Plugin.create('linkBooktype', {
      init: function () {
        var plugin = this;

        var insideLinkScope = false;

        PubSub.sub('aloha.selection.context-change', function (message) {
          if (!Aloha.activeEditable) {
            return;
          }
          var enteredLinkScope = false;
          enteredLinkScope = selectionChangeHandler(plugin, message.range);
          insideLinkScope = enteredLinkScope;
        });

        PubSub.sub('aloha.editable.deactivated', function (message) {
          if (insideLinkScope) {
            insideLinkScope = false;
          }
        });

        Aloha.bind('aloha-link-selected', function (event) {
          var range = event.target.Selection.rangeObject,
            limit = Aloha.activeEditable.obj,
            $lnk = getContainerAnchor(range.startContainer),
            linkContent = '';

          // check if link is not a comment bubble
          if (!$lnk || ($lnk && jQuery19($lnk).hasClass('comment-link')))
            return;

          if ($lnk === selectedLinkDomObj)
            return;
          else
            destroyPopup();

          var url = jQuery19($lnk).attr('href') || '';

          if (url.indexOf('../') === 0) {
            linkContent = url;
          } else {
            linkContent = [
              '<div style="white-space: pre-wrap; word-wrap: break-word;">',
              '<a href="#" rel="popover" style="cursor: pointer" onclick="window.open(\'',
              url, '\', \'_blank\')">', url, '</a></div>'
            ].join('');
          }

          if (!selectedLinkDomObj) {
            selectedLinkDomObj = $lnk;

            jQuery19(selectedLinkDomObj).popover({
              html: true,
              placement: 'bottom',
              trigger: 'manual',
              content: linkContent
            });
            jQuery19(selectedLinkDomObj).popover('show');
          }
        });

        Aloha.bind('aloha-link-unselected', function (event) {
          destroyPopup();
        });

        Aloha.bind('aloha-editable-deactivated', function (event) {
          destroyPopup();
        });

        // link to chapters
        jQuery19('.linktochapter-header i').click(function () {
          jQuery19(this).closest('.linktochapter').toggleClass('open');
        });

        jQuery19('#newLink').on('show.bs.modal', function () {
          var $dialog = jQuery19('#newLink');

          jQuery19('.linktochapter-content UL', $dialog).empty();

          _.each(booktype.editor.data.chapters.chapters, function (item) {
            var $link = jQuery19('<li><a href="#"><i class="fa fa-check-circle"></i>' + item.get('title') + '</a></li>');

            jQuery19('a', $link).on('click', function () {
              jQuery19('#newLink INPUT[name=url]').val('../' + item.get('urlTitle') + '/');

              return false;
            });

            jQuery19('.linktochapter-content UL', $dialog).append($link);
          });

          jQuery19('.linktochapter .linktochapter-content li a').click(function () {
            jQuery19(this).closest('ul').find('li a').removeClass('selected');
            jQuery19(this).addClass('selected');
          });
        });

        jQuery19('#newLink').on('hide.bs.modal', function () {
          jQuery19('.linktochapter').removeClass('open');
          jQuery19('.linktochapter .linktochapter-content ul').find('li a').removeClass('selected');
        });

        jQuery19('#newLink BUTTON.operation-unlink').on('click', function (event) {
          if ($a !== null) {
            var a = $a.get(0);

            // publish message indicating that a link will be removed
            PubSub.pub('aloha.link.removed', {'link': $a});

            var newRange = new GENTICS.Utils.RangeObject();
            newRange.startContainer = newRange.endContainer = a.parentNode;
            newRange.startOffset = GENTICS.Utils.Dom.getIndexInParent(a);
            newRange.endOffset = newRange.startOffset + 1;
            newRange.select();

            GENTICS.Utils.Dom.removeFromDOM(a, newRange, true);

            newRange.startContainer = newRange.endContainer;
            newRange.startOffset = newRange.endOffset;
            newRange.select();

            jQuery19('#newLink').modal('hide');

            // publish message notification that link was broke
            PubSub.pub('toolbar.action.triggered', {'event': event});
          }
        });

        jQuery19('#newLink BUTTON.operation-insert').on('click', function (event) {
          var title = jQuery19('#newLink INPUT[name=title]').val(),
            url = jQuery19('#newLink INPUT[name=url]').val(),
            rangeText = range.getText(),
            prevLink = null;

          if (jQuery19.trim(title).length > 0 && jQuery19.trim(url).length > 0) {

            if ($a == null) {
              $a = jQuery('<a/>').prop('href', url).text(title);
              var editable = Aloha.getEditableById('contenteditor');
              GENTICS.Utils.Dom.removeRange(range);
              GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
            } else {
              prevLink = $a.clone(); // this is just for tracking plugin
              $a.prop('href', url).text(title);
            }

            jQuery19('#newLink').modal('hide');
            range.select();

            // publish message indicating new was inserted in order to track it
            PubSub.pub('aloha.link.inserted', {
              'link': $a,
              'prevLink': prevLink,
              'rangeText': rangeText
            });

            // publish message notification that link was created
            PubSub.pub('toolbar.action.triggered', {'event': event});
          }
        });

        UI.adopt('insertLink', null, {
          click: function () {
            range = Aloha.Selection.getRangeObject();
            var a = getContainerAnchor(range.startContainer);

            if (a) {
              $a = jQuery(a);
              range.startContainer = range.endContainer = a;
              range.startOffset = 0;
              range.endOffset = a.childNodes.length;
              range.select();

              jQuery19('#newLink INPUT[name=title]').val(jQuery(a).text());
              jQuery19('#newLink INPUT[name=url]').val(a.getAttribute('href', 2));
              jQuery19('#newLink .operation-unlink').prop('disabled', false);
            } else {
              if (_.isEmpty(range)) {
                return;
              }

              $a = null;

              GENTICS.Utils.Dom.extendToWord(range);

              jQuery19('#newLink INPUT[name=title]').val(range.getText() || '');
              jQuery19('#newLink INPUT[name=url]').val('');

              jQuery19('#newLink .operation-unlink').prop('disabled', true);
            }

            jQuery19('#newLink').modal('show');
          }
        });
      },

      toggleLinkScope: function (show) {
        // Check before doing anything as a performance improvement.
        // The _isScopeActive_editableId check ensures that when
        // changing from a normal link in an editable to an editable
        // that is a link itself, the removeLinkButton will be
        // hidden.
        if (this._isScopeActive === show && Aloha.activeEditable && this._isScopeActive_editableId === Aloha.activeEditable.getId()) {
          return;
        }
        this._isScopeActive = show;
        this._isScopeActive_editableId = Aloha.activeEditable && Aloha.activeEditable.getId();

        if (show) {
          Scopes.enterScope(this.name, 'link');
        } else {
          Scopes.leaveScope(this.name, 'link', true);
        }
      },

      findLinkMarkup: function (range) {
        if (typeof range == 'undefined') {
          range = Aloha.Selection.getRangeObject();
        }
        if (Aloha.activeEditable) {
          // If the anchor element itself is the editable, we
          // still want to show the link tab.
          var limit = Aloha.activeEditable.obj;
          if (limit[0] && limit[0].nodeName === 'A') {
            limit = limit.parent();
          }
          return range.findMarkup(function () {
            return this.nodeName === 'A';
          }, limit);
        } else {
          return null;
        }
      },

      makeClean: function (obj) {
        jQuery('div.popover.fade.bottom').remove();
      }
    });
  }
);
