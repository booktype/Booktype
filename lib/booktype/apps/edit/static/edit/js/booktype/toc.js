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
  "use strict";

	jquery.namespace("win.booktype.editor.toc");

  win.booktype.editor.toc = (function () {

    var tabs = [],
      _obsHold = null,
      radix = 10; // this for parseInt

    /*******************************************************************************/
    /* MISC                                                                        */
    /*******************************************************************************/

    var getStatusName = function (statusID) {
      var $s = jquery.grep(win.booktype.editor.data.statuses, function (v, i) { return v[0] === statusID; });

      if ($s.length > 0) {
        return $s[0][1];
      }
    
      return "";
    };

    var reoderTOC = function (newOrder) {
      var lst = [];

      _.each(newOrder, function (item) {
        var c = win.booktype.editor.data.chapters.getTocItemWithID(item[0]);
        var clonedItem = _.clone(c);
        var parentID = (item[1] === "root") ? "root" : parseInt(item[1], radix);
        clonedItem.set("parentID", parentID);
        lst.push(clonedItem);
      });

      return lst;
    };

    var sortableInit = function () {
        jquery("ol.sortable").nestedSortable({
          attribute: "id",
          forcePlaceholderSize: true,
          handle: "div",
          helper: "clone",
          items: "li.item",
          opacity: 0.6,
          placeholder: "placeholder",
          revert: 250,
          tabSize: 25,
          tolerance: "pointer",
          toleranceElement: "> div",
          maxLevels: 10,
          disableNestingClass: "chapter",
          connectWith: ".hold-target-box",
          rootID: "root",
          isTree: true,
          expandOnHover: 700,
          startCollapsed: false,
          isAllowed: function (placeholder, parent, $item) {
            // We will probably in the future have some kind of validation system also
            // Not just the user defined one
            if (!_.isUndefined(win.booktype.editor.data.settings.config["toc"]["sortable"]["is_allowed"])) {
              return win.booktype.editor.data.settings.config["toc"]["sortable"]["is_allowed"](placeholder, parent, $item);
            }
            return true;
          },
          stop: function (event, ui) {
            var result = jquery(this).nestedSortable("toArray", {startDepthCount: 0, excludeRoot: true});

            win.booktype.sendToCurrentBook({
              "command": "chapters_changed",
              "chapters": result,
              "hold": [],
              "kind": "order",
              "chapter_id": null
            },
              function () {
                var lst = _.map(result, function (elem) { return [elem["item_id"], elem["parent_id"]]; });
                win.booktype.editor.data.chapters.chapters = reoderTOC(lst);
                win.booktype.ui.notify();

                // Trigger events
                jquery(document).trigger("booktype-toc-reorder");
              });

            return true;
          }
        });
      };

    var TocRouter = Backbone.Router.extend({
      routes: {
        "toc":      "toc",
      },

      toc: function () {
        var activePanel = win.booktype.editor.getActivePanel();

        activePanel.hide(function () {
          win.booktype.editor.data.activePanel = win.booktype.editor.data.panels["toc"];
          win.booktype.editor.data.activePanel.show();
        });
      }
    });

    var router = new TocRouter();

    /*******************************************************************************/
    /* CHAPTER                                                                     */
    /*******************************************************************************/

    var Chapter = Backbone.Model.extend({
      defaults: {
        chapterID: null,
        title: "",
        urlTitle: "",
        isSection: false,
        status: null,
        parentID: "root",
        tocID: null
      }
    });

    /*******************************************************************************/
    /* TABLE OF CONTENTS                                                           */
    /*******************************************************************************/

    // Now it is a list but it should be a Tree
    
    var TOC = function () { };

    _.extend(TOC.prototype, Backbone.Events, {
      chapters: [],

      getChapterIndexWithID: function (cid) {
        for (var i = 0; i < this.chapters.length; i++) {
          if (this.chapters[i].get("chapterID") === parseInt(cid, radix)) {
            return i;
          }
        }

        return -1;
      },

      getTocItemWithID: function (cid) {
        return _.find(this.chapters, function (elem) { return elem.get("tocID") === parseInt(cid, radix); });
      },

      getItemWithChapterID: function (cid) {
        return _.find(this.chapters, function (elem) { return elem.get("chapterID") === parseInt(cid, radix); });
      },

      addChapter: function (chap) {
        this.chapters.push(chap);
        this.modified();
      },

      clear: function () {
        this.chapters = [];
      },

      modified: function () {
        this.trigger("modified");
      },

      removeItem: function (cid) {
        var i = this.getChapterIndexWithID(cid);
        if (i !== -1) {
          this.chapters.splice(i, 1);
          this.modified();
        }
      },

      loadFromArray: function (arr) {
        for (var i = 0; i < arr.length; i++) {
          var c = new Chapter({
            "chapterID": arr[i][0],
            "title": arr[i][1],
            "urlTitle": arr[i][2],
            "isSection": arr[i][3] !== 1,
            "status": arr[i][4],
            "parentID": arr[i][5],
            "tocID": arr[i][6]
          });

          this.addChapter(c);
        }
      },

      removeChildren: function (parentID) {
        var self = this;
        _.each(this.chapters, function (item) {
          if (item.get("parentID") === parseInt(parentID, radix)) {
            self.removeItem(item.get("chapterID"));
          }
        });
      },

      moveChildrenToRoot: function (parentID) {
        _.each(this.chapters, function (item) {
          if (item.get("parentID") === parseInt(parentID, radix)) {
            item.set("parentID", "root");
          }
        });
      }

    });

    /*******************************************************************************/
    /* TABLE OF CONTENTS WIDGET                                                    */
    /*******************************************************************************/

    var CREATE_SECTION = function (item) {
      var sec = win.booktype.ui.getTemplate("templateTOCSection");
      win.booktype.ui.fillTemplate(sec, {"title": win.booktype.utils.escapeJS(item.get("title"))});
      sec.attr("data-id", item.get("tocID"));
      sec.attr("id", "list_" + item.get("tocID"));

      // hover for the menu
      jquery("div", sec).hover(
        function () {
          jquery(this).parent().find("div.btn-toolbar:first").show();
        },
        function () {
          jquery(this).parent().find("div.btn-toolbar:first").hide();
        }
      );

      jquery(".btn-toolbar", sec).hover(
        function () {
          jquery(this).closest("li.item").find("div:first").toggleClass("hover-effect");
        },
        function () {
          jquery(this).closest("li.item").find("div:first").toggleClass("hover-effect");
        }
      );

      // Rename chapter
      jquery("BUTTON.option-rename", sec).click(function () {
        jquery("#renameSection").modal("show");

        jquery("#renameSection INPUT[name=chapter_id]").val(item.get("chapterID"));
        jquery("#renameSection INPUT[name=chapter]").val(item.get("title"));

        return false;
      });

      jquery("BUTTON.option-delete", sec).on("click", function () {
        jquery("#removeSection").modal("show");

        jquery("#removeSection INPUT[name=chapter_id]").val(item.get("chapterID"));
        return false;
      });

      jquery(".disclose", sec).on("click", function () {
        jquery(this).closest("li").toggleClass("mjs-nestedSortable-collapsed").toggleClass("mjs-nestedSortable-expanded");
      });

      return sec;
    };

    var CREATE_CHAPTER = function (item) {
      var templateChapter = win.booktype.ui.getTemplate("templateTOCChapter");
      win.booktype.ui.fillTemplate(templateChapter, {"title": win.booktype.utils.escapeJS(item.get("title"))});

      templateChapter.attr("data-id", item.get("tocID"));
      templateChapter.attr("id", "list_" + item.get("tocID"));
      templateChapter.attr("data-chapter-id", item.get("chapterID"));

      // hover for the menu
      jquery("div", templateChapter).hover(
        function () {
          jquery(this).parent().find("div.btn-toolbar:first").show();
        },
        function () {
          jquery(this).parent().find("div.btn-toolbar:first").hide();
        }
      );
        
      jquery(".btn-toolbar", templateChapter).hover(
        function () {
          jquery(this).closest("li.item").find("div:first").toggleClass("hover-effect");
        },
        function () {
          jquery(this).closest("li.item").find("div:first").toggleClass("hover-effect");
        }
      );

      jquery(".operation-edit", templateChapter).click(function () {
        win.booktype.editor.editChapter(item.get("chapterID"));
          
        return false;
      });

      jquery("BUTTON.edit", templateChapter).click(function () {
        win.booktype.editor.editChapter(item.get("chapterID"));
      });

      // Insert status names
      var $l = [];
      jquery.each(win.booktype.editor.data.statuses, function (i, v) {
        var $a = jquery("<a />").attr({"href": "#", "data-status-id": v[0]}).text(v[1]);

        $l.push(jquery("<li/>").wrapInner($a));
      });

      jquery(".btn-toolbar .btn-group:first ul.status-options", templateChapter).append($l);

      // Change status
      jquery(".btn-toolbar .btn-group:first ul.status-options a", templateChapter).click(function (e) {
        var $this = jquery(this),
          statusID = $this.closest("A").attr("data-status-id"),
          oldStatusID = item.status;

        item.status = statusID;

        win.booktype.ui.notify(win.booktype._("set_status", "Set status."));

        win.booktype.sendToCurrentBook({
          "command": "change_status",
          "chapterID": item.get("chapterID"),
          "statusID": statusID
        },
          function () {
            win.booktype.ui.notify();

            $this.closest("DIV").trigger("click");
            tocWidget.refresh();

            // Trigger events
            jquery(document).trigger("booktype-document-status", [item, oldStatusID, statusID]);
          }
        );

        return false;
      });

      // check from the locks
      jquery(".toc-chapter-detail .username", templateChapter).html("");
      jquery(".toc-chapter-detail .status", templateChapter).html(getStatusName(item.get("status")));

      jquery("A.option-hold", templateChapter).on("click", function () {
        win.booktype.ui.notify("Sending data");

        win.booktype.sendToCurrentBook({
          "command": "chapter_hold",
          "chapterID": item.get("chapterID")
        },
          function () {
            win.booktype.ui.notify();

            // Trigger event
            jquery(document).trigger("booktype-document-hold", [item]);
          }
        );

        return false;
      });

      // Delete chapter
      jquery("A.option-delete", templateChapter).click(function () {
        jquery("#removeChapter").modal("show");

        jquery("#removeChapter INPUT[name=chapter_id]").val(item.get("chapterID"));
        return false;
      });

      // Rename chapter
      jquery("A.option-rename", templateChapter).click(function () {
        jquery("#renameChapter INPUT[name=toc_id]").val(item.get("tocID"));
        jquery("#renameChapter INPUT[name=chapter]").val(item.get("title"));

        jquery("#renameChapter").modal("show");
        return false;
      });

      return templateChapter;
    };

    var TOCWidget = function () {

      this.draw = function () {
        var lst = win.booktype.editor.data.chapters.chapters,
          orphans = [],
          sec = null;

        if (!lst) { return; }

        var $sortie = jquery(document.createElement("ol"));
        $sortie.addClass("sortable");

        _.each(lst, function (item) {
          var createFunc = (item.get("isSection") === true) ? CREATE_SECTION : CREATE_CHAPTER;
          sec = createFunc(item);

          if (item.get("parentID") === "root") {
            $sortie.append(sec);
          } else {
            var parentID = item.get("parentID");
            var parent = $sortie.find("#list_" + parentID + " > ol");
            (parent.length === 0) ? orphans.push(sec) : parent.append(sec);
          }
        });

        jquery("#content div.toc").empty().append($sortie);

        sortableInit();

        this._checkForEmptyTOC();
      };

      this._checkForEmptyTOC = function () {
        if (_.isUndefined(win.booktype.editor.data.chapters.chapters)) { return; }

        if (win.booktype.editor.data.chapters.chapters.length === 0) {
          jquery("#edit-info").removeClass("template");
        } else {
          if (!jquery("#edit-info").hasClass("template")) {
            jquery("#edit-info").addClass("template");
          }
        }
      };

      this.removeItem = function (item) {
        var $li = jquery("LI[data-id=" + item.get("tocID") + "]");

        $li.remove();
      };

      this.refreshItem = function (item) {
        // TODO
        var $li = jquery("LI[data-id=" + item.get("tocID") + "]");

        jquery(".title", $li).html(win.booktype.utils.escapeJS(item.get("title")));
        jquery(".toc-chapter-detail .status", $li).html(getStatusName(item.get("status")));
      };

      this.refresh = function () {
        var $this = this,
          lst = win.booktype.editor.data.chapters.chapters;

        jquery.each(lst, function (i, item) {
          $this.refreshItem(item);
        });

        this._checkForEmptyTOC();
      };
    };

    var tocWidget = new TOCWidget();

    /*******************************************************************************/
    /* EVENTS                                                                      */
    /*******************************************************************************/

    var expandChapters = function () {
      jquery(".sortable li.mjs-nestedSortable-collapsed").removeClass("mjs-nestedSortable-collapsed").addClass("mjs-nestedSortable-expanded");
    };

    var collapseChapters = function () {
      jquery(".sortable li.mjs-nestedSortable-expanded").removeClass("mjs-nestedSortable-expanded").addClass("mjs-nestedSortable-collapsed");
    };

    var _doDeleteChapter = function (chapterID) {
      var $d = jquery.Deferred();

      win.booktype.sendToCurrentBook({
        "command": "chapter_delete",
        "chapterID": chapterID
      },
        function (data) {
          win.booktype.ui.notify();

          // Trigger event
          jquery(document).trigger("booktype-document-deleted", [chapterID]);
          $d.resolve(data);
        }
      );

      return $d.promise();
    };

    var _doDeleteSection = function (sectionID, deleteChildren) {
      var $d = jquery.Deferred();

      if (deleteChildren === undefined) deleteChildren = 'off';

      win.booktype.sendToCurrentBook({
        "command": "section_delete",
        "chapterID": sectionID,
        "deleteChildren": deleteChildren
      },
        function (data) {
          win.booktype.ui.notify();

          // Trigger event
          var doc = win.booktype.editor.getChapterWithID(sectionID);

          jquery(document).trigger("booktype-section-deleted", [doc]);

          $d.resolve(data);
        }
      );

      return $d.promise();
    };

    var _doCreateChapter = function (name) {
      var $d = jquery.Deferred();

      win.booktype.sendToCurrentBook({
        "command": "create_chapter",
        "chapter": name
      },
        function (data) {
          // TODO:
          //   - check for errors

          if (!data.created) {
            if (!_.isUndefined(data["chapter_exists"])) {
              alert(win.booktype._("chapter_exists", "Chapter with this title already exists."));
            } else {
              alert(win.booktype._("chapter_couldnt_create", "Couldn't create chapter."));
            }
          } else {
            // Trigger event
            jquery(document).trigger("booktype-document-created", [data["chapter_id"], name]);
          }
          $d.resolve(data);
        }
      );

      return $d.promise();
    };

    var _doCreateSection = function (name) {
      var $d = jquery.Deferred();

      win.booktype.sendToCurrentBook({
        "command": "create_section",
        "chapter": name
      },
        function (data) {
          // Trigger event
          if (!data.created) {
            if (!_.isUndefined(data["section_exists"])) {
              alert(win.booktype._("section_exists", "Section with this title already exists."));
            } else {
              alert(win.booktype._("section_couldnt_create", "Couldn't create section."));
            }
          } else {
            jquery(document).trigger("booktype-section-created", [data["chapter_id"], name]);
          }

          $d.resolve(data);
        }
      );

      return $d.promise();
    };

    var _doRenameChapter = function (tocID, name) {
      var $d = jquery.Deferred();

      win.booktype.sendToCurrentBook({
        "command": "chapter_rename",
        "tocID": tocID,
        "chapter": name
      },
        function (data) {
          var c = win.booktype.editor.getChapterWithID(tocID);

          // Trigger event                                                    
          jquery(document).trigger("booktype-document-rename", [c, c.get("title"), name]);

          $d.resolve(data);
        }
      );

      return $d.promise();
    };

    var _doRenameSection = function (sectionID, name) {
      var $d = jquery.Deferred();

      win.booktype.sendToCurrentBook({
        "command": "section_rename",
        "chapterID": sectionID,
        "chapter": name
      },
        function (data) {
          var c = win.booktype.editor.getChapterWithID(sectionID);

          // Trigger event                                                    
          jquery(document).trigger("booktype-section-rename", [c, c.get("title"), name]);

          $d.resolve(data);
        }
      );

      return $d.promise();
    };

    // MISC
    var _toc = function () {
      // ToC / Expand/Collapse
      jquery("#expand").click(function () {
        expandChapters();
      });
      jquery("#collapse").click(function () {
        collapseChapters();
      });

      // ToC / Chapter details switch
      jquery("#detail-switch").click(function () {
        jquery(".sortable li").toggleClass("detail-switch");
      });

      // Tooltip
      jquery("DIV.contentHeader [rel=tooltip]").tooltip({container: "body"});
    };

    /*******************************************************************************/
    /* SHOW                                                                        */
    /*******************************************************************************/

    var _show = function () {
      win.booktype.ui.notify("Loading");

      jquery("#button-toc").addClass("active");

      // set toolbar
      var t = win.booktype.ui.getTemplate("templateTOCToolbar");
      jquery("DIV.contentHeader").html(t);

      var t2 = win.booktype.ui.getTemplate("templateTOCContent");
      jquery("#content").html(t2);


      tocWidget.draw();
      _toc();

      expandChapters();

      // show panels on the side

      window.scrollTo(0, 0);

      // panels
      tabs = [];

      if (win.booktype.editor.isEnabledTab("toc", "hold")) {
        var t2 = win.booktype.editor.createRightTab("hold-tab", "big-icon-hold", win.booktype._("chapter_on_hold", "Chapters on Hold"));

        t2.onActivate = function () {
          var tb = jquery("section[source_id=hold-tab]"),
            _msgUnhold = win.booktype._("unhold", "Unhold"),
            _msgEdit = win.booktype._("edit", "EDIT").toUpperCase();

          var holdBtnGroup = "<div class=\"btn-toolbar float-right\"><div class=\"btn-group\">" +
            "<button id=\"expand\" class=\"btn btn-default btn-xs option-hold\" rel=\"tooltip\" data-placement=\"left\" data-original-title=\"" + _msgUnhold + "\">" +
            "<i class=\"icon-arrow-left\"><\/i>" +
            "<\/button>" +
            "<button id=\"collapse\" class=\"btn btn-default btn-xs option-delete\">" +
            "<i class=\"icon-trash\"><\/i>" +
            "<\/button>" +
            "<\/div>" +
            "<div class=\"btn-group\">" +
            "<button id=\"edit\" class=\"btn btn-default btn-xs option-edit\">" +
            _msgEdit +
            "<\/button>" +
            "<\/div>" +
            "<\/div>";

          jquery("UL.hold-chapters", tb).empty();

          _.each(win.booktype.editor.data.holdChapters.chapters, function (v) {
            var $d = jquery("<li id=" + v.get("chapterID") + "><div>" + v.get("title") + "</div></li>");

            $d.hover(function () {
              jquery(this).append(holdBtnGroup);

              // This should not be on the global level
              jquery("[rel=tooltip]").tooltip({container: "body"});

              jquery("BUTTON.option-edit", jquery(this)).on("click", function () {
                win.booktype.editor.editChapter(v.get("chapterID"));
                return false;
              });

              jquery("BUTTON.option-delete", jquery(this)).on("click", function () {
                jquery("#removeChapter").modal("show");

                jquery("#removeChapter INPUT[name=chapter_id]").val(v.get("chapterID"));
              });

              jquery("BUTTON.option-hold", jquery(this)).on("click", function () {
                jquery(this).tooltip("destroy");
                
                win.booktype.ui.notify(win.booktype._("sending_data", "Sending data"));

                win.booktype.sendToCurrentBook({
                  "command": "chapter_unhold",
                  "chapterID": v.get("chapterID")
                },
                  function () {
                    win.booktype.ui.notify();

                    // Trigger event
                    jquery(document).trigger("booktype-document-unhold", [v]);
                  }
                );

                return false;
              });

            },
              function () {
                jquery(this).find("div.btn-toolbar").remove();
              }
            );

            jquery("UL.hold-chapters", tb).append($d);
          });
        };

        // Refresh this tab when list of hold chapters has changed
        _obsHold = function () { t2.onActivate(); };

        win.booktype.editor.data.holdChapters.on("modified", _obsHold);

        tabs.push(t2);
      }

      win.booktype.editor.activateTabs(tabs);
      win.booktype.ui.notify();

      // Trigger events
      jquery(document).trigger("booktype-ui-panel-active", ["toc", this]);
    };

    /*******************************************************************************/
    /* HIDE                                                                        */
    /*******************************************************************************/

    var _hide = function (callback) {
      // Destroy tooltip
      jquery("DIV.contentHeader [rel=tooltip]").tooltip("destroy");
      jquery("#button-toc").removeClass("active");

      // Clear content
      jquery("#content").empty();
      jquery("DIV.contentHeader").empty();

      win.booktype.editor.deactivateTabs(tabs);
      win.booktype.editor.hideAllTabs();

      if (_obsHold) {
        win.booktype.editor.data.holdChapters.off("modified", _obsHold);
        _obsHold = null;
      }
        
      if (!_.isUndefined(callback)) {
        callback();
      }
    };

    /*******************************************************************************/
    /* INIT                                                                        */
    /*******************************************************************************/

    var _init = function () {
      jquery("#button-toc").on("click", function (e) { Backbone.history.navigate("toc", true); });

      // remove chapter
      jquery("#removeChapter").on("show.bs.modal", function () {
        jquery("#removeChapter .operation-remove").prop("disabled", true);
        jquery("#removeChapter INPUT[name=understand]").prop("checked", false);
      });


      jquery("#removeChapter .operation-close").on("click", function () {
        jquery("#removeChapter").modal("hide");
      });

      jquery("#removeChapter INPUT[name=understand]").on("change", function () {
        var $this = jquery(this);

        jquery("#removeChapter .operation-remove").prop("disabled", !$this.is(":checked"));
      });

      jquery("#removeChapter .operation-remove").on("click", function () {
        if (jquery("#removeChapter INPUT[name=understand]:checked").val() === "on") {
          var chapterID = jquery("#removeChapter INPUT[name=chapter_id]").val();

          win.booktype.ui.notify(win.booktype._("removing_chapter", "Removing chapter"));

          if (jquery.trim(chapterID) === "") { return; }

          var _do = win.booktype.editor.toc.doDeleteChapter(chapterID);

          jquery.when(_do).done(function (data) {
            if (data.status === true) {
              jquery("#removeChapter").modal("hide");
            }
          });
        }
      });

      // remove section
      jquery("#removeSection").on("show.bs.modal", function () {
        jquery("#removeSection .operation-remove").prop("disabled", true);
        jquery("#removeSection INPUT[name=understand]").prop("checked", false);
      });

      jquery("#removeSection .operation-cancel").on("click", function () {
        jquery("#removeSection").modal("hide");
      });

      jquery("#removeSection INPUT[name=understand]").on("change", function () {
        var $this = jquery(this);

        jquery("#removeSection .operation-remove").prop("disabled", !$this.is(":checked"));
      });

      jquery("#removeSection .operation-remove").on("click", function () {
        if (jquery("#removeSection INPUT[name=understand]:checked").val() === "on") {
          var sectionID = jquery("#removeSection INPUT[name=chapter_id]").attr("value");
          var deleteChildren = jquery("#removeSection INPUT[name=delete_children]:checked").val()
          win.booktype.ui.notify("Removing chapter");

          if (jquery.trim(sectionID) === "") { return; }

          var _do = win.booktype.editor.toc.doDeleteSection(sectionID, deleteChildren);
          
          jquery.when(_do).done(function (data) {
            if (data.status === true) {
              jquery("#removeSection").modal("hide");
            }
          });
        }
      });

      //  new chapter

      jquery("#newChapter").on("show.bs.modal", function () {
        jquery("#newChapter INPUT").val("");
      });

      jquery("#newChapter").on("shown.bs.modal", function () {
        jquery("#newChapter INPUT").focus();
      });

      jquery("#newChapter BUTTON.operation-create").on("click", function () {
        var name = jquery("#newChapter INPUT").val();

        if (jquery.trim(name) === "") { return; }

        var _do = win.booktype.editor.toc.doCreateChapter(name);

        jquery.when(_do).done(function (data) {
          if (data.status === true) {
            jquery("#newChapter").modal("hide");
          }
        });
      });

      //  new chapter

      jquery("#newSection").on("show.bs.modal", function () {
        jquery("#newSection INPUT").val("");
      });

      jquery("#newSection").on("shown.bs.modal", function () {
        jquery("#newSection INPUT").focus();
      });

      jquery("#newSection BUTTON.operation-create").on("click", function () {
        var name = jquery("#newSection INPUT").val();

        if (jquery.trim(name) === "") { return; }

        var _do = win.booktype.editor.toc.doCreateSection(name);

        jquery.when(_do).done(function (data) {
          if (data.status === true) {
            jquery("#newSection").modal("hide");
          }
        });
      });

      // Rename chapter
      jquery("#renameChapter BUTTON.operation-rename").on("click", function () {
        var name = jquery("#renameChapter INPUT[name=chapter]").val();
        var tocID = jquery("#renameChapter INPUT[name=toc_id]").attr("value");

        if (jquery.trim(name) === "") { return; }

        var _do = win.booktype.editor.toc.doRenameChapter(tocID, name);

        jquery.when(_do).done(function (data) {
          if (data.status === true) {
            jquery("#renameChapter").modal("hide");
          }
        });
      });

      // Rename section
      jquery("#renameSection BUTTON.operation-rename").on("click", function () {
        var name = jquery("#renameSection INPUT[name=chapter]").val();
        var sectionID = jquery("#renameSection INPUT[name=chapter_id]").attr("value");

        if (jquery.trim(name) === "") { return; }

        var _do = win.booktype.editor.toc.doRenameSection(sectionID, name);

        jquery.when(_do).done(function (data) {
          if (data.status === true) {
            jquery("#renameSection").modal("hide");
          }
        });
      });

      win.booktype.subscribeToChannel("/booktype/book/" + win.booktype.currentBookID + "/" + win.booktype.currentVersion + "/",
        function (message) {
          // TODO
          // CHECK IF WE ARE IN THIS PANEL, ONLY THEN DO TRANSFORMATIONS
          var funcs = {
            "change_status": function () {
              var chap = win.booktype.editor.data.chapters.getTocItemWithID(message.chapterID);
              chap.status = message.statusID;

              if (win.booktype.editor.getActivePanel().name === "toc") {
                tocWidget.refresh();
              }
            },

            "chapter_hold": function () {
              var chap = _.clone(win.booktype.editor.data.chapters.getTocItemWithID(message.tocID));

              // should not use draw here
              if (win.booktype.editor.getActivePanel().name === "toc") {
                tocWidget.removeItem(chap);
              }

              win.booktype.editor.data.holdChapters.addChapter(chap);
              win.booktype.editor.data.chapters.removeItem(message.chapterID);

              tocWidget._checkForEmptyTOC();
            },

            "chapter_unhold": function () {
              var chap = _.clone(win.booktype.editor.data.holdChapters.getItemWithChapterID(message.chapterID));
              chap.set("tocID", message.tocID);

              win.booktype.editor.data.chapters.addChapter(chap);
              win.booktype.editor.data.holdChapters.removeItem(message.chapterID);

              // should not use draw here
              if (win.booktype.editor.getActivePanel().name === "toc")  {
                tocWidget.draw();
              }

              tocWidget._checkForEmptyTOC();
            },

            "section_delete": function () {
              var c1 = win.booktype.editor.data.chapters.getTocItemWithID(message.chapterID);

              if (win.booktype.editor.getActivePanel().name === "toc") {
                tocWidget.removeItem(c1);
              }

              // and remove the section from toc items
              win.booktype.editor.data.chapters.removeItem(message.chapterID);
              
              // delete section chapters or move them to root item
              if (message.deleteChildren === 'on') {
                win.booktype.editor.data.chapters.removeChildren(message.chapterID);
              } else {
                win.booktype.editor.data.chapters.moveChildrenToRoot(message.chapterID);

                // now redraw toc
                tocWidget.draw();
              }

              tocWidget._checkForEmptyTOC();
            },

            "chapter_delete": function () {
              var sectionID = parseInt(message.chapterID, radix);
              var chap = win.booktype.editor.data.chapters.getItemWithChapterID(sectionID);

              if (win.booktype.editor.getActivePanel().name === "toc" && chap !== undefined) {
                tocWidget.removeItem(chap);
              }

              // this is in case chapter is in hold chapters panel
              var $chapterOnHold = jquery("UL.hold-chapters > li#" + message.chapterID);
              if ($chapterOnHold.length > 0) {
                $chapterOnHold.remove();
              }

              win.booktype.editor.data.chapters.removeItem(message.chapterID);
              win.booktype.editor.data.holdChapters.removeItem(message.chapterID);

              tocWidget._checkForEmptyTOC();
            },

            "chapter_create": function () {
              var c = new Chapter({
                "chapterID": message.chapter[0],
                "isSection": message.chapter[3] !== 1,
                "title": message.chapter[1],
                "urlTitle": message.chapter[2],
                "status": message.chapter[4],
                "parentID": message.chapter[5],
                "tocID": message.chapter[6]
              });

              win.booktype.editor.data.chapters.addChapter(c);

              if (win.booktype.editor.getActivePanel().name === "toc") {
                var templateChapter;

                if (message.chapter[3] === 1) {
                  templateChapter = CREATE_CHAPTER(c);
                } else {
                  templateChapter = CREATE_SECTION(c);
                  templateChapter.addClass("mjs-nestedSortable-leaf mjs-nestedSortable-collapsed");
                }

                // This is not how this should work
                jquery("OL.sortable").append(templateChapter);

                tocWidget._checkForEmptyTOC();
              }
            },

            "chapters_changed": function () {
              win.booktype.editor.data.chapters.chapters = reoderTOC(message.ids);
              win.booktype.editor.data.chapters.modified();

              tocWidget.draw();
            },

            "chapter_rename": function () {
              var c = win.booktype.editor.getChapterWithID(message.tocID);

              c.set("title", message.chapter);

              if (!_.isUndefined(message["chapter_url"])) {
                c.set("urlTitle", message["chapter_url"]);
              }

              win.booktype.editor.data.chapters.modified();
              win.booktype.editor.data.holdChapters.modified();

              if (win.booktype.editor.getActivePanel().name !== "toc") { return; }

              tocWidget.refresh();
            },

            "section_rename": function () {
              var c1 = win.booktype.editor.data.chapters.getTocItemWithID(message.chapterID);

              if (c1) {
                c1.set("title", message.chapter);
              }

              win.booktype.editor.data.chapters.modified();
              win.booktype.editor.data.holdChapters.modified();

              if (win.booktype.editor.getActivePanel().name !== "toc") { return; }

              tocWidget.refresh();
            },

            "chapters_list": function () {
            }
          };

          if (funcs[message.command]) {
            funcs[message.command]();
          }
        }
      );
    };

    /*******************************************************************************/
    /* EXPORT                                                                      */
    /*******************************************************************************/

    return {
      "init": _init,
      "show": _show,
      "hide": _hide,
      "refresh": function () { tocWidget.refresh(); },
      "redraw": function () {
        tocWidget.draw();
        _toc();
        expandChapters();
        window.scrollTo(0, 0);
      },
      "TOC": TOC,
      "Chapter": Chapter,

      "doRenameChapter": _doRenameChapter,
      "doRenameSection": _doRenameSection,
      "doCreateChapter": _doCreateChapter,
      "doCreateSection": _doCreateSection,
      "doDeleteChapter": _doDeleteChapter,
      "doDeleteSection": _doDeleteSection,

      "name": "toc"
    };
  })();

})(window, jQuery, _);