/*
  This file is part of Booktype.
  Copyright (c) 2012 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
 
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

  jquery.namespace('win.booktype.editor');
  
  /*
    Hold some basic variables and functions that are needed on global level and almost in all situations.
   */
  
  win.booktype.editor = (function () {

    // Default settings
    var DEFAULTS = {
      panels: {
        'edit': 'win.booktype.editor.edit',
        'toc' : 'win.booktype.editor.toc',
        'media' : 'win.booktype.editor.media'
      },

      styles: {
        'style1': '/static/edit/css/style1.css',
        'style2': '/static/edit/css/style2.css',
        'style3': '/static/edit/css/style3.css'
      },

      tabs: {
        'icon_generator': function (tb) {
          var tl = '';

          if (!_.isUndefined(tb.title)) {
            if (tb.isLeft) {
              tl = 'rel="tooltip" data-placement="right" data-original-title="' + tb.title + '"';
            } else {
              tl = 'rel="tooltip" data-placement="left" data-original-title="' + tb.title + '"';
            }
          }

          return '<a href="#" id="' + tb.tabID + '"' + tl + '><i class="' + tb.iconID + '"></i></a>';
        }
      },

      config: {
        'global': {
          'tabs': ['online-users', 'chat', 'notes']
        },

        'edit': {
          'tabs': ['chapters', 'attachments', 'history', 'style'],
          'toolbar': {
            'H': ['table-dropdown', 'unorderedList', 'orderedList'],
            'TABLE': ['unorderedList', 'orderedList', 'indent-left', 'indent-right'],
            'PRE': ['table-dropdown', 'alignLeft', 'alignRight', 'indent-left', 'indent-right',
              'alignCenter', 'alignJustify', 'unorderedList', 'orderedList'],
            'ALL': ['table-dropdown', 'alignLeft', 'alignRight',  'indent-left', 'indent-right',
              'alignCenter', 'alignJustify', 'unorderedList', 'orderedList', 'currentHeading',
              'heading-dropdown']
          },
          'menu': {
            'H': ['insertImage', 'insertLink', 'horizontalline', 'pbreak'],
            'TABLE': ['horizontalline', 'pbreak', 'indent-left', 'indent-right'],
            'PRE': ['insertImage', 'insertLink', 'horizontalline', 'pbreak', 'indent-left', 'indent-right'],
            'ALL': ['insertImage', 'insertLink', 'horizontalline', 'pbreak', 'indent-left', 'indent-right']
          }
        },
        'media': {
          'allowUpload': ['.jpe?g$', '.png$']
        },
        'toc': {
          'tabs': ['hold'],
          'sortable': {'is_allowed': function (placeholder, parent, item) { return true; } }
        },
        'history': {}
      }
    };

    // Our global data
    var data = {
      'chapters': null,
      'holdChapters': null,
      'statuses': null,

      'activeStyle': 'style1',
      'activePanel': null,
      'panels': null,

      'settings': {}
    };

    var EditorRouter = Backbone.Router.extend({
      routes: {
        'edit/:id': 'edit'
      },

      edit: function (id) {
        _editChapter(id);
      }
    });

    var router = new EditorRouter();

    // ID of the chapter which is being edited    
    var currentEdit = null;

    // TABS

    var tabs = [];

    var Tab = function (tabID, iconID) {
      this.tabID = tabID;
      this.iconID = iconID;
      this.domID = '';
      this.isLeft = false;
      this.isOnTop = false;
      this.title = '';
    };

    Tab.prototype.onActivate = function () {};
    Tab.prototype.onDeactivate = function () {};


    var hideAllTabs = function () {
      jquery('.right-tabpane').removeClass('open hold');
      jquery('body').removeClass('opentabpane-right');
      jquery('.right-tablist li').removeClass('active');

      jquery('.left-tabpane').removeClass('open hold');
      jquery('body').removeClass('opentabpane-left');
      jquery('.left-tablist li').removeClass('active');
    };

    // Right tab
    var createRightTab = function (tabID, iconID, title) {
      var tb = new Tab(tabID, iconID);

      tb.isLeft = false;
      tb.domID = '.right-tablist li #' + tabID;
      if (!_.isUndefined(title)) {
        tb.title = title;
      }

      return tb;
    };

    // Left tab
    var createLeftTab = function (tabID, iconID, title) {
      var tb = new Tab(tabID, iconID);

      tb.isLeft = true;
      tb.domID = '.left-tablist li #' + tabID;

      if (!_.isUndefined(title)) {
        tb.title = title;
      }

      return tb;
    };

    // Initialise all tabs
    var activateTabs = function (tabList) {
      var _gen = data.settings.tabs['icon_generator'];

      jquery.each(tabList, function (i, v) {
        if (!v.isLeft) {
          if (v.isOnTop && jquery('DIV.right-tablist UL.navigation-tabs li').length > 0) {
            jquery('DIV.right-tablist UL.navigation-tabs li:eq(0)').before('<li>' + _gen(v) + '</li>');
          } else {
            jquery('DIV.right-tablist UL.navigation-tabs').append('<li>' + _gen(v) + '</li>');
          }

          jquery(v.domID).click(function () {
            //close left side
            jquery('.left-tabpane').removeClass('open hold');
            jquery('body').removeClass('opentabpane-left');
            jquery('.left-tablist li').removeClass('active');
            // check if the tab is open
            if (jquery('#right-tabpane').hasClass('open')) {
              // if clicked on active tab, close tab
              if (jquery(this).closest('li').hasClass('active')) {
                jquery('.right-tabpane').toggleClass('open');
                jquery('.right-tabpane').removeClass('hold');
                jquery('.right-tabpane section').hide();
                jquery('body').toggleClass('opentabpane-right');
                jquery(this).closest('li').toggleClass('active');
              } else {
                // open but not active, switching content
                jquery(this).closest('ul').find('li').removeClass('active');
                jquery(this).parent().toggleClass('active');
                jquery('.right-tabpane').removeClass('hold');
                var target = jquery(this).attr('id');
                jquery('.right-tabpane section').hide();
                jquery('.right-tabpane section[source_id="' + target + '"]').show();
                var isHold = jquery(this).attr('id');

                if (isHold === 'hold-tab') {
                  jquery('.right-tabpane').addClass('hold');
                }

                v.onActivate();
              }
            } else {
              // if closed, open tab
              jquery('body').toggleClass('opentabpane-right');
              jquery(this).parent().toggleClass('active');
              jquery('.right-tabpane').toggleClass('open');
              var target = jquery(this).attr('id');
              jquery('.right-tabpane section').hide();
              jquery('.right-tabpane section[source_id="' + target + '"]').show();
              var isHold = jquery(this).attr('id');
              if (isHold === 'hold-tab') {
                jquery('.right-tabpane').addClass('hold');
              }

              v.onActivate();
            }

            return false;
          });
        } else {
          if (v.isOnTop && jquery('DIV.left-tablist UL.navigation-tabs li').length > 0) {
            jquery('DIV.left-tablist UL.navigation-tabs li:eq(0)').before('<li>' + _gen(v) + '</li>');
          } else {
            jquery('DIV.left-tablist UL.navigation-tabs').append('<li>' + _gen(v) + '</li>');
          }

          jquery(v.domID).click(function () {
            //close right side
            jquery('.right-tabpane').removeClass('open hold');
            jquery('body').removeClass('opentabpane-right');
            jquery('.right-tablist li').removeClass('active');
            // check if the tab is open
            if (jquery('#left-tabpane').hasClass('open')) {
              // if clicked on active tab, close tab
              if (jquery(this).closest('li').hasClass('active')) {
                jquery('.left-tabpane').toggleClass('open');
                jquery('.left-tabpane').removeClass('hold');
                jquery('.left-tabpane section').hide();
                jquery('body').toggleClass('opentabpane-left');
                jquery(this).closest('li').toggleClass('active');
              } else {
                // open but not active, switching content
                jquery(this).closest('ul').find('li').removeClass('active');
                jquery(this).parent().toggleClass('active');
                jquery('.left-tabpane').removeClass('hold');
                var target = jquery(this).attr('id');
                jquery('.left-tabpane section').hide();
                jquery('.left-tabpane section[source_id="' + target + '"]').show();
                var isHold = jquery(this).attr('id');

                if (isHold === 'hold-tab') {
                  jquery('.left-tabpane').addClass('hold');
                }
                v.onActivate();
              }
            } else {
              // if closed, open tab

              jquery('body').toggleClass('opentabpane-left');
              jquery(this).parent().toggleClass('active');
              jquery('.left-tabpane').toggleClass('open');
              //jquery('.right-tabpane').removeClass('open');
              var target = jquery(this).attr('id');
              jquery('.left-tabpane section').hide();
              jquery('.left-tabpane section[source_id="' + target + '"]').show();
              var isHold = jquery(this).attr('id');
              if (isHold === 'hold-tab') {
                jquery('.left-tabpane').addClass('hold');
              }
              v.onActivate();
            }

            return false;
          });
        }
      });

      jquery('DIV.left-tablist [rel=tooltip]').tooltip({container: 'body'});
      jquery('DIV.right-tablist [rel=tooltip]').tooltip({container: 'body'});
    };

    var deactivateTabs = function (tabList) {
      jquery('DIV.left-tablist [rel=tooltip]').tooltip('destroy');
      jquery('DIV.right-tablist [rel=tooltip]').tooltip('destroy');

      jquery.each(tabList, function (i, v) {
        if (v.isLeft) {
          jquery('DIV.left-tablist UL.navigation-tabs #' + v.tabID).remove();
        } else {
          jquery('DIV.right-tablist UL.navigation-tabs #' + v.tabID).remove();
        }
      });
    };

    // UTIL FUNCTIONS        
    var _editChapter = function (id) {
      win.booktype.ui.notify(win.booktype._('loading_chapter', 'Loading chapter.'));

      win.booktype.sendToCurrentBook({
        'command': 'get_chapter',
        'chapterID': id
      },
        function (dta) {
          currentEdit = id;

          var activePanel = win.booktype.editor.getActivePanel();

          activePanel.hide(function () {
            data.activePanel = data.panels['edit'];
            data.activePanel.setChapterID(id);

            jquery('#contenteditor').html(dta.content);
            data.activePanel.show();
            win.booktype.ui.notify();

            // Trigger events
            var doc = win.booktype.editor.getChapterWithID(id);
            jquery(document).trigger('booktype-document-loaded', [doc]);
          });
        }
      );
    };

    // Init UI
    var _initUI = function () {
      win.booktype.ui.notify();

      // History
      Backbone.history.start({pushState: false, root: '/' + win.booktype.currentBookURL + '/_edit/', hashChange: true});

      // Main menu collapsible
      jquery('.collapse-navigation a').click(function () {
          jquery('body').toggleClass('menu-open');
      });

      jquery('[rel=tooltip]').tooltip({
        container: 'body'
      });

      // This is a default route. Instead of doing it from the Router we do it this way so user could easily
      // change his default route from the booktype events.
      // This should probably be some kind of default callback.
      var match = win.location.href.match(/#(.*)$/);

      if (!match) {
        data.activePanel = data.panels['toc'];
        data.activePanel.show();
      }

      // Check configuration for this. Do not show it if it is not enabled.
      //
      // ONLINE USERS TAB
      if (isEnabledTab('global', 'online-users')) {
        var t1 = createLeftTab('online-users-tab', 'big-icon-online-users');
        t1.onActivate = function () {
        };

        tabs.push(t1);
      }

      // CHAT TAB
      // Only activate if it is enabled.
      if (isEnabledTab('global', 'chat')) {
        var t2 = createLeftTab('chat-tab', 'big-icon-chat');

        t2.draw = function () {
          var $this = this;
          var $container = jquery('section[source_id=chat-tab]');

          var scrollBottom = function () {
            var scrollHeight = jquery('.notification-list', $container)[0].scrollHeight;
            jquery('.notification-list', $container).scrollTop(scrollHeight);
          };

          $this.formatString = function (frm, args) {
            return frm.replace(/\{\{|\}\}|\{(\d+)\}/g,
              function (m, n) {
                if (m === '{{') { return '{'; }
                if (m === '}}') { return '}'; }
                return win.booktype.utils.escapeJS(args[n]);
              }
            );
          };

          $this.showJoined = function (notice) {
            var $joinedMsg = _.template(jquery("#templateUserJoined").html());
            jquery('.notification-list', $container).append(
              $joinedMsg({
                'avatar': getGravatar(notice.email), 
                'info': new Date().toLocaleString(),
                'username': notice.user_joined
              })
            );
            scrollBottom();
          };

          $this.showInfo = function (notice) {
            var $infoMsg = _.template('<li class="personal"><figure class="notification-avatar"><img src="<%= avatar %>"/></figure><div class="notification-content"><p class="notification-text"><%= message %></p><span class="notification-info"><%= info %></span></div></li>');

            if (typeof notice.message_id !== 'undefined') {
              jquery('.notification-list', $container).append(
                  $infoMsg({
                    'avatar': getGravatar(notice.email), 
                    'info': new Date().toLocaleString(),
                    'message': $this.formatString(win.booktype._('message_info_' + notice.message_id, ''), notice.message_args)
                  })
              );
              scrollBottom();
            }
          };

          $this.formatMessage = function (from, message, email, important) {
            var gravatar = ''; 
            if (email){
              gravatar = getGravatar(email);
            } 
            var $t = _.template('<li class="<% if (important) {%>important<% } %><% if (personal) {%>personal<% } %>"><figure class="notification-avatar"><img src="<%= avatar %>" ></figure><div class="notification-content"><p class="notification-text"><span class="notification-author"><%= user %>:</span> <%= message %></p><span class="notification-info"><%= info %></span></div></li>');
            return $t({
                'avatar': gravatar,
                'user': from,
                'message': win.booktype.utils.escapeJS(message),
                'info': new Date().toLocaleString(),
                'important': important,
                'personal': from === win.booktype.user
            });
          };

          $this.showMessage = function (from, message, email, important) {

            var isChatOpen = jquery('#chat-tab').parent().hasClass('active');
            if (!isChatOpen){
              //updates the notification count
              var count = 1;
              if (('#chat-tab > span').length > 0){
                //this might return a NaN
                count = parseInt(jquery('#chat-tab > span').text(), 10);
                if (count > 0){
                  count += 1;
                } else{
                  //NaN case
                  count = 1;
                }
              }
              var notificationTemplate = _.template('<span class="label label-success"><%= count %></span>');
              jquery('#chat-tab > span').remove();
              jquery('#chat-tab').append(notificationTemplate({'count': count}));
            } 
            jquery('.notification-list', $container).append($this.formatMessage(from, message, email, important));
            scrollBottom();
          };

          jquery('.notification-writer').focus(function () {
            jquery('.tab-content.chat').addClass('typing-active');
            scrollBottom();
          });

          jquery('.notification-write-box .cancel-notif').click(function (e) {
            jquery('.tab-content.chat').removeClass('typing-active');
            jquery('.notification-writer').val('').removeClass('important');
            scrollBottom();
            return false;
          });

          jquery('.notification-important').click(function (e) {
            jquery('.notification-writer').toggleClass('important');
          });

          jquery('.notification-write-box .send-notif').click(function (e) {
            var msg = jquery.trim(jquery('.notification-writer').val());

            if (msg !== '') {
              if (jquery('.notification-writer').hasClass('important')) {
                $this.showMessage(win.booktype.username, msg, win.booktype.email, true);
              } else {
                $this.showMessage(win.booktype.username, msg, win.booktype.email, false);
              }

              jquery('.tab-content.chat').removeClass('typing-active');
              var important = jquery('.notification-writer').hasClass('important'); 
              jquery('.notification-writer').val('').removeClass('important');

              win.booktype.sendToChannel('/chat/' + win.booktype.currentBookID + '/', {
                'command': 'message_send',
                'message': msg,
                'important': important
              },
                function () { }
              );
            }
            scrollBottom();
            return false;
          });
        };

        t2.onActivate = function () {
          //clears notifications
          jquery('#chat-tab > span').remove();
        };
        t2.draw();

        tabs.push(t2);
      }

      //NOTES TAB
      if (isEnabledTab('global', 'notes')) {
        var t3 = createLeftTab('notes-tab', 'big-icon-notes');

        t3.onActivate = function () {

          // Get the current book notes
          win.booktype.ui.notify(win.booktype._('loading_data', 'Loading data.'));
          
          win.booktype.sendToCurrentBook({
            'command': 'get_notes'
          },
            function(data) {
              if (data.notes.length > 0) {
                jquery('.notes-tab-content textarea').val(data.notes[0].notes);
              }
              win.booktype.ui.notify();
            }
          );

        };

        tabs.push(t3);
      }

      activateTabs(tabs);

      jquery(document).trigger('booktype-ui-finished');
    };

    var _addOnlineUser = function(user){
      var $container = jquery('section[source_id=online-users-tab] ul');
      var template = _.template(jquery('#templateOnlineUser').html());
      var gravatar = getGravatar(user.email);
      var fullname = user.first_name + ' ' + user.last_name; 
      //Find if the user is already there
      jquery('#username-' + user.username).remove();
      $container.append(template({username: user.username, fullname: fullname, 
                                  user_role: 'editor', gravatar: gravatar}));
    };

    var _loadInitialData = function () {
      win.booktype.ui.notify(win.booktype._('loading_data', 'Loading data.'));

      win.booktype.sendToCurrentBook({'command': 'init_editor'},
        function (dta) {
          // Put this in the TOC    
          data.chapters.clear();
          data.chapters.loadFromArray(dta.chapters);
          data.holdChapters.clear();
          data.holdChapters.loadFromArray(dta.hold);

          // Attachments are not really needed
          //attachments = dta.attachments;
          data.statuses = dta.statuses;
          var $container = jquery('section[source_id=online-users-tab] ul');
          $container.html('');
          jquery.map(dta.onlineUsers, _addOnlineUser);

          // Initislize rest of the interface
          _initUI();
        }
      );
    };

    var _reloadEditor = function () {
      var $d = jquery.Deferred();

      win.booktype.ui.notify('Loading data.');

      win.booktype.sendToCurrentBook({'command': 'init_editor'},
        function (dta) {
          // Put this in the TOC
          data.chapters.clear();
          data.chapters.loadFromArray(dta.chapters);
          data.holdChapters.clear();
          data.holdChapters.loadFromArray(dta.hold);

          // Attachments are not really needed
          //attachments = dta.attachments;
          data.statuses = dta.statuses;

          // if activePanel == toc then redraw()
          if (win.booktype.editor.getActivePanel().name === 'toc') {
            win.booktype.editor.getActivePanel().redraw();
          } else {
            Backbone.history.navigate('toc', true);
          }

          jquery.map(dta.onlineUsers, _addOnlineUser);

          win.booktype.ui.notify();

          $d.resolve();
        }
      );

      return $d.promise();
    };

    var _disableUnsaved = function () {
      jquery(win).bind('beforeunload', function (e) {
        // CHECK TO SEE IF WE ARE CURRENTLY EDITING SOMETHING
        return 'not saved';
      });
    };

    var _fillSettings = function (sett, opts) {
      if  (!_.isObject(opts)) { return opts; }

      _.each(_.pairs(opts), function (item) {
        var key = item[0],
          value = item[1];

        if (_.isObject(value) && !_.isArray(value)) {
          if (_.isFunction(value)) {
            sett[key] = value;
          } else {
            sett[key] = _fillSettings(sett[key], value);
          }
        } else {
          sett[key] = value;
        }
      });

      return sett;
    };

    var _initEditor = function (settings) {
      // Settings
      data.settings = _fillSettings(_.clone(DEFAULTS), settings);

      // Initialize Panels
      data.panels = {};

      _.each(settings.panels, function (pan, name) {
        data.panels[name] = eval(pan);
      });

      jquery.each(data.panels, function (i, v) { v.init(); });

      // initialize chapters
      data.chapters = new win.booktype.editor.toc.TOC();
      data.holdChapters = new win.booktype.editor.toc.TOC();

      //_disableUnsaved();

      // Subscribe to the book channel
      win.booktype.subscribeToChannel('/booktype/book/' + win.booktype.currentBookID + '/' + win.booktype.currentVersion + '/',
        function (message) {
          var funcs = {
            'user_status_changed': function () {
              jquery('#users .user' + message.from + '  SPAN').html(message.message);
              jquery('#users .user' + message.from).animate({backgroundColor: 'yellow'}, 'fast',
                function () {
                  jquery(this).animate({backgroundColor: 'white'}, 3000);
                });
            },
            'user_add': function () {
              _addOnlineUser(message);
            },

            'user_remove': function () {
              jquery("#username-" + message.username).remove();
            }
          };

          if (funcs[message.command]) {
            funcs[message.command]();
          }
        }
      );

      // Do not subscribe to the chat channel if chat is not enabled
      win.booktype.subscribeToChannel('/chat/' + win.booktype.currentBookID + '/',
        function (message) {
          if (message.command === 'user_joined') {
            if (tabs[1]) {
              tabs[1].showJoined(message);
            }
          }

          if (message.command === 'message_info') {
            if (tabs[1]) {
              tabs[1].showInfo(message);
            }
          }

          if (message.command === 'message_received') {
            if (tabs[1]) {
              tabs[1].showMessage(message.from, message.message, message.email, message.important);
            }
          }
        }
      );

      _loadInitialData();

      try {
        var matches = /#(.*?)\//g.exec(win.location.hash);
        if ( matches === null ) matches = /#(.*?)$/g.exec(window.location.hash);
        
        var hash = matches[1];
        jquery('#button-'+hash).parent().addClass('active');
      } catch(err) {
        jquery('#button-toc').parent().addClass('active');
      }
    };

    var embedActiveStyle = function () {
      var styleURL = data.settings.styles[data.activeStyle];

      jquery('#aloha-embeded-style').attr('href', styleURL);
    };

    var setStyle = function (sid) {
      data.activeStyle = sid;
      embedActiveStyle();
      
      jquery(document).trigger('booktype-style-changed', [sid]);
    };

    var isEnabledTab = function (panelName, tabName) {
      return _.contains(data.settings.config[panelName]['tabs'], tabName);
    };


    return {
      data: data,
      editChapter: function (id) { Backbone.history.navigate('edit/' + id, true); },

      getCurrentChapterID: function () { return currentEdit; },
      getChapterWithID: function (cid) {
        var d = data.chapters.getTocItemWithID(cid);

        if (_.isUndefined(d)) {
          d = data.holdChapters.getTocItemWithID(cid);
        }

        return d;
      },

      setStyle: setStyle,
      embedActiveStyle: embedActiveStyle,

      isEnabledTab: isEnabledTab,

      initEditor: _initEditor,
      reloadEditor: _reloadEditor,

      getActivePanel: function () {
        if (data.activePanel) {
          return data.activePanel;
        }

        return {'name': 'unknown', 'hide': function (c) { c(); }};
      },

      hideAllTabs: hideAllTabs,
      activateTabs: activateTabs,
      deactivateTabs: deactivateTabs,
      createLeftTab: createLeftTab,
      createRightTab: createRightTab
    };
  })();

})(window, jQuery, _);
