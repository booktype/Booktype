/*
  This file is part of Booktype.
  Copyright (c) 2015 Aleksandar Erkalovic <aleksandar.erkalovic@sourcefabric.org>
 
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

  jquery.namespace('win.booktype.editor.themes');

  win.booktype.editor.themes = (function () {

    var _customData = {};

    var resetValues = function () {
      var $tab = jquery("section[source_id=style-tab]");

      // Alignment fix
      jquery('.heading-align label', $tab).removeClass('active');
      jquery('.heading-align input[data-align="left"]', $tab).parent().addClass('active');

      jquery('select.heading-font option[value=serif]', $tab).prop('selected', true);
      jquery('select.paragraph-font option[value=serif]', $tab).prop('selected', true);

      jquery('.heading-size', $tab).data('slider').setValue(18);

      jquery('.paragraph-indent', $tab).data('slider').setValue(0);
      jquery('.paragraph-line-height', $tab).data('slider').setValue(100);
      jquery('.color', $tab).get(0).color.fromString('000000');            
    };


    var getStyleData = function () {
      var $tab = jquery("section[source_id=style-tab]");
      var data = {};

      // Values
      var slider = jquery('.heading-size', $tab).data('slider');

      if (_.isUndefined(slider)) {
        return data;
      }
      data.fontSizeH1 = slider.getValue();
      data.fontH1 = jquery('select.heading-font option:selected', $tab).val();
      data.alignH1 = jquery('.heading-align input[name=align]:checked', $tab).attr('data-align');
      data.colorH1 = jquery('.color', $tab).get(0).color;

      if (_.isUndefined(data.colorH1)) {
        data.colorH1 = '000000';
      } else {
        data.colorH1 = data.colorH1.toString();
      }      

      data.indentP = jquery('.paragraph-indent', $tab).data('slider').getValue();
      data.lineHeightP = jquery('.paragraph-line-height', $tab).data('slider').getValue();
      data.fontP = jquery('select.paragraph-font option:selected', $tab).val();
      data.alignP = jquery('.paragraph-align input[name=align]:checked', $tab).attr('data-align');

      if (data.fontSizeH1 < 100) {
        data.fontSizeH1 = 100 + (data.fontSizeH1 - 12) * 10;
      }

      data.fontSizeH2 = data.fontSizeH1 - 20;
      data.fontSizeH3 = data.fontSizeH1 - 40;
      data.fontSizeH4 = data.fontSizeH1 - 60;

      return data;
    };


    var styleUpdated = function () {
      var $tab = jquery("section[source_id=style-tab]");
      var data = getStyleData();

      if (_.keys(data).length === 0) {
        return;
      }
      // Set values
      if (!_.isUndefined(data.fontSizeH1)) {
        jquery('.heading-view-size', $tab).text(data.fontSizeH1 + '%');
      }

      if (!_.isUndefined(data.indentP)) {
        jquery('.paragraph-view-indent', $tab).text(data.indentP.toFixed(2) + 'em');
      }
      if (!_.isUndefined(data.lineHeightP)) {
        jquery('.paragraph-view-line-height', $tab).text(data.lineHeightP + '%');
      }

      // CSS TEXT
      var s = jquery('#embedUserStyleTemplate').html();

      s += s.replace(/#contenteditor/g, '#contentrevision');
      
      var cssTemplate = _.template(s);
      var cssText = cssTemplate(data);

      jquery("#embeduserstyle").text(cssText);
      _customData = data;

      win.booktype.sendToCurrentBook({
        'command': 'save_custom_theme',
        'custom': data
      }, function (datum) {
      });      
    };


    var _sel = function ($this) {
      var styleName = $this.prop('value');
      var $tab = jquery('section[source_id=style-tab]');

      $tab.find('.style-option').hide();

      // Change this

      if (styleName === 'custom') {
        jquery("section[source_id=style-tab] .reset-button").show();

        styleUpdated();
      } else {
        jquery("#embeduserstyle").empty();
        jquery("section[source_id=style-tab] .reset-button").hide();
      }

      jquery("#style-option-" + styleName).show();
    };


    var setTheme = function (themeName) {
      win.booktype.editor.data.activeTheme = themeName;

      jquery('#styleoptions').val(themeName);
      _sel(jquery('#styleoptions'));

      var styleUrlTemplate = '%s/static/themes/%s/editor.css';

      if (win.booktype.externalStaticCache) {
        styleUrlTemplate += '?v=' + win.booktype.externalStaticCacheKey
      }

      var styleURL = _.sprintf(styleUrlTemplate, win.booktype.baseURL, themeName);

      jquery('#aloha-embeded-style').attr('href', styleURL);

      jquery(document).trigger('booktype-style-changed', [themeName]);
    };


    var saveTheme = function (themeName) {
      win.booktype.sendToCurrentBook({
        'command': 'set_theme',
        'theme': themeName
      }, function (datum) {
      });
    };


    var initPanel = function ($tab) {
      if (!_.isUndefined(win.booktype.editor.data.settings.config['themes']['active'])) {
      }

      if (win.booktype.editor.data.settings.config['themes']['has_custom']) {
        jquery('.reset-button', $tab).on('click', function () {
          resetValues();
          styleUpdated();
        });

        // Custom style modifications
        jquery(".heading-font", $tab).on('change', function (e) { 
          styleUpdated();
        });

        jquery(".paragraph-font", $tab).on('change', function (e) { 
          styleUpdated();
        });

        jquery(".heading-align input[type=radio]", $tab).on('change', function (e) { 
          styleUpdated();
        });

        jquery(".paragraph-align input[type=radio]", $tab).on('change', function (e) { 
          styleUpdated();
        });

        jquery('.paragraph-line-height', $tab).slider().on('slideStop', function (evt) {
          styleUpdated();
        });

        jquery('.paragraph-indent', $tab).slider().on('slideStop', function (evt) {
          styleUpdated();
        });

        jquery('.paragraph-indent', $tab).data('slider').setValue(0.0);

        jquery('.heading-size', $tab).slider().on('slideStop', function (evt) {
          styleUpdated();
        });

        jquery('.paragraph-size', $tab).slider().on('slideStop', function (evt) {
          styleUpdated();
        });

        jquery('.color', $tab).on('change', function (e) {
          styleUpdated();
        });      
        jquery('.heading-align label', $tab).removeClass('active');
        if (!_.isUndefined(_customData.alignH1)) {
          jquery('.heading-align input[data-align="' + _customData.alignH1 + '"]', $tab).parent().addClass('active');
          jquery('.heading-align input[data-align="' + _customData.alignH1 + '"]', $tab).attr('checked', 'checked');
        }

        if (!_.isUndefined(_customData.H1)) {
          jquery('select.heading-font option[value=' + _customData.fontH1 + ']', $tab).prop('selected', true);
        }

        if (!_.isUndefined(_customData.fontP)) {
          jquery('select.paragraph-font option[value=' + _customData.fontP + ']', $tab).prop('selected', true);
        }

        if (!_.isUndefined(_customData.fontSizeH1)) {
          if (_customData.fontSizeH1 < 100) {
            _customData.fontSizeH1 = 100 + (_customData.fontSizeH1 - 12) * 10;
          }

         jquery('.heading-size', $tab).data('slider').setValue(_customData.fontSizeH1);
        }

        if (!_.isUndefined(_customData.indentP)) {
          jquery('.paragraph-indent', $tab).data('slider').setValue(_customData.indentP);
        }

        if (!_.isUndefined(_customData.lineHeightP)) {
          jquery('.paragraph-line-height', $tab).data('slider').setValue(_customData.lineHeightP);
        }

        var $jq = jquery('.color', $tab).get(0);

        if (!_.isUndefined($jq)) {
          if (!_.isUndefined($jq.color)) {
            if (!_.isUndefined(_customData.colorH1)) {
              $jq.color.fromString(_customData.colorH1);
            }
          }
        }        
      }

      // Change style
      jquery('#styleoptions').on('change', function (e) {
        var $this = jquery(this);
        var styleName = $this.prop('value');

        setTheme(styleName);
        saveTheme(styleName);
      });

      // Set loaded values

      setTheme(win.booktype.editor.data.activeTheme);
    };

    var setCustom = function (data) {      
      _customData = data;
    };

    var activatePanel = function () {

    };


    return {
      'initPanel': initPanel,
      'activatePanel': activatePanel,
      'styleUpdated': styleUpdated,
      'setTheme': setTheme,
      'saveTheme': saveTheme,
      'setCustom': setCustom
    };
  })();

})(window, jQuery, _);
