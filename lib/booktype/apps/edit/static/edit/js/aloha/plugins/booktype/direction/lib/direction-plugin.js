define(
  ['aloha', 'aloha/plugin', 'aloha/ephemera', 'PubSub', 'jquery', 'jquery19', 'ui/ui', 'ui/button', 'underscore'],
  function (Aloha, Plugin, Ephemera, PubSub, jQuery, jQuery19, UI, Button, _) {
    'use strict';

    return Plugin.create('direction', {
      defaultSettings: {
        'directionTags': ["p", "td", "ul", "ol"]
      },

      init: function () {
        var lastSelectedBdoItem = null;
        var $this = this;
        this._buttonLTR = null;
        this._buttonRTL = null;
        this._menuInsertLTR = null;
        this._menuInsertRTL = null;
        this._menuApplyLTR = null;
        this._menuApplyRTL = null;

        // merge settings
        this.settings = jQuery.extend(true, $this.defaultSettings, $this.settings);

        // define buttons
        UI.adopt('direction-ltr', null, {
          click: function () {
            $this._changeDirection('ltr');
            $this._showDirection('ltr');
            return true;
          }
        });

        UI.adopt('direction-rtl', null, {
          click: function () {
            $this._changeDirection('rtl');
            $this._showDirection('rtl');
            return true;
          }
        });

        // define menu links
        UI.adopt('apply-direction-ltr', null, {
          click: function () {
            $this._changeDirection('ltr');
            $this._showDirection('ltr');
            return true;
          }
        });

        UI.adopt('apply-direction-rtl', null, {
          click: function () {
            $this._changeDirection('rtl');
            $this._showDirection('rtl');
            return true;
          }
        });

        UI.adopt('rtl-text-insert', null, {
          click: function () {
            $this._insertBdo('rtl');
            return true;
          }
        });

        UI.adopt('ltr-text-insert', null, {
          click: function () {
            $this._insertBdo('ltr');
            return true;
          }
        });

        // init buttons
        Aloha.bind('aloha-editable-created', function ($event, editable) {
          $this._buttonLTR = jQuery('.contentHeader .btn-toolbar .direction-ltr');
          $this._buttonRTL = jQuery('.contentHeader .btn-toolbar .direction-rtl');
          $this._menuInsertLTR = jQuery('.contentHeader .btn-toolbar .ltr-text-insert');
          $this._menuInsertRTL = jQuery('.contentHeader .btn-toolbar .rtl-text-insert');
          $this._menuApplyLTR = jQuery('.contentHeader .btn-toolbar .apply-direction-ltr');
          $this._menuApplyRTL = jQuery('.contentHeader .btn-toolbar .apply-direction-rtl');
        });

        Aloha.bind('aloha-selection-changed', function (event, rangeObject) {
          if (Aloha.activeEditable) {

            // highlight direction
            rangeObject.findMarkup(function () {
              var tagName = this.tagName.toLowerCase();
              if (this.getAttribute('dir') && (_.contains($this.settings.directionTags, tagName) || tagName === 'bdo')) {
                $this._showDirection(this.getAttribute('dir'));

                // disable ability change direction if cursor inside bdo tag
                if (tagName === 'bdo') {
                  if (this.getAttribute('dir') && this.getAttribute('dir') === 'ltr') {
                    $this._buttonRTL.attr("disabled", true);
                    $this._menuApplyRTL.hide();
                  } else if (this.getAttribute('dir') && this.getAttribute('dir') === 'rtl') {
                    $this._buttonLTR.attr("disabled", true);
                    $this._menuApplyLTR.hide();
                  }
                }

                return true;
              } else if (this.id === 'contenteditor') {
                $this._showDirection(this.getAttribute('dir'));
                return true;
              }
            });

            // catch bdo focus loosing
            rangeObject.findMarkup(function () {

              if (lastSelectedBdoItem && this.tagName.toLowerCase() !== 'bdo') {
                // remove tag if it almost empty
                if ($this._shouldDeleteBdo(lastSelectedBdoItem)) {
                  jQuery(lastSelectedBdoItem).remove();
                } else if (lastSelectedBdoItem.innerHTML !== '&nbsp;&nbsp;') {
                  // remove border
                  jQuery(lastSelectedBdoItem).removeClass('initial');
                }
                return true;

              } else if (this.tagName.toLowerCase() === 'bdo') {

                if (!lastSelectedBdoItem) {
                  // save last selected bdo
                  lastSelectedBdoItem = this;
                } else if (lastSelectedBdoItem !== this) {
                  // remove tag if it almost empty
                  if ($this._shouldDeleteBdo(lastSelectedBdoItem)) {
                    jQuery(lastSelectedBdoItem).remove();
                  } else if (lastSelectedBdoItem.innerHTML !== '&nbsp;&nbsp;') {
                    // remove border
                    jQuery(lastSelectedBdoItem).removeClass('initial');
                  }
                  lastSelectedBdoItem = this;
                }
                return true;
              }
            });
          }
        });
      },

      makeClean: function (obj) {
        var $this = this;
        // remove all almost empty tags
        jQuery(obj).find('bdo').each(function () {
          if ($this._shouldDeleteBdo(this)) {
            jQuery(this).remove();
          }
        });
      },

      _showDirection: function (direction) {
        if (!direction) {
          direction = window.booktype.bookDir;
        }

        if (direction === 'ltr') {
          this._buttonLTR.addClass('active');
          this._buttonLTR.attr("disabled", true);
          this._buttonRTL.removeClass('active');
          this._buttonRTL.attr("disabled", false);
          this._menuInsertLTR.hide();
          this._menuInsertRTL.show();
          this._menuApplyLTR.hide();
          this._menuApplyRTL.show();
        } else {
          this._buttonLTR.removeClass('active');
          this._buttonLTR.attr("disabled", false);
          this._buttonRTL.addClass('active');
          this._buttonRTL.attr("disabled", true);
          this._menuInsertLTR.show();
          this._menuInsertRTL.hide();
          this._menuApplyLTR.show();
          this._menuApplyRTL.hide();
        }
      },

      _changeDirection: function (direction) {
        var $this = this;
        var rangeObject = Aloha.Selection.getRangeObject();
        rangeObject.findMarkup(function () {
          if (_.contains($this.settings.directionTags, this.tagName.toLowerCase())) {
            this.setAttribute('dir', direction);
            return true
          }
        });
      },

      _insertBdo: function (direction) {
        var rangeObject = Aloha.Selection.getRangeObject();

        var $bdo = jQuery('<bdo>').attr('dir', direction);
        $bdo.html('&nbsp;&nbsp;');
        $bdo.addClass('initial');

        GENTICS.Utils.Dom.insertIntoDOM($bdo, rangeObject, Aloha.activeEditable.obj);
      },

      _shouldDeleteBdo: function (item) {
        return (item.innerHTML !== '&nbsp;&nbsp;' && item.textContent.length < 3 && item.textContent.trim() === '');
      }

    });
  }
);
