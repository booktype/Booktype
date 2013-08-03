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

(function(win, jquery) {

	jquery.namespace('win.booktype.editor.toc');

  win.booktype.editor.toc = function() {

      var tabs = [];

      /*******************************************************************************/
      /* MISC                                                                        */
      /*******************************************************************************/

      var getStatusName = function(statusID) {
                             var $s = jquery.grep(win.booktype.editor.data.statuses, function(v, i) { return v[0] == statusID;});

                             if($s.length > 0)
                                return $s[0][1];
                            
                              return '';
                          };  

      /*******************************************************************************/
      /* CHAPTER                                                                     */
      /*******************************************************************************/

      var Chapter = function(dta) {
                        jquery.extend(this, {chapterID: null,                          
                                             title: '',
                                             urlTitle: '',
                                             isSection: false,
                                             status: null});

                        if(typeof dta !== 'undefined') 
                            jquery.extend(this, dta);
                    };

      /*******************************************************************************/
      /* TABLE OF CONTENTS                                                           */
      /*******************************************************************************/

      var TOC = function() {
                    this.chapters = [];

                    this.getChapterIndexWithID = function(cid) {                        
                        for(var i=0; i<this.chapters.length; i++) {
                          if(this.chapters[i].getChapterID() == cid)
                            return i;
                        }

                        return -1;
                    }


                    this.getChapterWithID = function(cid) {
                        return _.findWhere(this.chapters, {'chapterID': cid});
                    }

                    this.addChapter = function(chap) {
                      this.chapters.push(chap);
                    }

                    this.loadFromArray = function(arr) {
                      for(var i=0; i<arr.length; i++) {
                          var c = new Chapter({'chapterID': arr[i][0],
                                              'isSection': arr[i][3] == 2,
                                              'title': arr[i][1],
                                              'status': arr[i][4],
                                              'url_title': arr[i][2]});

                          this.addChapter(c);
                      }
                    }
                 };

      /*******************************************************************************/
      /* TABLE OF CONTENTS WIDGET                                                    */
      /*******************************************************************************/

      var CREATE_SECTION = function(item) {
                                sec = win.booktype.ui.getTemplate("templateTOCSection");
                                win.booktype.ui.fillTemplate(sec, {'title': item.title});
                                sec.attr('data-id', item.chapterID);
                                sec.attr('id', 'list_'+item.chapterID);

                              // hover for the menu
                              jquery('div', sec).hover(
                                  function() {
                                      jquery(this).parent().find('div.btn-toolbar:first').show();    
                                  },
                                  function() {
                                      jquery(this).parent().find('div.btn-toolbar:first').hide();
                                  }
                              );
                              jquery('.btn-toolbar', sec).hover(
                                  function() {
                                      jquery(this).closest('li.item').find('div:first').toggleClass('hover-effect');
                                  },
                                  function() {
                                      jquery(this).closest('li.item').find('div:first').toggleClass('hover-effect');
                                  }
                              );


                                return sec;
                           };

      var CREATE_CHAPTER = function(item) {
                             var templateChapter = win.booktype.ui.getTemplate("templateTOCChapter");
                             win.booktype.ui.fillTemplate(templateChapter, {'title': item.title});

                              templateChapter.attr('data-id', item.chapterID);
                              templateChapter.attr('id', 'list_'+item.chapterID);

                              // hover for the menu
                              jquery('div', templateChapter).hover(
                                  function() {
                                      jquery(this).parent().find('div.btn-toolbar:first').show();    
                                  },
                                  function() {
                                      jquery(this).parent().find('div.btn-toolbar:first').hide();
                                  }
                              );
                              
                              jquery('.btn-toolbar', templateChapter).hover(
                                  function() {
                                      jquery(this).closest('li.item').find('div:first').toggleClass('hover-effect');
                                  },
                                  function() {
                                      jquery(this).closest('li.item').find('div:first').toggleClass('hover-effect');
                                  }
                              );

                             jquery('BUTTON.edit', templateChapter).click(function() {
                                win.booktype.editor.editChapter(item.chapterID);
                             });

                             // Insert status names
                             var $l = [];
                             jquery.each(win.booktype.editor.data.statuses, function(i, v) {
                                var $a = jquery('<a />').attr({'href': '#', 'data-status-id': v[0]}).text(v[1]);

                                $l.push(jquery('<li/>').wrapInner($a));
                             });

                             jquery('.btn-toolbar .btn-group:first ul.dropdown-menu', templateChapter).append($l);

                             // Change status
                             jquery('.btn-toolbar .btn-group:first ul.dropdown-menu a', templateChapter).click(function (e) {
                                  var $this = jquery(this);
                                  var statusID = $this.closest('A').attr('data-status-id');
                                  item.status = statusID;

                                  win.booktype.ui.notify('Set status.');

                                  win.booktype.sendToCurrentBook({"command": "change_status", 
                                                                  "chapterID": item.chapterID,
                                                                  "statusID": statusID}, 
                                                                  function() { 
                                                                    win.booktype.ui.notify();    
                                                                    $this.closest('DIV').trigger('click');
                                                                    tocWidget.refresh();
                                                                  });

                                  return false;
                            });

                             // check from the locks
                             jquery('.toc-chapter-detail .username', templateChapter).html('');
                             jquery('.toc-chapter-detail .status', templateChapter).html(getStatusName(item.status));


                             jquery('A.option-delete', templateChapter).click(function() {
                                 jquery('#removeChapter').modal('show');

                                 jquery('#removeChapter INPUT[name=chapter_id]').val(item.chapterID);                                 
                                 return false;
                             });

                             return templateChapter;
                          }; 


      var TOCWidget = function() {
                         this.draw = function() {
                            var lst = win.booktype.editor.data.chapters.chapters;
                            var s = [];
                            var s2 = [];
                            var inSection = false;
                            var sec = null;

                            if(!lst) return;

                            jquery.each(lst, function(i, item) {
                              if(item.isSection) {

                                if(inSection == true) {
                                  jquery('OL', sec).append(s2);
                                  s2 = [];
                                  s.push(sec);
                                } 

                                inSection = true;
                                sec = CREATE_SECTION(item);

                              } else {
                                  var templateChapter = CREATE_CHAPTER(item);

                                  if(inSection)
                                    s2.push(templateChapter);
                                  else
                                    s.push(templateChapter);
                              }
                            });

                            if(inSection == true) {
                                  jquery('OL', sec).append(s2);
                                  s.push(sec);
                            }

                            var $sortie = jquery('<ol class="sortable"></ol>');
                            jquery("#content").append($sortie.wrapInner(s));

                         };

                         this.refreshItem = function(item) {
                               var $li = jquery("LI[data-id="+item.chapterID+"]");

                              jquery('.toc-chapter-detail .status', $li).html(getStatusName(item.status));
                         };

                         this.refresh = function() {
                            var $this = this;
                            var lst = win.booktype.editor.data.chapters.chapters;

                            jquery.each(lst, function(i, item) {
                              $this.refreshItem(item);
                            });
                         };
      };

      var tocWidget = new TOCWidget();

      /*******************************************************************************/
      /* EVENTS                                                                      */
      /*******************************************************************************/

      var expandChapters = function () {
          jquery('.sortable li.mjs-nestedSortable-collapsed').removeClass('mjs-nestedSortable-collapsed').addClass('mjs-nestedSortable-expanded');
      }

      var collapseChapters = function() {
          jquery('.sortable li.mjs-nestedSortable-expanded').removeClass('mjs-nestedSortable-expanded').addClass('mjs-nestedSortable-collapsed');
      }


      // MISC
      var _toc = function() {
            
 // Nested sortable
        jquery('ol.sortable').nestedSortable({
            attribute: 'id',
            forcePlaceholderSize: true,
            handle: 'div',
            helper: 'clone',
            items: 'li.item',
            opacity: .6,
            placeholder: 'placeholder',
            revert: 250,
            tabSize: 25,
            tolerance: 'pointer',
            toleranceElement: '> div',
            maxLevels: 2,           
            disableNestingClass: 'chapter',
            connectWith: ".hold-target-box",
            rootID: 'link_id',
            isTree: true,
            expandOnHover: 700,
            startCollapsed: true,

            stop: function(event, ui) {             
                    var result = jquery(this).nestedSortable('toArray', {startDepthCount: 0, excludeRoot: true});

                    win.booktype.sendToCurrentBook({"command": "chapters_changed", 
                                                    "chapters": result,
                                                    "hold": [],
                                                    "kind": "order",
                                                    "chapter_id": null
                                                    }, 
                                                   function() {
                                                        // TODO:
                                                        // - refresh locks
                                                        win.booktype.ui.notify();
                                                   });
                    return true;
            }
        });

        jquery('.disclose').on('click', function() {
            jquery(this).closest('li').toggleClass('mjs-nestedSortable-collapsed').toggleClass('mjs-nestedSortable-expanded');
        })

        // ToC / Expand/Collapse
        jquery('#expand').click(function() {
                        expandChapters();
        });
        jquery('#collapse').click(function() {
              collapseChapters();
        });

        // ToC / Chapter details switch
        jquery('#detail-switch').click(function() {
            jquery('.sortable li').toggleClass('detail-switch')
        });

        var holdBtnGroup = "<div class=\"btn-group\">" + 
            "<button id=\"expand\" class=\"btn btn-mini\" rel=\"tooltip\" data-placement=\"bottom\" data-original-title=\"Unhold\">" +
            "<i class=\"icon-arrow-left\"><\/i>" +
            "<\/button>" +
            "<button id=\"collapse\" class=\"btn btn-mini\" rel=\"tooltip\" data-placement=\"bottom\" data-original-title=\"Delete\">" +
            "<i class=\"icon-trash\"><\/i>" +
            "<\/button>" +
            "<\/div>";

        jquery('.tabpane .hold-chapters li').hover(
            function() {                
                jquery(this).append(holdBtnGroup);
                jquery('[rel=tooltip]').tooltip();
            },
            function() {
                jquery(this).find('div.btn-group').remove();
            }
        );

        // Tooltip
        // this should be executed only once
        jquery('[rel=tooltip]').tooltip();

        }

        /*******************************************************************************/
        /* SHOW                                                                        */
        /*******************************************************************************/

        var _show = function() {
          win.booktype.ui.notify('Loading');

          // set toolbar
          var t = win.booktype.ui.getTemplate('templateTOCToolbar');
          jquery("DIV.contentHeader").html(t);

          tocWidget.draw();
          _toc();

          expandChapters();

          // show panels on the side

          window.scrollTo(0, 0);

          // panels
          var t2 = win.booktype.editor.createRightTab('hold-tab', 'big-icon-hold');
          t2.onActivate = function() {
              console.log('klikno na hold chapters');
          };          

          tabs = [t2];

          win.booktype.editor.activateTabs(tabs);
          win.booktype.ui.notify();
        }

        /*******************************************************************************/
        /* HIDE                                                                        */
        /*******************************************************************************/

        var _hide = function() {
          // clear content
          jquery('#content').empty();
          jquery("DIV.contentHeader").empty();

          win.booktype.editor.deactivateTabs(tabs);
          win.booktype.editor.hideAllTabs();
        }

        /*******************************************************************************/
        /* INIT                                                                        */
        /*******************************************************************************/

        var _init = function() {
            // remove chapter
            jquery("#removeChapter").on('show', function() {
               jquery("#removeChapter .btn-primary").prop('disabled', true); 
               jquery("#removeChapter INPUT[name=understand]").prop('checked', false);
            });

            jquery("#removeChapter .close-button").on('click', function() {
              jquery("#removeChapter").modal('hide');
            })

            jquery("#removeChapter INPUT[name=understand]").on('change', function() {
               var $this = jquery(this);

               jquery("#removeChapter .btn-primary").prop('disabled', !$this.is(':checked'));
            });

            jquery("#removeChapter .btn-primary").on('click', function() {
              if(jquery("#removeChapter INPUT[name=understand]:checked").val() == 'on') {
                  var chapter_id = jquery("#removeChapter INPUT[name=chapter_id]").attr("value");
                  win.booktype.ui.notify('Removing chapter');

                  win.booktype.sendToCurrentBook({"command": "chapter_delete", 
                                                  "chapterID": chapter_id}, 
                                                  function() { 
                                                    win.booktype.ui.notify(); 
                                                    jquery("#removeChapter").modal('hide');        

                                                    // This is not the answer but it works for now
                                                    jquery('OL.sortable LI[data-id='+chapter_id+']').remove();
                                                  });
                }

              });

            //  new chapter

            jquery("#newChapter").on('show', function() {
              jquery("#newChapter INPUT").val('');  
            });

            jquery("#newChapter BUTTON.btn-primary").on('click', function() {
                var name = jquery("#newChapter INPUT").val();

                if(jquery.trim(name) === '') return;

                 win.booktype.sendToCurrentBook({"command": "create_chapter", 
                                                 "chapter": name}, 
                                                  function(data) {
                                                      // TODO
                                                      // - check for errors
                                                }); 

                jquery('#newChapter').modal('hide')
            });


             win.booktype.subscribeToChannel("/booktype/book/"+win.booktype.currentBookID+"/"+win.booktype.currentVersion+"/", function(message) {

              // TODO
              // CHECK IF WE ARE IN THIS PANEL, ONLY THEN DO TRANSFORMATIONS
                 var funcs = {
                     "change_status": function() {
                        var chap = win.booktype.editor.data.chapters.getChapterWithID(message.chapterID);
                        chap.status = message.statusID;

                        if(win.booktype.editor.getActivePanel().name == 'toc')
                            tocWidget.refresh();
                     },

                     "chapter_delete": function() {

                     },

                     "chapter_create": function() {
                          var c = new Chapter({'chapterID': message.chapter[0],
                                               'isSection': false,
                                               'title': message.chapter[1],
                                               'urlTitle': message.chapter[2],
                                               'status': message.chapter[4]
                                              });

                          win.booktype.editor.chapters().addChapter(c);

                          if(win.booktype.editor.getActivePanel().name == 'toc') {
                              var templateChapter = CREATE_CHAPTER(c);
                              // This is not how this should work
                              jquery('OL.sortable').append(templateChapter);
                          }
                     },   

                     "chapters_changed": function() {
                     },

                     "chapter_rename": function() {
                     },

                     "chapters_list": function() {
                     },

                  };

                 if(funcs[message.command]) {
                    funcs[message.command]();
                 }

             });
      
        }

    /*******************************************************************************/
    /* EXPORT                                                                      */
    /*******************************************************************************/

    return {'init': _init,
            'show': _show,
            'hide': _hide,
            'TOC': TOC,
            'Chapter': Chapter,
            'name': 'toc'};

  }();

  
})(window, jQuery);