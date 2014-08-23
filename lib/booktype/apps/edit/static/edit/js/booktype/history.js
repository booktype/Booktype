(function (win, $) {
  'use strict';
  
  $.namespace('win.booktype.editor.history');

  win.booktype.editor.history = (function () {

    var self = this;
    var HistoryRouter = Backbone.Router.extend({
      initialize: function () {
        this.routesHit = 0;
        Backbone.history.on('route', function () { this.routesHit++; }, this);
      },

      back: function () {
        if (this.routesHit > 1) {
          win.history.back();
        } else {
          this.navigate('history', {trigger: true, replace: true});
        }
      },

      routes: {
        'history': 'history',
        'history/page/:pageid': 'showPage',
        'history/:chapter': 'chapterHistory',
        'history/:chapter/rev/:revid': 'viewRevision'
      },

      history: function () {
        var activePanel = win.booktype.editor.getActivePanel();

        activePanel.hide(function () {
          win.booktype.editor.data.activePanel = win.booktype.editor.data.panels['history'];
          win.booktype.editor.data.activePanel.show();
        });
      },

      chapterHistory: function (chapter) {
        renderHeader();
        $('#content').load(win.booktype.editor.historyURL + chapter);
      },

      viewRevision: function (chapter, revid) {
        renderHeader();
        $('#content').load(win.booktype.editor.historyURL + chapter + '/rev/' + revid);
      },

      showPage: function (pageid) {
        var page = parseInt(pageid) - 1;
        _show(page);
      }
    });

    var router = new HistoryRouter();

    var HistoryItem = Backbone.Model.extend({});

    var HistoryCollection = Backbone.PageableCollection.extend({
      model: HistoryItem,
      state: {
        firstPage: 0,
        pageSize: 15,
        sortKey: null
      }
    });

    var HistoryView = Backbone.View.extend({
      tmplRow : _.template('\
        <tr>\
          <td>\
            <%= verbose %> \
          </td>\
          <td><% if (has_link) { %><a href="#history/<%= link_url %>"><%= link_text %></a>\
          <% } else { %><%= link_text %><% } %></td>\
          <td><%= username %></td>\
          <td><%= modified %></td>\
        </tr>'
      ),
      tmplPage: _.template('\
        <% if (page === 0) { %>\
        <li <% if (isFirstPage) {%>class="disabled"<% } %>><a <% if (!isFirstPage) { %>href="#history/page/<%= state.currentPage %>"<% } %>>&laquo;</a></li>\
        <% } %>\
        <li <% if (isCurrent) { %>class="active"<% } %>>\
          <a href="#history/page/<%= page+1 %>"><%= page+1 %></a>\
        </li>\
        <% if (page === state.lastPage) { %>\
        <li <% if (isLastPage) {%>class="disabled"<% } %>><a <% if (!isLastPage) { %>href="#history/page/<%= state.currentPage+2 %>"<% } %>>&raquo;</a></li>\
        <% } %>'
      ),

      events: {
        'click #filterHistory': 'filterHistory',
        'click #clearHistory': 'clearHistory'
      },

      filterHistory: function () {
        var self = this;
        var params = {};
        params['user'] = $('input[name="user"]').val();
        params['chapter'] = $('input[name="chapter"]').val();

        win.booktype.ui.notify(win.booktype._('loading_data', 'Loading data.'));
        $.getJSON(win.booktype.editor.historyURL + '?' + $.param(params),
          function (data) {
            self.collection.fullCollection.reset(data);
            self.collection.reset(data);
            self.render({page: 0});
            router.navigate('history');
            win.booktype.ui.notify();
          }
        );
      },

      clearHistory: function () {
        var data = win.booktype.editor.historyData;
        
        // reset view collections data
        this.collection.fullCollection.reset(data);
        this.collection.reset(data);
        this.render({page: 0});

        // reset input filters
        _.each(this.filterElems, function (filter) {
          $(filter).select2('val', []);
        });
        
        // send navigation to history, just in case
        router.navigate('history');
      },

      render: function (params) {
        var $this = this;
        var page = params['page'];

        var rows = this.collection.getPage(page).map(function (item) {
          return $this.tmplRow(item.attributes);
        });

        this.$el.find('.historyTable tbody').html(rows.join(''));
        win.booktype.ui.notify();

        this.renderPagination();

        // enable tagging support for user input filter
        var userInputElem = this.$el.find('.history-filters input[name="user"]'),
          chapterInputElem = this.$el.find('.history-filters input[name="chapter"]');

        // initial arrays with values for tagging support
        var usersInitial = [],
            chaptersInitial = [];

        this.collection.fullCollection.map(function(item) {
          // pull users
          var username = item.get("username");
          if ($.inArray(username, usersInitial) === -1) usersInitial.push(username);

          // pull chapters
          if ( item.get('has_link') === true ) {
            var chapter = item.get("link_text")
            if ($.inArray(chapter, chaptersInitial) === -1) chaptersInitial.push(chapter);
          }
        });

        // enable tagging for users and chapters
        this.enableTagging(userInputElem, usersInitial);
        this.enableTagging(chapterInputElem, chaptersInitial);

        this.filterElems = [userInputElem, chapterInputElem];
        _.each(this.filterElems, function (elem) {
          $this.toggleClearFilters(elem);
        });

        return this;
      },

      renderPagination: function () {
        var $this = this,
            counter = 0,
            pages = [],
            paginator = $this.collection.state;

        while (counter < paginator.totalPages && paginator.totalPages > 1) {
          var params = {
            'page': counter,
            'isCurrent': (paginator.currentPage === counter),
            'isLastPage': (paginator.currentPage === paginator.lastPage),
            'isFirstPage': (paginator.currentPage === 0),
            'state': paginator
          };
          pages.push($this.tmplPage(params));
          counter++;
        }
        $('.pagination').html(pages.join(''));
        return this;
      },

      enableTagging: function (elem, init_values) {
        // add tagging support for filter inputs
        // param elem: current jquery element
        // param init_valus: array with some initial values that you want as suggestions
        elem.select2({
          tags: init_values
        });
      },

      toggleClearFilters: function (elem) {
        var self = this,
          filters = this.filterElems;

        elem.on('change', function () {
          var values = [];
          _.each(filters, function(filter) {
            var filter_values = $(filter).select2('val');

            _.each(filter_values, function (val) {
              values.push(val);
            });
          });

          if (values.length > 0) {
            self.$el.find('#clearHistory').removeAttr('disabled');
          } else {
            self.$el.find('#clearHistory').attr('disabled', true);
          }
        });
      }
    });

    var historyItems = new HistoryCollection([], { mode: 'client' });
    var historyView = null;

    var renderHeader = function () {
      var header = win.booktype.ui.getTemplate('templateHistoryHeader');
      $('DIV.contentHeader').html(header);
    };

    var _show = function (page) {
      var page = page || 0;
      win.booktype.ui.notify('Loading history');
      renderHeader();

      var t = win.booktype.ui.getTemplate('templateHistoryContent');
      $('#content').html(t);

      historyView = new HistoryView({collection: historyItems, el: $('#content')});
      if (win.booktype.editor.historyData.length > 0) {
        historyView.render({page: page});
      } else {
        $.getJSON(win.booktype.editor.historyURL,
          function (data) {
            win.booktype.editor.historyData = data;
            // set new data to collection
            historyView.collection.set(data);

            // order it before render
            historyView.collection.setSorting('modified', 1);
            historyView.collection.fullCollection.sort();

            // that's it, render
            historyView.render({page: page});
          }
        );
      }
    };

    var _showPage = function (page) {
      historyView.render({page: page});
    };

    var _hide = function (callback) {
      return callback();
    };

    var _init = function () {
      $('#button-history').on('change', function () { Backbone.history.navigate('history', true); });

      $(document).on('click', '#compare-chapter', function () {
        var target = $(this).data('target');
        var remote = $(this).data('compare-url');
        var rev1 = $('input[name="rev1"]:checked').val();
        var rev2 = $('input[name="rev2"]:checked').val();

        $(target).modal({
          'remote' : remote + '?rev1=' + rev1 + '&rev2=' + rev2
        });
      });

      // remove info from modal every time modal is closed
      $(document).on('hidden.bs.modal', '.cleanModalInfo', function () {
        $(this).removeData('bs.modal').html('');
      });
    };

    return {
      'init': _init,
      'show': _show,
      'router': router,
      'hide': _hide,
      'name': 'history'
    };
  })();

})(window, jQuery);