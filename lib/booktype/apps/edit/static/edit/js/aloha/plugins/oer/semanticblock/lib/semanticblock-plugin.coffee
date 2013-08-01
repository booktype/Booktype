define ['aloha', 'block/blockmanager', 'aloha/plugin', 'aloha/pluginmanager', 'jquery', 'aloha/ephemera', 'ui/ui', 'ui/button', 'css!semanticblock/css/semanticblock-plugin.css'], (Aloha, BlockManager, Plugin, pluginManager, jQuery, Ephemera, UI, Button) ->

  # hack to accomodate multiple executions
  return pluginManager.plugins.semanticblock  if pluginManager.plugins.semanticblock
  blockTemplate = jQuery('<div class="semantic-container"></div>')
  blockControls = jQuery('<div class="semantic-controls"><button class="semantic-delete" title="Remove this element."><i class="icon-remove"></i></button></div>')
  blockDragHelper = jQuery('<div class="semantic-drag-helper"><div class="title"></div><div class="body">Drag me to the desired location in the document</div></div>')
  activateHandlers = {}
  deactivateHandlers = {}
  pluginEvents = [
    name: 'mouseenter'
    selector: '.aloha-block-draghandle'
    callback: ->
      jQuery(this).parents('.semantic-container').addClass 'drag-active'
  ,
    name: 'mouseleave'
    selector: '.aloha-block-draghandle'
    callback: ->
      jQuery(this).parents('.semantic-container')
        .removeClass 'drag-active'  unless jQuery(this).parents('.semantic-container').is('.aloha-oer-dragging')
  ,
    name: 'mouseenter'
    selector: '.semantic-delete'
    callback: ->
      jQuery(this).parents('.semantic-container').addClass 'delete-hover'
  ,
    name: 'mouseleave'
    selector: '.semantic-delete'
    callback: ->
      jQuery(this).parents('.semantic-container').removeClass 'delete-hover'
  ,
    name: 'mousedown'
    selector: '.aloha-block-draghandle'
    callback: (e) ->
      e.preventDefault()
      jQuery(this).parents('.semantic-container').addClass 'aloha-oer-dragging', true
  ,
    name: 'mouseup'
    selector: '.aloha-block-draghandle'
    callback: ->
      jQuery(this).parents('.semantic-container').removeClass 'aloha-oer-dragging'
  ,
    name: 'click'
    selector: '.semantic-container .semantic-delete'
    callback: (e) ->
      e.preventDefault()
      jQuery(this).parents('.semantic-container').first().slideUp 'slow', ->
        jQuery(this).remove()
  ,
    name: 'mouseover'
    selector: '.semantic-container'
    callback: ->
      jQuery(this).parents('.semantic-container').removeClass('focused')
      jQuery(this).addClass('focused') unless jQuery(this).find('.focused').length
      jQuery(this).find('.aloha-block-handle').attr('title', 'Drag this element to another location.')
  ,
    name: 'mouseout'
    selector: '.semantic-container'
    callback: ->
      jQuery(this).removeClass('focused')
  ,
    # Toggle a class on elements so if they are empty and have placeholder text
    # the text shows up.
    # See the CSS file more info.
    name: 'blur'
    selector: '[placeholder],[hover-placeholder]'
    callback: ->
      $el = jQuery @
      # If the element does not contain any text (just empty paragraphs)
      # Clear the contents so `:empty` is true
      $el.empty() if not $el.text().trim()

      $el.toggleClass 'aloha-empty', $el.is(':empty')
  ]
  insertElement = (element) ->

  activate = (element) ->
    unless element.parent('.semantic-container').length or element.is('.semantic-container')
      element.addClass 'aloha-oer-block'
      element.wrap(blockTemplate).parent().append(blockControls.clone()).alohaBlock()
      
      for selector of activateHandlers
        if element.is(selector)
          activateHandlers[selector] element
          break

  deactivate = (element) ->
    if element.parent('.semantic-container').length or element.is('.semantic-container')
      element.removeClass 'aloha-oer-block ui-draggable'
      element.removeAttr 'style'

      for selector of deactivateHandlers
        if element.is(selector)
          deactivateHandlers[selector] element
          break
      element.siblings('.semantic-controls').remove()
      element.unwrap()

  bindEvents = (element) ->
    return  if element.data('oerBlocksInitialized')
    element.data 'oerBlocksInitialized', true
    event = undefined
    i = undefined
    i = 0
    while i < pluginEvents.length
      event = pluginEvents[i]
      element.on event.name, event.selector, event.callback
      i++

  cleanIds = (content) ->
    elements = content.find('[id]')
    ids = {}

    for i in [0..elements.length]
      element = jQuery(elements[i])
      id = element.attr('id')
      if ids[id]
        element.attr('id', '')
      else
        ids[id] = element

  Aloha.ready ->
    bindEvents jQuery(document)

  Plugin.create 'semanticblock',

    makeClean: (content) ->

      content.find('.semantic-container').each ->
        if jQuery(this).children().not('.semantic-controls').length == 0
          jQuery(this).remove()

      for selector of deactivateHandlers
        content.find(".aloha-oer-block#{selector}").each ->
          deactivate jQuery(this)

      cleanIds(content)

    init: ->
      # On activation add a `aloha-empty` class on all elements that:
      # - have a `placeholder` attribute
      # - and do not have any children
      #
      # See CSS for placeholder logic. This class is updated on blur.
      Aloha.bind 'aloha-editable-created', (e, params) =>
        jQuery('[placeholder],[hover-placeholder]').blur()

      Aloha.bind 'aloha-editable-created', (e, params) =>
        $root = params.obj

        # Add a `.aloha-oer-block` to all registered classes
        classes = []
        classes.push selector for selector of activateHandlers
        $root.find(classes.join()).each (i, el) ->
          $el = jQuery(el)
          $el.addClass 'aloha-oer-block' if not $el.parents('.semantic-drag-source')[0]
          activate $el

        if $root.is('.aloha-block-blocklevel-sortable') and not $root.parents('.aloha-editable').length

          # setting up these drag sources may break if there is more than one top level editable on the page
          jQuery('.semantic-drag-source').children().each ->
            element = jQuery(this)
            element.draggable
              connectToSortable: $root
              revert: 'invalid'
              helper: ->
                helper = jQuery(blockDragHelper).clone()
                helper.find('.title').text 'im a helper'
                helper

              start: (e, ui) ->
                $root.addClass 'aloha-block-dropzone'
                jQuery(ui.helper).addClass 'dragging'

              refreshPositions: true

          $root.sortable 'option', 'stop', (e, ui) ->
            $el = jQuery(ui.item)
            activate $el if $el.is(classes.join())

    insertAtCursor: (template) ->
      $element = jQuery(template)
      range = Aloha.Selection.getRangeObject()
      $element.addClass 'semantic-temp'
      GENTICS.Utils.Dom.insertIntoDOM $element, range, Aloha.activeEditable.obj
      $element = Aloha.jQuery('.semantic-temp').removeClass('semantic-temp')
      activate $element

    appendElement: ($element, target) ->
      $element.addClass 'semantic-temp'
      target.append $element
      $element = Aloha.jQuery('.semantic-temp').removeClass('semantic-temp')
      activate $element

    activateHandler: (selector, handler) ->
      activateHandlers[selector] = handler

    deactivateHandler: (selector, handler) ->
      deactivateHandlers[selector] = handler

    registerEvent: (name, selector, callback) ->
      pluginEvents.push
        name: name
        selector: selector
        callback: callback
