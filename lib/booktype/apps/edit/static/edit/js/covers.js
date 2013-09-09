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

	jquery.namespace('win.booktype.editor.covers');

  win.booktype.editor.covers = function() {

        var fileUpload = null;
        var covers = null;

        /*******************************************************************************/
        /* DISPLAY COVERS                                                              */
        /*******************************************************************************/

        var filterCovers = function(filterID) {
            var $this = jquery('.contentHeader .btn-toolbar .btn-group button.active');
            var filterID = filterID || jquery($this).prop('id');

            // Should go somewhere out
            if(filterID === 'button-all') {
              jquery("UL.thumbnails LI").css('display', '');
            }

            if(filterID === 'button-approved') {
              jquery("UL.thumbnails LI INPUT[type=checkbox]:checked").closest('LI').css('display', '');
              jquery("UL.thumbnails LI INPUT[type=checkbox]:not(:checked)").closest('LI').css('display', 'none');
            }

            if(filterID === 'button-pending') {
              jquery("UL.thumbnails LI INPUT[type=checkbox]:checked").closest('LI').css('display', 'none');              
              jquery("UL.thumbnails LI INPUT[type=checkbox]:not(:checked)").closest('LI').css('display', '');
            }          
        }

        var displayCovers = function() {
          var $t = _.template(jquery("#templateCovers").html());
          // u zavisnosti od flaga
          var $c = $t({'covers': covers});

          jquery('.thumbnails').empty().html($c);

          jquery('.thumbnails INPUT[type=checkbox]').change(function() {
            var $this = this;
            var isChecked = $($this).is(":checked");            
            var $li = jquery($this).closest('li');
            var cid = $li.attr('data-cid');

            win.booktype.sendToCurrentBook({"command": "cover_approve",
                                            "cid": cid,
                                            "cover_status": isChecked},
                                            function(dta) {
                                               // should not redraw everything for no reason
                                               loadCovers();
                                            });
          });
          
          jquery('.thumbnails BUTTON.btn-xs').on('click', function() {
            var $this = jquery(this);
            var $li = $this.parent().parent();

            var cid = $li.attr('data-cid');

            win.booktype.sendToCurrentBook({"command": "cover_load",
                                            "cid": cid},
                                            function(data) {
                                              win.booktype.ui.notify();

                                              var $upload = jquery('#editCover');

                                              jquery('input[name=cid]', $upload).val(data.cover.cid);
                                              jquery('input[name=title]', $upload).val(data.cover.title);
                                              jquery('input[name=creator]', $upload).val(data.cover.creator);
                                              jquery('textarea[name=notes]', $upload).val(data.cover.notes);

                                              var $lic = [];
                                              var $tc = _.template('<option value="<%= value %>" <%= selected? "selected" : "" %> ><%= name %></option>');

                                              _.each(data.licenses, function(elem) {
                                                $lic.push($tc({'selected': data.cover.license === elem[0], 'value': elem[0], 'name': elem[1]}));
                                              });
                                              jquery('select[name=license]', $upload).empty().append($lic);

                                              $upload.modal('show');
                                            });
          });

          filterCovers();
        }

        var loadCovers = function() {
                  win.booktype.sendToCurrentBook({"command": "covers_data"},
                                          function(data) {
                                            win.booktype.ui.notify();

                                            covers = data.covers;

                                            displayCovers();
                                          });
         };


        /*******************************************************************************/
        /* SHOW                                                                        */
        /*******************************************************************************/

        var _show = function() {
          win.booktype.ui.notify('Loading');

          // set toolbar
          var t = win.booktype.ui.getTemplate('templateCoversToolbar');
          jquery("DIV.contentHeader").html(t);


          var t2 = win.booktype.ui.getTemplate('templateCoversContent');
          jquery("#content").html(t2);

          fileUpload = null;
          jquery('#fileupload').fileupload({
                          dataType: 'json',
                          sequentialUploads: true,                        
                          done: function (e, data) {
                              loadCovers();
                              jquery("#uploadCover").modal('hide');
                          },
                          add: function (e, data) {
                            fileUpload = data;

                            win.booktype.sendToCurrentBook({"command": "cover_upload"},
                                                          function(data) {
                                                              var $upload = jquery('#uploadCover');

                                                              jquery('input[name=title]', $upload).val('');
                                                              jquery('input[name=creator]', $upload).val('');
                                                              jquery('textarea[name=notes]', $upload).val('');

                                                              var $lic = [];
                                                              var $tc = _.template('<option value="<%= value %>"><%= name %></option>');

                                                              _.each(data.licenses, function(elem) {
                                                                $lic.push($tc({'value': elem[0], 'name': elem[1]}));
                                                              });
                                                              jquery('select[name=license]', $upload).empty().append($lic);

                                                              $upload.modal('show');
                                                            });
                          },
                          progressall: function (e, data) {

                          }
                      });

          jquery('#button-all').parent().addClass('active');

          jquery('.contentHeader .btn-toolbar input').on('change', function() {
            var $this = this;
            var filterID = jquery($this).prop('id');

            filterCovers(filterID);
          });

          jquery('#uploadCover .btn-primary').on('click', function() {
              var title = jquery('#uploadCover input[name=title]').val();
              var creator = jquery('#uploadCover input[name=creator]').val();
              var notes = jquery('#uploadCover textarea[name=notes]').val();
              var license = jquery('#uploadCover select[name=license]').val();

              if(jquery.trim(title) !== '') {
                  fileUpload.formData = [{'name': 'title', 'value': title},
                                         {'name': 'creator', 'value': creator},
                                         {'name': 'notes', 'value': notes},
                                         {'name': 'license', 'value': license}];
                  fileUpload.submit();
              }
          });

          jquery('#editCover .btn-primary').on('click', function() {
              var $upload = jquery("#editCover");

              var cid = jquery('input[name=cid]', $upload).val();
              var title = jquery('input[name=title]', $upload).val();
              var creator = jquery('input[name=creator]', $upload).val();
              var notes = jquery('textarea[name=notes]', $upload).val();
              var license = jquery('select[name=license]', $upload).val();

              if(jquery.trim(title) !== '') {
                  win.booktype.sendToCurrentBook({"command": "cover_save",
                                                  "cid": cid,
                                                  "title": title,
                                                  "creator": creator,
                                                  "notes": notes,
                                                  "license": license},
                                                 function(data) {
                                                    loadCovers();
                                                    $upload.modal('hide');
                                                 });
              }
          });


          // Load cover data
          loadCovers();

          window.scrollTo(0, 0);
        }

        /*******************************************************************************/
        /* HIDE                                                                        */
        /*******************************************************************************/

        var _hide = function() {
          // clear content
          jquery('#content').empty();
          jquery("DIV.contentHeader").empty();
        }

        /*******************************************************************************/
        /* INIT                                                                        */
        /*******************************************************************************/

        var _init = function() {
            jquery("#button-cover").on('change', function(e) { win.booktype.editor.showCover(); });
        }

    /*******************************************************************************/
    /* EXPORT                                                                      */
    /*******************************************************************************/

    return {'init': _init,
            'show': _show,
            'hide': _hide,
            'name': 'covers'};

  }();

  
})(window, jQuery, _);