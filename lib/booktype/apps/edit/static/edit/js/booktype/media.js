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

  jquery.namespace('win.booktype.editor.media');

  win.booktype.editor.media = (function () {
    var fileUpload;

    var MediaItem = Backbone.Model.extend({
      defaults: {
        id: 0,
        name: '',
        preview: '',
        size: 0,
        created: '',
        status: null,
        dimension: null
      },

      getDimension: function () {
        var d = this.get('dimension');

        return d !== null ? d[0] + 'x' + d[1] : '';
      },

      getSize: function () {
        return win.booktype.utils.formatSize(this.get('size'));
      }
    });

    var MediaCollection = Backbone.Collection.extend({
      model: MediaItem
    });

    var MediaView = Backbone.View.extend({
      templRow: _.template('<tr>\
                      <td>\
                        <input type="checkbox" name="attachment" value="<%= id %>">\
                      </td>\
                      <td><a href="<%= link %>" target="_new"><img src="<%= preview %>" alt="<%= name %>" /></a></td>\
                      <td><a href="<%= link %>" target="_new"><%= name %></a></td>\
                      <td><%= dimension %></td>\
                      <td class="size"><%= size %></td>\
                      <td><%= date %></td>\
                    </tr>'),

      render: function () {
        var $this = this;
        var rows = this.model.map(function (item) {
          return $this.templRow({
            'name': item.get('name'),
            'preview': item.get('preview'),
            'id': item.get('id'),
            'link': 'static/' + item.get('name'),
            'size': item.getSize(),
            'dimension': item.getDimension(),
            'date': item.get('created')
          });
        });

        this.$el.html(rows.join(''));

        return this;
      }
    });

    var mediaItems = new MediaCollection();
    var mediaView = null;

    var MediaRouter = Backbone.Router.extend({
      routes: {
        'media': 'media'
      },

      media: function () {
        var $d = jquery.Deferred();

        var activePanel = win.booktype.editor.getActivePanel();

        activePanel.hide(function () {
          win.booktype.editor.data.activePanel = win.booktype.editor.data.panels['media'];
          win.booktype.editor.data.activePanel.show();

          $d.resolve();
        });

        return $d.promise();
      }
    });

    var router = new MediaRouter();


    var drawAttachments = function () {
      if (mediaView) {
        mediaView.render();
      }
    };

    var loadAttachments = function () {
      win.booktype.ui.notify(win.booktype._('loading_media_files', 'Loading media files'));

      win.booktype.sendToCurrentBook({'command': 'attachments_list'},
        function (data) {
          win.booktype.ui.notify();

          mediaItems.reset(_.map(data.attachments, function (itm) { return new MediaItem(itm); }));
          drawAttachments();
          // disable delete button by default
          jquery('#delete-selected-items').attr('disabled', 'disabled');
          window.scrollTo(0, 0);
        }
      );
    };

    var _hideUploadProgress = function () {
      jquery('span.cancel-upload').fadeOut(function () {
        jquery('DIV.contentHeader .progress-bar').css('width', '0%');
      });
      jquery('#media_fileupload').prop('disabled', false);
    };

    var _show = function () {
      jquery('#button-media').addClass("active");

      var t = win.booktype.ui.getTemplate('templateMediaContent');
      jquery('#content').html(t);

      jquery('DIV.contentHeader .progress-bar').css('width', '0px');
      jquery('span.cancel-upload').hide();

      var t2 = win.booktype.ui.getTemplate('templateMediaToolbar');

      jquery('DIV.contentHeader').html(t2);

      jquery('DIV.contentHeader [rel=tooltip]').tooltip({container: 'body'});

      // Setup media widget
      mediaView = new MediaView({model: mediaItems, el: jquery('#content table tbody')});
      loadAttachments();

      jquery('#content #delete-selected-items').on('click', function () {
        var lst = win._.map(jquery('#content table INPUT[type=checkbox]:checked'), function (elem) { return jquery(elem).val(); }).join(',');

        jquery('#removeMedia').modal('show');
        jquery('#removeMedia INPUT[name=attachments]').val(lst);
      });

      jquery(document).on('change', '#content .mediaTable input[type="checkbox"]', function () {
        var checked_count = jquery('#content .mediaTable input[type="checkbox"]:checked').length;
        if (checked_count) {
          jquery('#delete-selected-items').removeAttr('disabled');
        } else {
          jquery('#delete-selected-items').attr('disabled', 'disabled');
        }
      });

      jquery('#removeMedia .remove-media').bind('click.media', function () {
        if (jquery('#removeMedia INPUT[name=understand]:checked').val() === 'on') {
          var lst = jquery('#removeMedia INPUT[name=attachments]').attr('value').split(',');

          if (lst.length === 0) { return; }

          win.booktype.ui.notify(win.booktype._('removing_media_files', 'Removing media files'));

          win.booktype.sendToCurrentBook({'command': 'attachments_delete', 'attachments': lst},
            function (data) {
              win.booktype.ui.notify();
              loadAttachments();
              jquery('#removeMedia').modal('hide');

              // Trigger event
              jquery(document).trigger('booktype-attachment-deleted');
            }
          );
        }
      });

      fileUpload = null;
      jquery('#media_fileupload').fileupload({
        dataType: 'json',
        sequentialUploads: true,
        done: function (e, data) {
          // data.result.files
          _hideUploadProgress();
          loadAttachments();

          jquery(document).trigger('booktype-attachment-uploaded', [data.files]);
        },
        add: function (e, data) {
          if (win.booktype.editor.getActivePanel().name !== 'media') { return; }

          var fileName = null;

          if (!_.isUndefined(data.files[0])) {
            fileName = data.files[0].name;
          }

          if (fileName) {
            if (win.booktype.utils.isUploadAllowed(fileName)) {
              jquery('#progress').show();
              jquery('span.cancel-upload').show();
              jquery('#media_fileupload').prop('disabled', true);

              fileUpload = data.submit();
            } else {
              var $error = jquery('#uploadMediaError');
              $error.modal('show');
            }
          }
        },
        progressall: function (e, data) {
          var progress = parseInt(data.loaded / data.total * 100, 10);
          jquery('DIV.contentHeader .progress-bar').css('width', progress + '%');
        },
        formData: {'clientID': win.booktype.clientID}
      });

      jquery('span.cancel-upload').on('click', function () {
        fileUpload.abort();
        _hideUploadProgress();
      });

      // Trigger events
      jquery(document).trigger('booktype-ui-panel-active', ['media', this]);
    };

    var _hide = function (callback) {
      // Hide tooltip
      jquery('DIV.contentHeader [rel=tooltip]').tooltip('destroy');
      jquery('#button-media').removeClass("active");
         
      jquery('#removeMedia .remove-media').unbind('click.media');

      mediaView.remove();
      mediaView = null;

      // Hide content
      jquery('#content').empty();
      jquery('DIV.contentHeader').empty();

      if (!_.isUndefined(callback)) {
        callback();
      }
    };

    var _init = function () {
      jquery('#button-media').on('click', function (e) { Backbone.history.navigate('media', true); });

      // Remove Media
      jquery('#removeMedia').on('show.bs.modal', function () {
        jquery('#removeMedia .remove-media').prop('disabled', true);
        jquery('#removeMedia INPUT[name=understand]').prop('checked', false);
      });

      jquery('#removeMedia .close-button').on('click', function () {
        jquery('#removeMedia').modal('hide');
      });

      jquery('#removeMedia INPUT[name=understand]').on('change', function () {
        var $this = jquery(this);

        jquery('#removeMedia .remove-media').prop('disabled', !$this.is(':checked'));
      });
    };

    return {
      'init': _init,
      'show': _show,
      'hide': _hide,
      'name': 'media'
    };
  })();
  
})(window, jQuery, _);