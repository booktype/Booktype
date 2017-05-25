define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/ephemera', 'block/block', 'block/blockmanager', 'underscore', 'PubSub', 'booktype', 'toolbar/toolbar-plugin'],
  function(Aloha, Plugin, jQuery,  jQuery19, UI, Ephemera, block, BlockManager, _, PubSub, booktype, toolbar) {
    var selected = null;

    var setStyle = function ($elem, columns) {
      $elem.css({"column-count": columns,
        "-webkit-column-count": columns,
        "-moz-column-count": columns,
        "-webkit-column-width": Math.round(1 / columns),
        "column-width": Math.round(1 / columns)});

      resizeBlock($elem);
    };

    var drawInfo = function ($elem) {
      var _s = booktype._('columns_start_columns', 'Start columns:');
      $elem.find('.bk-columns-marker').html(_s + $elem.attr("data-column"));
    };

    var calculateMaxPosition = function (dataColumn, children) {
      var maxHeight = 0;
      var overflow = false;
      var forceOverflow = false;
      var _y = -1;

      var parentWidth = jQuery(children).parent().innerWidth();

      children.each(function (idx, elem) {
        var m = jQuery(elem).position().top + jQuery(elem).height();
        var left = jQuery(elem).position().left;
        var width = jQuery(elem).width();

        if (left > parentWidth) {
          overflow = true;
          forceOverflow = true;
        }

        if (left + width >= parentWidth) {
          overflow = true;
          forceOverflow = true;
        }

        _y = left + width;

        if (m > maxHeight) {
          maxHeight = m;
        }
      });

      if (overflow) {
        if (forceOverflow) {
          return [-1, maxHeight];
        } else {
          return [-2, maxHeight];
        }
      }
      return [0, maxHeight];
    };

    var resizeBlock = function (ed, n) {
      var data = calculateMaxPosition(parseInt(ed.parent().attr("data-column")), ed.children());
      var maxHeight = data[1];
      var num = _.isUndefined(n)?0:n;

      if (n > 20) {
        return;
      }

      if (data[0] === -1) {
        ed.css('height', ed.height() + 50);
        setTimeout(function () { resizeBlock(ed, num + 1); }, 0);
        return;
      }

      if (data[0] === -3) {
        if (ed.height() - maxHeight < 30) {
          ed.css('height', ed.height() + 50);
          setTimeout(function () { resizeBlock(ed, num + 1); }, 0);
          return;
        }
      }
      /*
      if (ed.height() - maxHeight < 30) {
        ed.css('height', ed.height() + 50);
      }
      */
      return;
    }

    var ColumnsBlock = block.AbstractBlock.extend({
      title: 'ColumnsTable',
      isDraggable: function () { return false; },
      init: function ($element, postProcessFn) {
        var that = this,
          ed = jQuery($element).find('.aloha-editable'),
          _s = booktype._('columns_title', 'Columns');

        ed.before('<div class="bk-columns-info"><a class="bk-help" href=""><span class="fa fa-question-circle"></span></a>\
  <span class="bk-title">' + _s + '</span> <a class="bk-action bk-remove" href=""><span class="fa fa-trash"></span></a>\
  <a class="bk-action bk-settings" href=""><span class="fa fa-cog"></span></a>  </div>');

        jQuery19($element).find('.bk-settings').on('click', function () {
          selected = $element;

          jQuery19('#columnsDialog').modal('show');
          return false;
        });

        var $help = jQuery19($element).find('.bk-help');

        $help.on('click', function () {
          var message = booktype._('columns_info', 'Some output formats do not have support for columns.');
          $help.popover({container: 'body', placement: 'top', trigger: 'manual', content: message, delay: 0});
          $help.popover('show');

          setTimeout(function () { $help.popover('hide'); }, 6000);
          return false;
        });

        jQuery19($element).find('.bk-remove').on('click', function () {
          if (confirm(booktype._('columns_delete', 'Do you want to remove the columns?'))) {
            var $content = $element.find('.aloha-editable').contents().unwrap();
            $element.mahaloBlock();
            $element.replaceWith($content);
          }
          return false;
        });

        jQuery19($element).find('.bk-columns-marker').on('click', function () {
          setTimeout(function () {
            var b1 = BlockManager.getBlock($element.attr('id'));
            b1.activate();
          }, 200);
        });

        var column = jQuery($element).attr('data-column');
        setStyle(ed, column);

        var observer = new MutationObserver(function (mutations) {
          resizeBlock(ed);
        });

        observer.observe(ed.get(0), {
          attributes: false,
          childList: true,
          characterData: true,
          subtree: true });

        return postProcessFn();
      },

      update: function ($element, postProcessFn) {
        return postProcessFn();
      }
    });

    var _initColumns = function(editable) {
      var $tables = editable.obj.find('div.bk-columns').each(function (idx, bl) {
        var $block = jQuery(bl),
          $content = $block.html();

        if ($block.hasClass('aloha-block-ColumnsBlock')) {
          return;
        }

        $block.addClass('aloha-columns');
        $block.empty();

        if (_.isUndefined($block.attr("data-column"))) {
          $block.attr("data-column", "3");
        }

        if (_.isUndefined($block.attr("data-gap"))) {
          $block.attr("data-gap", "");
        }

        if (_.isUndefined($block.attr("data-valign"))) {
          $block.attr("data-valign", "");
        }

        var $b = jQuery('<div class="aloha-editable"></div>');
        $b.append($content);
        $block.append($b);

        var $c = jQuery('<div class="bk-columns-marker">  </div>');
        $block.append($c);

        if ($block.hasClass('bk-marker')) {
          drawInfo($block);
        }

        $block.alohaBlock({'aloha-block-type': 'ColumnsBlock'});
      });
    }

    return Plugin.create('columns', {
      defaultSettings: {
        enabled: true
      },

      init: function () {
        var self = this;

        self.settings = jQuery.extend(true, self.defaultSettings, self.settings);

        if (!self.settings.enabled) { return; }

        Ephemera.attributes('data-aloha-block-type', 'contenteditable');

        BlockManager.registerBlockType('ColumnsBlock', ColumnsBlock);

        Aloha.bind('aloha-my-undo', function (event, args) {
          _initColumns(args.editable);
        });

        Aloha.bind('aloha-editable-created', function($event, editable) {
          _initColumns(editable);
        });

        var $dialog = jQuery19('#columnsDialog');

        $dialog.find('.btn-ok').on('click', function () {
          var dataColumn = $dialog.find('select[name="columnsNumber"]').val();
          var valignColumn = $dialog.find('select[name="valign"]').val();
          var gapColumn = $dialog.find('select[name="gap"]').val();
          var startColumn = $dialog.find('input[name="start"]:checked').val();

          selected.attr("data-column", dataColumn);
          selected.attr("data-gap", gapColumn);
          selected.attr("data-valign", valignColumn);

          setStyle(selected.find('.aloha-editable'), dataColumn);

          if (!_.isUndefined(startColumn)) {
            selected.addClass('bk-marker');
            drawInfo(selected);
          } else {
            selected.removeClass('bk-marker');
          }

          $dialog.modal('hide');

          setTimeout(function () {
            var b1 = BlockManager.getBlock(selected.attr('id'));
            b1.activate();
          }, 500);

        });

        $dialog.on('show.bs.modal', function () {
          var dataColumn = selected.attr("data-column");
          var valignColumn = selected.attr("data-valign");
          var gapColumn = selected.attr("data-gap");
          var hasStart = selected.hasClass('bk-marker');

          $dialog.find('select[name="columnsNumber"]').val(dataColumn);
          $dialog.find('input[name="valign"]').val(valignColumn);
          $dialog.find('select[name="gap"]').val(gapColumn);

          if (hasStart) {
            $dialog.find('input[name="start"]').prop('checked', true);
          } else {
            $dialog.find('input[name="start"]').prop('checked', false);
          }
        });

        UI.adopt('columns-insert', null, {
          click: function() {
            editable = Aloha.activeEditable;
            range = Aloha.Selection.getRangeObject();

            var $a = jQuery('<div class="aloha-columns" data-column="3" data-valign="" data-gap="5"><div class="aloha-editable"><p>  </p></div><div class="bk-columns-marker"> </div></div>');
            $a.alohaBlock({'aloha-block-type': 'ColumnsBlock'});

            setTimeout(function () {
              var b1 = BlockManager.getBlock($a.attr('id'));
              b1.activate();
            }, 200);

            GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
            return true;
          }
        });

        UI.adopt('column-break-insert', null, {
          click: function() {
            editable = Aloha.activeEditable;
            range = Aloha.Selection.getRangeObject();

            var $a = jQuery('<div class="bk-column-break"></div>');

            GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
            return true;
          }
        });
      },

      makeClean: function (obj) {
        jQuery('.aloha-block-ColumnsBlock', jQuery(obj)).each(function () {
          var $block = jQuery(this);
          var $content = $block.find('.aloha-editable').contents().unwrap();

          var dataColumn = $block.attr("data-column");
          var gapColumn = $block.attr("data-gap");
          var valignColumn = $block.attr("data-valign");
          var extra = '';

          if (_.isUndefined(dataColumn)) {
            dataColumn = 1;
          }

          if (_.isUndefined(gapColumn)) {
            gapColumn = 5;
          }

          if (_.isUndefined(valignColumn)) {
            valignColumn = "";
          }

          if ($block.hasClass('bk-marker')) {
            extra = ' bk-marker';
          }

          var $elem = jQuery('<div class="bk-columns' + extra + '" data-column="' + dataColumn +
            '" data-gap="' + gapColumn + '" data-valign="' + valignColumn + '"></div>');
          $elem.append($content);
          $block.replaceWith($elem);
        });
      }
    });
  }
);
