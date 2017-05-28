(function (win, $) {
  'use strict';

  $.namespace('win.booktype.editor.history');
  var historyData = [];

  win.booktype.editor.history = (function () {

    var HistoryRouter = Backbone.Router.extend({
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
        $('#content').load(win.booktype.editor.historyURL + chapter + '/');
      },

      viewRevision: function (chapter, revid) {
        renderHeader();
        $('#content').load(win.booktype.editor.historyURL + chapter + '/rev/' + revid + '/');
      },

      showPage: function (pageid) {
        var page = parseInt(pageid, 10) - 1;
        var reloadData = false;
        _show(page, reloadData);
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
      tmplRow: _.template('\
        <tr>\
          <td>\
            <%= verbose %> \
          </td>\
          <td><% if (has_link) { %><a href="#history/<%= link_url %>"><%= link_text %></a>\
          <% } else { %><%= link_text %><% } %></td>\
          <td><%= username %></td>\
          <td><%= formatted %></td>\
        </tr>'),
      tmplPage: _.template('\
        <% if (page === 0) { %>\
        <li <% if (isFirstPage) {%>class="disabled"<% } %>><a <% if (!isFirstPage) { %>href="#history/page/<%= state.currentPage %>"<% } %>>&laquo;</a></li>\
        <% } %>\
        <% if(fill){ %>\
          <li class="disabled">\
            <a><%= page %></a> \
          </li>\
        <% }else{ %> \
          <li <% if (isCurrent) { %>class="active"<% } %>>\
            <a href="#history/page/<%= page+1 %>"><%= page+1 %></a>\
          </li>\
        <% } %>\
        <% if (page === state.lastPage) { %>\
        <li <% if (isLastPage) {%>class="disabled"<% } %>><a <% if (!isLastPage) { %>href="#history/page/<%= state.currentPage+2 %>"<% } %>>&raquo;</a></li>\
        <% } %>'),

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
            self.render({
              page: 0
            });
            router.navigate('history', false);
            win.booktype.ui.notify();
          }
        );
      },

      clearHistory: function () {
        var data = historyData;

        // reset view collections data
        this.collection.fullCollection.reset(data);
        this.collection.reset(data);
        this.render({
          page: 0
        });

        // reset input filters
        _.each(this.filterElems, function (filter) {
          $(filter).select2('val', []);
        });

        // send navigation to history, just in case
        router.navigate('history');
      },

      render: function (params) {
        win.booktype.ui.notify();

        var $this = this;
        var page = params['page'];
        var firstRender = params['firstRender'];

        var rows = this.collection.getPage(page).map(function (item) {
          return $this.tmplRow(item.attributes);
        });

        // elements for tagging support for user input filter
        var userInputElem = this.$el.find('.history-filters input[name="user"]'),
          chapterInputElem = this.$el.find('.history-filters input[name="chapter"]');

        // initial arrays with values for tagging support
        var usersInitial = [],
          chaptersInitial = [];

        // render history and pagination
        this.$el.find('.historyTable tbody').html(rows.join(''));
        this.renderPagination();

        if (firstRender === true) {
          this.collection.fullCollection.map(function (item) {
            // pull users
            var username = item.get('username');
            if ($.inArray(username, usersInitial) === -1) {
              usersInitial.push(username);
            }

            // pull chapters
            if (item.get('has_link') === true) {
              var chapter = item.get('link_text');
              if ($.inArray(chapter, chaptersInitial) === -1) {
                chaptersInitial.push(chapter);
              }
            }
          });

          // enable tagging for users and chapters
          this.enableTagging(userInputElem, usersInitial);
          this.enableTagging(chapterInputElem, chaptersInitial);

          this.filterElems = [userInputElem, chapterInputElem];
          _.each(this.filterElems, function (elem) {
            $this.toggleClearFilters(elem);
          });
        }

        return this;
      },

      renderPagination: function () {
        var $this = this,
          pages = [],
          adjacentPages = 2,
          paginator = $this.collection.state;


        var pageNumbers = _.range(paginator.currentPage - adjacentPages, paginator.currentPage + adjacentPages + 1);
        pageNumbers = _.filter(pageNumbers, function (page) {
          return page >= 0 && page < paginator.totalPages;
        });

        if (pageNumbers[0] !== 0) {
          pageNumbers.unshift(0);
        }

        if (paginator.totalPages > 1 && pageNumbers[1] !== 1) {
          if (pageNumbers[2] === 3) {
            pageNumbers.splice(1, 0, 1);
          } else {
            pageNumbers.splice(1, 0, '...');
          }
        }

        if (pageNumbers[pageNumbers.length - 1] !== paginator.lastPage) {
          pageNumbers.push(paginator.lastPage);
        }

        if (paginator.totalPages > 1 && pageNumbers[pageNumbers.length - 2] !== paginator.lastPage - 1) {
          if (pageNumbers[pageNumbers.length - 2] === pageNumbers[pageNumbers.length - 1] - 2) {
            pageNumbers.splice(pageNumbers.length - 1, 0, paginator.lastPage - 1);
          } else {
            pageNumbers.splice(pageNumbers.length - 1, 0, '...');
          }
        }

        _.each(pageNumbers, function (counter) {
          var params = {
            'page': counter,
            'fill': counter === '...',
            'isCurrent': (paginator.currentPage === counter),
            'isLastPage': (paginator.currentPage === paginator.lastPage),
            'isFirstPage': (paginator.currentPage === 0),
            'state': paginator
          };
          pages.push($this.tmplPage(params));
        });

        $('.pagination').html(pages.join(''));
        return this;
      },

      enableTagging: function (elem, initValues) {
        // add tagging support for filter inputs
        // param elem: current jquery element
        // param init_valus: array with some initial values that you want as suggestions

        // check if elements dont have select2 already activated
        if ($(elem).data('select2') === undefined) {
          elem.select2({
            tags: initValues
          });
        }

        // show buttons
        $('.history-filters button').removeClass('hide');
      },

      toggleClearFilters: function (elem) {
        var self = this,
          filters = this.filterElems;

        elem.on('change', function () {
          var values = [];

          _.each(filters, function (filter) {

            var filterValues = $(filter).select2('val');
            _.each(filterValues, function (val) {
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

    var historyItems = new HistoryCollection([], {
      mode: 'client'
    });
    var historyView = null;

    var renderHeader = function () {
      var header = win.booktype.ui.getTemplate('templateHistoryHeader');
      $('DIV.contentHeader').html(header);
    };

    var _show = function (page, reloadData) {
      $('#button-history').addClass('active');

      if (page === undefined) {
        page = 0;
      }
      if (reloadData === undefined) {
        reloadData = true;
      }

      var noContent = ($('#content').text().length === 0);
      if (historyData.length === 0 || noContent) {
        var t = win.booktype.ui.getTemplate('templateHistoryContent');
        $('#content').html(t);
      }

      win.booktype.ui.notify('Loading history');
      historyView = new HistoryView({
        collection: historyItems,
        el: $('#content')
      });
      if (historyData.length > 0 && reloadData === false) {
        historyView.render({
          page: page
        });
      } else {
        renderHeader();
        $.getJSON(win.booktype.editor.historyURL,
          function (data) {
            historyData = data;
            // set new data to collection
            historyView.collection.fullCollection.reset(data);
            historyView.collection.reset(data);

            // order it before render
            historyView.collection.setSorting('modified', 1);
            historyView.collection.fullCollection.sort();

            // that's it, render
            historyView.render({
              page: page,
              firstRender: true
            });
          }
        );
      }
    };

    var _hide = function (callback) {
      // Destroy tooltip
      $('DIV.contentHeader [rel=tooltip]').tooltip('destroy');
      $('#button-history').removeClass('active');

      // Clear content
      $('#content').empty();
      $('DIV.contentHeader').empty();

      if (!_.isUndefined(callback)) {
        callback();
      }
    };

    var _init = function () {
      $('#button-history').on('click', function () {
        Backbone.history.navigate('history', true);
      });

      $(document).on('click', '#compare-chapter', function () {
        var target = $(this).data('target');
        var remote = $(this).data('compare-url');
        var rev1 = $('input[name="rev1"]:checked').val();
        var rev2 = $('input[name="rev2"]:checked').val();

        var url = remote + '/' + rev1 + '/' + rev2 + '/';
        $(target)
          .load(url)
          .modal('show');
      });

      $(document).on('click', '.compare-chapter-new-tab', function () {
        var remote = $(this).data('compare-url'),
          rev1 = $('input[name="rev1"]:checked').val(),
          rev2 = $('input[name="rev2"]:checked').val();

        var url = remote + '/' + rev1 + '/' + rev2 + '/';
        var win = window.open(url, '_blank');
        win.focus();
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

  // use button tag as link with trigger url attribute
  $(document).on('click', 'button[data-href]', function () {
    var target = $(this).data('target');
    var url = $(this).data('href');
    if (target === '_blank') {
      var win = window.open(url, '_blank');
      win.focus();
    } else {
      window.location.href = url;
    }
  });

})(window, jQuery);
