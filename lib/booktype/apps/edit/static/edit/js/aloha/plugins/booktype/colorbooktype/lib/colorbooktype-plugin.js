define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'PubSub'],
  function (Aloha, Plugin, jQuery,  jQuery19, PubSub) {
    'use strict';

    var range = null;
    var editable = null;

    var changeColor = function (color) {
      range.select();

      Aloha.execCommand('forecolor', false, color);
    };
                                
    return Plugin.create('colorbooktype', {
      init: function () {
        jQuery19(document).on('booktype-ui-panel-active', function ($evt, name, panel) {
          if (name === 'edit') {
            editable = Aloha.getEditableById('contenteditor');

            //color picker
            jQuery('DIV.contentHeader .color-picker button').on('click', function ($event) {
              var color = jQuery(this).attr('data-color');

              changeColor(color);

              // publish message notification that change-color element was clicked
              PubSub.pub('toolbar.action.triggered', {'event': $event});
              return true;
            });

            var myColor = jQuery('DIV.contentHeader #myColor');

            var myPicker = new jscolor.color(myColor.get(0), {
              pickerSmartPosition: false,
              pickerOnfocus : false,
              pickerBorder: 0,
              pickerInset: 0,
              pickerFace: 8
            }, jQuery('DIV.contentHeader #pickerHolder').get(0));

            myPicker.fromString('000');

            myColor.on('change', function ($event) {
              changeColor('#' + myPicker.toString());

              // publish message notification that change-color element was clicked
              PubSub.pub('toolbar.action.triggered', {'event': $event});
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