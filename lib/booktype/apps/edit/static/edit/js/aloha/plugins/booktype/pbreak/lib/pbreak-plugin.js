define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', , 'underscore'], 
        function(Aloha, Plugin, jQuery,  jQuery19, UI, _) {

            var editable = null;
            var range = null;

            return Plugin.create('pbreak', {
                init: function () {

                   UI.adopt('pbreak', null, {
                      click: function() {        
                         editable = Aloha.activeEditable;
                         range = Aloha.Selection.getRangeObject();

                         var $a = jQuery('<p>(*)</p>');

                         GENTICS.Utils.Dom.insertIntoDOM($a, range, editable.obj);
                      }
                    });
                }
            });

        }
);