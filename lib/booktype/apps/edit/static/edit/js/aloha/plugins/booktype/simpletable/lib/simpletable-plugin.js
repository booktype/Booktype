define(['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui', 'aloha/ephemera', 'block/block', 'block/blockmanager', 'underscore', 'PubSub','booktype', 'toolbar/toolbar-plugin'],
  function (Aloha, Plugin, jQuery, jQuery19, UI, Ephemera, block, BlockManager, _, PubSub, booktype, toolbar) {
    'use strict';

    var n = 0;

    var SimpleTableBlock = block.AbstractBlock.extend({
      title: 'SimpleTable',
      isDraggable: function () {
        return false;
      },

      init: function ($element, postProcessFn) {
        jQuery($element).find('td, .caption_table').each(function () {
          var $elem = jQuery(this);
          $elem.wrapInner('<div></div>')
          $elem.find('div').contentEditable(true);
        });

        return postProcessFn();
      },

      update: function ($element, postProcessFn) {

        jQuery($element).find('td, .caption_table').each(function () {
          var $elem = jQuery(this);

          if (!jQuery($elem.children().get(0)).hasClass('aloha-editable')) {
            $elem.wrapInner('<div></div>');
            $elem.find('div').contentEditable(true);
          }
        });

        return postProcessFn();
      }
    });

    var updateValue = function () {
      var $dropdown = jQuery19('.contentHeader ul.table-dropdown');
      var cols = jQuery19('.cols-size', $dropdown).data('slider').getValue();
      var rows = jQuery19('.rows-size', $dropdown).data('slider').getValue();

      jQuery19('.rows-value', $dropdown).html(rows);
      jQuery19('.cols-value', $dropdown).html(cols);
    };

    var _initTables = function (editable) {
      // let's see if there are some raw tables in content
      $tables = editable.obj.find('table');

      $tables.each(function (id, table) {
        var table = $(table);
        var tableParent = table.parent();

        // first is to check if table is already initiated
        if (tableParent.is(':not(.group_table)')) {

          if (tableParent.is('#contenteditor')) {
            table.wrap('<div class="group_table"></div>');
          } else if (tableParent.is('div') && table.is(':first-child')) {
            tableParent.addClass('group_table');
          } else {
            // last case, we should just wrap the table
            table.wrap('<div class="group_table"></div>');
          }

          // TODO: check if we should clean out tables when importing content
          // and also if we should remove other tags than p and span tags

          table.find('p, span').replaceWith(
            function() { return $(this).contents();
          });

          // let's also clean out empty tags
          table.find('p, span').each(function() {
            var $this = $(this);
            if ($this.html().replace(/\s|&nbsp;/g, '').length == 0)
                $this.remove();
          });
        }
      });

      var $tables = editable.obj.find('.group_table');
      $tables.addClass('aloha-table').alohaBlock({
        'aloha-block-type': 'SimpleTableBlock'
      });
    };


    var _removeTemp = function () {
      var $ed = Aloha.getEditableById('contenteditor');

      jQuery('.to-insert', $ed.obj).remove();
      jQuery('.to-delete', $ed.obj).each(function () {
        var $td = jQuery(this);

        $td.removeClass('to-delete');
      });

      return;
    };

    return Plugin.create('simpletable', {
      defaultSettings: {
        enabled: true
      },

      init: function () {
        var self = this;

        self.settings = jQuery.extend(true, self.defaultSettings, self.settings);

        if (!self.settings.enabled)
          return;

        Ephemera.attributes('data-aloha-block-type', 'contenteditable');
           
        BlockManager.registerBlockType('SimpleTableBlock', SimpleTableBlock);

        Aloha.bind('aloha-my-undo', function (event, args) {
          _initTables(args.editable);
        });

        PubSub.sub('aloha.editable.created', function (data) {
          var editable = data.editable;

          if (editable.obj && editable.obj.attr('id') === 'contenteditor') {
            _initTables(editable);

            var $dropdown = jQuery19('.contentHeader ul.table-dropdown');

            jQuery19('li.createtable', $dropdown).on('click', function (e) {
              return (e.target.nodeName === 'BUTTON');
            });

            jQuery19('.cols-size', $dropdown).slider().on('slide', function () {
              updateValue();
              return false;
            });

            jQuery19('.rows-size', $dropdown).slider().on('slide', function () {
              updateValue();
              return false;
            });

            jQuery19('.deleterow', $dropdown).hover(function () {
              var range = Aloha.Selection.getRangeObject();
              var $tr = jQuery(range.startContainer).closest('tr');
              $tr.addClass('to-delete');
            }, function () {
              _removeTemp();
            });

            jQuery19('.deletecolumn', $dropdown).hover(function () {
              var $td, $table, tds;

              editable = Aloha.activeEditable;
              var range = Aloha.Selection.getRangeObject();

              $td = jQuery(range.startContainer).closest('td');
              tds = 1 + $td.index();
              $table = $td.closest('table');

              $table.find('tr').each(function () {
                var $tr = jQuery(this);
                var $tmp = $tr.find('td:nth-child(' + tds + ')');
                $tmp.addClass('to-delete');
              });
            }, function () {
              _removeTemp();
              return;
            });

            jQuery19('.insertrowbefore', $dropdown).hover(function () {
              var $tr, tds;
              var _isFirst = false;

              editable = Aloha.activeEditable;
              var range = Aloha.Selection.getRangeObject();

              var $table = jQuery(range.startContainer).closest('table');
              var $tr = jQuery(range.startContainer).closest('tr');

              if ($tr.index() === 0)
                _isFirst = true;

              tds = $tr.find('td').length;

              var $row = '';

              _(tds).times(function () {
                $row += '<td>&nbsp;</td>';
              });

              if (_isFirst) {
                $table.prepend('<tr class="to-insert">' + $row + '</tr>');
              } else {
                $tr.before('<tr class="to-insert">' + $row + '</tr>');
              }
            }, function () {
              _removeTemp();
            });

            jQuery19('.insertrowafter', $dropdown).hover(function () {
              var $tr, tds;

              var range = Aloha.Selection.getRangeObject();
              $tr = jQuery(range.startContainer).closest('tr');

              tds = $tr.find('td').length;

              var $row = '';

              _(tds).times(function () {
                $row += '<td>&nbsp;</td>';
              });

              $tr.after('<tr class="to-insert">' + $row + '</tr>');
            }, function () {
              _removeTemp();
            });

            jQuery19('.insertcolumnafter', $dropdown).hover(function () {
              var $td, $table, tds;

              editable = Aloha.activeEditable;
              var range = Aloha.Selection.getRangeObject();

              $td = jQuery(range.startContainer).closest('td');

              $table = $td.closest('table');
              tds = 1 + $td.index();

              $table.find('tr').each(function () {
                var $t = jQuery(this);
                $t.find('td:nth-child(' + tds + ')').after('<td class="to-insert" style="width: 10px;">&nbsp;</td>');
              });
            }, function () {
              _removeTemp();
            });

            jQuery19('.insertcolumnbefore', $dropdown).hover(function () {
              var $td, $table, tds;
              var range = Aloha.Selection.getRangeObject();

              $td = jQuery(range.startContainer).closest('td');
              $table = $td.closest('table');
              tds = 1 + $td.index();

              $table.find('tr').each(function () {
                var $t = jQuery(this);
                $t.find('td:nth-child(' + tds + ')').before('<td class="to-insert" style="width: 10px;">&nbsp;</td>');
              });
            }, function () {
              _removeTemp();
            });
          }
        });

        PubSub.sub('aloha.selection.context-change', function (m) {
          var $groupTable = jQuery(m.range.startContainer).closest('.group_table');
          var $dropdown = jQuery19('.contentHeader ul.table-dropdown');

          var _buttons = booktype.editor.data.settings.config.edit.toolbar['TABLE'];
          var _menus = booktype.editor.data.settings.config.edit.menu['TABLE'];

          if ($groupTable.length > 0) {
            // let's populate table caption input in case the table has it
            var $captionText = $groupTable.find('.caption_table').text();

            if ($captionText.length > 0)
              $dropdown.find('[name="table-caption"]').val($captionText);

            $dropdown.find('.inserttable').addClass('hidden');
            $dropdown.find('.updatetable').removeClass('hidden');
            $dropdown.find('.deletetable').parent().removeClass('disabled');

            $dropdown.find('.insertrowafter').parent().removeClass('disabled');
            $dropdown.find('.insertrowbefore').parent().removeClass('disabled');
            $dropdown.find('.insertcolumnafter').parent().removeClass('disabled');
            $dropdown.find('.insertcolumnbefore').parent().removeClass('disabled');

            $dropdown.find('.deleterow').parent().removeClass('disabled');
            $dropdown.find('.deletecolumn').parent().removeClass('disabled');

            $dropdown.find('.slider2').addClass('hidden');
            $dropdown.find('.slider2').prev('h4').addClass('hidden');
            $dropdown.find('.slider2').next('.value').addClass('hidden');

            $dropdown.find('.dropdown-header').addClass('hidden');
            $dropdown.find('.dropdown-header-modify').removeClass('hidden');

            toolbar.enableToolbarAll();
            toolbar.enableMenuAll();

            _.each(_buttons, function (btn) {
              toolbar.disableToolbar(btn);
            });

            _.each(_menus, function (btn) {
              toolbar.disableMenu(btn);
            });
          } else {
            $dropdown.find('[name="table-caption"]').val('');

            $dropdown.find('.updatetable').addClass('hidden');
            $dropdown.find('.inserttable').removeClass('hidden');
            $dropdown.find('.deletetable').parent().addClass('disabled');

            $dropdown.find('.insertrowafter').parent().addClass('disabled');
            $dropdown.find('.insertrowbefore').parent().addClass('disabled');
            $dropdown.find('.insertcolumnafter').parent().addClass('disabled');
            $dropdown.find('.insertcolumnbefore').parent().addClass('disabled');

            $dropdown.find('.deleterow').parent().addClass('disabled');
            $dropdown.find('.deletecolumn').parent().addClass('disabled');

            $dropdown.find('.slider2').removeClass('hidden');
            $dropdown.find('.slider2').prev('h4').removeClass('hidden');
            $dropdown.find('.slider2').next('.value').removeClass('hidden');

            $dropdown.find('.dropdown-header').removeClass('hidden');
            $dropdown.find('.dropdown-header-modify').addClass('hidden');
          }
        });

        UI.adopt('inserttable', null, {
          click: function () {
            var editable = Aloha.getEditableById('contenteditor');
            var range = Aloha.Selection.getRangeObject();

            var $dropdown = jQuery19('.contentHeader ul.table-dropdown');
            var $captionField = jQuery19('[name="table-caption"]', $dropdown);
            var cols = jQuery19('.cols-size', $dropdown).data('slider').getValue();
            var rows = jQuery19('.rows-size', $dropdown).data('slider').getValue();
            var caption  = $captionField.val();

            var html = '';

            for (var i = 0; i < rows; i++) {
              html += '<tr>';

              for (var j = 0; j < cols; j++) {
                html += '<td>&nbsp;</td>';
              }

              html += '</tr>';
            }

            // add caption to table if any
            if (caption.length > 0)
              caption = '<p class="caption_table">' + caption + '</p>';


            var $a = jQuery('<div class="aloha-table group_table">' + caption + '<table><tbody>' + html + '</tbody></table></div>');
            $a.alohaBlock({
              'aloha-block-type': 'SimpleTableBlock'
            });

            GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
            $captionField.val('');

            return true;
          }
        });

        UI.adopt('updatetable', null, {
          click: function () {
            var $dropdown = jQuery19('.contentHeader ul.table-dropdown');
            var $captionField = jQuery19('[name="table-caption"]', $dropdown);
            var $captionText = '<div>' + $captionField.val() + '</div>';

            var range = Aloha.Selection.getRangeObject();
            var $groupTable = jQuery(range.startContainer).closest('.group_table');
            var $captionTable = $groupTable.find('.caption_table');

            // if table has caption already, let's just update it
            if ($captionTable.length > 0) {
              $captionTable
                .html($captionText)
                .find('div').aloha();
            } else {
              $captionTable = jQuery(document.createElement('p'));
              $captionTable
                .addClass('caption_table')
                .html($captionText)
                .prependTo($groupTable);

              $captionTable
                .find('div').aloha();
            }

            $captionField.val('');
            return true;
          }
        });

        UI.adopt('deletetable', null, {
          click: function () {
            // TODO
            // Should ask user if this is possible
            var range = Aloha.Selection.getRangeObject();
            var $tr = jQuery(range.startContainer).closest('tr');

            var $block = BlockManager.getBlock($tr.closest('.aloha-block-SimpleTableBlock'));
            $block.unblock();
            $tr.closest('.aloha-block-SimpleTableBlock').remove();

            return true;
          }
        });

        UI.adopt('insertrowbefore', null, {
          click: function () {
            var _isFirst = false;
            var range = Aloha.Selection.getRangeObject();

            var $table = jQuery(range.startContainer).closest('table');
            var $tr = jQuery(range.startContainer).closest('tr');

            if ($tr.index() === 0)
              _isFirst = true;

            var $block = BlockManager.getBlock($tr.closest('.aloha-block-SimpleTableBlock'));
            var tds = $tr.find('td').length;

            var $row = '';

            _(tds).times(function () {
              $row += '<td>&nbsp;</td>';
            });

            if (_isFirst) {
              $table.prepend('<tr>' + $row + '</tr>');
            } else {
              $tr.before('<tr>' + $row + '</tr>');
            }

            if (!_.isUndefined($block) && $block)
              $block.attr('one', n);

            n += 1;
            range.select();

            return true;
          }
        });

        UI.adopt('insertrowafter', null, {
          click: function () {
            var range = Aloha.Selection.getRangeObject();
            var $tr = jQuery(range.startContainer).closest('tr');
            var $block = BlockManager.getBlock($tr.closest('.aloha-block-SimpleTableBlock'));

            var tds = $tr.find('td').length;
            var $row = '';

            _(tds).times(function () {
              $row += '<td>&nbsp;</td>';
            });

            $tr.after('<tr>' + $row + '</tr>');

            if (!_.isUndefined($block) && $block)
              $block.attr('one', n);

            n += 1;
            range.select();

            return true;
          }
        });

        UI.adopt('insertcolumnafter', null, {
          click: function () {
            var $td, $table, tds;
            var range = Aloha.Selection.getRangeObject();

            $td = jQuery(range.startContainer).closest('td');

            $table = $td.closest('table');
            var $block = BlockManager.getBlock($table.closest('.aloha-block-SimpleTableBlock'));

            tds = 1 + $td.index();

            $table.find('tr').each(function () {
              var $t = jQuery(this);
              $t.find('td:nth-child(' + tds + ')').after('<td>&nbsp;</td>');
            });

            if (!_.isUndefined($block) && $block)
              $block.attr('one', n);

            n += 1;
            range.select();

            return true;
          }
        });

        UI.adopt('insertcolumnbefore', null, {
          click: function () {
            var $td, $table, tds;
            var range = Aloha.Selection.getRangeObject();

            $td = jQuery(range.startContainer).closest('td');
            $table = $td.closest('table');

            var $block = BlockManager.getBlock($table.closest('.aloha-block-SimpleTableBlock'));

            tds = 1 + $td.index();

            $table.find('tr').each(function () {
              var $t = jQuery(this);
              $t.find('td:nth-child(' + tds + ')').before('<td>&nbsp;</td>');
            });

            if (!_.isUndefined($block) && $block)
              $block.attr('one', n);

            n += 1;
            range.select();

            return true;
          }
        });

        UI.adopt('deleterow', null, {
          click: function () {
            var range = Aloha.Selection.getRangeObject();
            var $tr = jQuery(range.startContainer).closest('tr');
            $tr.remove();
          }
        });

        UI.adopt('deletecolumn', null, {
          click: function () {
            var $tr, $td, $table, tds;
            var range = Aloha.Selection.getRangeObject();

            $td = jQuery(range.startContainer).closest('td');
            tds = 1 + $td.index();
            $table = $td.closest('table');

            $table.find('tr').each(function () {
              $tr = jQuery(this);
              var $tmp = $tr.find('td:nth-child(' + tds + ')');
              $tmp.remove();
            });
          }
        });
      },

      makeClean: function (obj) {
        jQuery('.aloha-block-SimpleTableBlock', jQuery(obj)).each(function () {
          var $block = jQuery(this);
          var $wrapper = jQuery('<div class="group_table"></div>');

          jQuery('td, .caption_table', $block).each(function () {
            var $td = jQuery(this);
            var $elems = $td.find('div').html();

            $td
              .html($elems)
              .removeClass('aloha-editable')
              .removeAttr('id');
          });

          $wrapper.html($block.html());
          $block.replaceWith($wrapper);
        });
      }
    });
  }
);
