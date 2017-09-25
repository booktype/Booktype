define(
  ['aloha', 'aloha/plugin', 'jquery', 'jquery19', 'ui/ui', 'aloha/ephemera', 'block/block'],
  function (Aloha, Plugin, jQuery, jQuery19, UI, Ephemera, block) {
    "use strict";

    var EndnoteBlock = block.AbstractBlock.extend({
      title: 'EndnoteBlock',
      isDraggable: function () {
        return false;
      },
      init: function ($element, postProcessFn) {
        this.ENDNOTES_CONTAINER_HTML = '<div class="endnotes-container"></div>';
        this.ENDNOTES_INFO_BAR_HTML = '<div class="info-bar">' + window.booktype._('endnotes', 'endnotes').toUpperCase() +'</div>';
        this.ORPHANS_CONTAINER_HTML = '<div class="orphans-container"></div>';
        this.ORPHANS_INFO_BAR_HTML = '<div class="info-bar orphans-info-bar">' +
                                     window.booktype._('endnotes_without_reference', 'endnotes without reference').toUpperCase() +
                                     '</div>';
        var $this = this;
        var $endnotesContainer = jQuery($this.ENDNOTES_CONTAINER_HTML);
        var $orphansContainer = jQuery($this.ORPHANS_CONTAINER_HTML);

        $element.find('ol').before($this.ENDNOTES_INFO_BAR_HTML);

        // convert existing endnotes
        $element.find('li:not([class="orphan-endnote"])').each(function (idx, elem) {
          var $_this = jQuery(elem);
          $endnotesContainer.append($this._getRowHtml($_this.attr("id").substr(8), idx + 1, $_this.html()));
        });
        $element.append($endnotesContainer);

        // convert orphans endnotes
        if ($element.find('li[class="orphan-endnote"]').length) {
          $element.append($this.ORPHANS_INFO_BAR_HTML);
          $element.append($orphansContainer);
          $element.find('li[class="orphan-endnote"]').each(function (idx, elem) {
            var $_this = jQuery(elem);
            if ($_this.html().trim()) $orphansContainer.append($this._getRowOrphanHtml(idx + 1, $_this.html()));
          });
        }

        // add onclick handlers
        $element.find('div.endnotes-container a').on('click', function (e) {
          $this._trash(e);
          return false;
        });
        $element.find('div.orphans-container a').on('click', function (e) {
          $this._trashOrphan(e);
          return false;
        });

        $element.find('ol').remove();

        // assign additional handler for using custom method to activate block
        $element.click(function () {
          $this.makeActive();
        });

        return postProcessFn();
      },
      recalculate: function () {
        var $this = this;
        var obj = jQuery(Aloha.getEditableById('contenteditor').obj);
        var $block = obj.find('div.aloha-block-EndnoteBlock');
        var $endnotesContainer = $block.find('div.endnotes-container');
        var $endnotes = obj.find('sup.endnote[data-id]');
        var $orphansContainer = $block.find('div.orphans-container');
        var $orphans = $block.find('div.orphans-container div.elem');
        var $orphansCount = $orphans.length;

        // some additionals filters and conditions for better work with icejs tracking changes
        $endnotes = $endnotes.filter(function (index) {
          var $sup = jQuery(this);

          if (!$sup.html().trim()) {
            $sup.remove();
            return false;
          } else if ($sup.find('span.del').length) {
            $sup.removeAttr('data-id');
            return false;
          }
          return true;
        });

        // reindex existing orphans
        $orphans.each(function(idx, el) {
          jQuery('span.endnote-counter', el).html(idx + 1 + '.');
        });

        // detect and move orphans to special area
        $endnotesContainer.find('div[data-id]').each(function (idx, el) {
          var $el = jQuery(el);

          if (!obj.find('sup.endnote[data-id="' + $el.attr('data-id') + '"]').length) {

            // ignore empty
            if (!$el.find('div.endnoteText').html().trim()) { $el.remove(); return true;}

            if (!$orphansContainer.length) {
              $orphansContainer = jQuery($this.ORPHANS_CONTAINER_HTML);
              $endnotesContainer.parent().append($this.ORPHANS_INFO_BAR_HTML);
              $endnotesContainer.parent().append($orphansContainer);
            }

            $orphansContainer.append($this._getRowOrphanHtml($orphansCount + 1, $el.find('div.endnoteText').html()));
            $orphansContainer.find('span.endnote-counter:eq(' + ($orphansCount) + ')').parent().find('a').on('click', function (e) {
              $this._trashOrphan(e);
              return false;
            });

            $orphansCount++;
            $el.remove();
          }
        });

        // create endnotes container if needed
        if ($endnotes.length && !$endnotesContainer.length) {
          $endnotesContainer = jQuery($this.ENDNOTES_CONTAINER_HTML);
          $block.prepend($endnotesContainer);
          $block.prepend($this.ENDNOTES_INFO_BAR_HTML);
        }

        // reindex existing endnotes and add new
        $endnotes.each(function (idx, el) {
          var $el = jQuery(el);
          $el.html(idx + 1);
          var $row = $block.find('div[data-id="' + $el.attr('data-id') + '"]');

          if ($row.length > 0) {
            $row.find('span.endnote-counter:first').html((idx + 1) + '.');
            return true;
          } else if (idx === 0) {
            $endnotesContainer.prepend($this._getRowHtml($el.attr('data-id'), idx + 1, ''));
          } else {
            $endnotesContainer.find('span.endnote-counter:eq(' + (idx - 1) + ')').parent().after(
              $this._getRowHtml($el.attr('data-id'), idx + 1, '')
            );
          }
          $endnotesContainer.find('span.endnote-counter:eq(' + (idx) + ')').parent().find('a').on('click', function (e) {
            $this._trash(e);
            return false;
          });
        });

        // delete block if needed
        if (!$block.find('div.elem').length) {
          $block.remove();
          return;
        }

        // delete orphans label and container if needed
        if (jQuery($orphans.selector).length === 0) {
          $block.find('div.orphans-info-bar').remove();
          $block.find('div.orphans-container').remove();
        }

        // delete endnotes label and container if needed
        if ($endnotesContainer.find('div[data-id]').length === 0) {
          $block.find('div.info-bar:not(div[class~="orphans-info-bar"])').remove();
          $block.find('div.endnotes-container').remove();
        }

      },
      update: function ($element, postProcessFn) {
        this.recalculate();
        return postProcessFn();
      },
      makeActive: function () {
        var $this = this;
        setTimeout(function () {
          $this.activate();
        }, 10);
      },
      _trash: function (e) {
        var obj = jQuery('#contenteditor');
        var target = jQuery(e.target);
        var e_id = target.closest('div[data-id]').attr('data-id');
        var $confirm = confirm(window.booktype._('aloha_endnotes_confirm_deletion', 'Do you want to delete this endnote?'));

        if ($confirm === true) {
          var targetSup = obj.find('sup.endnote[data-id="' + e_id + '"]');
          var blockRow = obj.find('div.aloha-block-EndnoteBlock').find('div[data-id="' + e_id + '"]');

          // remove sup from editor and row from block
          targetSup.remove();
          blockRow.remove();
          this.recalculate();
        }
        return false;
      },
      _trashOrphan: function (e) {
        var target = jQuery(e.target);
        var $confirm = confirm(window.booktype._('aloha_endnotes_confirm_deletion', 'Do you want to delete this endnote?'));

        if ($confirm === true) {
          var blockRow = target.closest('div.orphan-endnote');

          // remove sup row from block
          blockRow.remove();
          this.recalculate();
        }
        return false;
      },
      _getRowHtml: function (dataID, index, endnoteText) {
        if (window.booktype.bookDir === 'rtl') {
          return '<div class="row elem" data-id="' + dataID + '">' +
                 '<div class="command">' +
                 '<a href="#" class="pull-right ml10 mr10"><i class="fa fa-trash"></i></a>' +
                 '</div>' +
                 '<div valign="top" class="endnoteText aloha-editable col-md-10">' + endnoteText + '</div>' +
                 '<span style="margin-right: 10px;" valign="top" class="pull-right endnote-counter">' + index + '.</span>' +
                 '</div>';
        }
        return '<div class="row elem" data-id="' + dataID + '">' +
               '<span style="margin-left: 10px;" valign="top" class="pull-left endnote-counter">' + index + '.</span>' +
               '<div valign="top" class="endnoteText aloha-editable col-md-10">' + endnoteText + '</div>' +
               '<div class="command">' +
               '<a href="#" class="pull-right ml10 mr10"><i class="fa fa-trash"></i></a>' +
               '</div>' +
               '</div>'
      },
      _getRowOrphanHtml: function (index, endnoteText) {
        if (window.booktype.bookDir === 'rtl') {
          return '<div class="row elem orphan-endnote">' +
                 '<div class="command">' +
                 '<a href="#" class="pull-right ml10 mr10"><i class="fa fa-trash"></i></a>' +
                 '</div>' +
                 '<div valign="top" class="endnoteText col-md-10">' + endnoteText + '</div>' +
                 '<span style="margin-right: 10px;" valign="top" class="pull-right endnote-counter">' + index + '.</span>' +
                 '</div>'
        }
        return '<div class="row elem orphan-endnote">' +
               '<span style="margin-left: 10px;" valign="top" class="pull-left endnote-counter">' + index + '.</span>' +
               '<div valign="top" class="endnoteText col-md-10">' + endnoteText + '</div>' +
               '<div class="command">' +
               '<a href="#" class="pull-right ml10 mr10"><i class="fa fa-trash"></i></a>' +
               '</div>' +
               '</div>'
      }
    });

    return {EndnoteBlock: EndnoteBlock}
  }
);
