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
      var _obsHold = null;

      /*******************************************************************************/
      /* MISC                                                                        */
      /*******************************************************************************/

      var getStatusName = function(statusID) {
                             var $s = jquery.grep(win.booktype.editor.data.statuses, function(v, i) { return v[0] == statusID;});

                             if($s.length > 0)
                                return $s[0][1];
                            
                              return '';
                          };  

      var sortableInit = function() {
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
                                startCollapsed: false,

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
                        } ;

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
                    this.observable = new Observable();

                    this.getChapterIndexWithID = function(cid) {                        
                        for(var i=0; i<this.chapters.length; i++) {
                          if(this.chapters[i].chapterID == cid)
                            return i;
                        }

                        return -1;
                    }


                    this.getChapterWithID = function(cid) {
                        return _.findWhere(this.chapters, {'chapterID': cid});
                    }

                    this.addChapter = function(chap) {
                      this.chapters.push(chap);
                      this.observable.emit('modified');
                    }

                    this.removeItem = function(cid) {
                      var i = this.getChapterIndexWithID(cid);
                      if(i !== -1) {
                          this.chapters.splice(i, 1);
                          this.observable.emit('modified');                                            
                      }
                    }

                    this.loadFromArray = function(arr) {
                      for(var i=0; i<arr.length; i++) {
                          var c = new Chapter({'chapterID': arr[i][0],
                                              'isSection': arr[i][3] != 1,
                                              'title': arr[i][1],
                                              'status': arr[i][4],
                                              'urlTitle': arr[i][2]});

                          this.addChapter(c);
                      }
                    }
                 };

      /*******************************************************************************/
      /* TABLE OF CONTENTS WIDGET                                                    */
      /*******************************************************************************/

      var CREATE_SECTION = function(item) {
                                sec = win.booktype.ui.getTemplate("templateTOCSection");
                                win.booktype.ui.fillTemplate(sec, {'title': win.booktype.utils.escapeJS(item.title)});
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

                             // Rename chapter
                             jquery('BUTTON.option-rename', sec).click(function() {
                                 jquery('#renameSection').modal('show');

                                 jquery('#renameSection INPUT[name=chapter_id]').val(item.chapterID);                                 
                                 jquery('#renameSection INPUT[name=chapter]').val(item.title);                                 

                                 return false;
                             });

                              jquery('BUTTON.option-delete', sec).on('click', function() {
                                  jquery('#removeSection').modal('show');

                                  jquery('#removeSection INPUT[name=chapter_id]').val(item.chapterID);                                 
                                  return false;
                              });

                              jquery('.disclose', sec).on('click', function() {
                                  jquery(this).closest('li').toggleClass('mjs-nestedSortable-collapsed').toggleClass('mjs-nestedSortable-expanded');
                              });

                                return sec;
                           };

      var CREATE_CHAPTER = function(item) {
                             var templateChapter = win.booktype.ui.getTemplate("templateTOCChapter");
                             win.booktype.ui.fillTemplate(templateChapter, {'title': win.booktype.utils.escapeJS(item.title)});

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

                            jquery('A.option-hold', templateChapter).on('click', function() {
                                win.booktype.ui.notify('Sending data');    

                                win.booktype.sendToCurrentBook({"command": "chapter_hold", 
                                                                "chapterID": item.chapterID},
                                                                function() { 
                                                                  win.booktype.ui.notify();    
                                                                });                                
                                return false;
                            });

                            // Delete chapter
                             jquery('A.option-delete', templateChapter).click(function() {
                                 jquery('#removeChapter').modal('show');

                                 jquery('#removeChapter INPUT[name=chapter_id]').val(item.chapterID);                                 
                                 return false;
                             });

                             // Rename chapter
                             jquery('A.option-rename', templateChapter).click(function() {
                                 jquery('#renameChapter').modal('show');

                                 jquery('#renameChapter INPUT[name=chapter_id]').val(item.chapterID);                                 
                                 jquery('#renameChapter INPUT[name=chapter]').val(item.title);                                 

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
                            var $html = $sortie.wrapInner(s);
                            jquery("#content").empty().append($html);

                            sortableInit();
                         };

                         this.removeItem = function(item) {
                            var $li = jquery("LI[data-id="+item.chapterID+"]");

                            $li.remove();
                         }

                         this.refreshItem = function(item) {
                            // TODO
                              var $li = jquery("LI[data-id="+item.chapterID+"]");

                              jquery('.title', $li).html(win.booktype.utils.escapeJS(item.title));
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
          tabs = [];
          if(win.booktype.editor.isEnabledTab('toc', 'hold')) {
              var t2 = win.booktype.editor.createRightTab('hold-tab', 'big-icon-hold');
              t2.onActivate = function() {
                  var tb = jquery("section[source_id=hold-tab]");

                  var holdBtnGroup = "<div class=\"btn-group\">" + 
                      "<button id=\"expand\" class=\"btn btn-mini option-hold\" rel=\"tooltip\" data-placement=\"bottom\" data-original-title=\"Unhold\">" +
                      "<i class=\"icon-arrow-left\"><\/i>" +
                      "<\/button>" +
                      "<button id=\"collapse\" class=\"btn btn-mini option-delete\" rel=\"tooltip\" data-placement=\"bottom\" data-original-title=\"Delete\">" +
                      "<i class=\"icon-trash\"><\/i>" +
                      "<\/button>" +
                      "<\/div>";

                  jquery("UL.hold-chapters", tb).empty();
                  _.each(win.booktype.editor.data.holdChapters.chapters, function(v) {
                      var $d = jquery("<li><div>"+v.title+"</div></li>");
                      $d.hover(
                          function() {                
                              jquery(this).append(holdBtnGroup);

                              // This should not be on the global level
                              jquery('[rel=tooltip]').tooltip();

                              jquery('BUTTON.option-delete', jquery(this)).on('click', function() {
                                     jquery('#removeChapter').modal('show');

                                     jquery('#removeChapter INPUT[name=chapter_id]').val(v.chapterID);    
                              });

                              jquery('BUTTON.option-hold', jquery(this)).on('click', function() {
                                        win.booktype.ui.notify('Sending data');    

                                        win.booktype.sendToCurrentBook({"command": "chapter_unhold", 
                                                                        "chapterID": v.chapterID},
                                                                        function() { 
                                                                          win.booktype.ui.notify();    
                                                                        });                                
                                        return false;
                                    });


                          },
                          function() {
                              jquery(this).find('div.btn-group').remove();
                          }
                      );



                      jquery("UL.hold-chapters", tb).append($d);                  
                  });
              };          

              // Refresh this tab when list of hold chapters has changed
              _obsHold = win.booktype.editor.data.holdChapters.observable.on('modified', function() {  t2.onActivate(); });
              tabs.push(t2);
          }

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

          if(_obsHold) {
            win.booktype.editor.data.holdChapters.observable.off(_obsHold);
          }
        }

        /*******************************************************************************/
        /* INIT                                                                        */
        /*******************************************************************************/

        var _init = function() {
            jquery("#button-toc").on('click', function(e) { win.booktype.editor.showTOC(); });

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

                  if(jquery.trim(chapter_id) === '') return;

                  win.booktype.sendToCurrentBook({"command": "chapter_delete", 
                                                  "chapterID": chapter_id}, 
                                                  function() { 
                                                    win.booktype.ui.notify(); 
                                                    jquery("#removeChapter").modal('hide');        
                                                  });
                }

              });

            // remove section
            jquery("#removeSection").on('show', function() {
               jquery("#removeSection .btn-primary").prop('disabled', true); 
               jquery("#removeSection INPUT[name=understand]").prop('checked', false);
            });

            jquery("#removeSection .close-button").on('click', function() {
              jquery("#removeSection").modal('hide');
            })

            jquery("#removeSection INPUT[name=understand]").on('change', function() {
               var $this = jquery(this);

               jquery("#removeSection .btn-primary").prop('disabled', !$this.is(':checked'));
            });

            jquery("#removeSection .btn-primary").on('click', function() {
              if(jquery("#removeSection INPUT[name=understand]:checked").val() == 'on') {
                  var chapter_id = jquery("#removeSection INPUT[name=chapter_id]").attr("value");
                  win.booktype.ui.notify('Removing chapter');

                  if(jquery.trim(chapter_id) === '') return;

                  win.booktype.sendToCurrentBook({"command": "section_delete", 
                                                  "chapterID": chapter_id}, 
                                                  function() { 
                                                    win.booktype.ui.notify(); 
                                                    jquery("#removeSection").modal('hide');        
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

            //  new chapter

            jquery("#newSection").on('show', function() {
              jquery("#newSection INPUT").focus().val('');  
            });

            jquery("#newSection BUTTON.btn-primary").on('click', function() {
                var name = jquery("#newSection INPUT").val();

                if(jquery.trim(name) === '') return;

                 win.booktype.sendToCurrentBook({"command": "create_section", 
                                                 "chapter": name}, 
                                                  function(data) {
                                                    console.log('evo ti ga na');
                                                      // TODO
                                                      // - check for errors
                                                }); 

                jquery('#newSection').modal('hide')
            });

            // Rename chapter
            jquery("#renameChapter BUTTON.btn-primary").on('click', function() {
                var name = jquery("#renameChapter INPUT[name=chapter]").val();
                var chapter_id = jquery("#renameChapter INPUT[name=chapter_id]").attr("value");

                if(jquery.trim(name) === '') return;
                 win.booktype.sendToCurrentBook({"command": "chapter_rename", 
                                                  "chapterID": chapter_id,
                                                  "chapter": name}, 
                                                  function(data) {
                                                    console.log('evo ti ga na');
                                                      // TODO
                                                      // - check for errors
                                                }); 

                jquery('#renameChapter').modal('hide')
            });

            // Rename section
            jquery("#renameSection BUTTON.btn-primary").on('click', function() {
                var name = jquery("#renameSection INPUT[name=chapter]").val();
                var chapter_id = jquery("#renameSection INPUT[name=chapter_id]").attr("value");

                if(jquery.trim(name) === '') return;
                 win.booktype.sendToCurrentBook({"command": "section_rename", 
                                                  "chapterID": chapter_id,
                                                  "chapter": name}, 
                                                  function(data) {
                                                    console.log('evo ti ga na');
                                                      // TODO
                                                      // - check for errors
                                                }); 

                jquery('#renameSection').modal('hide')
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

                     "chapter_hold": function() {
                        var chap = _.clone(win.booktype.editor.data.chapters.getChapterWithID(message.chapterID));

                        // should not use draw here
                        if(win.booktype.editor.getActivePanel().name == 'toc') {
                            tocWidget.removeItem(chap);
                        }

                        win.booktype.editor.data.holdChapters.addChapter(chap);
                        win.booktype.editor.data.chapters.removeItem(message.chapterID);

                     },

                     "chapter_unhold": function() {
                        var chap = _.clone(win.booktype.editor.data.holdChapters.getChapterWithID(message.chapterID));

                        win.booktype.editor.data.chapters.addChapter(chap);
                        win.booktype.editor.data.holdChapters.removeItem(message.chapterID);

                        // should not use draw here
                        if(win.booktype.editor.getActivePanel().name == 'toc') 
                            tocWidget.draw();                        
                     },

                     "section_delete": function() {
                          var c1 = win.booktype.editor.data.chapters.getChapterWithID(message.chapterID);

                          if(win.booktype.editor.getActivePanel().name == 'toc') {
                            tocWidget.removeItem(c1);
                          }

                          win.booktype.editor.data.chapters.removeItem(message.chapterID);                          
                     },

                     "chapter_delete": function() {
                          // TODO:
                          // check if it is in hold chapters maybe
                            var c1 = win.booktype.editor.data.chapters.getChapterWithID(parseInt(message.chapterID));

                            if(win.booktype.editor.getActivePanel().name == 'toc') {
                                 tocWidget.removeItem(c1);
                            }


                            win.booktype.editor.data.chapters.removeItem(message.chapterID);
                            win.booktype.editor.data.holdChapters.removeItem(message.chapterID);
                     },

                     "chapter_create": function() {
                          if(win.booktype.editor.getActivePanel().name != 'toc') return;

                          var c = new Chapter({'chapterID': message.chapter[0],
                                               'isSection': message.chapter[3] != 1,
                                               'title': message.chapter[1],
                                               'urlTitle': message.chapter[2],
                                               'status': message.chapter[4]
                                              });

                          win.booktype.editor.data.chapters.addChapter(c);

                          if(win.booktype.editor.getActivePanel().name == 'toc') {
                             var templateChapter;

                             if(message.chapter[3] == 1)
                                templateChapter = CREATE_CHAPTER(c);
                              else {
                                templateChapter = CREATE_SECTION(c);
                                templateChapter.addClass("mjs-nestedSortable-leaf mjs-nestedSortable-collapsed");
                              }

                              // This is not how this should work
                              jquery('OL.sortable').append(templateChapter);
                          }
                     },   

                     "chapters_changed": function() {
                     },

                     "chapter_rename": function() {
                        var c1 = win.booktype.editor.data.chapters.getChapterWithID(parseInt(message.chapterID));
                        var c2 = win.booktype.editor.data.holdChapters.getChapterWithID(parseInt(message.chapterID));

                        if(c1)
                            c1.title = message.chapter;

                        if(c2)    
                            c2.title = message.chapter;

                        if(win.booktype.editor.getActivePanel().name != 'toc') return;

                        tocWidget.refresh();
                     },

                     "section_rename": function() {
                        var c1 = win.booktype.editor.data.chapters.getChapterWithID(message.chapterID);

                        if(c1)
                            c1.title = message.chapter;

                        if(win.booktype.editor.getActivePanel().name != 'toc') return;

                        tocWidget.refresh();
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