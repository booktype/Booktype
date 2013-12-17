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

	jquery.namespace('win.booktype.editor.edit');

  win.booktype.editor.edit = function() {
      var chapterID = null;
      var tabs = [];

      var _fixFootnotes = function() {
        jquery('#content #footnotes OL').empty();

        _.each(jquery('sup.footnote', jquery('#contenteditor')), function(item, n) {
          var $foot = jquery(item);
          var footID = $foot.attr('id');

          var content = jquery('span', $foot).html();

          $foot.empty().html(n+1);

          var $l = jquery('<li/>').attr('id', 'content_'+footID).html(content);
          jquery('#content #footnotes OL').append($l); 
        });
      }

      var saveContent = function(_call) {
          var content = Aloha.getEditableById('contenteditor').getContents();
          var footnotes = {};

          _.each(jquery('#content #footnotes LI'), function(item, n) {
            footnotes[jquery(item).attr('id')] = jquery(item).html();
          });

          win.booktype.ui.notify(win.booktype._('saving_chapter', 'Saving chapter.'));

          win.booktype.sendToCurrentBook({"command": "chapter_save",
                                  "chapterID": chapterID,
                                  "content": content,
                                  "footnotes": footnotes,
                                  "continue": true,
                                  "comment": "",
                                  "author": "",
                                  "authorcomment": ""},
                                  function(data) {
                                    win.booktype.ui.notify();

                                    // Set content as unmodified after the save
                                    Aloha.getEditableById('contenteditor').setUnmodified();

                                    jquery('div.contentHeader span.info-message').html(win.booktype._('saved', 'Saved...'));
                                    setTimeout(function() { jquery('div.contentHeader span.info-message').empty(); }, 2000);

                                    if(!_.isUndefined(_call))
                                      _call();  

                                    var doc = win.booktype.editor.getChapterWithID(chapterID);
                                    jquery(document).trigger('booktype-document-saved', [doc]);                                    
                                  });

       }

        var _checkIfModified = function(callback, errback) {
          var $editor = Aloha.getEditableById('contenteditor');
  
          if(!_.isUndefined($editor) && $editor && $editor.isModified()) {
              var result = confirm(win.booktype._('content_has_been_modified', 'Content has been modified. Do you want to save it before?'));

              if(result) {              
                win.booktype.editor.edit.saveContent(function() {
                   callback();
                });
                return true;
              }
          } 
          callback();     
          return true;
        }


      var _show = function() {
        var t = win.booktype.ui.getTemplate('templateAlohaToolbar');

        // Disable active options
        jquery('#button-toc').parent().removeClass('active');

        // Embed selected style
        win.booktype.editor.embedActiveStyle();

        jquery("DIV.contentHeader").html(t);
        jquery("DIV.contentHeader [rel=tooltip]").tooltip({container: 'body'});

        var t2 = win.booktype.ui.getTemplate('templateAlohaContent');
        jquery("#content").html(t2);

        jquery("#content #footnotes OL").empty();
        // fix Footnotes
        _fixFootnotes();

        Aloha.jQuery('#contenteditor').aloha();    

        // HIDE
        jquery("#right-tabpane section[source_id=hold-tab]").hide();
        jquery('#hold-tab').hide();

        // Cancel editing
        jquery('#button-cancel').on('click', function() {
          win.booktype.editor.showTOC();        

          jquery('#button-toc').parent().addClass('active');
        });

        // Save chapter
        jquery('#button-save').on('click', function() { win.booktype.editor.edit.saveContent(); });

        // Tabs
        tabs = [];
               

        if(win.booktype.editor.isEnabledTab('edit', 'chapters')) {
            var t1 = win.booktype.editor.createLeftTab('chapters-tab', 'big-icon-chapters', win.booktype._('table_of_contents', 'Table Of Contents'));
            var $panel = jquery("SECTION[source_id=chapters-tab]");

            jquery("BUTTON[rel=tooltip]", $panel).tooltip({container: 'body'});

            // Expand TOC
            jquery("BUTTON[rel=tooltip]", $panel).on('click', function() {
                jquery("BUTTON[rel=tooltip]", $panel).tooltip('destroy');
                // TODO
                // Must check if this content has been edited
                win.booktype.editor.showTOC();
            });

            t1.isOnTop = true;
            t1.onActivate = function() {
                 var _draw = function() {
                      jquery('UL.edit-toc', $panel).empty();

                      jquery.each(win.booktype.editor.data.chapters.chapters, function(i, chap) {
                          if(chap.isSection) {
                            jquery('UL.edit-toc', $panel).append(jquery('<li><div><span class="section">'+chap.title+'</span></div></li>'));
                          } else {
                            var $l = jquery('<a href="#"/>').text(chap.title);

                            $l.on('click', function() {
                                win.booktype.editor.editChapter(chap.chapterID);
                            });

                            var $a = jquery('<li/>').wrapInner('<div/>').wrapInner($l);
                            if(win.booktype.editor.getCurrentChapterID() == chap.chapterID)
                                ("LI", $a).addClass('active');
                          
                            jquery('UL.edit-toc', $panel).append($a);                  
                          }

                      });
                 }

                 _draw();
                 
                 this._tc = win.booktype.editor.data.chapters.observable.on('modified', function() {  
                     _draw();
                 });

                 return false;
            };

            t1.onDeactivate = function() {
              if(this._tc)
                  win.booktype.editor.data.chapters.observable.off(this._tc);
            }

            tabs.push(t1);
        }

        if(win.booktype.editor.isEnabledTab('edit', 'attachments')) {
            var t2 = win.booktype.editor.createRightTab('attachments-tab', 'big-icon-attachments');
            t2.onActivate = function() {
                console.log('klikno na attachments');
            };

            tabs.push(t2);
        }

        if(win.booktype.editor.isEnabledTab('edit', 'notes')) {
            var t3 = win.booktype.editor.createRightTab('notes-tab', 'big-icon-notes');
            t3.onActivate = function() {
                console.log('klikno na notes');
            };

            tabs.push(t3);
        }

        if(win.booktype.editor.isEnabledTab('edit', 'history')) {
            var t4 = win.booktype.editor.createRightTab('history-tab', 'big-icon-history');
            t4.onActivate = function() {
                console.log('klikno na history');
            };

            tabs.push(t4);
        }

        if(win.booktype.editor.isEnabledTab('edit', 'style')) {
            var t5 = win.booktype.editor.createLeftTab('style-tab', 'big-icon-style', win.booktype._('choose_your_design', 'Chose your Design'));

            var $container = jquery("section[source_id=style-tab]");        
            jquery('A', $container).on('click', function() {
                  win.booktype.editor.setStyle(jquery(this).attr('data-style'));

                  return false;
            });

            t5.onActivate = function() {
              var $this = this;
              var $container = jquery("section[source_id=style-tab]");

            };

            tabs.push(t5);
        }

        win.booktype.editor.activateTabs(tabs);

        // Trigger events
        jquery(document).trigger('booktype-ui-panel-active', ['edit', this]);
      }      

    var _hide = function(callback) {
      _checkIfModified(function() {
          jquery("DIV.contentHeader [rel=tooltip]").tooltip('destroy');

          Aloha.jQuery('#contenteditor').mahalo();      
          jquery('#content').empty();
          jquery("DIV.contentHeader").empty();

          win.booktype.editor.deactivateTabs(tabs);
          win.booktype.editor.hideAllTabs();

          if(!_.isUndefined(callback))
            callback();
      }, function() {
          setTimeout(function() {
              jquery(".btn-toolbar label").removeClass("active");
          }, 0);
      });
    }

    var _init = function() {
      Aloha.bind('beforepaste', function(e) {
        console.log('*before paste*');
      }); 

      Aloha.bind('paste', function(e) {
        console.log('*before paste*');
      }); 

      // check if content has changed
      Aloha.bind('aloha-smart-content-changed', function(evt, args) {
              console.log('[aloha-smart-content-changed] ', args);
      })


      Aloha.bind('aloha-link-selected', function() {
      })

      Aloha.bind('aloha-link-unselected', function() {
      })

      Aloha.bind('aloha-image-selected', function(a) {
          console.log('Image selected');
      })

      Aloha.bind('aloha-image-unselected', function(a) {
          console.log('Image unselected');
      })

      Aloha.bind('aloha-editable-activated', function(evt, data) {
        console.log('[aloha-editable-activated]');
        // data.oldActive
        // data.editable
      });

     Aloha.bind('aloha-editable-created', function(e, editable) {
       console.log('[aloha-editable-created] ', editable);

       if(editable.obj.attr('id') == 'contenteditor') {
          win.scrollTo(0, 0);

          var $p = jquery('#contenteditor').find('p');

          if($p.length > 0) {
              // Select first paragraph
              newRange = new GENTICS.Utils.RangeObject();
              
              newRange.startContainer = newRange.endContainer = $p.get(0);

              newRange.startOffset = newRange.endOffset = 0;
              newRange.select();

              // This is needed for Firefox
              editable.obj.focus();
          }           
        }
      });


    }

    var setChapterID = function(id) {
      chapterID = id;
    }

    return {'init': _init,
            'name': 'edit',
            'show': _show,
            'checkIfModified': _checkIfModified,
            'setChapterID': setChapterID,
            'getChapterID': function() { return chapterID; },
            'saveContent': saveContent,
            'hide': _hide};

  }();

  
})(window, jQuery, _);