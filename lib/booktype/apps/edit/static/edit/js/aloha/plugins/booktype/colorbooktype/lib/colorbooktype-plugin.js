define(['aloha', 'aloha/plugin', 'jquery',  'jquery19'],
  function (Aloha, Plugin, jQuery,  jQuery19) {
    'use strict';

    var range = null;
    var editable = null;

    var changeColor = function (color) {
      range.select();

      Aloha.execCommand('forecolor', false, color);
    }
                                
    return Plugin.create('colorbooktype', {
      init: function () {
        jQuery19(document).on('booktype-ui-panel-active', function ($evt, name, panel) {
          if (name === 'edit') {
            editable = Aloha.getEditableById('contenteditor');

            //color picker
            jQuery('DIV.contentHeader .color-picker button').on('click', function (e) {
              var color = jQuery(this).attr('data-color');

              changeColor(color);
              return true;
            });

            var myPicker = new jscolor.color(jQuery('DIV.contentHeader #myColor').get(0), {
              pickerSmartPosition: false,
              pickerOnfocus : false,
              pickerBorder: 0,
              pickerInset: 0,
              pickerFace: 8
            }, jQuery('DIV.contentHeader #pickerHolder').get(0));

            myPicker.fromString('000');

            jQuery('DIV.contentHeader #myColor').on('change', function (e) {
                changeColor('#' + myPicker.toString());

                return false;
              });

            jQuery('.color-picker-item').click(function () {
                if (!$(this).hasClass('open')) {
                  range = Aloha.Selection.getRangeObject();

                  myPicker.showPicker();
                }
              });

          }

        });
      }
    });
  }
);