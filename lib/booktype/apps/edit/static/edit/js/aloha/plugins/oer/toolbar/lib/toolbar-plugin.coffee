define [ 'jquery', 'aloha', 'aloha/plugin', 'ui/ui', 'PubSub' ], (
    jQuery, Aloha, Plugin, Ui, PubSub) ->

  squirreledEditable = null
  $ROOT = jQuery('body') # Could also be configured to some other div

  makeItemRelay = (slot) ->
    # This class adapts button functions Aloha expects to functions the toolbar
    # uses
    class ItemRelay
      constructor: () ->
      show: () -> $ROOT.find(".action.#{slot}").removeClass('hidden')
      hide: () -> #$ROOT.find(".action.#{slot}").addClass('hidden')
      setActive: (bool) ->
        $ROOT.find(".action.#{slot}").removeClass('active') if not bool
        $ROOT.find(".action.#{slot}").addClass('active') if bool
      setState: (bool) -> @setActive bool
      enable: (bool=true) ->
        # If it is a button, set the disabled attribute, otherwise find the
        # parent list item and set disabled on that.
        if $ROOT.find(".action.#{slot}").is('.btn')
          $ROOT.find(".action.#{slot}").attr('disabled', 'disabled') if !bool
          $ROOT.find(".action.#{slot}").removeAttr('disabled') if bool
        else
          $ROOT.find(".action.#{slot}").parent().addClass('disabled') if !bool
          $ROOT.find(".action.#{slot}").parent().removeClass('disabled') if bool
      disable: () -> @enable(false)
      setActiveButton: (a, b) ->
        console && console.log "#{slot} TODO:SETACTIVEBUTTON:", a, b
      focus: (a) ->
        console && console.log "#{slot} TODO:FOCUS:", a
      foreground: (a) ->
        console && console.log "#{slot} TODO:FOREGROUND:", a
    return new ItemRelay()


  # Store `{ actionName: action() }` object so we can bind all the clicks when we init the plugin
  adoptedActions = {}

  # Hijack the toolbar buttons so we can customize where they are placed.
  Ui.adopt = (slot, type, settings) ->
    # publish an adoption event, if item finds a home, return the
    # constructed component
    evt = $.Event('aloha.toolbar.adopt')
    $.extend(evt,
        params:
            slot: slot,
            type: type,
            settings: settings
        component: null)
    PubSub.pub(evt.type, evt)
    if evt.isDefaultPrevented()
      evt.component.adoptParent(toolbar)
      return evt.component

    adoptedActions[slot] = settings
    return makeItemRelay slot


  # Delegate toolbar actions once all the plugins have initialized and called `UI.adopt`
  Aloha.bind 'aloha-ready', (event, editable) ->
    jQuery.each adoptedActions, (slot, settings) ->

      selector = ".action.#{slot}"
      $ROOT.on 'click', selector, (evt) ->
        evt.preventDefault()
        Aloha.activeEditable = Aloha.activeEditable or squirreledEditable
        # The Table plugin requires this.element to work so it can pop open a
        # window that selects the number of rows and columns
        # Also, that's the reason for the bind(@)
        $target = jQuery(evt.target)
        if not ($target.is(':disabled') or $target.parent().is('.disabled'))
          @element = @
          settings.click.bind(@)(evt)
      if settings.preview
        $ROOT.on 'mouseenter', selector, (evt) ->
          $target = jQuery(evt.target)
          if not ($target.is(':disabled') or $target.parent().is('.disabled'))
            settings.preview.bind(@)(evt)
      if settings.unpreview
        $ROOT.on 'mouseleave', selector, (evt) ->
          $target = jQuery(evt.target)
          if not ($target.is(':disabled') or $target.parent().is('.disabled'))
            settings.unpreview.bind(@)(evt)

  ###
   register the plugin with unique name
  ###
  Plugin.create "toolbar",
    init: ->

      toolbar = @

      changeHeading = (evt) ->
        evt.preventDefault()
        $el = jQuery(@)
        hTag = $el.attr('data-tagname')
        rangeObject = Aloha.Selection.getRangeObject()
        GENTICS.Utils.Dom.extendToWord rangeObject  if rangeObject.isCollapsed()

        Aloha.Selection.changeMarkupOnSelection Aloha.jQuery("<#{hTag}></#{hTag}>")
        # Change the label for the Heading button to match the newly selected formatting
        jQuery('.currentHeading')[0].innerHTML = $el[0].innerHTML
        # Attach the id and classes back onto the new element
        $oldEl = Aloha.jQuery(rangeObject.getCommonAncestorContainer())
        $newEl = Aloha.jQuery(Aloha.Selection.getRangeObject().getCommonAncestorContainer())
        $newEl.addClass($oldEl.attr('class'))
        # $newEl.attr('id', $oldEl.attr('id))
        # Setting the id is commented because otherwise collaboration wouldn't register a change in the document

      $ROOT.on 'click', '.action.changeHeading', changeHeading

      # Stop mousedown events from propagating to aloha's handler, which will
      # cause the editor to deactivate.
      $ROOT.on 'mousedown', ".action", (evt) ->
        evt.stopPropagation()

      Aloha.bind 'aloha-editable-activated', (event, data) ->
        squirreledEditable = data.editable

      PubSub.sub 'aloha.selection.context-change', (data) ->
        el = data.range.commonAncestorContainer
        # Use the first button in the headings area
        button = $ROOT.find('.headings button').first()
        currentHeading = $ROOT.find('.headings .currentHeading')
        headings = $ROOT.find('.action.changeHeading')
        tagnames = []
        headings.each () ->
          tagnames.push($(this).attr('data-tagname').toUpperCase())

        # Figure out if we are in any particular heading
        h = $(el).parentsUntil('.aloha-editable').andSelf()
        h = h.filter(tagnames.join(',')).first()

        if not h.length
          button.prop('disabled', true)
          currentHeading.html(headings.first().text())
        else
          button.prop('disabled', false)
          active = $.grep headings, (elem, i) ->
            $(elem).attr('data-tagname').toUpperCase()==h[0].tagName
          if active.length
            currentHeading.html($(active[0]).html())
          else
            currentHeading.html(headings.first().text())

    # Components of which we are the parent (not buttons) will call
    # these when they are activated. Change it into an event so it can
    # be implemented elsewhere.
    childVisible: (childComponent, visible) ->
        # publish an event
        evt = $.Event('aloha.toolbar.childvisible')
        evt.component = childComponent
        evt.visible = visible
        PubSub.pub(evt.type, evt)
    childFocus: (childComponent) ->
        # publish an event
        evt = $.Event('aloha.toolbar.childfocus')
        evt.component = childComponent
        PubSub.pub(evt.type, evt)
    childForeground: (childComponent) ->
        # publish an event
        evt = $.Event('aloha.toolbar.childforeground')
        evt.component = childComponent
        PubSub.pub(evt.type, evt)

    ###
     toString method
    ###
    toString: ->
      "toolbar"
