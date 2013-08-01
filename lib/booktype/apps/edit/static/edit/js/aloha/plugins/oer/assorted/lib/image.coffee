# Aloha Image Plugin
# * -----------------
# * This plugin handles when the insertImage button is clicked and provides a bubble next to an image when it is selected
#
define ['aloha', 'jquery', 'aloha/plugin', 'image/image-plugin', 'ui/ui', 'semanticblock/semanticblock-plugin', 'css!assorted/css/image.css'], (Aloha, jQuery, AlohaPlugin, Image, UI, semanticBlock) ->

  # This will be prefixed with Aloha.settings.baseUrl
  WARNING_IMAGE_PATH = '/../plugins/oer/image/img/warning.png'

  DIALOG_HTML = '''
    <form class="plugin image modal hide fade" id="linkModal" tabindex="-1" role="dialog" aria-labelledby="linkModalLabel" aria-hidden="true" data-backdrop="false">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
        <h3>Insert image</h3>
      </div>
      <div class="modal-body">
        <div class="image-options">
            <a class="upload-image-link">Choose an image to upload</a> OR <a class="upload-url-link">get image from the Web</a>
            <div class="placeholder preview hide">
              <h4>Preview</h4>
              <img class="preview-image"/>
            </div>
            <input type="file" class="upload-image-input" />
            <input type="url" class="upload-url-input" placeholder="Enter URL of image ..."/>
        </div>
        <div class="image-alt">
          <div class="forminfo">
            <i class="icon-warning"></i><strong>Describe the image for someone who cannot see it.</strong> This description can be read aloud, making it possible for visually impaired learners to understand the content.
          </div>
          <div>
            <textarea name="alt" type="text" placeholder="Enter description ..."></textarea>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button type="submit" disabled="true" class="btn btn-primary action insert">Save</button>
        <button class="btn action cancel">Cancel</button>
      </div>
    </form>'''

  showModalDialog = ($el) ->
      settings = Aloha.require('assorted/assorted-plugin').settings
      root = Aloha.activeEditable.obj
      dialog = jQuery(DIALOG_HTML)

      # Find the dynamic modal elements and bind events to the buttons
      $placeholder = dialog.find('.placeholder.preview')
      $uploadImage = dialog.find('.upload-image-input').hide()
      $uploadUrl =   dialog.find('.upload-url-input').hide()
      $submit = dialog.find('.action.insert')

      # If we're editing an image pull in the src.
      # It will be undefined if this is a new image.
      #
      # This variable is updated when one of the following occurs:
      # * selects an image from the filesystem
      # * enters a URL (TODO: Verify it's an image)
      # * drops an image into the drop div

      # On submit $el.attr('src') will point to what is set in this variable
      # preserve the alt text if editing an image
      imageSource = $el.attr('src')
      imageAltText = $el.attr('alt')

      if imageSource
        dialog.find('.action.insert').removeAttr('disabled')

      editing = Boolean(imageSource)

      dialog.find('[name=alt]').val(imageAltText)

      if /^https?:\/\//.test(imageSource)
        $uploadUrl.val(imageSource)
        $uploadUrl.show()

      # Set onerror of preview image
      ((img, baseurl) ->
        img.onerror = ->
          errimg = baseurl + WARNING_IMAGE_PATH
          img.src = errimg unless img.src is errimg
      ) dialog.find('.placeholder.preview img')[0], Aloha.settings.baseUrl

      setImageSource = (href) ->
        imageSource = href
        $submit.removeAttr('disabled')

      # Uses the File API to render a preview of the image
      # and updates the modal's imageSource
      loadLocalFile = (file, $img, callback) ->
        reader = new FileReader()
        reader.onloadend = () ->
          $img.attr('src', reader.result) if $img
          # If we get an image then update the modal's imageSource
          setImageSource(reader.result)
          callback(reader.result) if callback
        reader.readAsDataURL(file)

      # Add click handlers
      dialog.find('.upload-image-link').on 'click', (evt) ->
        evt.preventDefault()
        $placeholder.hide()
        $uploadUrl.hide()
        $uploadImage.click()
        $uploadImage.show()

      dialog.find('.upload-url-link').on 'click', (evt) ->
        evt.preventDefault()
        $placeholder.hide()
        $uploadImage.hide()
        $uploadUrl.show()

      $uploadImage.on 'change', () ->
        files = $uploadImage[0].files
        # Parse the file and if it's an image set the imageSource
        if files.length > 0
          if settings.image.preview
            $previewImg = $placeholder.find('img')
            loadLocalFile files[0], $previewImg
            $placeholder.show()
          else
            loadLocalFile files[0]

      $uploadUrl.on 'change', () ->
        $previewImg = $placeholder.find('img')
        url = $uploadUrl.val()
        setImageSource(url)
        if settings.image.preview
          $previewImg.attr 'src', url
          $placeholder.show()

      # On save update the actual img tag. Use the submit event because this
      # allows the use of html5 validation.
      deferred = $.Deferred()
      dialog.on 'submit', (evt) =>
        evt.preventDefault() # Don't submit the form

        altAdded = (not $el.attr 'alt') and dialog.find('[name=alt]').val()

        $el.attr 'src', imageSource
        $el.attr 'alt', dialog.find('[name=alt]').val()

        if altAdded
          setThankYou $el.parent()
        else
          setEditText $el.parent()

        deferred.resolve(target: $el[0], files: $uploadImage[0].files)
        $el.parents('.media').removeClass('aloha-ephemera')
        dialog.modal('hide')

      dialog.on 'click', '.btn.action.cancel', (evt) =>
        evt.preventDefault() # Don't submit the form
        $el.parents('.semantic-container').remove() unless editing
        deferred.reject(target: $el[0])
        dialog.modal('hide')

      dialog.on 'hidden', (event) ->
        # If hidden without being confirmed/cancelled, reject
        if deferred.state()=='pending'
          deferred.reject(target: $el[0])
        # Clean up after dialog was hidden
        dialog.remove()

      # Return promise, with an added show method
      jQuery.extend true, deferred.promise(),
        show: (title) ->
            if title
              dialog.find('.modal-header h3').text(title)
            dialog.modal 'show'

  uploadImage = (file, callback) ->
    plugin = @
    settings = Aloha.require('assorted/assorted-plugin').settings
    xhr = new XMLHttpRequest()
    if xhr.upload
      if not settings.image.uploadurl
        throw new Error("uploadurl not defined")

      xhr.onload = () ->
        if settings.image.parseresponse
          url = parseresponse(xhr)
        else
          url = JSON.parse(xhr.response).url
        callback(url)

      xhr.open("POST", settings.image.uploadurl, true)
      xhr.setRequestHeader("Cache-Control", "no-cache")
      f = new FormData()
      f.append(settings.image.uploadfield or 'upload', file, file.name)
      xhr.send(f)

  UI.adopt 'insertImage-oer', null,
    click: () ->
      template = $('<span class="media aloha-ephemera"><img /></span>')
      semanticBlock.insertAtCursor(template)
      newEl = template.find('img')
      promise = showModalDialog(newEl)

      promise.done (data)->
        # Uploading if a local file was chosen
        if data.files.length
          newEl.addClass('aloha-image-uploading')
          uploadImage data.files[0], (url) ->
            jQuery(data.target).attr('src', url)
            newEl.removeClass('aloha-image-uploading')

      # Finally show the dialog
      promise.show()

  $('body').bind 'aloha-image-resize', ->
    setWidth Image.imageObj

  setWidth = (image) ->
    wrapper = image.parents('.image-wrapper')
    if wrapper.length
      wrapper.css('width', image.css('width'))

  setThankYou = (wrapper) ->
    editDiv = wrapper.children('.image-edit')
    editDiv.html('<i class="icon-edit"></i> Thank You!').removeClass('passive')
    editDiv.css('background', 'lightgreen')
    editDiv.animate({backgroundColor: 'white', opacity: 0}, 2000, 'swing', -> setEditText wrapper)

  setEditText = (wrapper) ->
    alt = wrapper.children('img').attr('alt')
    editDiv = wrapper.children('.image-edit').css('opacity', 1)
    if alt
        editDiv.html('<i class="icon-edit"></i>').addClass('passive')
    else
        editDiv.html('<i class="icon-warning"></i><span class="warning-text">Description missing</span>').removeClass('passive')
 
  activate = (element) ->
    wrapper = $('<div class="image-wrapper">').css('width', element.css('width'))
    edit = $('<div class="image-edit">')

    img = element.find('img')
    element.children().remove()

    img.appendTo(element).wrap(wrapper)

    setEditText element.children('.image-wrapper').prepend(edit)
    element.find('img').load ->
      setWidth $(this)

  deactivate = (element) ->
    img = element.find('img')
    element.children().remove()
    element.append(img)
    element.attr('data-alt', img.attr('alt') || '')

    # wrap the whole thing in a paragraph just so it passes the server's validation rules
    element.parents('.semantic-container').wrap('<p>')

  # Return config
  AlohaPlugin.create('oer-image', {
    init: () ->
      semanticBlock.activateHandler('.media', activate)
      semanticBlock.deactivateHandler('.media', deactivate)
      semanticBlock.registerEvent 'click', '.aloha-oer-block .image-edit', ->
        img = $(this).siblings('img')
        promise = showModalDialog(img)
        promise.show('Edit image')
  })
