 /*
  This file is part of Booktype.
  Copyright (c) 2013 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>

  Booktype is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  Booktype is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public License
  along with Booktype.  If not, see <http://www.gnu.org/licenses/>.
*/

(function (win, jquery, _) {
  'use strict';

  jquery.namespace('win.booktype.editor.covers');

  win.booktype.editor.covers = (function () {
    var fileUpload;

    var CoverItem = Backbone.Model.extend({
      defaults: {
        cid: 0,
        title: '',
        notes: '',
        filename: '',
        imageSrc: '',
        preview: '',
        size: 0,
        dimension: null,
        approved: null
      },

      getDimension: function () {
        var d = this.get('dimension');

        return d !== null ? d[0] + 'x' + d[1] : '';
      },

      getSize: function () {
        return win.booktype.utils.formatSize(this.get('size'));
      }
    });

    var CoverCollection = Backbone.Collection.extend({
      model: CoverItem
    });

    var CoverView = Backbone.View.extend({
      events: {
        'change input[type=checkbox]': 'approvedChanged',
        'click #btnEditCover': 'editCover',
        'click #btnDeleteCover': 'deleteCover'
      },

      initialize : function () {
        this.templItem = _.template(jquery('#templateCoverBox').clone().html());
      },

      approvedChanged: function (e) {
        var isChecked = $(e.currentTarget).is(':checked');
        var cid = e.currentTarget.id;

        win.booktype.sendToCurrentBook({
          'command': 'cover_approve',
          'cid': cid,
          'cover_status': isChecked
        },
        function () {
          loadCovers();
        });
      },

      editCover: function (e) {
        var $this = jquery(e.currentTarget);
        var $li = $this.parent().parent().parent();

        var cid = $li.data('cid');

        win.booktype.sendToCurrentBook({'command': 'cover_load', 'cid': cid},
          function (data) {
            win.booktype.ui.notify();

            var $upload = jquery('#editCover');

            jquery('input[name=cid]', $upload).val(data.cover.cid);
            jquery('input[name=title]', $upload).val(data.cover.title);
            jquery('input[name=creator]', $upload).val(data.cover.creator);
            jquery('textarea[name=notes]', $upload).val(data.cover.notes);

            var $lic = [];
            var $tc = _.template('<option value="<%= value %>" <%= selected? "selected" : "" %> ><%= name %></option>');

            _.each(data.licenses, function (elem) {
              $lic.push($tc({'selected': data.cover.license === elem[0], 'value': elem[0], 'name': elem[1]}));
            });
            jquery('select[name=license]', $upload).empty().append($lic);

            $upload.modal('show');
          }
        );
      },

      deleteCover: function (e) {
        var $this = jquery(e.currentTarget);
        var cid = $this.parent().parent().parent().data('cid');

        if (confirm(win.booktype._('cover_delete', 'Do you really want to delete this cover?')) === true) {
          win.booktype.sendToCurrentBook({'command': 'cover_delete', 'cid': cid},
            function (data) {
              loadCovers();
            });
        }
        return false;
      },

      render: function () {
        var $this = this;
        var covers = this.model.map(function (item) {
          return $this.templItem({
            'cid': item.get('cid'),
            'title': item.get('title'),
            'notes': item.get('notes'),
            'filename': item.get('filename'),
            'imageSrc': '../_cover/' + item.get('cid') + '/cover' + item.get('filename') +'?preview=1',
            'preview': item.get('preview'),
            'size': item.getSize(),
            'dimension': item.getDimension(),
            'approved': item.get('approved')
          });
        });

        this.$el.html(covers.join(''));

        return this;
      }
    });

    var coverItems = new CoverCollection();
    var coverView = null;

    var CoverRouter = Backbone.Router.extend({
      routes: {
        'covers': 'covers'
      },

      covers: function () {
        var $d = jquery.Deferred();

        var activePanel = win.booktype.editor.getActivePanel();

        activePanel.hide(function () {
          win.booktype.editor.data.activePanel = win.booktype.editor.data.panels.cover;
          win.booktype.editor.data.activePanel.show();

          $d.resolve();
        });

        return $d.promise();
      },
    });

    var router = new CoverRouter();

    /*******************************************************************************/
    /* DISPLAY COVERS                                                              */
    /*******************************************************************************/

    var filterCovers = function (filterID) {
      var $this = jquery('.contentHeader .btn-toolbar .btn-group .active input');
      var filterID = filterID || jquery($this).prop('id');

      // Should go somewhere out
      if (filterID === 'button-all') {
        jquery('DIV.coverThumbnail').css('display', '');
      }

      if (filterID === 'button-approved') {
        jquery('DIV.coverThumbnail DIV.coverOptions INPUT[type=checkbox]:checked').parent().parent().css('display', '');
        jquery('DIV.coverThumbnail DIV.coverOptions INPUT[type=checkbox]:not(:checked)').parent().parent().css('display', 'none');
      }

      if (filterID === 'button-pending') {
        jquery('DIV.coverThumbnail DIV.coverOptions INPUT[type=checkbox]:checked').parent().parent().css('display', 'none');
        jquery('DIV.coverThumbnail DIV.coverOptions INPUT[type=checkbox]:not(:checked)').parent().parent().css('display', '');
      }
    };

    var displayCovers = function () {
      if (coverView) {
          coverView.render();
      }

      filterCovers();

      // Init cover tooltips
      jquery('.coverOptions .btn').tooltip();

    };

    var loadCovers = function () {
      win.booktype.ui.notify(win.booktype._('loading_cover_files', 'Loading Cover Files'));
      win.booktype.sendToCurrentBook({'command': 'covers_data'},
        function (data) {
          win.booktype.ui.notify();

          coverItems.reset(_.map(data.covers, function (itm) { return new CoverItem(itm); }));
          displayCovers();
        });
    };


    /*******************************************************************************/
    /* SHOW                                                                        */
    /*******************************************************************************/

    var _show = function () {
      win.booktype.ui.notify('Loading');

      jquery('#button-cover').addClass('active');
      jquery('#cover_error').hide();
      jquery(document).on('click', '#cover_error .close', function () {
        jquery('#cover_error').hide();
      });

      // set toolbar
      var t = win.booktype.ui.getTemplate('templateCoversToolbar');
      jquery('DIV.contentHeader').html(t);


      var t2 = win.booktype.ui.getTemplate('templateCoversContent');
      jquery('#content').html(t2);

      jquery('DIV.contentHeader [rel=tooltip]').tooltip({container: 'body'});

      coverView = new CoverView({model: coverItems, el: jquery('#content DIV.coversContainer')});
      loadCovers();

      fileUpload = null;
      jquery('#cover_fileupload').fileupload({
        dataType: 'json',
        sequentialUploads: true,
        done: function (e, data) {
          loadCovers();
          jquery('#uploadCover').modal('hide');
        },
        add: function (e, data) {
          fileUpload = data;
          jquery('#cover_error').hide();

          if (!(/\.(gif|jpe?g|png|tif?f|xcf|psd|pdf|ps|svg|eps|ai|indd)$/i).test(fileUpload.files[0].name)) {
            jquery('#cover_error').show();
            return false;
          } else {
            win.booktype.sendToCurrentBook({'command': 'cover_upload'},
              function (data) {
                var $upload = jquery('#uploadCover');

                jquery('input[name=title]', $upload).val('');
                jquery('input[name=creator]', $upload).val('');
                jquery('textarea[name=notes]', $upload).val('');

                var $lic = [];
                var $tc = _.template('<option value="<%= value %>"><%= name %></option>');

                _.each(data.licenses, function (elem) {
                  $lic.push($tc({'value': elem[0], 'name': elem[1]}));
                });
                jquery('select[name=license]', $upload).empty().append($lic);

                $upload.modal('show');
              });
          }
        },
        progressall: function (e, data) { }
      });

      jquery('#button-all').parent().addClass('active');

      jquery('.contentHeader .btn-toolbar input').on('change', function () {
        var $this = this;
        var filterID = jquery($this).prop('id');

        filterCovers(filterID);
      });

      jquery('#uploadCover .btn-primary').on('click', function () {
        var title = jquery('#uploadCover input[name=title]').val();
        var creator = jquery('#uploadCover input[name=creator]').val();
        var notes = jquery('#uploadCover textarea[name=notes]').val();
        var license = jquery('#uploadCover select[name=license]').val();

        if (jquery.trim(title) !== '') {
          fileUpload.formData = [{'name': 'title', 'value': title},
            {'name': 'creator', 'value': creator},
            {'name': 'notes', 'value': notes},
            {'name': 'license', 'value': license},
            {'name': 'clientID', 'value': win.booktype.clientID}];
          fileUpload.submit();
        } else {
          var title_input = jquery('#uploadCover input[name=title]');

          title_input.parent().parent().addClass('has-error');
          title_input.tooltip('destroy')
            .data('title', win.booktype._('title-validation-error', 'Title field is required.'))
            .addClass('error')
            .tooltip();

          return false;
        }
      });

      jquery('#uploadCover input[name=title]').on('keyup', function (e) {
        var $this = jquery(e.currentTarget);
        var parent = jquery($this).parent().parent();

        e.preventDefault();

        if ($this.val().length > 0 && parent.hasClass('has-error')) {
          parent.removeClass('has-error');
          $this.data('title', '')
            .removeClass('error')
            .tooltip('destroy');
        }
      });

      jquery('#editCover .btn-primary').on('click', function () {
        var $upload = jquery('#editCover');

        var cid = jquery('input[name=cid]', $upload).val();
        var title = jquery('input[name=title]', $upload).val();
        var creator = jquery('input[name=creator]', $upload).val();
        var notes = jquery('textarea[name=notes]', $upload).val();
        var license = jquery('select[name=license]', $upload).val();

        if (jquery.trim(title) !== '') {
          win.booktype.sendToCurrentBook({
            'command': 'cover_save',
            'cid': cid,
            'title': title,
            'creator': creator,
            'notes': notes,
            'license': license
          },
            function (data) {
              loadCovers();
              $upload.modal('hide');
            });
        }
      });

      jquery('.coverMessageButton').on('click', function() {
        jquery('.coverMessage').toggleClass('open');
      });

      // Load cover data
      loadCovers();

      window.scrollTo(0, 0);

      // Trigger events
      jquery(document).trigger('booktype-ui-panel-active', ['covers', this]);
    };

    /*******************************************************************************/
    /* HIDE                                                                        */
    /*******************************************************************************/

    var _hide = function (callback) {
      jquery('#button-cover').removeClass('active');

      // Destroy tooltip
      jquery('DIV.contentHeader [rel=tooltip]').tooltip('destroy');

      // clear content
      jquery('#content').empty();
      jquery('DIV.contentHeader').empty();

      if (!_.isUndefined(callback)) {
        callback();
      }
    };

    /*******************************************************************************/
    /* INIT                                                                        */
    /*******************************************************************************/

    var _init = function () {
      jquery('#button-cover').on('click', function (e) { Backbone.history.navigate('covers', true); });
    };

    /*******************************************************************************/
    /* EXPORT                                                                      */
    /*******************************************************************************/

    return {
      'init': _init,
      'show': _show,
      'hide': _hide,
      'name': 'covers'
    };
  })();

})(window, jQuery, _);
