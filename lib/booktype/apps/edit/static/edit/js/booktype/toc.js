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
      radix = 10, // this for parseInt
      detailViewOn = true;

    /*******************************************************************************/
    /* MISC                                                                        */
    /*******************************************************************************/

    var getStatusName = function (statusID) {
      var $s = _.filter(win.booktype.editor.data.statuses, function (v, i) { return v[0] === statusID; });

      if ($s.length > 0) {
        return $s[0][1];
      }

      return "";
    };

    var getStatusColor = function (statusID) {
      var $s = _.filter(win.booktype.editor.data.statuses, function (v, i) { return v[0] === statusID; });

      if ($s.length > 0) {
        return $s[0][2];
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
            // prevent from nesting section inside ot another sections
            if (parent !== null && parent.hasClass("section") && $item.hasClass("section")) {
              return false;
            }

            // We will probably in the future have some kind of validation system also
            // Not just the user defined one
            if (!_.isUndefined(win.booktype.editor.data.settings.config["toc"]["sortable"]["is_allowed"])) {
              return win.booktype.editor.data.settings.config["toc"]["sortable"]["is_allowed"](placeholder, parent, $item);
            }
            return true;
          },
          update: function (event, ui) {

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
        "toc": "toc"
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

    var drawChapterEditLock = function (chapterItem, chapterTemplate) {
      /**
       Update chapter view regarding edit lock.
       If chapter under edit at the moment,
       display needed elements, opposite - hide them.

       :Args:
       - chapterItem (:class:`Backbone.Model`): Chapter instance
       - chapterTemplate (:class:`object`): jQuery object instance
       */

      if (chapterItem.isUnderEdit()) {
        // If chapter hasn't allready editby information
        if (!jquery(".edit-by", chapterTemplate).length) {
          jquery(".btn-group", chapterTemplate).hide();
          jquery(".status", chapterTemplate).hide();
          jquery(".terminate-edit-chapter", chapterTemplate).show();
          jquery("a.operation-edit", chapterTemplate).css("pointer-events", "none");

          // create username profile link
          var icon = jquery('<span>').attr({class: 'fa fa-pencil'});
          var profileLink = jquery("<a>").attr({
            href: "/accounts/" + chapterItem.get("editBy") + "/",
            class: "edit-by label label-info",
            target: "_blank"
          });
          profileLink.html(icon).append("&nbsp;" + chapterItem.get("editBy"));
          jquery(".btn-toolbar .chapter-labels", chapterTemplate).append(profileLink);
        }
      } else {
        jquery(".btn-group", chapterTemplate).show();
        jquery(".status", chapterTemplate).show();
        jquery(".terminate-edit-chapter", chapterTemplate).hide();
        jquery("a.operation-edit", chapterTemplate).css("pointer-events", "");
        jquery(".edit-by", chapterTemplate).remove();
      }
    };

    var drawHoldChapterEditLock = function (chapterItem, chapterTemplate) {
      /**
       Update hold chapter view regarding edit lock.
       If chapter under edit at the moment,
       display needed elements, opposite - hide them.

       :Args:
       - chapterItem (:class:`Backbone.Model`): Chapter instance
       - chapterTemplate (:class:`object`): jQuery object instance
       */

      if (chapterItem.isUnderEdit()) {
        // If chapter hasn't allready editby information
        if (!jquery(".edit-by", chapterTemplate).length) {
          jquery(".btn-group", chapterTemplate).hide();
          jquery(".terminate-edit-chapter", chapterTemplate).show();

          // create username profile link
          var icon = jquery("<span>").attr({class: "fa fa-pencil"});
          var profileLink = jquery("<a>").attr({
            href: "/accounts/" + chapterItem.get("editBy") + "/",
            class: "edit-by label label-primary",
            target: "_blank"
          });
          profileLink.html(icon).append("&nbsp;" + chapterItem.get("editBy"));
          jquery(".chapter-labels", chapterTemplate).append(profileLink);
        }
      } else {
        jquery(".btn-group", chapterTemplate).show();
        jquery(".terminate-edit-chapter", chapterTemplate).hide();
        jquery(".edit-by", chapterTemplate).remove();
      }
    };

    /*******************************************************************************/
    /* USER                                                                        */
    /*******************************************************************************/

    var User = Backbone.Model.extend({
      defaults: {
        username: "",
        firstName: "",
        lastName: "",
        email: "",
        isSuperuser: false,
        isStaff: false,
        isAdmin: false,
        isBookOwner: false,
        isBookAdmin: false,
        permissions: []
      },
      hasPerm: function (perm) {
        /**
         Check user permissions.
         This method will also check if user is admin. In case
         user is admin, it will get any kind of permissions they ask for.

         :Example:
         window.booktype.currentUser.hasPerm('edit.add_comment')

         :Args:
         - perm (:class:`string`): permission to check for in {app_name}.{perm_name} format

         :Returns:
         true or false.
         */

        return this.get("isAdmin") === true || _.indexOf(this.get("permissions"), perm) !== -1;
      }
    });

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
        lockType: null,
        lockUsername: null,
        parentID: "root",
        tocID: null,
        state: "normal",
        editBy: null,
        hasComments: false,
        hasMarker: false
      },
      isLocked: function () {
        // 0 - unlocked,
        // 1 - locked from everyone,
        // 2 - simple lock
        var locked = 0;
        return this.get("lockType") !== locked;
      },
      isUnderEdit: function () {
        // "normal" - chapter not edit now,
        // "edit" - chapter is under edit now,
        var edit = "edit";
        return this.get("state") === edit;
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
        return _.find(this.chapters, function (elem) {
          return elem.get("chapterID") === parseInt(cid, radix) && elem.get("isSection") !== true;
        });
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
            "lockType": arr[i][5],
            "lockUsername": arr[i][6],
            "parentID": arr[i][7],
            "tocID": arr[i][8],
            "state": arr[i][9],
            "editBy": arr[i][10]
          });
          this.addChapter(c);
        }
      },

      loadFromTocDict: function (arr) {
        var self = this;
        arr.forEach(function (item) {
          var c = new Chapter(item);
          self.addChapter(c);
        });
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

      // apply view mode
      if (detailViewOn) {
        sec.toggleClass("detail-switch");
      }

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

      // Sections settings
      jquery("BUTTON.option-settings", sec).click(function () {
        jquery("#section-settings INPUT[name=section_id]").val(item.get("chapterID"));
        jquery("#section-settings").modal("show");

        return false;
      });

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

    var CREATE_CHAPTER = function (item, template) {
      var tmpl = (typeof(template) === 'undefined') ? jquery("#templateTOCChapter").html() : template;

      var renderedChapter = _.template(tmpl)({
        "data_id": item.get("tocID"),
        "id": "list_" + item.get("tocID"),
        "data_chapter_id": item.get("chapterID"),
        "title": win.booktype.utils.escapeJS(item.get("title")),
        "is_locked": item.isLocked(),
        "item_status": item.get("status"),
        "assigned": item.get("assigned"),
        "statuses": win.booktype.editor.data.statuses,
        "checked_statuses": item.get("checked_statuses"),
        "lock_type": item.get("lockType"),
        "lock_username": item.get("lockUsername"),
        "username": win.booktype.username,
        "hasComments": item.get("hasComments"),
        "hasMarker": item.get("hasMarker")
      });

      // convert from rendered html to native DOM and then to jquery object
      var templateChapter = jquery(jquery.trim(renderedChapter));

      // edit lock
      drawChapterEditLock(item, templateChapter);

      // terminate link available only for book owner or superuser
      if (jquery(".terminate-edit-chapter", templateChapter).length) {
        jquery("a.terminate-edit-chapter", templateChapter).click(function () {
          win.booktype.ui.notify(win.booktype._("terminate_editing", "Terminate editing."));
          win.booktype.sendToCurrentBook({
              "command": "chapter_kill_editlock",
              "chapterID": item.get("chapterID")
            },
            function () {
              win.booktype.ui.notify();
            }
          );
          return false;
        });
      }

      // apply view mode
      if (detailViewOn) {
        templateChapter.toggleClass("detail-switch");
      }

      jquery(".operation-edit", templateChapter).click(function () {
        win.booktype.editor.editChapter(item.get("chapterID"));

        return false;
      });

      jquery("BUTTON.edit", templateChapter).click(function () {
        win.booktype.editor.editChapter(item.get("chapterID"));
      });

      // Change status
      jquery(".btn-toolbar .btn-group ul.status-options a", templateChapter).click(function (e) {
        var $this = jquery(this),
          statusID = parseInt($this.closest("A").attr("data-status-id")),
          oldStatusID = item.status;

        item.set("status", statusID);
        $this.closest("ul.status-options").find("li.selected").removeClass("selected");
        $this.parent("li").addClass("selected");

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

      // enable selectize plugin to make the selection neat :)
      jquery(".toc-chapter-detail select[name='assign_user']", templateChapter).selectize({
        create: true,
        closeAfterSelect: true,

        onChange: function (username) {
          var $this = jquery(this);

          win.booktype.ui.notify(win.booktype._("assign_user", "Assigning user"));

          win.booktype.sendToCurrentBook({
            "command": "assign_chapter",
            "chapterID": item.get("chapterID"),
            "username": username
          },
            function (data) {
              win.booktype.ui.notify();

              // let's update the local item
              if (data.result) {
                item.set("assigned", data.assigned);
              }

              tocWidget.refresh();

              // Trigger events
              jquery(document).trigger("booktype-document-chapter-assigned", [item, data.assigned]);
            }
          );
        }
      });

      // mark status as un/checked (from dropdown and direct from current status checkbox)
      jquery("input[name='mark_status']", templateChapter).click(function (e) {
        var $this = jquery(this),
          statusID = parseInt($this.val()),
          checkedState = $this.is(":checked");

        win.booktype.ui.notify(win.booktype._("status_checked", "Saving status"));

        win.booktype.sendToCurrentBook({
          "command": "status_checked",
          "chapterID": item.get("chapterID"),
          "statusID": statusID,
          "checkedState": checkedState
        },
          function (data) {
            win.booktype.ui.notify();

            // let's update the local item
            if (data.result) {
              item.set("checked_statuses", data.checked_statuses);

              // check other checkbox related to same status and chapter
              // for example, check direct from status name, so update dropdown checkbox
              jquery("input[name='mark_status'][value=" + statusID +  "]", templateChapter)
                .attr('checked', checkedState);
            }

            tocWidget.refresh();

            // Trigger events
            jquery(document).trigger("booktype-document-status-checked", [item, statusID]);
          }
        );
      });

      _renderStatus(item, templateChapter);

      jquery("A.option-hold", templateChapter).on("click", function () {
        win.booktype.ui.notify(win.booktype._("sending_data", "Sending data."));

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

      // lock for everyone
      jquery("A.option-lock-everyone", templateChapter).on("click", function () {
        win.booktype.ui.notify(win.booktype._("sending_data", "Sending data."));

        win.booktype.sendToCurrentBook({
            "command": "chapter_lock",
            "chapterID": item.get("chapterID"),
            "lockType": 1
          },
          function () {
            win.booktype.ui.notify();
          }
        );
        return false;
      });

      // lock simple
      jquery("A.option-lock-simple", templateChapter).on("click", function () {
        win.booktype.ui.notify(win.booktype._("sending_data", "Sending data."));

        win.booktype.sendToCurrentBook({
            "command": "chapter_lock",
            "chapterID": item.get("chapterID"),
            "lockType": 2
          },
          function () {
            win.booktype.ui.notify();
          }
        );
        return false;
      });

      // unlock
      jquery("A.option-unlock, button.unlock", templateChapter).on("click", function () {
        win.booktype.ui.notify(win.booktype._("sending_data", "Sending data."));
        win.booktype.sendToCurrentBook({
            "command": "chapter_unlock",
            "chapterID": item.get("chapterID")
          },
          function () {
            win.booktype.ui.notify();
          }
        );
        return false;
      });

      // export chapter content
      jquery("A.option-export", templateChapter).on("click", function (e) {
        e.preventDefault();

        win.booktype.ui.notify(win.booktype._("loading_data"));
        win.booktype.sendToCurrentBook({
            "command": "export_chapter_html",
            "chapterID": item.get("chapterID")
          },
          function (data) {
            var $modalElem = $("#exportContentDialog");
            $modalElem.data({
              'chapterID': item.get("chapterID"),
              'urlTitle': item.get("urlTitle")
            });

            $modalElem.find('textarea').val(jquery.trim(data.content));
            $modalElem.find('.chapterTitle').text(": " + item.get("title"));
            $modalElem.modal('show');

            win.booktype.ui.notify();
          }
        );
      });

      // import to chapter action
      jquery("A.option-import", templateChapter).on("click", function (e) {
        e.preventDefault();

        var OVERWRITE = "overwrite";
        var APPEND = "append";
        var ALLOWED_MODES = [OVERWRITE, APPEND];

        var uploadDocxForm = jquery('#uploadDocxForm');
        var actionUrl = uploadDocxForm.data('action')
        actionUrl = actionUrl.replace('chapter-pk-to-replace', item.get("chapterID"));

        uploadDocxForm.attr('action', actionUrl);

        // custom template to avoid more html and have custom buttons
        var alertTemplate = $('.template.templateAlertModal').clone().removeClass('template');
        var overrideBtn = alertTemplate.find('.btn.btn-default');
        overrideBtn
          .removeClass('btn-default')
          .addClass('btn-primary');

        var importCallback = function (mode) {
          var importMode = mode ? APPEND : OVERWRITE;
          uploadDocxForm.find('input[name=import_mode]').val(importMode)
          uploadDocxForm.find('input[type=file]')
            .val('')
            .trigger("click");
        };

        // check if default mode was provided for the instance
        var defaultMode = uploadDocxForm.find('[name=upload_docx_default_mode]').val();
        if (defaultMode.trim().length > 0 && ALLOWED_MODES.indexOf(defaultMode) > -1) {
          importCallback(defaultMode);
          return;
        }

        win.booktype.utils.confirm({
          alertTitle: win.booktype._('choose_import_mode'),
          message: win.booktype._('how_should_import_content'),
          width: 370,
          acceptText: win.booktype._('append_label'),
          cancelText: win.booktype._('overwrite_label'),
          showCloseButton: true,
          customTemplate: alertTemplate
        }, importCallback);
      });

      return templateChapter;
    };

    // just small helper to avoid redundant code
    var _renderStatus = function (item, template) {
      var statusID = item.get("status");
      var statusLabel = getStatusName(statusID);
      var statusColor = getStatusColor(statusID);
      var uniqueID = booktype.utils.uuid4();

      if (!item.get('isSection')) {
        var checkedStatuses = item.get('checked_statuses');
        var statusChecked = checkedStatuses.indexOf(statusID) !== -1;

        // let's set the color, then label and checkbox status and value
        jquery(".toc-chapter-detail .status", template)
          .css("background-color", statusColor);

        jquery(".toc-chapter-detail .status label", template)
          .attr("for", uniqueID)
          .text(statusLabel);

        jquery(".toc-chapter-detail .status input[type=checkbox]", template)
          .val(statusID)
          .attr({
            id: uniqueID,
            checked: statusChecked
          });

        // let's update checked statuses in dropdown
        var statusDropdown = jquery(".dropdown-menu.status-options", template);
        $.each(checkedStatuses, function (idx, statusID) {
          statusDropdown.find("[name=mark_status][value=" + statusID + "]").prop("checked", true);
        });
      }
    };

    var TOCWidget = function () {

      this.draw = function () {
        var lst = win.booktype.editor.data.chapters.chapters,
          orphans = [],
          sec = null;

        if (!lst) { return; }

        var $chapContainer = jquery('#templateTOCChapterContainer').html();
        // convert from rendered html to native DOM and then to jquery object
        $chapContainer = jquery(jquery.trim($chapContainer));

        _.each(lst, function (item) {
          var createFunc = (item.get("isSection") === true) ? CREATE_SECTION : CREATE_CHAPTER;
          sec = createFunc(item);

          if (item.get("parentID") === "root") {
            $chapContainer.append(sec);
          } else {
            var parentID = item.get("parentID");
            var parent = $chapContainer.find("#list_" + parentID + " > ol");
            (parent.length === 0) ? orphans.push(sec) : parent.append(sec);
          }
        });

        jquery("#content div.toc").empty().append($chapContainer);

        // todo think about permissions in js retrieved from edit_config.html
        if ($chapContainer.hasClass("allow-reorder")){
          sortableInit();
        } else {
          // add classes for displaying arrows for sections and expand section by default
          jquery("li.section", $chapContainer).addClass("mjs-nestedSortable-branch mjs-nestedSortable-expanded");
        }

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
        var $li = jquery("LI[data-id=" + item.get("tocID") + "]");

        var chapterTitle = win.booktype.utils.escapeJS(item.get("title"));
        var hasComments = item.get('hasComments') ? $("#templateChapterHasComments").html() : '';
        var hasMarker = item.get('hasMarker') ? $("#templateChapterHasMarker").html() : '';

        jquery(".title", $li).html(chapterTitle);

        // marker icons like comments and [[ ]] sign
        jquery(".toc-chapter-detail .icons", $li).html(hasComments + hasMarker);

        // let's render status with checkbox and all that
        _renderStatus(item, $li);

        jquery("ul.status-options li", $li).removeClass("selected");
        jquery("ul.status-options a[data-status-id='" + item.get("status") + "']", $li).parent().addClass("selected");

        // edit lock
        drawChapterEditLock(item, $li);
      };

      this.recreateItem = function (item) {
        /**
         Create new chapter html, add new bindings and events.
         Replace current chapter with new one.

         :Args:
         - item (:class:`Backbone.Model`): Chapter instance
         */

        var $li = jquery("LI[data-id=" + item.get("tocID") + "]");
        $li.replaceWith(CREATE_CHAPTER(item));
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

    var HoldWidget = function () {

      this.draw = function () { throw new Error("Not implemented"); };
      this.removeItem = function (item) { throw new Error("Not implemented"); };
      this.refresh = function () { throw new Error("Not implemented"); };

      this.refreshItem = function (item) {
        var $li = jquery("ul.hold-chapters li[id=" + item.get("chapterID") + "]");
        // edit lock
        drawHoldChapterEditLock(item, $li);
      };
    };

    var holdWidget = new HoldWidget();

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

      if (deleteChildren === undefined) deleteChildren = "off";

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
        detailViewOn = !detailViewOn;
      });

      if (detailViewOn) {
        jquery("#detail-switch").toggleClass("active");
      }

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
          var holdBtnGroupTemplate = _.template(jquery('#templateHoldButtonGroup').html());
          var tb = jquery("section[source_id=hold-tab]");
          jquery("UL.hold-chapters", tb).empty();

          _.each(win.booktype.editor.data.holdChapters.chapters, function (chap) {
            var holdBtnGroup = jquery(jquery.trim(holdBtnGroupTemplate({
              "is_locked": chap.isLocked(),
              "lock_type": chap.get("lockType"),
              "lock_username": chap.get("lockUsername"),
              "username": win.booktype.username
            })));

            holdBtnGroup.hide();

            // edit
            jquery("BUTTON.option-edit", holdBtnGroup).on("click", function () {
              win.booktype.editor.editChapter(chap.get("chapterID"));
              return false;
            });

            // delete
            jquery("BUTTON.option-delete", holdBtnGroup).on("click", function () {
              jquery("#removeChapter").modal("show");

              jquery("#removeChapter INPUT[name=chapter_id]").val(chap.get("chapterID"));
            });

            // unhold
            jquery("BUTTON.option-hold", holdBtnGroup).on("click", function () {
              jquery(this).tooltip("destroy");

              win.booktype.ui.notify(win.booktype._("sending_data", "Sending data"));

              win.booktype.sendToCurrentBook({
                  "command": "chapter_unhold",
                  "chapterID": chap.get("chapterID")
                },
                function () {
                  win.booktype.ui.notify();

                  // Trigger event
                  jquery(document).trigger("booktype-document-unhold", [chap]);
                }
              );
              return false;
            });

            var $li = jquery("<li id=" + chap.get("chapterID") + "><div>" + chap.get("title") + "</div></li>");
            // Similar to toc, create template and add events only once.
            // On hover only do hide/show
            $li.append(holdBtnGroup);
            $li.hover(function () {
                jquery(this).find("div.btn-toolbar").show();
                // This should not be on the global level
                jquery("[rel=tooltip]").tooltip({container: "body"});
              },
              function () {
                jquery(this).find("div.btn-toolbar").hide();
              }
            );

            // edit lock
            drawHoldChapterEditLock(chap, $li);

            // terminate link available only for book owner or superuser
            if (jquery(".terminate-edit-chapter", $li).length) {
              jquery("a.terminate-edit-chapter", $li).click(function () {
                win.booktype.ui.notify(win.booktype._("terminate_editing", "Terminate editing."));
                win.booktype.sendToCurrentBook({
                    "command": "chapter_kill_editlock",
                    "chapterID": chap.get("chapterID")
                  },
                  function () {
                    win.booktype.ui.notify();
                  }
                );
                return false;
              });
            }

            jquery("UL.hold-chapters", tb).append($li);

          });
        };

        // Refresh this tab when list of hold chapters has changed
        _obsHold = function () { t2.onActivate(); };

        win.booktype.editor.data.holdChapters.on("modified", _obsHold);

        tabs.push(t2);
      }

      jquery("#section-settings .wizard-section-settings").steps({
        headerTag: "h3",
        bodyTag: "section",
        transitionEffect: "slideLeft",
        autoFocus: true,
        enableAllSteps: true,
        enableFinishButton: true,
        showFinishButtonAlways: true,

        onFinished: function() {
          var $dialog = jquery("#section-settings");
          var sectionID = $dialog.find("input[name='section_id']").val();

          var $target = $dialog.find("form");

          // serialize form values base jquery.serialize-object.min library
          var settings = new FormSerializer($, $target)
            .addPairs($target.serializeArray())
            // add unchecked value
            .addPairs(
              $target.find(':checkbox[name]:not(:checked)')
              .toArray()
              .map(function (checkbox) { return {name: checkbox.name, value: false} })
            )
            .serialize();

          win.booktype.ui.notify(win.booktype._("sending_data"));
          win.booktype.sendToCurrentBook({
            "command": "section_settings_set",
            "section_id": sectionID,
            "settings": settings
          }, function() {
            win.booktype.ui.notify();
            $dialog.modal("hide");
          });
        },
        labels: {
          next: win.booktype._("next", "Next"),
          previous: win.booktype._("previous", "Previous"),
          finish: win.booktype._("export_save", "Save")
        }
      });

      // on section settings modal hidden
      jquery(document).on("hidden.bs.modal", "#section-settings", function () {
        var $dialog = $(this);
        $dialog.find("form")[0].reset();
        $dialog.find("form input[name^='show_in_outputs']").attr("disabled", true);
      });

      // on section settings modal shown
      jquery(document).on("show.bs.modal", "#section-settings", function () {
        var $dialog = jquery(this);
        var sectionID = $dialog.find("input[name='section_id']").val();

        win.booktype.sendToCurrentBook({
          "command": "section_settings_get",
          "section_id": sectionID
        },
          function (data) {
            if (data.result) {
              var settings = data.settings;

              _.each(settings["show_in_outputs"], function (value, key) {
                var selector = "input#id_" + key + "_checkbox";
                $dialog.find(selector).prop("checked", value);
              });

              // set values for each section on TOC options
              _.each(settings["toc"], function (value, key) {
                var selector = "#id_" + key + "_toc";
                $dialog.find(selector).val(value);
              });

              // set mark_section_as as option
              var markAs = settings.mark_section_as;

              // if markAs is not created, we default to mainmatter
              if (typeof markAs === "undefined")
                markAs = "mainmatter";

              $dialog.find("#id_" + markAs).prop("checked", true);

              // set custom mark if any
              $dialog.find("[name='custom_mark']").val(settings.custom_mark);

              $dialog.find("form input[name^='show_in_outputs']").attr("disabled", false);
            }
          }
        );
      });

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

      jquery("#section-settings .wizard-section-settings").steps("destroy");

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

      jquery("#exportContentDialog").on("shown.bs.modal", function () {
        var textArea = $(this).find("textarea");
        textArea
          .focus()
          .scrollTop(0);
      });

      jquery("#exportContentDialog .download").on("click", function () {
        var $modalElem = $("#exportContentDialog");
        var content = $modalElem.find("textarea").val();
        var filename = $modalElem.data("urlTitle") + "_content.html";

        win.booktype.utils.download(content, filename, 'text/html');
      });

      jquery("#exportContentDialog .edit").on("click", function () {
        var chapterID = $("#exportContentDialog").data("chapterID");
        win.booktype.editor.editChapter(chapterID);
      });

      // bind input file in uploadDocxForm and submit
      jquery(document).on("change", "#uploadDocxForm input[type=file]", function () {
        var form = $(this).closest("form");
        var formData = new FormData(form[0]);
        var urlAction = form.attr("action");

        // notify things
        win.booktype.ui.notify(window.booktype._("sending_data"));
        var notify = win.booktype.utils.notification;

        // submit form with file for import
        $.ajax({
          url: urlAction,
          type: 'POST',
          data: formData,
          async: false,
          success: function (data) {
            var _60secs = 60*1000;

            // let's show the warnings if any
            data.warnings.forEach(function (warnMsg) {
              notify(warnMsg, "", { type: "warning", delay: _60secs });
            });

            if (data.url) {
              var successTitle = win.booktype._("doc_imported_successfully");
              notify(successTitle, "", { type: "success", delay: _60secs })

              // if callback was set to uploadDocxForm, we use it. Otherwise we just redirect.
              // This is tricky but the easier way right now.
              var uploadCallback = form.attr("data-upload-callback");
              if (typeof window[uploadCallback] === "function")
                window[uploadCallback](data);
              else
                win.location.href = data.url;

            } else {
              // let's show the warnings if any
              data.errors.forEach(function (errMsg) {
                notify(errMsg, "", { type: "danger", icon: "fa fa-exclamation-triangle", delay: _60secs });
              });
            }

            win.booktype.ui.notify()
          },
          cache: false,
          contentType: false,
          processData: false
        });
      });

      win.booktype.subscribeToChannel("/booktype/book/" + win.booktype.currentBookID + "/" + win.booktype.currentVersion + "/",
        function (message) {
          // TODO
          // CHECK IF WE ARE IN THIS PANEL, ONLY THEN DO TRANSFORMATIONS
          var funcs = {
            "change_status": function () {
              var chap = win.booktype.editor.data.chapters.getItemWithChapterID(message.chapterID);
              chap.set('status', message.statusID);

              if (win.booktype.editor.getActivePanel().name === "toc") {
                tocWidget.refresh();
              }
            },

            "chapter_state": function () {
              var chap;
              var widget;

              // if chapter in toc
              chap = win.booktype.editor.data.chapters.getItemWithChapterID(message.chapterID);

              widget = tocWidget;

              // if chapter in hold area
              if (!chap) {
                chap = win.booktype.editor.data.holdChapters.getItemWithChapterID(message.chapterID);
                widget = holdWidget;
              }

              chap.set('state', message.state);
              chap.set('editBy', message.username || null);

              var chapterItem = message.chapterItem || null;
              if (chapterItem) {
                chap.set('hasComments', chapterItem.hasComments || false);
                chap.set('hasMarker', chapterItem.hasMarker || false);
                chap.set('status', chapterItem.statusID);
                chap.set('checked_statuses', chapterItem.checked_statuses);
              }

              if (win.booktype.editor.getActivePanel().name !== "toc") { console.log("Returning since it's not TOC"); return; }

              widget.refreshItem(chap);
            },

            "chapter_hold": function () {

              var chap = _.clone(win.booktype.editor.data.chapters.getTocItemWithID(message.tocID));

              // should not use draw here
              if (win.booktype.editor.getActivePanel().name === "toc") {
                tocWidget.removeItem(chap);
              }

              // for now after unhold chapters should display in the end of toc root
              chap.set("parentID", "root");

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

            "chapter_lock_changed": function () {
              var chap = win.booktype.editor.data.chapters.getItemWithChapterID(message.chapterID);

              chap.set("lockType", message.lockType);
              if (chap.isLocked()) {
                chap.set("lockUsername", message.lockUsername);
              } else {
                chap.set("lockUsername", null);
              }

              if (win.booktype.editor.getActivePanel().name !== "toc") { return; }

              // Recreating chapter.
              // Using refresh item in this case produce very complex logic.
              tocWidget.recreateItem(chap);
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
                "title": message.chapter[1],
                "urlTitle": message.chapter[2],
                "isSection": message.chapter[3] !== 1,
                "status": message.chapter[4],
                "lockType": message.chapter[5],
                "lockUsername": message.chapter[6],
                "parentID": message.chapter[7],
                "tocID": message.chapter[8],
                "state": message.chapter[9],
                "editBy": message.chapter[10],
                "checked_statuses": message.chapter[11]
              });

              if (message.chapter[8] === null) {
                // chapter on hold (without toc)
                win.booktype.editor.data.holdChapters.addChapter(c);
              } else {
                // chapter/section in the toc
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

            "chapters_list": function () {},

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

            "theme_changed": function () {
              // editor
              if (win.booktype.editor.getCurrentChapterID()) {
                var themeChangedModal = jquery('#themeChangedModal');

                themeChangedModal.find('button').click(function () {
                  if (this.dataset.action === 'apply') {
                    win.booktype.editor.themes.setTheme(message.theme);
                  } else {
                    win.booktype.editor.data.activeTheme = message.theme;
                  }
                  themeChangedModal.modal('hide');
                });

                themeChangedModal.modal('show');
              }
              // toc
              else {
                win.booktype.editor.themes.setTheme(message.theme);
              }
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
      "User": User,

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
