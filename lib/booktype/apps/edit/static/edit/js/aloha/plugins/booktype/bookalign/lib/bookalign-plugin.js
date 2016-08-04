/* align-plugin.js is part of Aloha Editor project http://aloha-editor.org
 *
 * Aloha Editor is a WYSIWYG HTML5 inline editing library and editor.
 * Copyright (c) 2010-2012 Gentics Software GmbH, Vienna, Austria.
 * Contributors http://aloha-editor.org/contribution.php
 *
 * Aloha Editor is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or any later version.
 *
 * Aloha Editor is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * As an additional permission to the GNU GPL version 2, you may distribute
 * non-source (e.g., minimized or compacted) forms of the Aloha-Editor
 * source code without the copy of the GNU GPL normally required,
 * provided you include this license notice and a URL through which
 * recipients can access the Corresponding Source.
 */

define(
  ['aloha', 'aloha/plugin', 'ui/ui', 'ui/toggleButton', 'i18n!align/nls/i18n', 'i18n!aloha/nls/i18n', 'jquery', 'PubSub'], function (Aloha, Plugin, Ui, ToggleButton, i18n, i18nCore, jQuery, PubSub) {
    'use strict';

    var GENTICS = window.GENTICS;

    /**
     * register the plugin with unique name
     */
    return Plugin.create('bookalign', {
      _constructor: function () {
        this._super('bookalign');
      },
      /**
       * Configuration (available align options)
       */
      config: {
        alignment: ['right', 'left', 'center', 'justify']
      },

      /**
       * Initialize the plugin and set initialize flag on true
       */
      init: function () {
        this.createButtons();
        var that = this;
        this.imageInFocus = null;

        Aloha.bind('aloha-selection-changed', function (event, rangeObject, originalEvent) {

          // only if editable was created
          if (Aloha.activeEditable) {
            that.imageInFocus = null;

            var rangeParent = rangeObject.getCommonAncestorContainer();
            var $rangeParent = jQuery(rangeParent);
            var $rangeDblParent = $rangeParent.parent();

            // if caption in range, put image in focus
            if ($rangeParent.hasClass('caption_small') && $rangeDblParent.hasClass('caption_wrapper')) {
              that.highlightAlign($rangeDblParent.closest('div.group_img')[0].style.textAlign);
              that.imageInFocus = $rangeDblParent.parent().find('img');
              return;
            }

            if (jQuery('DIV.contentHeader button.unorderedList').hasClass('active') === false) {
              that.toggleButtons('enabled');
            } else {
              that.toggleButtons('disabled');
            }

            if (jQuery('DIV.contentHeader button.orderedList').hasClass('active') === false) {
              that.toggleButtons('enabled');
            } else {
              that.toggleButtons('disabled');
            }

            that.buttonPressed(rangeObject);
          }
        });

        // source imagesimple-plugin
        PubSub.sub('imagesimple.image.selected', function (message) {
          that.imageInFocus = message.image;
          that.highlightAlign(jQuery(message.image).closest('div.group_img')[0].style.textAlign);
        });

        PubSub.sub('bookalign.hook.align', function (message) {
          that.align(message.align);
        });

      },

      toggleButtons: function (toggle_type) {
        jQuery('DIV.contentHeader button.alignLeft').prop(toggle_type, true);
        jQuery('DIV.contentHeader button.alignCenter').prop(toggle_type, true);
        jQuery('DIV.contentHeader button.alignRight').prop(toggle_type, true);
        jQuery('DIV.contentHeader button.alignJustify').prop(toggle_type, true);
      },

      buttonPressed: function (rangeObject) {
        this.horizontalButtonPressed(rangeObject);
      },

      horizontalButtonPressed: function (rangeObject) {
        var that = this;

        //reset current alignment
        this.alignment = '';

        rangeObject.findMarkup(function () {
          // try to find explicitly defined text-align style property
          if (this.style.textAlign !== "") {
            that.alignment = this.style.textAlign;
            return true;
          }

          that.alignment = jQuery(this).css('text-align');
        }, Aloha.activeEditable.obj);

        that.highlightAlign(this.alignment);
      },

      /**
       * applys a configuration specific for an editable
       * buttons not available in this configuration are hidden
       * @param {Object} id of the activated editable
       * @return void
       */
      applyButtonConfig: function (obj) {
        var config;

        if (typeof Aloha.settings.plugins.bookalign === 'undefined') {
          config = this.config;
        } else {
          config = Aloha.settings.plugins.bookalign.config;
        }

        if (config && config.alignment && !this.settings.alignment) {
          config = config;
        } else if (config[0] && config[0].alignment) {
          config = config[0];
        } else if (this.settings.alignment) {
          config.alignment = this.settings.alignment;
        }

        if (typeof config.alignment === 'undefined') {
          config = this.config;
        }

        if (jQuery.inArray('right', config.alignment) != -1) {
          this._alignRightButton.show(true);
        } else {
          this._alignRightButton.show(false);
        }

        if (jQuery.inArray('left', config.alignment) != -1) {
          this._alignLeftButton.show(true);
        } else {
          this._alignLeftButton.show(false);
        }

        if (jQuery.inArray('center', config.alignment) != -1) {
          this._alignCenterButton.show(true);
        } else {
          this._alignCenterButton.show(false);
        }

        if (jQuery.inArray('justify', config.alignment) != -1) {
          this._alignJustifyButton.show(true);
        } else {
          this._alignJustifyButton.show(false);
        }
      },

      createButtons: function () {
        var that = this;

        this._alignLeftButton = Ui.adopt("alignLeft", ToggleButton, {
          tooltip: i18n.t('button.alignleft.tooltip'),
          icon: 'aloha-icon aloha-icon-align aloha-icon-align-left',
          scope: 'Aloha.continuoustext',
          click: function () {
            that.align('left');
          }
        });

        this._alignCenterButton = Ui.adopt("alignCenter", ToggleButton, {
          tooltip: i18n.t('button.aligncenter.tooltip'),
          icon: 'aloha-icon aloha-icon-align aloha-icon-align-center',
          scope: 'Aloha.continuoustext',
          click: function () {
            that.align('center');
          }
        });

        this._alignRightButton = Ui.adopt("alignRight", ToggleButton, {
          tooltip: i18n.t('button.alignright.tooltip'),
          icon: 'aloha-icon aloha-icon-align aloha-icon-align-right',
          scope: 'Aloha.continuoustext',
          click: function () {
            that.align('right');
          }
        });

        this._alignJustifyButton = Ui.adopt("alignJustify", ToggleButton, {
          tooltip: i18n.t('button.alignjustify.tooltip'),
          icon: 'aloha-icon aloha-icon-align aloha-icon-align-justify',
          scope: 'Aloha.continuoustext',
          click: function () {
            that.align('justify');
          }
        });

      },

      /**
       * Higlight toolbar align button
       */
      highlightAlign: function (align) {
        this._alignRightButton.setState(false);
        this._alignLeftButton.setState(false);
        this._alignCenterButton.setState(false);
        this._alignJustifyButton.setState(false);

        // default align
        if (!align) {
          align = 'left'
        }

        PubSub.pub('bookalign.hook.highlight', {'align': align});

        switch (align) {
          case 'right':
            this._alignRightButton.setState(true);
            break;
          case 'center':
            this._alignCenterButton.setState(true);
            break;
          case 'justify':
            this._alignJustifyButton.setState(true);
            break;
          default:
            this._alignLeftButton.setState(true);
            break;
        }
      },

      /**
       * Align the selection or remove it
       */
      align: function (tempAlignment) {
        var that = this;

        this.alignment = tempAlignment;

        var range = Aloha.Selection.getRangeObject();
        var rangeParent = range.getCommonAncestorContainer();

        // check if the image selected now
        if (that.imageInFocus) {
          jQuery(that.imageInFocus).closest('div.group_img').css('text-align', this.alignment);
        } else {
          // check if the selection range is inside a table
          var selectedCells = this.getSelectedCells(range);

          if (selectedCells) {
            that.toggleAlign(selectedCells);
          } else if (!GENTICS.Utils.Dom.isEditingHost(rangeParent)) {

            // if the parent node is not the main editable node and align
            // OR iterates the whole selectionTree and align
            that.toggleAlign(rangeParent);
          } else {
            var alignableElements = [];
            jQuery.each(Aloha.Selection.getRangeObject().getSelectionTree(), function () {
              if (this.selection !== 'none' && this.domobj.nodeType !== 3) {
                alignableElements.push(this.domobj);
              }
            });

            that.toggleAlign(alignableElements);
          }
          // select the (possibly modified) range
          range.select();
        }
        this.highlightAlign(tempAlignment);
      },

      getSelectedCells: function (range) {

        var selectedCell;

        var activeTable = range.findMarkup(function () {
          if (jQuery(this).is('td,th')) {
            selectedCell = this;
          }
          return jQuery(this).is('table.aloha-table');
        }, Aloha.activeEditable.obj);

        var selectedCells = jQuery(activeTable).find('.aloha-cell-selected');

        return (  selectedCells.length ? selectedCells : selectedCell );

      },

      mover: function (root, newAlignment) {
        var currentAlignment = jQuery(root).css('text-align');

        if (currentAlignment === newAlignment) {
          jQuery(root).css('text-align', '');
        } else {
          jQuery(root).css('text-align', newAlignment);
        }
      },

      toggleAlign: function () {
        var highestObject, root, rangeTree;
        var that = this;
        var newAlignment = that.alignment;
        var rangeObject = Aloha.Selection.getRangeObject();
        var common = rangeObject.getCommonAncestorContainer();
        var limit = Aloha.activeEditable.obj;
        var markup = jQuery("<p>");
        var nodeName = markup.get(0).nodeName;
        var selected_element;

        highestObject = GENTICS.Utils.Dom.findHighestElement(common, nodeName, limit);

        if (highestObject !== undefined) {
          root = highestObject ? highestObject : common;
        } else {
          root = common;
        }

        // only in case you have selected text, do styling to heading and align immediately after that - works in FF without that
        if (common.childNodes.length === 0) {
          // reselect - selection is wrong
          root = rangeObject.startContainer.parentNode; // selecting the text inside
          this.mover(root, newAlignment);
        }

        // selection so go through elements and do align
        if (rangeObject.startContainer !== rangeObject.endContainer) {
          rangeTree = rangeObject.getRangeTree(root);

          jQuery.each(rangeTree, function (cnt, el) {
            if (el.type !== "none") {
              selected_element = el.domobj;
              that.mover(selected_element, newAlignment);
            }
          });
        } else {
          common = rangeObject.getCommonAncestorContainer();
          limit = Aloha.activeEditable.obj;
          markup = jQuery("<p>");
          nodeName = markup.get(0).nodeName;
          highestObject = GENTICS.Utils.Dom.findHighestElement(common, nodeName, limit);
          if (highestObject !== undefined) {
            root = highestObject ? highestObject : common;
          } else {
            root = common;
          }
          var elements = ["H1", "H2", "H3", "H4", "H5", "H6", "P", "TD"];
          var new_root = root;

          while (new_root && elements.indexOf(new_root.tagName) === -1) { // styling in the elements - need to find which elements are parents
            new_root = new_root.parentNode;
          }

          this.mover(new_root, newAlignment);
        }
      }
    });
  });