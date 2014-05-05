  define(['aloha', 'aloha/plugin', 'jquery',  'jquery19', 'ui/ui', 'aloha/ephemera', 'block/block', 'block/blockmanager', 'underscore', 'booktype', 'PubSub', 'toolbar/toolbar-plugin'], 
  		function(Aloha, Plugin, jQuery,  jQuery19, UI, Ephemera, block, BlockManager, _, booktype, PubSub, toolbar) {

        var TitleBlock = block.AbstractBlock.extend({
          title: 'Title',
          isDraggable: function() {return false;},

          init: function ($element, postProcessFn) {       
            $element.find('h1').addClass("aloha-editable");
            return postProcessFn();
          },

          update: function ($element, postProcessFn) {
            return postProcessFn();
          }
        });  

        var _checkEmptyParagraph = function () {
          var $editor = Aloha.getEditableById('contenteditor');

          if(!_.isUndefined($editor) && $editor && !_.isUndefined($editor.obj)) {
            var $elems = _.rest($editor.obj.children());
            
            var isEmpty = _.every(_.map($elems, function($node) { 
                return jQuery19.trim(jQuery($node).text()).length === 0;
            }));

            if(isEmpty) {
              $editor.obj.find('p').addClass('aloha-empty-paragraph');
            } else {
              $editor.obj.find('p').each(function(n, elem) {
                  var $elem = jQuery(elem);

                  $elem.removeClass('aloha-empty-paragraph');

                  if($elem.prop("class") === "")
                     $elem.removeAttr("class");
              });
            }
          }
        };

        var _mouseEnter = function() {
          jQuery("#contenteditor").addClass("aloha-mouse-over");

          _checkEmptyParagraph();
        };      

        var _mouseLeave = function() {
          jQuery("#contenteditor").removeClass("aloha-mouse-over");
        };

        var _initHeadings = function(editable, unmodify) {
          editable.obj.find('h1').each(function () {
            var $elem = jQuery(this);

            var $newParent = jQuery('<div class="aloha-book-title"></div>');
            $elem.wrap($newParent);

            var $parent = $elem.parent();

            $parent.alohaBlock({'aloha-block-type': 'TitleBlock'});

           if(!_.isUndefined(unmodify) && unmodify === true)
             editable.setUnmodified();

           return true;
        });          
      };




  			return Plugin.create('booktitle', {
  				defaultSettings: {
  					enabled: true
  			   	}, 
		      init: function () {
        	  var self = this;

            self.settings = jQuery.extend(true, self.defaultSettings, self.settings);			        	

	        	if(!self.settings.enabled) { return; }

				    Ephemera.attributes('data-aloha-block-type', 'contenteditable');
    					
            BlockManager.registerBlockType('TitleBlock', TitleBlock);

            var wasInHeading = false;

            // Undo action will setup new html for the editable. This will destory
            // all active blocks. We need to update them somehow. Undo will fire
            // certain event, we bind to this event and recreate all of our blocks again.
            Aloha.bind('aloha-my-undo', function (event, args) {
              _initHeadings(args.editable, false);
            });

            PubSub.sub('aloha.selection.context-change', function (evt, args) {
              // Check if there is no paragraph in the main editor. Create one if it is missing.
              var $editor = Aloha.getEditableById('contenteditor');

              if(!_.isUndefined($editor) && !_.isUndefined($editor.obj) && $editor.obj.find('p').length == 0) {
                $editor.obj.append('<p class="aloha-empty-paragraph"><br/></p>');
              }

              _checkEmptyParagraph();

              var $block = jQuery(evt.range.startContainer).closest('.aloha-block-TitleBlock');

              // List of buttons and menu items we want to manipulate with
              // This should be somehow configured in settings
              var _buttons = ['table-dropdown', 'alignLeft', 'alignRight',
                              'alignCenter', 'alignJustify', 'unorderedList', 
                              'insertImage', 'insertLink',
                              'orderedList', 'currentHeading', 'heading-dropdown'];
              var _menus = ['insertImage', 'insertLink', 'horizontalline', 'pbreak'];

              if($block.length > 0) {
                _.each(_buttons, function(btn) {
                  toolbar.disableToolbar(btn);
                });

                _.each(_menus, function(itm) {
                  toolbar.disableMenu(itm);
                })

                wasInHeading = true;
              } else if(wasInHeading) {
                _.each(_buttons, function(btn) {
                  toolbar.enableToolbar(btn);
                });
                
                _.each(_menus, function(itm) {
                  toolbar.enableMenu(itm);
                })

                wasInHeading = false;
              }

              if(!Aloha.activeEditable || !Aloha.activeEditable.obj) return;

              // We really want to create title blocks in the main editor. Ignore changes in
              // other editables.
              if(Aloha.activeEditable.obj.attr('id') != 'contenteditor') return;

              // Check if there is brand new heading. Initialise it if there is.
//              var $blocks = Aloha.activeEditable.obj.find(".aloha-book-title");
//              var $headings = Aloha.activeEditable.obj.find("h1");

              // if($headings.length > 0 && $blocks.length == 0)
              //   _initHeadings(Aloha.activeEditable, true);                 

              }
            );

            Aloha.bind('aloha-editable-destroyed', function($event, editable) {
               if(editable.obj && editable.obj.attr('id') == 'contenteditor') {
                   var $c = jQuery("#content");

                   $c.off('mouseleave', _mouseLeave);
                   $c.off('mouse', _mouseEnter);
               }
            });

            Aloha.bind('aloha-editable-created', function($event, editable) {
               _initHeadings(editable, true);

               if(editable.obj && editable.obj.attr('id') == 'contenteditor') {
                     var $c = jQuery("#content");

                     $c.on('mouseleave', _mouseLeave);
                     $c.on('mouseenter ', _mouseEnter);

                     _checkEmptyParagraph();
                }
            });

	        },		        
  				makeClean: function(obj) {
            jQuery(obj).find('.aloha-book-title').each(function () {
              var $elem = jQuery(this);
              $elem.replaceWith(jQuery('<h1>'+$elem.find('h1').text()+'</h1>'));
            });
          }
  		});
   }
);