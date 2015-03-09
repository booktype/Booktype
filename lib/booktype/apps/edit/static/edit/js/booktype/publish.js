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
  'use strict';

	jquery.namespace('win.booktype.editor.publish');

  win.booktype.editor.publish = (function () {


    var ExportModel = Backbone.Model.extend({
      defaults: {
          name: 'Export',
          formats: {},
          username: '',
          exported: ''
        }
      });

    var ExportView = Backbone.View.extend({
      tagName: 'div',
      className: 'box',

      events: {
        'click .dropdown-menu a': 'doOption'
      },

      doOption: function (event) {
        console.log('selected something');
      },

      initialize: function () {
        this.template = _.template(jquery('#templatePublishLine').html());
      },

      render: function () {
        this.$el.html(this.template(this.model.toJSON()));

        return this;
      },

      destoryView: function () {
        this.undelegateEvents();
        this.$el.removeData().unbind();
        this.remove();
        Backbone.View.prototype.remove.call(this);
      }
    });


    var ExportListView = Backbone.View.extend({
      el: 'div.publish_history',

      initialize: function () {
        this.template = _.template(jquery('#templatePublishHistory').html());
        this.render();
      },

      showProgress: function () {
        var $t = _.template(jquery('#templatePublishProgress').html());
        this.$el.prepend($t());
      },

      render: function () {
        var $this = this;

        $this.$el.empty();

        this.collection.each(function (expo) {
          var expoView = new ExportView({model: expo });
          expoView.render();
          $this.$el.append(expoView.$el);
        }, this);

        return this;
      },

      destoryView: function () {
        this.undelegateEvents();
        this.$el.removeData().unbind();
        this.remove();
        Backbone.View.prototype.remove.call(this);
      }
    });


    // A List of People
    var ExportCollection = Backbone.Collection.extend({
      model: ExportModel
    });

    var FilterView = Backbone.View.extend({
      el: '#publish-filter',
      events: {
        'click input[type=checkbox]': 'doCheckbox',
        'click button.btn-publish': 'doPublish'
      },

      initialize: function () {
        this.template = _.template(jquery('#templatePublishFilter').html());
      
        this.render();
        this.enableCheckboxes(true);
        this.enablePublish(false);
      },

      render: function () {
        this.$el.html(this.template({}));
      },

      enableCheckboxes: function (state) {
        if (state) {
          this.$el.find('input[type=checkbox]').removeAttr('disabled');
        } else {
          this.$el.find('input[type=checkbox]').prop('disabled', true);
        }
      },

      enablePublish: function (state) {
        if (state) {
          this.$el.find('button.btn-publish').attr('aria-disabled', true).removeClass('disabled');
        } else {
          this.$el.find('button.btn-publish').attr('aria-disabled', true).addClass('disabled');
        }
      },

      doPublish: function (event) {
        win.booktype.ui.notify('Publishing book');
        showProgress();
        this.enablePublish(false);
        this.enableCheckboxes(false);

        var formats = jquery.map(this.$el.find('input[type=checkbox]:checked'), function (v) { return jquery(v).attr('name'); });

        win.booktype.sendToCurrentBook({'command': 'publish_book',
          'book_id': win.booktype.currentBookID,
          'formats': formats},
          function (data) {
            if (data.result === false) {
              console.log('Some kind of error during the publishing');
              // Show some kind of error message
            }
            win.booktype.ui.notify();
          });

      },

      doCheckbox: function (event) {
        if (this.$el.find('input[type=checkbox]:checked').length === 0) {
          this.enablePublish(false);
        } else {
          this.enablePublish(true);
        }
      },
      destoryView: function () {
        this.undelegateEvents();
        this.$el.removeData().unbind();
        this.remove();
        Backbone.View.prototype.remove.call(this);
      }
    });

    var PublishRouter = Backbone.Router.extend({
      routes: {
        'publish': 'publish'
      },

      publish: function () {
        var activePanel = win.booktype.editor.getActivePanel();

        activePanel.hide(function () {
          win.booktype.editor.data.activePanel = win.booktype.editor.data.panels['publish'];
          win.booktype.editor.data.activePanel.show();
        });
      }
    });

    var router = new PublishRouter();
    var filterView = null;
    var exportList = null;
    var exportCollection = null;

    var showProgress = function () {
      exportList.showProgress();
    };

    /*******************************************************************************/
    /* SHOW                                                                        */
    /*******************************************************************************/

    var _show = function () {
      // set toolbar
      jquery('DIV.contentHeader').html(jquery('#templatePublishHeader').html());      
      jquery('#content').html(jquery('#templatePublishContent').html());

      exportCollection = new ExportCollection();

      filterView = new FilterView();
      exportList = new ExportListView({collection: exportCollection});

      // Show tooltips
      jquery('DIV.contentHeader [rel=tooltip]').tooltip({container: 'body'});

      window.scrollTo(0, 0);

      // Trigger events
      jquery(document).trigger('booktype-ui-panel-active', ['publish', this]);
    };

    /*******************************************************************************/
    /* HIDE                                                                        */
    /*******************************************************************************/

    var _hide = function (callback) {
      // Destroy tooltip
      jquery('DIV.contentHeader [rel=tooltip]').tooltip('destroy');


      filterView.destoryView();
      exportList.destoryView();

      // Clear content
      jquery('#content').empty();
      jquery('DIV.contentHeader').empty();

      if (!_.isUndefined(callback)) {
        callback();
      }
    };

    /*******************************************************************************/
    /* INIT                                                                        */
    /*******************************************************************************/

    var _init = function () {
      jquery('#button-publish').on('click', function (e) { Backbone.history.navigate('publish', true); });

      win.booktype.subscribeToChannel('/booktype/book/' + win.booktype.currentBookID + '/' + win.booktype.currentVersion + '/',
        function (message) {
          var funcs = {
            'book_published': function () {
              if (message.state === 'SUCCESS') {
                jquery('#content .publish_history .publishing-message').fadeOut().remove();

                exportCollection.add(new ExportModel({name: 'Export',
                  formats: message.urls,
                  username: message.username,
                  exported: message.exported}),
                  {at: 0});

                exportList.render();
                filterView.enableCheckboxes(true);

                if (jquery('#content input[type=checkbox]:checked').length !== 0) {
                  filterView.enablePublish(true);
                }
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
      'init': _init,
      'show': _show,
      'hide': _hide,
      'name': 'publish'
    };
  })();

  
})(window, jQuery, _);