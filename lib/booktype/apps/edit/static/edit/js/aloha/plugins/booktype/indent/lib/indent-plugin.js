define(['aloha', 'aloha/plugin', 'jquery', 'ui/ui', 'underscore'],
  function (Aloha, Plugin, jquery,  UI, _) {
    'use strict';
    var changeNumber = function (fromUnit, toUnit) {
      // no centimeters - I have no idea how to convert them
      // the source for the values is http://reeddesign.co.uk/test/points-pixels.html
      var conversion = 1.0;
      if (fromUnit === 'px') {
        switch (toUnit) {
          case 'pt':
            conversion = 0.8571; // 6/7
            break;
          case 'em':
            conversion = 0.0625; // 1/16
            break;
          case '%':
            conversion = 6.25; // 50/8
            break;
        }
      }
      if (fromUnit === 'pt') {
        switch (toUnit) {
          case 'px':
            conversion = 1.3333; // 8/6
            break;
          case 'em':
            conversion = 0.08333; // 1/12
            break;
          case '%':
            conversion = 8.12; // 6/50
            break;
        }
      }
      if (fromUnit === '%') {
        switch (toUnit) {
          case 'pt':
            conversion = 8.3333; // 50/6
            break;
          case 'em':
            conversion = 0.01; // 1/100
            break;
          case 'px':
            conversion = 0.16; // 8/50
            break;
        }
      }
      if (fromUnit === 'em') {
        switch (toUnit) {
          case 'pt':
            conversion = 12;
            break;
          case '%':
            conversion = 100;
            break;
          case 'px':
            conversion = 16;
            break;
        }
      }
      return conversion;
    };

    function getUnit(invalue) {
      var unitValue = invalue.replace(/[\d\.,]/g, ''); // remove numbers
      if ((unitValue !== 'em') && (unitValue !== '%') && (unitValue !== 'px') && (unitValue !== 'pt')) {
        unitValue = 'px'; // if unit value is missing or is wrong - return px
      }
      return unitValue;
    }

    function increaseIndent(dataToAdd) {
      var userMarginText = '48px'; // default left margin value
      if (typeof Aloha.settings.plugins.indent !== 'undefined') {
        if (typeof Aloha.settings.plugins.indent.marginLeft !== 'undefined') {
          userMarginText = Aloha.settings.plugins.indent.marginLeft;
        }
      }
      var marginType = getUnit(userMarginText);
      var marginText = jquery(dataToAdd).prop('style').marginLeft;
      var currentMargin = parseFloat(marginText);
      if (isNaN(currentMargin)) {
        currentMargin = 0.0;
      }
      var pageUnitValue = getUnit(marginText);
      if (currentMargin === 0) {
        pageUnitValue = marginType; // if left-margin of the page is 0 use unit from settings
      }
      var newMarginValue = currentMargin * changeNumber(pageUnitValue, marginType) + parseFloat(userMarginText);
      jquery(dataToAdd).css('margin-left', newMarginValue + marginType);
    }

    function decreaseIndent(dataToAdd) {
      var userMarginText = '48px'; // default left margin value                    
      if (typeof Aloha.settings.plugins.indent !== 'undefined') {
        if (typeof Aloha.settings.plugins.indent.marginLeft !== 'undefined') {
          userMarginText = Aloha.settings.plugins.indent.marginLeft;
        }
      }
      var marginText = jquery(dataToAdd).prop('style').marginLeft;
      var currentMargin = parseFloat(marginText);
      var marginType = getUnit(marginText);
      if (isNaN(currentMargin)) {
        currentMargin = 0.0;
      }
      var pageUnitValue = getUnit(marginText);
      if (currentMargin === 0) {
        pageUnitValue = marginType; // if left-margin of the page is 0 use unit from settings
      }
      if (currentMargin * changeNumber(pageUnitValue, marginType) >= parseFloat(userMarginText)) {
        var newMarginValue = currentMargin * changeNumber(pageUnitValue, marginType) - parseFloat(userMarginText);
        jquery(dataToAdd).css('margin-left', newMarginValue + marginType);
      }
    }

    var foundGoodParent = function (node) {
      if (node && _.contains(['SPAN', 'A', 'B', 'I', 'U', 'SUP', 'SUB'], node.tagName)) {
        node = foundGoodParent(node.parentNode);
      }

      return node;
    };

    return Plugin.create('indent', {
      init: function () {
        UI.adopt('indent-right', null, { // increase indent
          click: function () {
            var range = Aloha.Selection.getRangeObject();
            var rangeObject = range.getSelectionTree();
            var startContainer = range.startContainer.parentElement;
            var endContainer = range.endContainer.parentElement;

            var $dataToAdd = jquery();

            if (startContainer === endContainer) {
              $dataToAdd = foundGoodParent(rangeObject[0].domobj.parentNode);
              increaseIndent($dataToAdd);
            } else {
              jquery.each(rangeObject, function (cnt, el) {
                if (el.selection !== 'none') {
                  $dataToAdd = el.domobj;
                  increaseIndent($dataToAdd);
                }
              });
            }
          }
        });

        UI.adopt('indent-left', null, { // decrease indent
          click: function () {
            var range = Aloha.Selection.getRangeObject();
            var rangeObject = range.getSelectionTree();
            var startContainer = range.startContainer.parentElement;
            var endContainer = range.endContainer.parentElement;

            var $dataToAdd = jquery();

            if (startContainer === endContainer) {
              $dataToAdd = foundGoodParent(rangeObject[0].domobj.parentNode);
              decreaseIndent($dataToAdd);
            } else {
              jquery.each(rangeObject, function (cnt, el) {
                if (el.selection !== 'none') {
                  $dataToAdd = el.domobj;
                  decreaseIndent($dataToAdd);
                }
              });
            }
          }
        });
      }
    });
});