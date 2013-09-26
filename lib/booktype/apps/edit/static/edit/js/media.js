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

(function(win, jquery, _) {

	jquery.namespace('win.booktype.editor.media');

  win.booktype.editor.media = function() {
    var attachments;
    var fileUpload;
    var templ = '<tr>\
                  <td>\
                    <input type="checkbox" name="attachment" value="<%= id %>">\
                  </td>\
                  <td><a href="<%= link %>" target="_new"><%= name %></a></td>\
                  <td><%= dimension %></td>\
                  <td class="size"><%= size %></td>\
                  <td><%= date %></td>\
                </tr>';

    var drawAttachments = function() {
      var s = '';

      jquery.each(attachments, function(i, item) {
          var t = _.template(templ);
          var d = '';

          if(item.dimension !== null)
            d = item.dimension[0]+'x'+item.dimension[1];

          var a = t({'name': item.name,
                     'id': item.id, 
                     'link': 'static/'+item.name,
                     'size': win.booktype.utils.formatSize(item.size),
                     'dimension': d,
                     'date': item.created });
          s += a;
      });

      jquery("#content table tbody").html(s);
    }

    var loadAttachments = function() {
      win.booktype.ui.notify('Loading media files');

      win.booktype.sendToCurrentBook({"command": "attachments_list"}, 
                                      function(data) {
                                          win.booktype.ui.notify();
                                          attachments = data.attachments;

                                          drawAttachments();
                                          window.scrollTo(0, 0);
                                      });
    }

    var _hideUploadProgress = function() {
            jquery("span.cancel-upload").fadeOut();
            jquery('#progress .bar').css('width', '0%');  
            jquery("#progress .perc").empty();       

            jquery("#fileupload").prop('disabled', false);  
    }

    var _show = function() {
      var t = win.booktype.ui.getTemplate('templateMediaContent');
      jquery("#content").html(t);
      jquery("#progress").hide();
      jquery("span.cancel-upload").hide();

      var t2 = win.booktype.ui.getTemplate('templateMediaToolbar');

      jquery("DIV.contentHeader").html(t2);

      jquery("DIV.contentHeader [rel=tooltip]").tooltip({container: 'body'});          

      loadAttachments();

      jquery("#content #delete-selected-items").on('click', function() {      
        var lst = win._.map(jquery("#content table INPUT[type=checkbox]:checked"), function(elem) { return jquery(elem).val() }).join(',');

        jquery('#removeMedia').modal('show');
        jquery('#removeMedia INPUT[name=attachments]').val(lst);                                 
      });      


      // Remove Media
      jquery("#removeMedia").on('show.bs.medal', function() {
         jquery("#removeMedia .btn-primary").prop('disabled', true); 
         jquery("#removeMedia INPUT[name=understand]").prop('checked', false);
      });

      jquery("#removeMedia .close-button").on('click', function() {
        jquery("#removeMedia").modal('hide');
      })

      jquery("#removeMedia INPUT[name=understand]").on('change', function() {
         var $this = jquery(this);

         jquery("#removeMedia .btn-primary").prop('disabled', !$this.is(':checked'));
      });

      jquery("#removeMedia .btn-primary").on('click', function() {
        if(jquery("#removeMedia INPUT[name=understand]:checked").val() == 'on') {
            var lst = jquery("#removeMedia INPUT[name=attachments]").attr("value").split(",");
            
            if(lst.length == 0) return;

            win.booktype.ui.notify('Removing media files');

            win.booktype.sendToCurrentBook({"command": "attachments_delete",
                                            "attachments": lst},
                                            function(data) {
                                                win.booktype.ui.notify();
                                                loadAttachments();
                                                jquery("#removeMedia").modal('hide');

                                                // Trigger event
                                                jquery(document).trigger('booktype-attachment-deleted'); 
                                            });
          }

        });

        fileUpload = null;
        jquery('#fileupload').fileupload({
                        dataType: 'json',
                        sequentialUploads: true,                        
                        done: function (e, data) {
                            // data.result.files
                          _hideUploadProgress();
                          loadAttachments();

                          jquery(document).trigger('booktype-attachment-uploaded', [data.files]);   
                        },
                        add: function (e, data) {
                          jquery("#progress").show();
                          jquery("span.cancel-upload").show();
                          jquery("#fileupload").prop('disabled', true);

                          fileUpload = data.submit();
                        },
                        progressall: function (e, data) {
                                var progress = parseInt(data.loaded / data.total * 100, 10);
                                jquery("#progress .perc").html(progress+'%');
                                jquery('#progress .bar').css('width', progress + '%');          

                            }
                    });

        jquery("span.cancel-upload").on('click', function() {
          fileUpload.abort();
          _hideUploadProgress();
        });

        // Trigger events
        jquery(document).trigger('booktype-ui-panel-active', ['media', this]);
    }

    var _hide = function() {
                  // Hide tooltip
                  jquery("DIV.contentHeader [rel=tooltip]").tooltip('destroy');      

                  // Hide content
                  jquery('#content').empty();
                  jquery("DIV.contentHeader").empty();
                }

    var _init = function() {
                  jquery("#button-media").on('change', function(e) { win.booktype.editor.showMedia(); });
                }


    return {'init': _init,
            'show': _show,
            'hide': _hide,
            'name': 'media'};

  }();

  
})(window, jQuery, _);